FROM python:3.11-slim
RUN pip install --no-cache-dir streamlit requests docker
COPY app.py config.py airflow_client.py yarn_client.py /
CMD ["streamlit", "run", "/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
