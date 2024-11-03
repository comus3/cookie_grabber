import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

def send_email(to_email, subject, body_html, body_text=None):

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = to_email
    msg["Subject"] = subject


    if body_text:
        part1 = MIMEText(body_text, "plain")
        msg.attach(part1)
    part2 = MIMEText(body_html, "html")
    msg.attach(part2)

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            if EMAIL_USE_TLS:
                server.starttls()  
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)  

            server.sendmail(EMAIL_HOST_USER, to_email, msg.as_string())
            print(f"Email envoyé avec succès à {to_email}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
