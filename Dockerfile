# Use the official lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose the port used by Flask
EXPOSE 8080

# Set environment variable for Flask
ENV PORT=8080

# Run the app
CMD ["python", "app.py"]