#!/bin/sh

echo "Aguardando banco de dados..."

while ! nc -z db 3306; do
  sleep 2
done

echo "Banco de dados pronto! Iniciando as migrações..."
python manage.py migrate

echo "Criando superusuário se não existir..."
python manage.py createsuperuser --noinput || true

echo "Iniciando o servidor da API..."
python manage.py runserver 0.0.0.0:8000