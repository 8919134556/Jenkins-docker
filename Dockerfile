FROM ubuntu:latest

# Update and install basics
RUN apt-get update -y && apt-get install -y python3 python3-pip

# Setting up working directory and copying files
WORKDIR /app
COPY server.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose the port server is expected to work on
EXPOSE 5000

# Run the server script
CMD ["python3", "server.py"]
