FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=config.prod

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
    
RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN chmod +x ./entrypoint.sh

RUN python manage.py collectstatic --noinput --settings=config.prod

EXPOSE 8000
