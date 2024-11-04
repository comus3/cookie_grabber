from functools import wraps
from flask import Flask, session, redirect, url_for, request, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from pymongo import MongoClient

# Initialize Flask app
app = Flask(__name__)

# Database connection
client = MongoClient('mongodb://localhost:27017/')
db = client['cookie_grabber']

# Configuration supplémentaire pour Flask
def configure_auth(app):
    app.secret_key = secrets.token_hex(16)  # Clé secrète pour les sessions
    
    # Création d'une nouvelle collection pour les admins
    global admins_collection
    admins_collection = db['admins']
    
    # Création d'un admin par défaut si aucun n'existe
    if admins_collection.count_documents({}) == 0:
        default_admin = {
            'username': 'admin',
            'password': generate_password_hash('password')
        }
        admins_collection.insert_one(default_admin)

# Décorateur pour protéger les routes qui nécessitent une authentification
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes d'authentification
def add_auth_routes(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            admin = admins_collection.find_one({'username': username})
            
            if admin and check_password_hash(admin['password'], password):
                session['admin_logged_in'] = True
                session['admin_username'] = username
                return redirect(url_for('admin_panel'))
            else:
                flash('Invalid username or password')
                return redirect(url_for('login'))
                
        return '''
            <form method="post">
                <h2>Admin Login</h2>
                <div>
                    <label>Username:</label>
                    <input type="text" name="username" required>
                </div>
                <div>
                    <label>Password:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit">Login</button>
            </form>
        '''

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # Route pour changer le mot de passe
    @app.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            admin = admins_collection.find_one({'username': session['admin_username']})
            
            if not check_password_hash(admin['password'], current_password):
                flash('Current password is incorrect')
                return redirect(url_for('change_password'))
                
            if new_password != confirm_password:
                flash('New passwords do not match')
                return redirect(url_for('change_password'))
                
            admins_collection.update_one(
                {'username': session['admin_username']},
                {'$set': {'password': generate_password_hash(new_password)}}
            )
            
            flash('Password updated successfully')
            return redirect(url_for('admin_panel'))
            
        return '''
            <form method="post">
                <h2>Change Password</h2>
                <div>
                    <label>Current Password:</label>
                    <input type="password" name="current_password" required>
                </div>
                <div>
                    <label>New Password:</label>
                    <input type="password" name="new_password" required>
                </div>
                <div>
                    <label>Confirm New Password:</label>
                    <input type="password" name="confirm_password" required>
                </div>
                <button type="submit">Change Password</button>
            </form>
        '''

# Modification des routes existantes pour ajouter l'authentification
@app.route('/admin_panel')
@login_required
def admin_panel():
    return send_from_directory('public', 'admin_panel.html')

@app.route('/load_users')
@login_required
def load_users():
    users = list(users_collection.find({}))
    users = convert_objectid_to_str(users)
    return jsonify(users), 200

@app.route('/delete_user/<user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    result = users_collection.delete_one({"id": user_id})
    if result.deleted_count > 0:
        return jsonify({"status": "success", "message": "User deleted"}), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/update_user/<user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    updated_data = request.json
    result = users_collection.update_one({"id": user_id}, {"$set": updated_data})
    if result.modified_count > 0:
        updated_user = users_collection.find_one({"id": user_id})
        updated_user = convert_objectid_to_str(updated_user)
        return jsonify({"status": "success", "user_data": updated_user}), 200
    else:
        return jsonify({"error": "User not found or no change detected"}), 404

# Fonction pour initialiser l'authentification
def init_auth(app):
    configure_auth(app)
    add_auth_routes(app)
    
    # Remplacer les routes existantes par les versions protégées
    app.view_functions['admin_panel'] = admin_panel
    app.view_functions['load_users'] = load_users
    app.view_functions['delete_user'] = delete_user
    app.view_functions['update_user'] = update_user

# Initialize authentication
init_auth(app)

if __name__ == '__main__':
    app.run(debug=True)