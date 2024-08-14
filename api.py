import os
import json
import base64
import logging
from io import BytesIO
import numpy as np
import pandas as pd
from PIL import Image
import face_recognition
import bcrypt
from django.http import HttpResponse
import requests
from docx import Document
from html import escape
from flask import Flask, request, make_response, jsonify

from flask import Flask, request, jsonify, send_from_directory, send_file, url_for, session, render_template, redirect
from flask_cors import CORS
from pdf2image import convert_from_path

app = Flask(__name__)
CORS(app)

# Loglama ayarları
logging.basicConfig(level=logging.DEBUG)

# Sabit değişkenler
ANLIK_KULLANICI_FOLDER = 'anlik_kullanici'  #TODO sisteme anlık giriş yapan kullanıcının verisini saklar

UPLOAD_FACE = "face_id_info"  #TODO Fotografı cekilen fotografın embeding base64 verisini kayıt eder
UPLOAD_FOLDER = 'uploaded_files'  #TODO  kullanıcıların sisteme yükldiği dosyaların saklandıgı yer
FACE_ENCODINGS_FOLDER = 'face_encodings'  #TODO embeding yapılan resimlerin (.npz) formatında  saklandıgı yer
ALLOWED_EXTENSIONS = {'pdf', 'jpeg', 'png', 'jpg', 'xls', 'xlsx', 'txt', 'doc', 'docx'}  #TODO  Deskteklenen dosya formatları

json_folder = 'file_password_app copy/anlik_kullanici/' #TODO BURAYA  cıhazınızda ki "anlik_kullanici" klasor yolunu yazınız
json_filename = 'data.json'

app.config['UPLOAD_FOLDER'] = 'uploaded_files'





@app.route('/to_index', methods=['GET'])
def to_index():
    # 'index' adında bir rota tanımlanmış olmalı
    return redirect(url_for('index'))


