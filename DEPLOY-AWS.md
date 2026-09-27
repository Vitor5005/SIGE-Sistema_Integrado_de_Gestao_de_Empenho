# Deploy na AWS (EC2 + Docker Compose)

Tudo roda em uma única instância: **MySQL**, **API Django (gunicorn)** e **nginx**, que serve o Angular e repassa `/api` e `/admin` para a API. Só a porta 80 fica exposta.

```
navegador ──:80──> nginx (app) ──/api, /admin──> api:8000 (gunicorn) ──> db:3306 (MySQL)
```

Instância testada: **t3.small, Amazon Linux 2023, usuário `ec2-user`**.

## 1. Security Group (regras de entrada)

| Tipo | Porta | Origem |
|------|-------|--------|
| SSH  | 22    | Meu IP |
| HTTP | 80    | 0.0.0.0/0 |

Não abra 3306 nem 8000: banco e API só são acessados por dentro do Docker.

## 2. Preparar a instância

Conecte pelo **EC2 Instance Connect** (usuário `ec2-user`) e rode:

```bash
git clone -b deploy https://github.com/Vitor5005/SIGE-Sistema_Integrado_de_Gestao_de_Empenho.git sige
cd sige
bash scripts/aws/preparar-ec2.sh
exit
```

O script instala Docker, Docker Compose, Buildx e cria 2 GB de swap. O `exit` é necessário para o usuário entrar no grupo `docker`; conecte-se novamente depois.

> Se o repositório for privado, o `git clone` pedirá usuário e um **Personal Access Token** do GitHub no lugar da senha.

## 3. Configurar o `.env`

```bash
cd ~/sige
cp .env.production.example .env
curl -s http://checkip.amazonaws.com      # mostra o IP público da instância
openssl rand -base64 48                   # gere uma para cada senha/chave
nano .env
```

Para acessar pelo IP (sem domínio/HTTPS), preencha assim, trocando `54.123.45.67` pelo IP real:

```ini
DB_PASSWORD=<senha gerada>
DB_ROOT_PASSWORD=<outra senha gerada>
DJANGO_SECRET_KEY=<chave gerada>
ALLOWED_HOSTS=54.123.45.67
CSRF_TRUSTED_ORIGINS=http://54.123.45.67
SECURE_COOKIES=False
```

## 4. Subir o sistema

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

O primeiro build demora (≈5–10 min na t3.small). A API aplica as migrações sozinha ao iniciar. Acompanhe com:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f api
```

## 5. Criar os usuários iniciais

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api python seed.py
```

Cria um usuário para cada papel — `diretor`, `tecnico`, `nutricionista` e `estoquista` — e **mostra a senha aleatória de cada um uma única vez**: anote-as. O `diretor` também acessa o `/admin`. O script não apaga nem altera outros dados e pode ser rodado de novo sem trocar senhas já criadas.

Para definir você mesmo a senha inicial dos quatro:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -e SEED_SENHA='sua-senha-forte' api python seed.py
```

Acesse `http://SEU_IP_PUBLICO`.

## Operação

Para não repetir os `-f`, defina uma vez por sessão:

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml
```

| Tarefa | Comando |
|--------|---------|
| Atualizar para o último commit | `git pull && docker compose up -d --build` |
| Ver logs | `docker compose logs -f api` (ou `app`, `db`) |
| Reiniciar | `docker compose restart` |
| Backup do banco | `docker compose exec db sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > backup-$(date +%F).sql` |
| Liberar espaço de builds antigos | `docker image prune -f` |

## Cuidados

- **IP público muda ao parar/iniciar a instância** (reiniciar não muda). Se mudar, atualize `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` no `.env` e rode `docker compose up -d`. Um IP elástico evita isso.
- **HTTPS**: com um domínio apontando para a instância, coloque um certificado (ex.: Let's Encrypt) e então use `https://` em `CSRF_TRUSTED_ORIGINS` e `SECURE_COOKIES=True`.
- O volume `mysql_data` guarda o banco. `docker compose down` preserva os dados; **`docker compose down -v` apaga o banco**.
