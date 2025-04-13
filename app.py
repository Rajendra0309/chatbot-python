from flask import Flask, render_template, request, jsonify, session
import os
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import pytesseract
from PIL import Image
import pdfplumber
from flask_cors import CORS
import uuid
import bleach
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))
CORS(app)

gemini_api_key = os.getenv('GEMINI_API_KEY')
gemini_model = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')

if not gemini_api_key:
    raise ValueError("No Gemini API key found. Please set the GEMINI_API_KEY environment variable.")

genai.configure(api_key=gemini_api_key)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_gemini_response(user_input):
    try:
        model = genai.GenerativeModel(gemini_model)
        response = model.generate_content(
            user_input,
            generation_config={"temperature": 0.7, "max_output_tokens": 2048}
        )
        
        if hasattr(response, 'text'):
            lines = response.text.split('\n')
            in_list = False
            result = []
            
            for line in lines:
                if line.strip().startswith('* ') or line.strip().startswith('- '):
                    if not in_list:
                        result.append('<ul>')
                        in_list = True
                    item_text = line.strip()[2:]
                    result.append(f'<li>{item_text}</li>')
                elif line.strip().startswith('**') and line.strip().endswith('**'):
                    if in_list:
                        result.append('</ul>')
                        in_list = False
                    heading_text = line.strip().replace('**', '')
                    result.append(f'<h4>{heading_text}</h4>')
                else:
                    if in_list:
                        result.append('</ul>')
                        in_list = False
                    if line.strip():
                        result.append(f'<p>{line}</p>')
                    else:
                        result.append('<br>')
            
            if in_list:
                result.append('</ul>')
                
            return ''.join(result)
        else:
            return "The AI couldn't generate a response for this query. Please try rephrasing your question."
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        return f"An error occurred with Gemini AI: {str(e)}"

def extract_text(filepath, file_extension):
    extractors = {
        'pdf': extract_text_from_pdf,
        'docx': extract_text_from_docx,
        'jpg': extract_text_from_image,
        'jpeg': extract_text_from_image,
        'png': extract_text_from_image
    }
    
    extractor = extractors.get(file_extension)
    if not extractor:
        return ""
    
    return extractor(filepath)

def extract_text_from_pdf(filepath):
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            if text.strip():
                return text
       
        return extract_text_from_pdf_plumber(filepath)
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_docx(filepath):
    try:
        doc = Document(filepath)
        text = ""
        for para in doc.paragraphs:
            text += para.text + '\n'
        return text
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

def extract_text_from_image(filepath):
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        return f"Error extracting text from Image: {str(e)}"

def extract_text_from_pdf_plumber(filepath):
    try:
        with pdfplumber.open(filepath) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text
    except Exception as e:
        return f"Error extracting text from PDF using pdfplumber: {str(e)}"

def sanitize_input(text):
    return bleach.clean(text)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_response", methods=["POST"])
def get_response():
    try:
        user_input = sanitize_input(request.json.get("message", ""))
        if not user_input:
            return jsonify({"error": "Empty message"}), 400
            
        response_text = get_gemini_response(user_input)
        return jsonify({"response": response_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/upload_file", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_id = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            safe_filename = f"{file_id}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
                
            file.save(filepath)
            
            file_extension = filename.rsplit('.', 1)[1].lower()
            extracted_text = extract_text(filepath, file_extension)
            
            if not extracted_text:
                return jsonify({"response": "File uploaded but no text could be extracted. Is this file readable?"})
            
            prompt = f"Here's the extracted text from a {file_extension.upper()} file. Please analyze it and provide a comprehensive summary: \n\n{extracted_text}"
            ai_response = get_gemini_response(prompt)
            
            return jsonify({"response": ai_response, "filename": filename})
            
        except Exception as e:
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    
    return jsonify({"error": "Invalid file type. Only PDF, DOCX, JPG, JPEG, PNG files are allowed."}), 400

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"error": "File too large. Maximum size is 10MB."}), 413

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    app.run(debug=True, host="0.0.0.0")