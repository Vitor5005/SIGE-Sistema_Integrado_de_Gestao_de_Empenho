#!/bin/sh

echo "Esperando o banco de dados..."

while ! nc -z db 3306; do
  sleep 1
done

echo "Banco iniciado!"

python manage.py migrate

echo "Criando superusuário se não existir..."

python manage.py createsuperuser --noinput || true

echo "Iniciando servidor..."

python manage.py runserver 0.0.0.0:8000
