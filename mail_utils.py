
from flask import Flask
from flask_mail import Mail, Message
from config import EMAIL_ADDRESS, EMAIL_PASSWORD






app = Flask(__name__)


app.config['MAIL_SERVER'] = 'smtp.office365.com'  # Pour Microsoft 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_ADDRESS 
app.config['MAIL_PASSWORD'] = EMAIL_PASSWORD  

mail = Mail(app)

@app.route('/send-email')
def send_email():
    try:
        msg = Message(
            subject="Hello from Flask-Mail",
            sender=app.config['MAIL_USERNAME'],
            recipients=['....'],  # adresse de destination
            body="Hello There"
        )
        mail.send(msg)
        return "Email envoyé avec succès !"
    except Exception as e:
        return f"Erreur lors de l'envoi de l'email : {e}"

if __name__ == "__main__":
    app.run(debug=True)
