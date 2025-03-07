import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


@dataclass
class SendEmailResponse:
    success: bool
    message: str


def send_email(
    smtp_server: str,
    smtp_port: int,
    username: str,
    password: str,
    subject: str,
    body: str,
    recipients: list[str],
) -> SendEmailResponse:
    """
    Sends an email via SMTP to a list of recipients.

    Args:
        smtp_server (str): The address of the SMTP server.
        smtp_port (int): The port number for the SMTP server.
        username (str): Your email address or username for the SMTP server.
        password (str): Your password for the SMTP server.
        subject (str): The subject of the email.
        body (str): The body text of the email.
        recipients (list): A list of recipient email addresses.
    """
    message = MIMEMultipart()
    message["From"] = username
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, recipients, message.as_string())
        return SendEmailResponse(success=True, message="Email sent successfully!")
    except Exception as e:
        return SendEmailResponse(success=False, message=str(e))


# Smoke test
if __name__ == "__main__":
    smtp_server = "smtp.example.com"
    smtp_port = 587
    username = "email@example.com"
    password = "password"
    subject = "Test Email"
    body = "This is a test email sent from Python."
    recipients: list[str] = ["recipient1@example.com", "recipient2@example.com"]

    send_email(smtp_server, smtp_port, username, password, subject, body, recipients)
