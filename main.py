import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv  # Load environment variables from a .env file
import openai
from pinecone import Pinecone, ServerlessSpec

# Load environment variables from the .env file
load_dotenv()

# Retrieve environment variables
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "your-index-name")
# Set the OpenAI API key for generating embeddings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client using the latest API
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize Pinecone client using the new API
pc = Pinecone(api_key=PINECONE_API_KEY)

# Get the Pinecone index instance
index = pc.Index(INDEX_NAME)

# Define the request body schema
class MarkdownData(BaseModel):
    filename: str
    content: str

def split_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Splits the input text into chunks of specified size with overlap.
    This is useful when processing large files.
    """
    chunks = []
    start = 0
    text_length = len(text)
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap  # Shift start index to allow overlap
    return chunks

def get_embedding(text: str, model: str = "text-embedding-3-small"):
    """
    Retrieves the vector embedding for the given text using OpenAI's API.
    """
    try:
        response = openai_client.embeddings.create(input=text, model=model)
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        raise RuntimeError(f"Error obtaining embedding: {e}")

app = FastAPI()

@app.post("/upload")
async def upload_markdown(data: MarkdownData):
    filename = data.filename.strip()
    filename_escaped = filename.encode('unicode_escape').decode('utf-8')
    content = data.content

    if not filename or not content:
        raise HTTPException(status_code=400, detail="Both 'filename' and 'content' are required.")

    # Delete any existing vectors that have the same filename to replace old data.
    try:
        # TODO: it doesn't work due to SDK's bug
        index.delete(filter={"filename": {"$eq": filename}})
    except Exception as e:
        # Log deletion error; ignore if no data exists.
        print(f"Error during deletion (ignored): {e}")

    # If content is large, split it into chunks; otherwise, use the content as a single chunk.
    CHUNK_SIZE = 1000  # Adjust as necessary
    if len(content) > CHUNK_SIZE:
        chunks = split_text(content, chunk_size=CHUNK_SIZE, overlap=200)
    else:
        chunks = [content]

    # Generate embeddings for each chunk and prepare vectors for upsert.
    vectors = []
    for i, chunk in enumerate(chunks):
        try:
            embedding = get_embedding(chunk)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")
        # Create a unique vector ID using the filename and chunk index.
        vector_id = f"{filename_escaped}_{i}"
        metadata = {"filename": filename, "chunk_index": i, "text": chunk}
        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })

    # Upsert the new vectors into Pinecone.
    try:
        index.upsert(vectors=vectors)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone upsert failed: {e}")

    return {"message": "Data has been successfully uploaded and stored."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
