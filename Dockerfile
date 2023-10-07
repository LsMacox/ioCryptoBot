FROM python:3.8-slim

RUN pip install poetry

WORKDIR /app
COPY . /app/
RUN poetry config virtualenvs.create false && poetry install --only main

CMD ["python", "/app/src/main.py"]
