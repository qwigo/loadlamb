FROM python:3.14
COPY . /code/loadlamb
WORKDIR /code/loadlamb
RUN pip install poetry
RUN poetry install
