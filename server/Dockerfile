# Server image for ICS 4104 Assignment 1, Task 1.
# Person C: this should work as-is once server.py is implemented.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 5000

CMD ["python", "server.py"]
