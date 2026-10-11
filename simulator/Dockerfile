FROM python:3.13-slim

WORKDIR /app

RUN useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY simulator.py .

USER appuser

ENTRYPOINT ["python", "simulator.py"]
CMD ["--mode", "continuous", "--rate", "1.5", "--duration", "0"]
