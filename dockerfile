FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/app:/app/src:${PYTHONPATH}"

EXPOSE 8000

CMD ["sh", "-c", "python pipeline.py && python main.py"]

