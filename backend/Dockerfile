FROM python:3.9

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/bin/bash", "-c", "uvicorn app:app --host 0.0.0.0 --port 5000"]
