#!/bin/sh
set -e

echo "Aguardando banco de dados..."

while ! nc -z "${DB_HOST:-db}" "${DB_PORT:-3306}"; do
  sleep 2
done

echo "Banco de dados pronto! Aplicando migracoes..."
python manage.py migrate

if [ "${CREATE_SUPERUSER:-False}" = "True" ]; then
  echo "Criando superusuario se nao existir..."
  python manage.py createsuperuser --noinput || true
fi

if [ "${SEED_DATA:-False}" = "True" ]; then
  echo "Populando dados iniciais..."
  python seed.py
fi

if [ "$#" -eq 0 ]; then
  set -- gunicorn sige_api.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}"
fi

echo "Iniciando a API..."
exec "$@"
