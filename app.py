from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import json
import os
import requests
import csv
from statistics import mean

app = Flask(__name__)
CORS(app)

# Configuration de la connexion à MongoDB
mongo_uri = "mongodb://localhost:27017"
client = MongoClient(mongo_uri)
db = client['cookie_awareness']
users_collection = db['users']

@app.route('/email', methods=['POST'])
def send_email():
    """
    Handle the form submission to send an email.
    """
    # Extract the user ID and form data
    user_id = request.form.get('user_id')
    email = request.form.get('email')
    
    # You can extract other form data similarly if needed
    
    # Simulate sending an email
    try:
        send_mail(user_id, email)  # Call the send_mail function
        return send_from_directory('public', "awareness_info.html")
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({"error": "Failed to send email"}), 500

def send_mail(user_id, recipient_email):
    """
    Simulated email sending function.
    This should connect to your email service and send an email.
    """
    print(f"Sending email to {recipient_email} for user ID {user_id}")
    # Here, implement the actual email sending logic using an email library



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

# Fonction utilitaire pour convertir ObjectId en chaîne de caractères
def convert_objectid_to_str(doc):
    """
    Convert MongoDB ObjectId to string for easier JSON serialization.
    """
    if isinstance(doc, list):
        return [convert_objectid_to_str(d) for d in doc]
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

@app.route('/')
def index():
    """
    Serve the main HTML page for the application.
    """
    return send_from_directory('public', 'index.html')

@app.route('/stats', methods=['GET'])
def get_statistics():
    """
    Retrieve statistics about the users in the database.
    """
    try:
        user_count = users_collection.count_documents({})
        times_of_visit = [user['timeOfVisit'] for user in users_collection.find({"timeOfVisit": {"$exists": True}})]
        avg_time_of_visit = mean(times_of_visit) if times_of_visit else None
        locations = get_user_location_distribution()
        
        stats = {
            "total_users": user_count,
            "average_time_of_visit": avg_time_of_visit,
            "users_by_location": locations
        }

        return jsonify(stats), 200

    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({"error": "Unable to fetch statistics"}), 500

def get_user_location_distribution():
    """
    Helper function to aggregate user locations from the database.
    """
    try:
        locations = list(users_collection.aggregate([
            {"$group": {"_id": "$location.country", "count": {"$sum": 1}}}
        ]))
        locations_dict = {loc['_id']: loc['count'] for loc in locations if loc['_id']}
        return locations_dict
    except Exception as e:
        print(f"Error fetching location distribution: {e}")
        return {}

@app.route('/average-time-of-visit', methods=['GET'])
def get_average_time_of_visit():
    """
    Calculate the average time of visit for users.
    """
    try:
        times_of_visit = [user['timeOfVisit'] for user in users_collection.find({"timeOfVisit": {"$exists": True}})]
        avg_time_of_visit = mean(times_of_visit) if times_of_visit else None
        return jsonify({"average_time_of_visit": avg_time_of_visit}), 200
    except Exception as e:
        print(f"Error fetching average time of visit: {e}")
        return jsonify({"error": "Unable to fetch average time of visit"}), 500

@app.route('/location-distribution', methods=['GET'])
def get_location_distribution():
    """
    Get the distribution of users by location.
    """
    try:
        locations = get_user_location_distribution()
        return jsonify({"locations": locations}), 200
    except Exception as e:
        print(f"Error fetching location distribution: {e}")
        return jsonify({"error": "Unable to fetch location distribution"}), 500

@app.route('/update-db', methods=['POST'])
def update_db():
    """
    Update the user database with new user data and IP location.
    """
    user = request.json
    ip_address = request.remote_addr

    ip_info = fetch_ip_info(ip_address)
    user.update({
        "ipAddress": ip_address,
        "location": ip_info
    })

    whois_data = fetch_whois_data(ip_address)
    user["whoisData"] = whois_data

    # Sauvegarder l'utilisateur dans la base de données MongoDB
    users_collection.insert_one(user)
    user = convert_objectid_to_str(user)

    return jsonify({"status": "success", "user_data": user}), 201

def fetch_ip_info(ip_address):
    """
    Fetch IP information from the external API.
    """
    ip_info_url = f'https://ipinfo.io/{ip_address}/json?token={api_key}'
    try:
        ip_info = requests.get(ip_info_url).json()
        return {
            "city": ip_info.get("city"),
            "region": ip_info.get("region"),
            "country": ip_info.get("country"),
            "postal": ip_info.get("postal"),
            "org": ip_info.get("org"),
            "location": ip_info.get("loc")
        }
    except Exception as e:
        print(f"Error fetching IP info: {e}")
        return {}

