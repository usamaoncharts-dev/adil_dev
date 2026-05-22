import smtplib
import ssl
from email.message import EmailMessage
from bot.config import Config


class EmailNotifier:
    def __init__(self, config: Config):
        self.config = config

    def send(self, subject: str, body: str) -> bool:
        if not self.config.email_enabled:
            print('[notifier] email disabled, skipping send')
            return False

        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = self.config.email_from
        message['To'] = self.config.email_to
        message.set_content(body)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.email_username, self.config.email_password)
                server.send_message(message)
            print(f'[notifier] email sent: {subject}')
            return True
        except Exception as exc:
            print(f'[notifier] failed to send email: {exc}')
            return False
