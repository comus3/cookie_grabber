from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import json
import os
import requests

app = Flask(__name__)
CORS(app)  # Activer CORS pour permettre les requêtes cross-origin

# Configuration de la connexion à MongoDB
mongo_uri = "mongodb://localhost:27017"  # Remplace par ton URI MongoDB
client = MongoClient(mongo_uri)
db = client['cookie_awareness']  # Nom de la base de données
users_collection = db['users']    # Nom de la collection pour les utilisateurs

# Charger les clés API
def load_api_keys():
    try:
        with open(os.path.join('ressources', 'api.json'), 'r') as f:
            api_data = json.load(f)
            return api_data['apiKey'], api_data['whoIs']
    except Exception as e:
        print(f"Erreur de chargement de la clé API : {e}")
        return None, None

api_key, who_is_api_key = load_api_keys()


@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


# Route pour traiter et sauvegarder les données des utilisateurs
@app.route('/update-db', methods=['POST'])
def update_db():
    user = request.json
    ip_address = request.remote_addr  # Obtenir l'adresse IP

    # Appel à l'API ipinfo.io pour obtenir les informations d'IP
    ip_info_url = f'https://ipinfo.io/{ip_address}/json?token={api_key}'
    ip_info = requests.get(ip_info_url).json()

    # Ajouter les informations de géolocalisation au dictionnaire user
    user.update({
        "ipAddress": ip_address,
        "location": {
            "city": ip_info.get("city"),
            "region": ip_info.get("region"),
            "country": ip_info.get("country"),
            "postal": ip_info.get("postal"),
            "org": ip_info.get("org"),
            "location": ip_info.get("loc")
        }
    })

    # Appel à l'API WHOIS pour les informations de domaine
    whois_url = f'https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey={who_is_api_key}&domainName={ip_address}&outputFormat=JSON'
    whois_data = requests.get(whois_url).json()
    user["whoisData"] = whois_data

    # Sauvegarder l'utilisateur dans la base de données MongoDB
    users_collection.insert_one(user)

    return jsonify({"status": "success", "user_data": user}), 201

# Route pour charger tous les utilisateurs
@app.route('/load', methods=['GET'])
def load_users():
    users = list(users_collection.find({}, {'_id': 0}))  # Ne pas inclure l'_id de MongoDB
    return jsonify(users), 200

# Route pour envoyer des données spécifiques d'un utilisateur
@app.route('/send/<int:user_id>', methods=['GET'])
def send_user(user_id):
    user = users_collection.find_one({"id": user_id}, {'_id': 0})
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Route pour sauvegarder de nouvelles données utilisateur
@app.route('/save', methods=['POST'])
def save_user():
    new_user = request.json
    users_collection.insert_one(new_user)
    return jsonify({"status": "success", "user_data": new_user}), 201

# Servir les fichiers statiques (HTML, CSS, JS)
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)

# Lancer l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)