def fetch_whois_data(ip_address):
    """
    Fetch WHOIS data for the given IP address.
    """
    whois_url = f'https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey={who_is_api_key}&domainName={ip_address}&outputFormat=JSON'
    try:
        whois_data = requests.get(whois_url).json()
        return whois_data
    except Exception as e:
        print(f"Error fetching WHOIS data: {e}")
        return {}

@app.route('/load', methods=['GET'])
def load_users():
    """
    Load all users from the database.
    """
    users = list(users_collection.find({}))
    users = convert_objectid_to_str(users)
    return jsonify(users), 200

@app.route('/send/<int:user_id>', methods=['GET'])
def send_user(user_id):
    """
    Retrieve a specific user's data by ID.
    """
    user = users_collection.find_one({"id": user_id})
    if user:
        user = convert_objectid_to_str(user)
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/export-users', methods=['GET'])
def export_users():
    """
    Export user data to a CSV file.
    """
    users = list(users_collection.find({}))
    output = Response(content_type='text/csv')
    output.headers["Content-Disposition"] = "attachment; filename=users.csv"
    
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Time of Visit', 'Location'])
    
    for user in users:
        writer.writerow([str(user['_id']), user.get('name'), user.get('email'), user.get('timeOfVisit'), user.get('location', {}).get('country')])
    
    return output

@app.route('/save', methods=['POST'])
def save_user():
    """
    Save a new user to the database.
    """
    new_user = request.json
    users_collection.insert_one(new_user)
    new_user = convert_objectid_to_str(new_user)
    return jsonify({"status": "success", "user_data": new_user}), 201

@app.route('/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user from the database by ID.
    """
    result = users_collection.delete_one({"id": user_id})
    if result.deleted_count > 0:
        return jsonify({"status": "success", "message": "User deleted"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/update/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update a user's information in the database.
    """
    updated_data = request.json
    result = users_collection.update_one({"id": user_id}, {"$set": updated_data})
    if result.modified_count > 0:
        updated_user = users_collection.find_one({"id": user_id})
        updated_user = convert_objectid_to_str(updated_user)
        return jsonify({"status": "success", "user_data": updated_user}), 200
    else:
        return jsonify({"error": "User not found or no change detected"}), 404

@app.route('/sort', methods=['GET'])
def sort_users():
    """
    Sort users based on a specified field.
    """
    sort_field = request.args.get('field', 'id')
    sort_order = request.args.get('order', 'asc')

    sort_direction = 1 if sort_order == 'asc' else -1
    sorted_users = list(users_collection.find({}).sort(sort_field, sort_direction))
    sorted_users = convert_objectid_to_str(sorted_users)

    return jsonify(sorted_users), 200

@app.route('/search-users', methods=['GET'])
def search_users():
    """
    Search for users based on name or email.
    """
    name = request.args.get('name')
    email = request.args.get('email')
    query_filter = {}
    
    if name:
        query_filter['name'] = {"$regex": name, "$options": "i"}  # Case-insensitive search
    if email:
        query_filter['email'] = {"$regex": email, "$options": "i"}
    
    users = list(users_collection.find(query_filter))
    users = convert_objectid_to_str(users)
    
    return jsonify(users), 200

@app.route('/count-users', methods=['GET'])
def count_users():
    """
    Count the total number of users in the database.
    """
    user_count = users_collection.count_documents({})
    return jsonify({"user_count": user_count}), 200

@app.route('/<path:path>')
def static_files(path):
    print("AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
    print(path)
    return send_from_directory('public', path)

@app.route('/filter-users', methods=['GET'])
def filter_users():
    """
    Filter users based on time of visit and WHOIS data presence.
    """
    max_time_of_visit = request.args.get('max_time_of_visit', type=int)
    exclude_whois_none = request.args.get('exclude_whois_none', default=False, type=bool)
    
    # Construction du filtre MongoDB
    query_filter = {}

    # Exclure les utilisateurs avec timeOfVisit > max_time_of_visit
    if max_time_of_visit is not None:
        query_filter['timeOfVisit'] = {"$lte": max_time_of_visit}
    
    # Exclure les utilisateurs avec whois = None
    if exclude_whois_none:
        query_filter['whoisData'] = {"$ne": None}

    # Effectuer la requête MongoDB avec les filtres spécifiés
    users = list(users_collection.find(query_filter))
    users = convert_objectid_to_str(users)

    return jsonify(users), 200

# Lancer l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
