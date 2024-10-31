from flask import Flask, request, jsonify, send_from_directory
import json
import os
import requests

app = Flask(__name__)

# Chemins vers les fichiers nécessaires
api_key_path = os.path.join('ressources', 'api.json')
db_file_path = 'db.json'

# Charger les clés API
def load_api_keys():
    try:
        with open(api_key_path, 'r') as f:
            api_data = json.load(f)
            return api_data['apiKey'], api_data['whoIs']
    except Exception as e:
        print(f"Erreur de chargement de la clé API : {e}")
        return None, None

api_key, who_is_api_key = load_api_keys()

# Fonction pour lire la base de données
def read_database():
    try:
        with open(db_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": []}  # Structure vide si le fichier n'existe pas

# Fonction pour écrire dans la base de données
def write_database(data):
    with open(db_file_path, 'w') as f:
        json.dump(data, f, indent=4)

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

    # Lire les données actuelles de la base de données
    db_data = read_database()

    # Ajouter le nouvel utilisateur
    db_data['users'].append(user)

    # Écrire les données mises à jour dans db.json
    write_database(db_data)

    return jsonify({"status": "success", "user_data": user}), 201

# Servir les fichiers statiques (HTML, CSS, JS)
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)

# Lancer l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