@app.route('/uploaded_files/<filename>')
def uploaded_files(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


def convert_word_to_html(file_path):
    doc = Document(file_path)
    html_content = "<html><body>"

    for para in doc.paragraphs:
        html_content += f"<p>{escape(para.text)}</p>"

    html_content += "</body></html>"
    return html_content


def determine_file_type(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension in ['.txt']:
        return 'text'
    elif file_extension in ['.html']:
        return 'html'
    elif file_extension in ['.pdf']:
        return 'pdf'
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
        return 'image'
    elif file_extension in ['.xls']:
        return 'xls'
    elif file_extension in ['.xlsx']:
        return 'xlsx'
    elif file_extension in ['.docx']:
        return 'docx'
    elif file_extension in ['.doc']:
        return 'doc'
    elif file_extension in ['.ppt', '.pptx']:
        return 'powerpoint'
    else:
        return 'Dosya Formatı bulunamadı .'



def get_current_username():
    # Kullanıcının oturum açıp açmadığını kontrol et
    if 'username' in session:
        return session['username']
    return None


@app.route('/anlik_kullanici/data.json', methods=['GET'])
def get_user_data():
    try:
        return send_from_directory(json_folder, json_filename)
    except FileNotFoundError:
        return jsonify({'error': 'Kullanıcı dosyası bulunamadı.'}), 404


# Klasör oluşturma
for folder in [ANLIK_KULLANICI_FOLDER, UPLOAD_FOLDER, FACE_ENCODINGS_FOLDER, UPLOAD_FACE]:
    os.makedirs(folder, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def decode_base64(base64_string):
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        padding = '=' * (-len(base64_string) % 4)
        base64_string += padding
        return base64.b64decode(base64_string)
    except Exception as e:
        raise ValueError(f"Base64 çözme hatası: {str(e)}")


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)


def detect_and_encode_face(image):
    face_image = np.array(image)
    face_locations = face_recognition.face_locations(face_image)
    if not face_locations:
        raise ValueError("Yüz bulunamadı.")
    face_encodings = face_recognition.face_encodings(face_image, face_locations)
    if not face_encodings:
        raise ValueError("Yüz kodlaması alınamadı.")
    return face_encodings


def save_username(username):  #TODO  Anlık sisteme giriş yapan kullanıcıların verisini kayıt eder
    file_path = os.path.join(ANLIK_KULLANICI_FOLDER, "data.json")
    with open(file_path, 'w') as file:
        json.dump({'username': username}, file)



@app.route('/get_current_username', methods=['GET'])
def get_current_username():

    filename = request.args.get('filename')
    username = request.args.get('username')

    if not filename or not username:
        return jsonify({'error': 'Geçersiz istek'}), 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': 'Dosya bulunamadı'}), 404

    ext = filename.split('.')[-1].lower()

    if ext in ['txt', 'html']:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        return jsonify({'type': ext, 'content': content})
    elif ext in ['xls', 'xlsx']:
        df = pd.read_excel(filepath)
        html_table = df.to_html(classes='table table-striped', index=False)
        return jsonify({'type': ext, 'content': html_table})

    elif ext in ['pdf']:
        return jsonify({'type': ext, 'url':f'/uploaded_files/{filename}'})


    elif ext in ['docx', 'doc']:
          with open(filepath, 'rb') as f:
           encoded_content = base64.b64encode(f.read()).decode('utf-8')
           return jsonify({'type': ext, 'content': encoded_content})





    elif ext in ['jpg', 'jpeg', 'png']:
        return jsonify({'type': ext, 'url': f'/uploaded_files/{filename}'})

    else:
        return jsonify({'error': 'Desteklenmeyen dosya türü'}), 400

@app.route('/')  #TODO Flask Api kullanımı icin ana sayfa
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/to_file_management', methods=['GET', 'POST'])
def to_file_management():
    return send_from_directory('templates', 'file_management.html')



@app.route('/file_management')  #TODO Flask Api icin dosya paylaşımı yapılan sayfa
def file_management():

    username = request.cookies.get('username')
    face_encoding = request.cookies.get('face_encoding')

    if not username or not face_encoding:
        return redirect('to_file_management')
    return send_from_directory('templates', 'file_management.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Dosya mevcut değil'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Dosya adı boş'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Desteklenmeyen dosya türü'}), 400

    try:
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        _, ext = os.path.splitext(filename)
        ext = ext.lower().strip('.')
        if ext == 'pdf':
            pdf_url = url_for('serve_file', filename=filename, _external=True)
            return jsonify({'success': True, 'message': f'Dosya {filename} olarak yüklendi', 'pdf_url': pdf_url})

        return jsonify({'success': True, 'message': f'Dosya {filename} olarak yüklendi'})

    except Exception as e:
        logging.error(f"Dosya yükleme hatası: {str(e)}")
        return jsonify({'success': False, 'message': 'Dosya yükleme hatası'}), 500


@app.route('/files', methods=['GET'])
def list_files():
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify(files)


@app.route('/download', methods=['GET'])
def download():
    filename = request.args.get('filename')
    if not filename:
        return "Dosya bulunamadı", 404

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        return "Dosya bulunamadı", 404

    return send_file(filepath, as_attachment=True)

@app.route('/preview', methods=['GET'])
def preview():
    filename = request.args.get('filename')
    username = request.args.get('username')
    face_encoding = request.args.get('face_encoding')

    logging.debug(f"Filename: {filename}")
    logging.debug(f"Username: {username}")
    logging.debug(f"Face Encoding: {face_encoding[:30]}...")  # Log only the first 30 characters for readability

    if not filename:
        return "Dosya adı sağlanmamış", 400

    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        return "Dosya bulunamadı", 404

    # Face ID doğrulama
    face_id_verification = verify_face_id(username, face_encoding)
    if not face_id_verification.get("success"):
        return jsonify({"error": "Face ID doğrulaması başarısız"}), 401

    _, ext = os.path.splitext(filename)
    ext = ext.lower().strip('.')

    if ext == 'txt':
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'type': 'text', 'content': content})

    elif ext in ['xls', 'xlsx']:
        df = pd.read_excel(filepath)
        html_table = df.to_html(classes='table table-striped', index=False)
        return jsonify({'type': ext, 'content': html_table})

    elif ext == 'pdf':
        pdf_folder = os.path.join(UPLOAD_FOLDER, f"{os.path.splitext(filename)[0]}_Fold")
        if not os.path.exists(pdf_folder):
            return "PDF dönüştürme hatası", 500

        image_files = [f for f in os.listdir(pdf_folder) if f.endswith('.png')]
        image_files.sort()
        return jsonify({'type': 'pdf',
                        'images': [
                            url_for('serve_image', filename=os.path.join(f"{os.path.splitext(filename)[0]}_Fold", img))
                            for img in image_files]})

    elif ext in ['jpeg', 'png', 'jpg']:
        return jsonify({'type': 'image', 'url': url_for('serve_image', filename=filename)})

    elif ext in ['docx', 'doc']:
        try:
            html_content = convert_word_to_html(filepath)
            return jsonify({'type': ext, 'content': html_content})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


    else:
        return jsonify({'error': 'Desteklenmeyen dosya türü'}), 400



@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Kullanıcı adı ve şifre gerekli"}), 400

    user_file = os.path.join(FACE_ENCODINGS_FOLDER, f"{username}.npz")
    password_file = os.path.join(UPLOAD_FACE, f"{username}_password.txt")

    if os.path.exists(user_file) and os.path.exists(password_file):
        with open(password_file, 'rb') as f:
            stored_hash = f.read().strip()

        if verify_password(password, stored_hash):
            save_username(username)
            return jsonify({"message": "Başarılı giriş", "redirect": url_for('file_management')})

    return jsonify({"message": "Geçersiz kullanıcı adı veya şifre"}), 401


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    face_encoding = data.get('face_encoding')

    if not username or not password or not face_encoding:
        return jsonify({"message": "Kullanıcı adı, şifre ve yüz verisi gerekli"}), 400

    user_file = os.path.join(FACE_ENCODINGS_FOLDER, f"{username}.npz")
    password_file = os.path.join(UPLOAD_FACE, f"{username}_password.txt")
    json_file = os.path.join('persons', f'{username}.json')

    if os.path.exists(user_file) or os.path.exists(password_file):
        return jsonify({"message": "Kullanıcı zaten mevcut"}), 400

    try:
        face_image_data = decode_base64(face_encoding)
        face_image = Image.open(BytesIO(face_image_data))
        face_encodings = detect_and_encode_face(face_image)

        if face_encodings:
            np.savez_compressed(user_file, encodings=face_encodings[0])
            hashed_password = hash_password(password)
            with open(password_file, 'wb') as f:
                f.write(hashed_password)

            user_data = {
                "username": username,
                "password": hashed_password.decode(),
                "face_encoding": face_encoding
            }
            with open(json_file, 'w') as f:
                json.dump(user_data, f, indent=4)

            return jsonify({"message": "Kullanıcı başarıyla kaydedildi"})

    except Exception as e:
        logging.error(f"Kullanıcı kaydı hatası: {str(e)}")
        return jsonify({"message": "Kullanıcı kaydı başarısız"}), 500


