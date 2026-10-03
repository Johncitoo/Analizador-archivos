FROM python:3.13-slim

# No generar archivos .pyc y mostrar logs al instante
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Junta los archivos estáticos (admin, Swagger) para que WhiteNoise los sirva
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Producción: aplica migraciones y levanta gunicorn en el puerto que asigne la plataforma.
# En local, docker-compose.yml reemplaza este comando por runserver.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2"]
