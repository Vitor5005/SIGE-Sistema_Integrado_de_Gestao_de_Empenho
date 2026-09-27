#!/bin/sh
set -e

echo "Aguardando banco de dados..."

while ! nc -z db 3306; do
  sleep 2
done

echo "Banco de dados pronto! Iniciando as migrações..."
python manage.py migrate

SEED_MODE="${SIGE_SEED_MODE:-if_empty}"

if [ "$SEED_MODE" = "refresh_demo" ]; then
  case "${DEBUG:-}" in
    true|True|1)
      echo "Validando catálogo antes de recriar os dados de demonstração..."
      python seed.py --validate-catalog
      echo "Recriando dados de demonstração..."
      python manage.py flush --noinput
      ;;
    *)
      echo "ERRO: refresh_demo só pode ser usado com DEBUG=True."
      exit 1
      ;;
  esac
fi

echo "Criando superusuário se não existir..."
python manage.py createsuperuser --noinput || true

echo "Executando seed (modo: $SEED_MODE)..."
python seed.py

echo "Iniciando o servidor da API..."
python manage.py runserver 0.0.0.0:8000
