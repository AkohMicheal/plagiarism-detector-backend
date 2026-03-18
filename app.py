import os

from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
from docx import Document
import io

app = Flask(__name__) # Create a Flask application instance
CORS(app) # Allow CORS for all routes

def extract_text(file): # Determine file type and extract text accordingly
    filename = file.filename.lower() # Get the filename and convert to lowercase for easier comparison
    if filename.endswith('.pdf'): # If it's a PDF, use PyPDF2 to read and extract text
        reader = PyPDF2.PdfReader(file) # Create a PDF reader object
        return " ".join([page.extract_text() for page in reader.pages]) # Extract text from each page and join them into a single string
    elif filename.endswith('.docx'): # If it's a Word document, use python-docx to read and extract text
        doc = Document(file) # Create a Document object from the uploaded file
        return " ".join([para.text for para in doc.paragraphs]) # Extract text from each paragraph and join them into a single string
    return file.read().decode('utf-8') # Default for .txt

@app.route('/compare', methods=['POST']) # Define a route for comparing two files
def compare(): # Check if both files are present in the request
    THRESHOLD = 20.0  # Common academic benchmark for plagiarism detection

    if 'file1' not in request.files or 'file2' not in request.files: # If either file is missing, return an error response
        return jsonify({"error": "Please upload two files"}), 400 # Return a JSON response with an error message and a 400 Bad Request status code

    # Extract text from uploaded files
    text1 = extract_text(request.files['file1'])
    text2 = extract_text(request.files['file2'])

    # Group 5 Requirement: N-grams (2, 3) and Cosine Similarity
    vectorizer = TfidfVectorizer(ngram_range=(2, 3)) # Create a TF-IDF vectorizer that considers both bigrams and trigrams
    tfidf_matrix = vectorizer.fit_transform([text1, text2]) # Fit the vectorizer to the two texts and transform them into TF-IDF matrices
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100 # Calculate the cosine similarity between the two TF-IDF vectors and extract the similarity score as a percentage

    # Automatic Labeling - Convert similarity score to binary prediction
    prediction = 1 if score >= THRESHOLD else 0

    return jsonify({
        "similarity": round(score, 2),
        "prediction": prediction,
        "status": "Plagiarized" if prediction == 1 else "Original"
    }) # Return a JSON response with the similarity score, prediction, and status

if __name__ == '__main__':
    # Render and other cloud providers dynamically assign a port. 
    # This checks for that port, and defaults to 5000 for local testing.
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)