FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set the port Cloud Run will use
ENV PORT 8080

# Run Streamlit service
CMD streamlit run health_agent.py --server.port 8080

