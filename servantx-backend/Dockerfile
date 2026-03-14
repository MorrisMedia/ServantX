FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    bash \
    postgresql-client \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x start.sh
CMD ["./start.sh"]
# CMD ["bash", "-lc", "tr -d '\\r' < /app/start.sh > /tmp/start.sh && chmod +x /tmp/start.sh && exec /tmp/start.sh"]