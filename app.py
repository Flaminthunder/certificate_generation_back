from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import pandas as pd
from werkzeug.utils import secure_filename

# Initialize the Flask app
app = Flask(__name__)

# Set up the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
TEMPLATE_FILE = 'template.csv'  # Your template file name

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to check if the file is a CSV
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to serve the template CSV file
@app.route('/download_template')
def download_template():
    return send_from_directory(directory=os.getcwd(), path=TEMPLATE_FILE, as_attachment=True)

# Route for the home page (upload form)
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if a file is part of the request
        file = request.files.get('file')
        
        if file and allowed_file(file.filename):
            # Secure the filename and save it
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Optionally, process the CSV file using pandas
            df = pd.read_csv(filepath)

            # Return the CSV content (can display the first few rows)
            return render_template('index.html', tables=[df.head().to_html(classes='data')], filename=filename)

        else:
            return "Invalid file type. Only CSV files are allowed."

    # Render the upload form on GET request
    return render_template('index.html')

if __name__ == '__main__':
    # Create the uploads folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Run the Flask app
    app.run(debug=True)
