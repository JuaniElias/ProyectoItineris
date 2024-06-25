from django.core.mail import EmailMessage
from django.conf import settings


def send_email(to_email, subject, message, file):
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
    )
    if file:
        email.attach(file.name, file.read(), file.content_type)

    email.send()
