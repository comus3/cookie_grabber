from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import json
import os
import requests
import csv
from statistics import mean
from flask_caching import Cache
from datetime import datetime 
  

app = Flask(__name__)
CORS(app)

# Setting up the Flask app
app = Flask(__name__)
CORS(app)

# Redis Cache Configuration
cache = Cache(app, config={
    "CACHE_TYPE": "redis",
    "CACHE_REDIS_HOST": os.getenv("CACHE_REDIS_HOST", "localhost"),
    "CACHE_REDIS_PORT": int(os.getenv("CACHE_REDIS_PORT", 6379)),
})

# MongoDB Configuration
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(mongo_uri)
db = client['cookie_awareness']
users_collection = db['users']
email_history_collection = db['email_history']  




# Load API keys
def load_api_keys():
    try:
        with open(os.path.join('ressources', 'api.json'), 'r') as f:
            api_data = json.load(f)
            return api_data['apiKey'], api_data['WhoIs']
    except Exception as e:
        print(f"Erreur de chargement de la clé API : {e}")
        return None, None

api_key, who_is_api_key = load_api_keys()

# Utility function to convert Object to string
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
        times_of_visit = [user['time of visit'] for user in users_collection.find({"time of visit": {"$exists": True}})]
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
    Helper function to aggregate user count per region from the database.
    Returns a dictionary with regions as keys and user counts as values.
    """
    try:
        # Group by region and count the users in each region
        locations = list(users_collection.aggregate([
            {"$group": {"_id": "$location.region", "count": {"$sum": 1}}}
        ]))
        
        # Convert to dictionary format with region as key and count as value
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
    
    user = request.json
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Using the cache function to get IP information
    ip_info = get_ip_info(ip_address)

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

    # Using the cache function to get Whois data
    whois_data = get_whois_data(ip_address)
    user["whoisData"] = whois_data

    # Save user to MongoDB database
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
@app.route('/email-history', methods=['GET'])
def get_email_history():
    """
    Retrieve the history of sent emails.
    """
    try:
        email_history = list(email_history_collection.find({}))
        email_history = convert_objectid_to_str(email_history)    # Convert Object Id to string for JSON serialization
        return jsonify(email_history), 200
    except Exception as e:
        print(f"Error fetching email history: {e}")
        return jsonify({"error": "Unable to fetch email history"}), 500

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
    
@app.route('/delete-all', methods=['DELETE'])
def delete_all_users():
    """
    Delete all users from the database.
    """
    users_collection.delete_many({})
    return jsonify({"status": "success", "message": "All users deleted"}), 200

@app.route('/generate-file', methods=['POST'])
def generate_file():
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)    # Get the user data from the request
    data = request.json
    user_id = data.get('userId')
    user_data = data.get('userData')
    
    user_data['ipAddress'] = ip_address
    user_data['WhoIs_Data'] = get_whois_data(ip_address)
    user_data['ip_info'] = get_ip_info(ip_address)
    

    # Define a filename based on the user ID
    file_name = f"user_data_report_{user_id}.json"
    file_path = os.path.join("public/exports", file_name)

    # Write the user data to the file
    with open(file_path, 'w') as f:
        json.dump(user_data, f, indent=4)

    # Return the file name in the response
    return jsonify({'fileName': file_name})



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
    #print("AHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH")
    #print(path)
    return send_from_directory('public', path)

@app.route('/filter-users', methods=['GET'])
def filter_users():
    """
    Filter users based on time of visit and WHOIS data presence.
    """
    max_time_of_visit = request.args.get('max_time_of_visit', type=int)
    exclude_whois_none = request.args.get('exclude_whois_none', default=False, type=bool)
    
    # Building the MongoDB filter
    query_filter = {}

    # Exclude users with timeOfVisit > max_time_of_visit
    if max_time_of_visit is not None:
        query_filter['timeOfVisit'] = {"$lte": max_time_of_visit}
    
    # Exclude users with whois = None
    if exclude_whois_none:
        query_filter['whoisData'] = {"$ne": None}

    # Perform the MongoDB query with the specified filters
    users = list(users_collection.find(query_filter))
    users = convert_objectid_to_str(users)

    return jsonify(users), 200


@cache.memoize(timeout=300)
def get_ip_info(ip_address):
    """
    Retrieves IP information using ipinfo.io and caches the results.
    """
    ip_info_url = f'https://ipinfo.io/{ip_address}/json?token={api_key}'
    response = requests.get(ip_info_url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error getting IP information.")
        return None
    

@cache.memoize(timeout=300)
def get_whois_data(ip_address):
    """
    Retrieves Whois data and caches the results.
    """
    whois_url = f'https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey={who_is_api_key}&domainName={ip_address}&outputFormat=JSON'
    response = requests.get(whois_url)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error getting WHOIS data.")
        return None    
      
      
    
      
      
      
      
      
      
      
################################################ OLD MAIL


# Configuration de Flask-Mail
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
# app.config['MAIL_PORT'] = 587  
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = os.environ.get('...')  #  email username
# app.config['MAIL_PASSWORD'] = os.environ.get('...')  # email password 
# app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('...')  #  default sender email


#mail = Mail(app)

# @app.route('/email', methods=['POST'])
# def send_email():
#     """
#     Handle the form submission to send an email.
#     """
#     # Extract the user ID and form data
#     user_id = request.form.get('user_id')
#     email = request.form.get('email')
    
#     if not user_id or not email:
#         return jsonify({"error": "User ID and email are required"}), 400

#     try:
#        # send_mail(user_id, email)  
#         return send_from_directory('public', "awareness_info.html")
#     except Exception as e:
#         print(f"Error sending email: {e}")
#         return jsonify({"error": "Failed to send email"}), 500
    
    
# @app.route('/email', methods=['POST'])
# def send_email():
#     return send_from_directory('public', "awareness_info.html")
    


# def send_mail(user_id, recipient_email):
#     """
#     Simulated email sending function.
#     This should connect to your email service and send an email.
#     """
#     try:
#         msg = Message(
#             subject="Your Requested Information",
#             recipients=[recipient_email],
#             body=f"Hello,\n\nThis is a message containing details for user ID: {user_id}.\n\nThank you!",
#         )
#         mail.send(msg)
#         print(f"Email successfully sent to {recipient_email} for user ID {user_id}")
        
#         # Log the email sent in the email history collection
#         email_history_collection.insert_one({
#             "user_id": user_id,
#             "recipient_email": recipient_email,
#             "sent_at": datetime.now(),
#             "subject": msg.subject,
#             "body": msg.body,
#         })
#     except Exception as e:
#         print(f"Failed to send email: {e}")
#         raise e

######################################################################################################################
      
      
      
   
      
      
      

# lunch application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
