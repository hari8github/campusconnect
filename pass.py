from pymongo import MongoClient
from flask_bcrypt import Bcrypt

# Initialize Bcrypt
bcrypt = Bcrypt()

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI
db = client["admin"]  # Database name
new_collection = db["CampusConnect"]  # New collection name

# Document to be added
username = "admin"
password = "admin"  # Plaintext password

# Hash the password
hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

# Create the document
user_document = {
    "username": username,
    "password": hashed_password
}

# Insert the document into the collection
new_collection.insert_one(user_document)

print("User added to new_collection!")
