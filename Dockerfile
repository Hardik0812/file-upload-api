# Use the official Python image as the base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code to the container
COPY . /app

# Install any necessary Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that your app runs on
EXPOSE 8000

# Command to run the Python application
CMD ["python", "app.py"]