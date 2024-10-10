# Stage 1: Install dependencies
FROM python:3.10-slim AS build

WORKDIR /app

# Install dependencies
COPY ./src/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY src/ /app/

# Stage 2: Final image with a non-root user
FROM python:3.10-slim

WORKDIR /app

# Create a non-root user
RUN useradd -m appuser

# Copy only the installed dependencies and app from the first stage
COPY --from=build /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=build /app /app

# Create the db directory and set permissions before switching user
RUN mkdir -p /app/db && chown -R appuser:appuser /app/db

# Set non-root user
USER appuser

# Expose port and run app
EXPOSE 5000
CMD ["python", "./app.py"]
