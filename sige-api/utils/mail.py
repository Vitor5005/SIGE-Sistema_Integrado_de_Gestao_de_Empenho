import os
from pathlib import Path

import yagmail
from dotenv import dotenv_values

ARQUIVO_ENV_API = Path(__file__).resolve().parent.parent / '.env'


def _configuracao(nome):
    # O docker-compose define EMAIL_HOST_* vazias quando o .env da raiz não as tem, e o
    # load_dotenv das settings não sobrescreve variáveis já existentes; por isso, quando
    # vierem vazias, lê o valor diretamente de sige-api/.env.
    valor = os.getenv(nome)
    if valor:
        return valor
    if ARQUIVO_ENV_API.exists():
        return dotenv_values(ARQUIVO_ENV_API).get(nome)
    return None


def get_email_client():
    email_user = _configuracao("EMAIL_HOST_USER")
    email_password = _configuracao("EMAIL_HOST_PASSWORD")

    if not email_user or not email_password:
        raise ValueError("Defina EMAIL_HOST_USER e EMAIL_HOST_PASSWORD no arquivo .env.")

    return yagmail.SMTP(user=email_user, password=email_password)
