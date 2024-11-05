# Utilisez une image Python comme base
FROM python:3.9

# Définissez le répertoire de travail
WORKDIR /app

# Copiez le fichier requirements.txt et installez les dépendances
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiez le reste du code dans l'image
COPY . .

# Définissez les variables d'environnement pour Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Exposez le port sur lequel Flask écoutera
EXPOSE 80

# Commande pour lancer l'application
CMD ["flask", "run", "--host=0.0.0.0", "--port=80"]
