import os

import yagmail


def get_email_client():
    email_user = os.getenv("EMAIL_HOST_USER")
    email_password = os.getenv("EMAIL_HOST_PASSWORD")

    if not email_user or not email_password:
        raise ValueError("Defina EMAIL_HOST_USER e EMAIL_HOST_PASSWORD no arquivo .env.")

    return yagmail.SMTP(user=email_user, password=email_password)