# Use a specific version of Python to ensure consistent builds
FROM python:3.12.4

# Set the working directory inside the container
WORKDIR /app

# Copy all the files from the current directory to the working directory in the container
COPY . /app

# Install dependencies using pip
RUN pip install --no-cache-dir psycopg2 google-generativeai

# Specify the command to run your Python script
CMD ["python3", "geminiApi2.py"]
