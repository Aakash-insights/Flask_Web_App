from flask import Flask, render_template, request, redirect
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017/")  # Connect to localhost MongoDB
db = client.mydatabase  # Select the database

@app.route('/')
def home():
    admin_data = db.admin.find_one()  # Get admin details
    notes = list(db.notes.find())  # Get all notes
    return render_template('index.html', admin=admin_data, notes=notes)

@app.route('/add_note', methods=['POST'])
def add_note():
    note_content = request.form.get('note')  # Get note from form
    if note_content:
        db.notes.insert_one({"content": note_content})  # Store in MongoDB
    return redirect('/')  # Redirect to home after submission

if __name__ == '__main__':
    app.run(debug=True)
