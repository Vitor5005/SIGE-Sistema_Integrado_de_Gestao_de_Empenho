# S.I.G.E — Sistema Integrado de Gestão de Empenho 🍽️

> Plataforma para gestão de **licitações**, **atas (ARP)**, **empenhos** e **entregas** no contexto do Restaurante Universitário (UFAC).

![Status](https://img.shields.io/badge/status-em_desenvolvimento-green?style=for-the-badge)
![Local](https://img.shields.io/badge/local-Rio_Branco--AC-red?style=for-the-badge)
![Backend](https://img.shields.io/badge/backend-Django%206-092E20?style=for-the-badge&logo=django&logoColor=white)
![Frontend](https://img.shields.io/badge/frontend-Angular%2021-DD0031?style=for-the-badge&logo=angular&logoColor=white)
![Database](https://img.shields.io/badge/database-MySQL%208-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

## 📚 Sumário

- [Visão geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Tecnologias](#-tecnologias)
- [Como rodar com Docker](#-como-rodar-com-docker)
- [Como rodar localmente (sem Docker)](#-como-rodar-localmente-sem-docker)
- [API (rotas principais)](#-api-rotas-principais)
- [Variáveis de ambiente](#-variáveis-de-ambiente)
- [Estrutura do repositório](#-estrutura-do-repositório)
- [DER](#-der)
- [Equipe](#-equipe)

## 🔎 Visão geral

O projeto é dividido em dois módulos principais:

- `sige-api`: API REST com regras de negócio.
- `sige-app`: aplicação web para uso administrativo.

Objetivos centrais do sistema:

- centralizar o fluxo entre licitação, ata, empenho e entrega;
- preservar integridade de saldo ao longo do processo;
- aumentar rastreabilidade das operações.

## 🧩 Arquitetura

No ambiente Docker, o sistema sobe com 3 serviços:

| Serviço | Stack | Porta (host) | Finalidade |
|---|---|---:|---|
| `db` | MySQL 8 | `3308` | Persistência de dados |
| `api` | Django + DRF | `8000` | API REST + autenticação |
| `app` | Angular | `4200` | Interface web |

## 🛠 Tecnologias

- **Backend:** Python 3.12, Django 6, Django REST Framework, `django-filter`, JWT (`simplejwt`)
- **Frontend:** Angular 21, Bootstrap 5
- **Banco de dados (execução Docker):** MySQL 8
- **Orquestração:** Docker Compose

## 🚀 Como rodar com Docker

### Pré-requisitos

- Docker
- Docker Compose

### Subir o ambiente de desenvolvimento

Na raiz do repositório:

```bash
cp .env.development.example .env.development
docker compose --env-file .env.development -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Endereços

- Frontend: `http://localhost:4200`
- API: `http://localhost:8000`
- Django Admin: `http://localhost:8000/admin`
- MySQL (host): `localhost:3308`

### Subir o ambiente de produção

Preencha as credenciais e os domínios antes de iniciar:

```bash
cp .env.production.example .env.production
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Em produção, o frontend é compilado e servido pelo Nginx na porta definida por `APP_PORT` (porta `80` por padrão). O Nginx encaminha `/api`, `/admin` e `/static` para o Django.

### Deploy no Render

O arquivo `render.yaml` cria os recursos necessários pelo Render Blueprint:

- `sige-mysql`: MySQL privado com disco persistente de 10 GB;
- `sige-api`: API Django/Gunicorn;
- `sige-app`: frontend Angular servido pelo Nginx.

Depois de enviar a branch `deploy` para o repositório remoto, acesse **New > Blueprint** no Render, conecte o repositório, selecione essa branch e aplique o Blueprint. As senhas do MySQL e a chave do Django são geradas automaticamente pelo Render.

> O MySQL privado e a API usam o plano `starter`. O frontend usa o plano `free` e pode entrar em suspensão quando ficar ocioso.

### Fluxo automático da API no startup

Quando o container da API inicia, o `entrypoint.sh` executa:

1. espera o MySQL ficar disponível;
2. executa `python manage.py migrate`;
3. opcionalmente cria o superusuário quando `CREATE_SUPERUSER=True`;
4. opcionalmente carrega dados iniciais quando `SEED_DATA=True`;
5. inicia o comando definido pelo ambiente: servidor de desenvolvimento ou Gunicorn.

**Credenciais padrão (ambiente Docker):**

- usuário: `admin`
- senha: `admin`

## 💻 Como rodar localmente (sem Docker)

### Backend (`sige-api`)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

> O backend usa MySQL configurado por variáveis de ambiente em `sige_api/settings.py`.

### Frontend (`sige-app`)

```bash
npm install
npm start
```

No ambiente de desenvolvimento, o frontend aponta para:

`API_URL = http://localhost:8000/api/v1`

## 🔌 API (rotas principais)

Prefixo base:

`http://localhost:8000/api/v1/`

### Módulos disponíveis

- `cadastro` (endereços, fornecedores, itens genéricos)
- `licitacao` (licitações, atas e itens de ata)
- `empenho` (empenhos, itens e operações)
- `entrega` (ordens e itens de entrega)
- `usuario` (usuários e autenticação)

### Autenticação JWT

- `POST /api/v1/login/`
- `POST /api/v1/login/refresh/`
- `POST /api/v1/login/verify/`

## ⚙ Variáveis de ambiente

Use `.env.development.example` como base para desenvolvimento e `.env.production.example` como base para produção. As principais variáveis são:

```env
DB_NAME=sige
DB_USER=sige
DB_PASSWORD=troque-esta-senha
DB_ROOT_PASSWORD=troque-esta-senha-root

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@gmail.com
DJANGO_SUPERUSER_PASSWORD=troque-esta-senha
CREATE_SUPERUSER=False
SEED_DATA=False

DEBUG=False
DJANGO_SECRET_KEY=gere-uma-chave-secreta-longa-e-aleatoria
ALLOWED_HOSTS=seu-dominio.example.com
CORS_ALLOWED_ORIGINS=https://seu-dominio.example.com
CSRF_TRUSTED_ORIGINS=https://seu-dominio.example.com

EMAIL_HOST_USER=seu_email_google@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app_google
```

Para executar sem Docker, crie `sige-api/.env`. O backend lê esse arquivo automaticamente via `python-dotenv`. Nunca versione arquivos `.env` com segredos reais.

## 📁 Estrutura do repositório

```text
.
├── Artefatos/
│   └── DER/
├── sige-api/
├── sige-app/
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
└── README.md
```

## 🧱 DER

Os arquivos de modelagem estão em `Artefatos/DER/`.

## 👥 Equipe

- Andrey da Cunha Marques
- Carlos Eduardo Marin Bezerra
- Gabriela Santos de Oliveira
- João Vitor Ferreira da Silva
- Marcos Antonio da Silva Manuares

---

Rio Branco - AC, 2026
