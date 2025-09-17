from flask import Flask, jsonify, request
import os

app = Flask(__name__)

@app.route('/status')
def status():
    return jsonify({'status': 'ok'})

@app.route('/files', methods=['GET'])
def list_files():
    upload_dir = 'uploaded_files'
    files = []
    if os.path.exists(upload_dir):
        for file in os.listdir(upload_dir):
            files.append(file)
    return jsonify({'files': files})

if __name__ == '__main__':
    app.run(port=5000)