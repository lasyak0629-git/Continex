
# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --default-timeout=120 --retries 10 -r requirements.txt
COPY . .
RUN useradd -m app && mkdir -p /app/media /app/staticfiles && chown -R app /app
USER app
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 180"]
