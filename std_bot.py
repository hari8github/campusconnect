from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from test2 import StudentAcademicChatbot
import json, os
from datetime import datetime, timedelta
import secrets
from dotenv import load_dotenv
from signup import signup_app
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from mail import send_email  # Import both functions

load_dotenv()

# Initialize Flask and Bcrypt
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "your-secret-key"
app.register_blueprint(signup_app, url_prefix='/signup')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# User model for Flask-Login
class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

# Load user callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({"email": user_id})
    if user_data:
        return User(user_data["email"], user_data["email"])
    return None

# Google OAuth blueprint
google_blueprint = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["profile", "email"],
    redirect_to="google_login"
)
app.register_blueprint(google_blueprint, url_prefix="/login")

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI
db = client["admin"]  # Database name
campus_connect_collection = db["CampusConnect"]  # Collection with admin credentials
users_collection = db["Signed_up_users"]  # Collection with user credentials

# Initialize chatbot
academic_chatbot = StudentAcademicChatbot()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    # Fetch user from MongoDB
    user = campus_connect_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):
        # Set session to indicate user is logged in
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"message": "Login successful!", "redirect": url_for('chatbot')}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    # Redirect to login page
    return redirect(url_for('home'))

@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    # Check if user is logged in
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    return render_template('test.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    # Check if user is logged in
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    query = data.get('message', '')
    student_id = data.get('student_id')

    try:
        response = academic_chatbot.chat(query, student_id)
        return jsonify({"message": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/forgot-password', methods=['GET'])
def forgot_password_page():
    return render_template('forgot_password.html')

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email address is required."}), 400

    try:
        send_email(
            subject="Password Reset Request",
            body=(
                "Dear User,\n\n"
                "We received a request to reset your password. If you did not initiate this request, please ignore this email.\n\n"
                "To reset your password, please click the link below:\n"
                "http://example.com/reset-password?email={email}\n\n"
                "This link will expire in 24 hours. If you need further assistance, contact our support team.\n\n"
                "Best regards,\n"
                "Campus Connect Team"
            ).format(email=email),
            to_email=email
        )
        return jsonify({"message": "Password reset link has been sent."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password_endpoint():
    if request.method == 'POST':
        data = request.json
        token = data.get('token')
        new_password = data.get('new_password')

        # Validate token and find user
        user = campus_connect_collection.find_one({"reset_token": token})

        if not user or user['reset_token_expiry'] < datetime.utcnow():
            return jsonify({'error': 'Invalid or expired token'}), 400

        # Hash new password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        # Update user password and clear reset token
        campus_connect_collection.update_one(
            {"reset_token": token},
            {
                "$set": {
                    "password": hashed_password,
                    "reset_token": None,
                    "reset_token_expiry": None
                }
            }
        )

        return jsonify({'message': 'Password has been reset successfully.'}), 200

    return render_template('reset_password.html')

@app.route("/login/google")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return "Failed to fetch user info from Google.", 400

    user_info = resp.json()
    email = user_info["email"]

    # Check if user exists in the database
    user = users_collection.find_one({"email": email})
    if not user:
        # Create a new user in the database
        users_collection.insert_one({
            "email": email,
            "username": user_info.get("name", email.split("@")[0]),
            "password": None  # No password for Google-authenticated users
        })

    # Log the user in
    user_obj = User(email, email)
    login_user(user_obj)
    session['logged_in'] = True
    session['username'] = email

    return redirect(url_for("chatbot"))

@app.route('/compare_students', methods=['GET'])
def compare_students_route():
    student1 = request.args.get('student1')
    student2 = request.args.get('student2')
    
    if not student1 or not student2:
        return jsonify({'error': 'Please provide both student IDs'}), 400
    
    try:
        # Use the chatbot's retrieve_student_data method
        student_data1 = academic_chatbot.retrieve_student_data(student1)
        student_data2 = academic_chatbot.retrieve_student_data(student2)
        
        if not student_data1 or not student_data2:
            return jsonify({'error': 'One or both student IDs are invalid'}), 404
        
        comparison_data = {
            'Student 1': {
                'name': student1.split(' - ')[0],  # Extract name from ID
                'GPA': student_data1.get('academic_details', {}).get('academic_performance', {}).get('cgpa', 'N/A'),
                'Credits': student_data1.get('academic_details', {}).get('credits_completed', 'N/A'),
                'Attendance': student_data1.get('academic_details', {}).get('attendance', {}).get('percentage', 'N/A')
            },
            'Student 2': {
                'name': student2.split(' - ')[0],  # Extract name from ID
                'GPA': student_data2.get('academic_details', {}).get('academic_performance', {}).get('cgpa', 'N/A'),
                'Credits': student_data2.get('academic_details', {}).get('credits_completed', 'N/A'),
                'Attendance': student_data2.get('academic_details', {}).get('attendance', {}).get('percentage', 'N/A')
            }
        }
        
        return jsonify(comparison_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/handle_common_details_query', methods=['GET'])
def handle_common_details_query():
    try:
        # Use the method from your StudentAcademicChatbot class
        common_details = academic_chatbot.handle_common_details_query()
        
        # Add ranking based on CGPA
        sorted_students = sorted(common_details, key=lambda x: x['cgpa'], reverse=True)
        for i, student in enumerate(sorted_students, 1):
            student['rank'] = i
        
        return jsonify(sorted_students)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)