from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
import os
import pandas as pd
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import shutil

# Initialize the Flask app
app = Flask(__name__)

# Set up the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
TEMPLATE_FILE = 'template.csv'  # Your template file name
OUTPUT_FOLDER = 'output'
TEMPLATES_FOLDER = 'templates'
FONT_PATH = 'arial.TTF'
FONT_PATH_BOLD = 'ARIALBD.TTF'

# Clear folders before creating them
# for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
#     if os.path.exists(folder):
#         shutil.rmtree(folder)  # Remove all files and subdirectories
#     os.makedirs(folder, exist_ok=True)  # Recreate empty folder


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

static_var = {  'name1': 'Aayushman',
                'name2': 'Mayank',
                'sign1': os.path.join(UPLOAD_FOLDER, 'sign1.png'),
                'sign2': os.path.join(UPLOAD_FOLDER, 'sign1.png'),
                'event': 'Code For Good',
              }

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

@app.route('/generate/<filename>')
def generate_certificates(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return "File not found. Please upload a CSV file."

    df = pd.read_csv(filepath)
    certificates = []
    df.columns = df.columns.str.strip()
    
    for _, row in df.iterrows():
        cert_path = generate_certificate(row['StudentName'], row['Rank'], row['CollegeName'])
        certificates.append(cert_path)
    
    pdf_path = create_pdf(certificates)
    return send_file(pdf_path, as_attachment=True)

from textwrap import wrap

def generate_certificate(name, rank, college):
    """Generates a certificate based on the rank with exact center alignment and text wrapping."""
    
    # Select template based on rank
    template_file = (
        os.path.join(TEMPLATES_FOLDER, 'certificate_excellence.png')
        if rank.lower() != 'participation' else os.path.join(TEMPLATES_FOLDER, 'certificate_participation.png')
    )
    
    img = Image.open(template_file)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    font_large = ImageFont.truetype(FONT_PATH, 80)
    font_small = ImageFont.truetype(FONT_PATH, 50)

    font_bold = ImageFont.truetype(FONT_PATH_BOLD, 50)


    if rank.lower() == 'participation':
        text_parts = [
            "This certificate is awarded to ", (name, True),
            " from ", (college, True),
            " for participation in ", (static_var['event'], True), "."
        ]
    else:
        text_parts = [
            "This certificate is awarded to ", (name, True),
            " from ", (college, True),
            " for achieving ", (rank, True),
            " rank in ", (static_var['event'], True), "."
        ]

    # **Wrap text to fit within 1600px width**
   # **Wrap text while keeping bold formatting**
    max_width = 1600  
    wrapped_lines = []
    current_line = []
    current_width = 0

    for part in text_parts:
        word, is_bold = part if isinstance(part, tuple) else (part, False)
        font = font_bold if is_bold else font_small
        word_width = draw.textbbox((0, 0), word, font=font)[2]

        # If adding the word exceeds max width, start a new line
        if current_width + word_width > max_width:
            wrapped_lines.append(current_line)
            current_line = []
            current_width = 0

        current_line.append((word, is_bold))
        current_width += word_width

    if current_line:
        wrapped_lines.append(current_line)

    # **Center and draw wrapped text**
    y_position = 600  
    for line_parts in wrapped_lines:
        text_width = sum(draw.textbbox((0, 0), word, font=(font_bold if is_bold else font_small))[2] for word, is_bold in line_parts)
        text_x = 1000 - (text_width // 2)  # Center align

        x_cursor = text_x
        for word, is_bold in line_parts:
            font = font_bold if is_bold else font_small
            draw.text((x_cursor, y_position), word, fill="black", font=font)
            x_cursor += draw.textbbox((0, 0), word, font=font)[2]  # Move cursor forward

        y_position += 60  # Move down for the next line






    # Load signatures & resize
    sign1 = Image.open(static_var['sign1']).convert("RGBA").resize((100, 80))
    sign2 = Image.open(static_var['sign2']).convert("RGBA").resize((100, 80))

    # Draw names with center alignment
    name1_width = draw.textbbox((0, 0), static_var['name1'], font=font_small)[2]
    name2_width = draw.textbbox((0, 0), static_var['name2'], font=font_small)[2]

    name1_x = 550 - (name1_width // 2)  # Center at 500px
    name2_x = 1450 - (name2_width // 2)  # Center at 1400px

    draw.text((name1_x, 1100), static_var['name1'], fill="black", font=font_small)
    draw.text((name2_x, 1100), static_var['name2'], fill="black", font=font_small)

    # Paste signatures centered at (500, 950) and (1400, 950)
    sign1_x = 550 - (100 // 2)  # Center at 500px
    sign2_x = 1450 - (100 // 2)  # Center at 1400px

    img.paste(sign1, (sign1_x, 950), sign1)
    img.paste(sign2, (sign2_x, 950), sign2)

    # Save the certificate
    cert_path = os.path.join(OUTPUT_FOLDER, f"{name}_certificate.png")
    img.save(cert_path)
    
    return cert_path



def create_pdf(certificates):
    """Combines all certificates into a single PDF."""
    pdf_path = os.path.join(OUTPUT_FOLDER, 'certificates.pdf')
    c = canvas.Canvas(pdf_path, pagesize=(2000, 1400))
    
    for cert in certificates:
        c.drawInlineImage(cert, 0, 0, width=2000, height=1400)
        c.showPage()
    
    c.save()
    return pdf_path


if __name__ == '__main__':
    # Create the uploads folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # Run the Flask app
    app.run(debug=True)
