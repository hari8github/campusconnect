from flask import Blueprint, request, jsonify, render_template
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from flask_cors import CORS
import re, os
import secrets
from datetime import datetime

# Create a Blueprint
signup_app = Blueprint('signup_app', __name__)

# Initialize Bcrypt
bcrypt = Bcrypt()

# MongoDB Connection
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["admin"]
    users_collection = db["Signed_up_users"]
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # In a production environment, you'd want more robust error handling

@signup_app.route('/')
def signup_page():
    return render_template('signup.html')

@signup_app.route('/signup', methods=['POST'])
def signup():
    # Get data from request
    data = request.json
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirmPassword', '')
    institution = data.get('institution', '').strip()
    course = data.get('course', '').strip()

    # Validation checks
    if not email or not password or not confirm_password:
        return jsonify({
            'success': False, 
            'message': 'All fields are required'
        }), 400

    # Validate email format (assuming srcas email)
    if not re.match(r'^[a-zA-Z0-9._%+-]+@srcas\.ac.in$', email):
        return jsonify({
            'success': False, 
            'message': 'Please use a valid srcas email'
        }), 400

    # Check if email already exists
    existing_user = users_collection.find_one({'email': email})
    if existing_user:
        return jsonify({
            'success': False, 
            'message': 'Email already registered'
        }), 400

    # Password validation
    if password != confirm_password:
        return jsonify({
            'success': False, 
            'message': 'Passwords do not match'
        }), 400

    # Password strength validation
    if not is_password_strong(password):
        return jsonify({
            'success': False, 
            'message': 'Password must be at least 8 characters long, contain uppercase, lowercase, number, and special character'
        }), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Create new user document
    new_user = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': hashed_password,
        'institution': institution,
        'course': course,
        'created_at': datetime.utcnow()
    }

    # Insert new user
    try:
        users_collection.insert_one(new_user)
        
        return jsonify({
            'success': True, 
            'message': 'Account created successfully'
        }), 201
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'Error creating account. Please try again.'
        }), 500

def is_password_strong(password):
    """
    Password strength validation:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    
    # Check for at least one uppercase, one lowercase, one digit, and one special character
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    
    return True