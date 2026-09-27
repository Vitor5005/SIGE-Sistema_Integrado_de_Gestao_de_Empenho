#!/bin/sh
set -e

echo "Aguardando banco de dados..."

# Espera apenas a conexão; erros de migração não devem ser repetidos, pois no
# MySQL uma migração que falha no meio não é desfeita.
attempt=1
until DJANGO_SETTINGS_MODULE=sige_api.settings python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection()" 2>/dev/null; do
  if [ "$attempt" -ge 30 ]; then
    echo "Banco indisponivel apos $attempt tentativas."
    exit 1
  fi

  echo "Banco indisponivel. Nova tentativa em 2 segundos ($attempt/30)..."
  attempt=$((attempt + 1))
  sleep 2
done

echo "Aplicando migracoes..."
python manage.py migrate --noinput

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
