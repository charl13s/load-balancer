# Load balancer image for ICS 4104 Assignment 1, Task 3.
# Runtime requires: --privileged and -v /var/run/docker.sock:/var/run/docker.sock
# (configured in docker-compose.yml in substep 3f).
FROM python:3.12-slim

WORKDIR /app

# Python deps first so code changes don't bust the pip cache layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code. _mocks/ ships for now; deleted after 3b/3c integration.
COPY app.py .
COPY _mocks/ _mocks/

# Unbuffered stdout so `docker logs lb` streams in real time.
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "app.py"]
