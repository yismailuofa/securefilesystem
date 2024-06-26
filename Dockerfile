# Use an official Python runtime as a parent image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
RUN pip install bcrypt cryptography

# Run main.py when the container launches
CMD ["python", "main.py"]
