# md-to-pinecone

This is a FastAPI web API that accepts Markdown text (filename and content), vectorizes the content using OpenAI embeddings, and stores the vectors in Pinecone. If data with the same filename exists, it attempts to delete the old data before upserting the new vectors.

**Important:**  
Due to a known bug in the Pinecone Python client, deletion using filters (i.e. `index.delete(filter={"filename": {"$eq": filename}})`) does not work reliably. See [issue #432](https://github.com/pinecone-io/pinecone-python-client/issues/432) for more details.

## Requirements

- Python 3.8+
- FastAPI, uvicorn, python-dotenv, openai (>=1.63.2), pinecone (v2 API)

## Setup

1. **Clone the repository and create a virtual environment:**
    ```bash
    git clone https://github.com/kohei_april20/md-to-pinecone.git
    cd md-to-pinecone
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. **Create a `.env` file** in the project root with:
    ```
    PINECONE_API_KEY=your-pinecone-api-key
    PINECONE_INDEX_NAME=your-index-name
    OPENAI_API_KEY=your-openai-api-key
    ```

## Run

Start the API server with:
```bash
uvicorn main:app --reload
