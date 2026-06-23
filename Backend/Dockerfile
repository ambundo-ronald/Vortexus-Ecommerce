FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl libjpeg62-turbo-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

ARG INSTALL_ML_DEPS=false

COPY requirements.txt requirements-ml.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && if [ "$INSTALL_ML_DEPS" = "true" ]; then pip install -r requirements-ml.txt; fi

COPY . .

RUN mkdir -p /app/staticfiles /app/media

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
