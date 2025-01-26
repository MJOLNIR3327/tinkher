from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
import sqlite3
from PIL import Image
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'doc', 'docx'}

# Ensure uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Setup
DATABASE = 'files.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        image_data BLOB)''')
    conn.commit()
    conn.close()

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/submit', methods=['POST'])
def upload_file():
    # Validate request
    if 'fileUpload' not in request.files or 'email' not in request.form:
        return jsonify({"error": "Invalid request"}), 400
    
    email = request.form['email']
    file = request.files['fileUpload']

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Open and process the image (example: convert to grayscale)
        with Image.open(filepath) as img:
            img = img.convert("L")  # Convert to grayscale
            img_data = io.BytesIO()
            img.save(img_data, format='JPEG')
            img_data = img_data.getvalue()  # Binary data for SQL storage

        # Save to database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (email, filename, image_data) VALUES (?, ?, ?)",
                       (email, filename, img_data))
        conn.commit()
        conn.close()

        return jsonify({"message": "File uploaded successfully"}), 200
    
    return jsonify({"error": "Invalid file type"}), 400

if __name__ == '__main__':
    init_db()
    app.run(debug=True)