#!/bin/sh

echo "Banco de dados pronto! Iniciando as migrações..."
python manage.py migrate

echo "Criando superusuário se não existir..."
python manage.py createsuperuser --noinput || true

echo "Iniciando o servidor da API..."
python manage.py runserver 0.0.0.0:8000