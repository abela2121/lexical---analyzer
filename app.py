from flask import Flask, request, jsonify, render_template
import lexer
from docx import Document
import io
import os

app = Flask(__name__)

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tokenize', methods=['POST'])
def tokenize_endpoint():
    try:
        if request.is_json:
            data = request.get_json()
            source_code = data.get('code', '')

        else:
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400

            file = request.files['file']
            filename = file.filename.lower()

            if filename.endswith(('.txt', '.py', '.cpp', '.c', '.java', '.js', '.ts')):
                source_code = file.read().decode('utf-8')
            elif filename.endswith('.docx'):
                doc = Document(io.BytesIO(file.read()))
                source_code = '\n'.join(para.text for para in doc.paragraphs)
            else:
                return jsonify({'error': f'Unsupported file type: {os.path.splitext(filename)[1]}'}), 400

        if not source_code.strip():
            return jsonify({'error': 'Empty source code provided'}), 400

        tokens = lexer.tokenize(source_code)
        return jsonify({'tokens': tokens})

    except UnicodeDecodeError:
        return jsonify({'error': 'File encoding error — please use UTF-8 encoded files'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)