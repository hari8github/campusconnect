import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def send_email(subject, body, to_email, attachment_path=None):
    # Email configuration
    from_email = os.getenv("EMAIL_ADDRESS")
    password = os.getenv("EMAIL_PASSWORD")

    if not from_email or not password:
        raise ValueError("Email credentials are not set in the environment variables.")

    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    if attachment_path:
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)
        except Exception as e:
            raise ValueError(f"Failed to attach file: {e}")

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        return True
    except Exception as e:
        raise ConnectionError(f"Failed to send email: {e}")
    finally:
        server.quit()

# Example usage
if __name__ == "__main__":
    try:
        send_email(
            subject="Test Email",
            body="This is a test email.",
            to_email="toharivenkat@gmail.com"
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error: {e}")