@app.route('/face_id_login', methods=['POST'])
def face_id_login():
    data = request.json
    username = data.get('username')
    face_encoding = data.get('face_encoding')

    if not username or not face_encoding:
        return jsonify({"message": "Kullanıcı adı ve yüz verisi gerekli"}), 400

    user_file = os.path.join(FACE_ENCODINGS_FOLDER, f"{username}.npz")

    if not os.path.exists(user_file):
        return jsonify({"message": "Kullanıcı bulunamadı"}), 404

    try:
        face_image_data = decode_base64(face_encoding)
        face_image = Image.open(BytesIO(face_image_data))
        face_encodings = detect_and_encode_face(face_image)

        if not face_encodings:
            return jsonify({"message": "Yüz kodlaması alınamadı"}), 400

        npz_data = np.load(user_file)
        user_face_encoding = npz_data['encodings']
        matches = face_recognition.compare_faces([user_face_encoding], face_encodings[0])

        if True in matches:
            save_username(username)
            return jsonify({"message": "Başarıyla giriş yapıldı", "redirect": url_for('file_management')})

    except Exception as e:
        logging.error(f"Face ID login hatası: {str(e)}")
        return jsonify({"message": "Giriş işlemi başarısız"}), 500

    return jsonify({"message": "Geçersiz yüz verisi"}), 401


"""
    Sisteme giriş yapan kullanıcının username bilgisini,
    "anlik_kullanici/data.json" ile otomatik alır ve aynı username'e sahip (.npz) dosyasını karşılaştırır.

"""


@app.route('/verify-face-id', methods=['POST'])
def verify_face_id():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    username = data.get('username')
    face_encoding = data.get('face_encoding')

    if not username or not face_encoding:
        return jsonify({"success": False, "message": "Kullanıcı adı ve yüz verisi gerekli"}), 400

    user_file = os.path.join(FACE_ENCODINGS_FOLDER, f"{username}.npz")

    if not os.path.exists(user_file):
        return jsonify({"success": False, "message": "Kullanıcı bulunamadı"}), 404

    try:
        face_image_data = decode_base64(face_encoding)
        face_image = Image.open(BytesIO(face_image_data))
        face_encodings = detect_and_encode_face(face_image)

        if not face_encodings:
            return jsonify({"success": False, "message": "Yüz kodlaması alınamadı"}), 400

        npz_data = np.load(user_file)
        user_face_encoding = npz_data['encodings']

        matches = face_recognition.compare_faces([user_face_encoding], face_encodings[0])
        if True in matches:
            return jsonify({"success": True, "message": "Başarıyla doğrulandı"})

        return jsonify({"success": False, "message": "Geçersiz yüz verisi"}), 401

    except Exception as e:
        logging.error(f"Face ID doğrulama hatası: {str(e)}")
        return jsonify({"success": False, "message": "Doğrulama işlemi başarısız"}), 500


@app.route('/serve_file/<path:filename>')
def serve_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)





@app.route('/set_cookies', methods=['POST'])
def set_cookies():
    data = request.json
    username = data.get('username')
    face_encoding = data.get('face_encoding')

    resp = make_response(jsonify(message="Çerezler ayarlandı!"))
    resp.set_cookie('username', username)
    resp.set_cookie('face_encoding', face_encoding)
    print(f"Çerezler ayarlandı: username={username}, face_encoding={face_encoding}")

    return resp


@app.route('/get_cookies', methods=['GET'])
def get_cookies():
    username = request.cookies.get('username')
    face_encoding = request.cookies.get('face_encoding')

    return jsonify({
        'username': username,
        'face_encoding': face_encoding
    })


@app.route('/clear_cookies', methods=['POST'])
def clear_cookies():

    resp = make_response(jsonify(message="Çerezler temizlendi!"))
    resp.set_cookie('username', 'verified', expires=0)
    resp.set_cookie('face_encoding', 'verified', expires=0)
    print("Çerezler temizlendi!")
    return resp




if __name__ == '__main__':
    app.run(port=0, debug=True)

    #TODO ios cıhazlar icin port numarası "5001" den büyük olunması lazım (AirDrop Cakışması)

