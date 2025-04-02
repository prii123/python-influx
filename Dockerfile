FROM python:3.11

WORKDIR /app

COPY app/ /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "/app/main.py"]

