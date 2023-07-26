# syntax=docker/dockerfile:1

FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV DJANGO_SETTINGS_MODULE=configuration.settings
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code
CMD ["python3", "manage.py", "makemigrations"]
CMD ["python3", "manage.py", "migrate"]
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]