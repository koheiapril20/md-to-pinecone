# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures that Python output is sent straight to terminal (without buffering)
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . /app/

# Expose the port on which the app will run
EXPOSE 8000

# Run the application using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
