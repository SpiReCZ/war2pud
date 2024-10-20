
FROM ubuntu:latest

# Install dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y wine64 wine32

# Create a directory for the application
RUN mkdir /app
WORKDIR /app

# Copy the executable to the container
COPY etc/* /app/

# Set the entrypoint to run the executable with Wine
ENTRYPOINT ["wine", "PUDPIC.exe"]