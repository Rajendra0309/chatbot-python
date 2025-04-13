# Gemini Chatbot

A Flask-based web application that integrates with Google's Gemini AI to create an interactive chatbot interface. This application allows users to ask questions directly or upload documents (PDF, DOCX, images) for the AI to process and respond to.

## Features

- 💬 Real-time chat interface with Gemini AI
- 📁 Document upload and processing (PDF, DOCX, JPG, PNG)
- 🔍 Text extraction from various file formats
- 💾 Chat history persistence using local storage
- 🔄 Loading indicators during AI processing
- 🌓 Light/Dark mode toggle with system preference detection
- 📱 Responsive design for mobile and desktop
- 🔒 Input sanitization and error handling
- 🧹 Clear chat functionality

## Technologies Used

- **Backend**: Python, Flask, Flask-CORS
- **Frontend**: HTML, CSS, JavaScript, jQuery
- **AI**: Google Generative AI (Gemini 1.5 Pro)
- **Document Processing**:
  - PDF: PyPDF2, pdfplumber
  - DOCX: python-docx
  - Images: Pillow, pytesseract (OCR)
- **Security**: Bleach (input sanitization), UUID (secure file naming)

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key

### Installation Steps

1. Clone this repository:
   ```
   git clone https://github.com/Rajendra0309/chatbot-python.git
   cd chatbot-python
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your Gemini API key:
   ```
   SITE_NAME=Gemini Chatbot
   SITE_URL=http://localhost:5000
   GEMINI_MODEL=gemini-1.5-pro
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_secret_key_here
   DEBUG=True
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your browser and navigate to `http://127.0.0.1:5000/`

## Usage

### Text Interaction

1. Type your question in the input field at the bottom of the interface
2. Press "Send" or hit Enter to submit your question
3. The AI will process your request and display the response in the chat window

### File Upload

1. Click the "Upload" button
2. Select a PDF, DOCX, or image file
3. The application will extract text from the file and send it to Gemini AI
4. View the AI's analysis or summary of the document in the chat

### Theme Selection

- Use the dropdown menu in the top-right corner to switch between:
  - System Default (follows your device settings)
  - Light Mode
  - Dark Mode

### Chat Management

- Click the "Clear Chat" button to reset the conversation
- Chat history is automatically saved in your browser's local storage

## Project Structure

- `app.py`: Main Flask application file
- `templates/index.html`: Frontend user interface
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (not tracked in git)
- `uploads/`: Directory for temporarily storing uploaded files
