FROM python:3.9
COPY . /code/loadlamb
WORKDIR /code/loadlamb
RUN pip install poetry
RUN poetry install
