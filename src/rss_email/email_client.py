import smtplib
from email.message import EmailMessage
from typing import List


class EmailClient:
    def __init__(self, host: str, port: int, username: str, password: str, sender: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender = sender

    def send(
        self,
        recipients: List[str],
        subject: str,
        html_body: str,
        text_body: str = "",
        cc: List[str] | None = None,
        bcc: List[str] | None = None,
    ) -> None:
        cc = cc or []
        bcc = bcc or []
        recipients = recipients or []

        # Ensure at least one visible recipient for MTAs that reject empty To header
        display_to = recipients if recipients else [self.sender]

        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = ", ".join(display_to)
        if cc:
            message["Cc"] = ", ".join(cc)
        message["Subject"] = subject
        message.set_content(text_body or "See HTML body for details.")
        message.add_alternative(html_body, subtype="html")

        all_rcpt = list(recipients)
        all_rcpt.extend(cc)
        all_rcpt.extend(bcc)

        try:
            print(f"Connecting to {self.host}:{self.port}...")

            if self.port == 465:
                # Port 465 uses SMTP_SSL
                smtp = smtplib.SMTP_SSL(self.host, self.port, timeout=30)
            else:
                # Port 587 uses STARTTLS
                smtp = smtplib.SMTP(self.host, self.port, timeout=30)
                smtp.starttls()

            smtp.set_debuglevel(2)

            print(f"Logging in as {self.username}...")
            smtp.login(self.username, self.password)

            print("Sending message...")
            smtp.send_message(message, to_addrs=all_rcpt)
            smtp.quit()
            print("Message sent successfully!")
        except Exception as e:
            print(f"SMTP Error: {type(e).__name__}: {e}")
            raise
