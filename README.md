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
| `db` | MySQL 8 | `3307` | Persistência de dados |
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

### Subir o ambiente

Na raiz do repositório:

```bash
docker compose up --build
```

### Endereços

- Frontend: `http://localhost:4200`
- API: `http://localhost:8000`
- Django Admin: `http://localhost:8000/admin`
- MySQL (host): `localhost:3307`

### Fluxo automático da API no startup

Quando o container da API inicia, o `entrypoint.sh` executa:

1. espera o MySQL ficar disponível;
2. `python manage.py makemigrations`;
3. `python manage.py migrate`;
4. `python manage.py createsuperuser --noinput` (se necessário);
5. `python seed.py` para carga inicial;
6. `python manage.py runserver 0.0.0.0:8000`.

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

Exemplo utilizado no ambiente Docker:

```env
DB_NAME=sige
DB_USER=root
DB_PASSWORD=root
DB_HOST=db
DB_PORT=3306

DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@gmail.com
DJANGO_SUPERUSER_PASSWORD=admin

DEBUG=True
DJANGO_SECRET_KEY=chave_super_secreta_aqui
```

## 📁 Estrutura do repositório

```text
.
├── Artefatos/
│   └── DER/
├── sige-api/
├── sige-app/
├── docker-compose.yml
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