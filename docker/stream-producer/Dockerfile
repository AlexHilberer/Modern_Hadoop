FROM python:3.11-slim
RUN pip install --no-cache-dir hdfs
COPY producer.py /producer.py
CMD ["python3", "/producer.py"]
