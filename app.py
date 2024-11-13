from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from dotenv import load_dotenv  # Import dotenv
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import pytesseract
from PIL import Image
import pdfplumber
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Enable CORS
CORS(app)

# Configure Gemini API
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])

# Set file upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_gemini_response(user_input):
    try:
        response = chat.send_message(user_input)
        formatted_response = response.text.replace('\n', '<br>')
        return formatted_response
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Function to extract text from PDF
def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

# Function to extract text from DOCX
def extract_text_from_docx(filepath):
    try:
        doc = Document(filepath)
        text = ""
        for para in doc.paragraphs:
            text += para.text + '\n'
        return text
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

# Function to extract text from images (using OCR)
def extract_text_from_image(filepath):
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"Error extracting text from Image: {str(e)}"

# Function to extract text from PDF using pdfplumber (for better formatting)
def extract_text_from_pdf_plumber(filepath):
    try:
        with pdfplumber.open(filepath) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        return f"Error extracting text from PDF using pdfplumber: {str(e)}"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    user_input = request.json.get("message")
    response_text = get_gemini_response(user_input)
    return jsonify({"response": response_text})

@app.route("/upload_file", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"response": "No file part"}), 400
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"response": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Process the file based on its type
        file_extension = filename.rsplit('.', 1)[1].lower()
        extracted_text = ""

        if file_extension == 'pdf':
            extracted_text = extract_text_from_pdf(filepath)  # Use pdfplumber as fallback
        elif file_extension == 'docx':
            extracted_text = extract_text_from_docx(filepath)
        elif file_extension in ['jpg', 'jpeg', 'png']:
            extracted_text = extract_text_from_image(filepath)

        if not extracted_text:
            return jsonify({"response": "File uploaded successfully. Do you want to extract text from it?"})

        # Send extracted text to Gemini for processing
        gemini_response = get_gemini_response(extracted_text)
        return jsonify({"response": gemini_response})

    return jsonify({"response": "Invalid file type. Only PDF, DOC, DOCX, JPG, PNG files are allowed."}), 400

if __name__ == "__main__":
    # Ensure the uploads folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(debug=True)
