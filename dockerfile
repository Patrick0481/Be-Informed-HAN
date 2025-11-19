# Gebruik een officiële Python-image als basis
FROM python:3.10-slim

# Stel omgevingsvariabelen in
ENV PYTHONUNBUFFERED=1 \
    # Standaardpoort voor Streamlit
    PORT=8501 \
    # Ollama Host - 'host.docker.internal' is een speciale DNS naam die verwijst naar de hostmachine
    # Pas dit aan als je Ollama op een andere server draait.
    OLLAMA_HOST=host.docker.internal:11434

# Werk de werkmap in de container bij
WORKDIR /app

# Kopieer de requirements en installeer afhankelijkheden
# Dit optimaliseert de Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer de rest van de applicatiecode
COPY app.py .

# Exposeer de poort die Streamlit gebruikt
EXPOSE 8501

# Commando om de Streamlit-app te starten
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]