"""import json
import os
import uuid
import cv2
import time
import numpy as np
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import hashlib
import sys
import fitz  # PyMuPDF için gerekli
import pandas as pd  # CSV ve Excel için gerekli
from docx import Document
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

# Sabit değişkenler
DATA_FILE = 'user_data.json'
FACE_ID_DIR = 'face_id_data'
UPLOAD_DIR = 'uploaded_files'


class UserManager:
    @staticmethod
    def load_user_data():
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_user_data(data):
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def register_user(cls, username, password):
        user_data = cls.load_user_data()
        if username in user_data:
            raise ValueError("Kullanıcı adı zaten mevcut!")

        user_data[username] = {
            'password': cls.hash_password(password),
            'face_id_registered': False
        }
        cls.save_user_data(user_data)

    @classmethod
    def login_user(cls, username, password):
        user_data = cls.load_user_data()
        if username in user_data and user_data[username]['password'] == cls.hash_password(password):
            return username
        raise ValueError("Kullanıcı adı veya şifre yanlış!")

    @classmethod
    def get_user_data(cls, username):
        user_data = cls.load_user_data()
        return user_data.get(username, None)


class FaceRecognitionManager:
    @staticmethod
    def register_face_id(username):
        user_data = UserManager.load_user_data()
        if username not in user_data:
            raise ValueError("Kullanıcı adı bulunamadı.")

        face_id_path = os.path.join(FACE_ID_DIR, username)
        os.makedirs(face_id_path, exist_ok=True)

        cap = cv2.VideoCapture(0)
        for i in range(10):
            ret, frame = cap.read()
            if not ret:
                cap.release()
                raise IOError("Kameradan görüntü alınamadı!")

            face_image_path = os.path.join(face_id_path, f'image_{uuid.uuid4().hex}.jpg')
            cv2.imwrite(face_image_path, frame)
            time.sleep(1)

        cap.release()

        user_data[username]['face_id_registered'] = True
        UserManager.save_user_data(user_data)

    @staticmethod
    def load_face_id_data(username):
        face_id_path = os.path.join(FACE_ID_DIR, username)
        face_images = []
        if os.path.exists(face_id_path):
            for file_name in os.listdir(face_id_path):
                img_path = os.path.join(face_id_path, file_name)
                img = cv2.imread(img_path)
                if img is not None:
                    face_images.append(img)
        return face_images

    @staticmethod
    def compare_faces(face1, face2):
        face1_gray = cv2.cvtColor(face1, cv2.COLOR_BGR2GRAY)
        face2_gray = cv2.cvtColor(face2, cv2.COLOR_BGR2GRAY)

        detector = cv2.face.LBPHFaceRecognizer_create()
        detector.train([face1_gray], np.array([0]))
        label, confidence = detector.predict(face2_gray)

        return confidence < 100

    @classmethod
    def face_recognition(cls, username):
        face_images = cls.load_face_id_data(username)
        if not face_images:
            raise ValueError("Yüz görüntüleri bulunamadı.")

        cap = cv2.VideoCapture(0)
        for _ in range(30):
            ret, frame = cap.read()
            if not ret:
                break

            for face_image in face_images:
                if cls.compare_faces(face_image, frame):
                    cap.release()
                    return True

        cap.release()
        return False


class FileManager:
    @staticmethod
    def upload_file():
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(UPLOAD_DIR, file_name)
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            with open(file_path, 'rb') as src, open(dest_path, 'wb') as dest:
                dest.write(src.read())
            return True
        return False

    @staticmethod
    def download_file(file_name):
        src_path = os.path.join(UPLOAD_DIR, file_name)
        if os.path.exists(src_path):
            dest_path = filedialog.asksaveasfilename(initialfile=file_name)
            if dest_path:
                with open(src_path, 'rb') as src, open(dest_path, 'wb') as dest:
                    dest.write(src.read())
                return True
        return False

    @staticmethod
    def preview_file(file_name, root):
        src_path = os.path.join(UPLOAD_DIR, file_name)
        if not os.path.exists(src_path):
            raise FileNotFoundError("Dosya bulunamadı!")

        preview_window = tk.Toplevel(root)
        preview_window.title("Dosya Önizleme")
        preview_window.geometry("600x600")

        file_ext = file_name.lower().split('.')[-1]

        if file_ext == 'pdf':
            pdf_document = fitz.open(src_path)
            page = pdf_document.load_page(0)
            pix = page.get_pixmap()

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img_tk = ImageTk.PhotoImage(img)

            label = tk.Label(preview_window, image=img_tk)
            label.image = img_tk
            label.pack()

            pdf_document.close()

        elif file_ext in ('png', 'jpg', 'jpeg'):
            img = Image.open(src_path)
            img.thumbnail((600, 600))
            img_tk = ImageTk.PhotoImage(img)
            label = tk.Label(preview_window, image=img_tk)
            label.image = img_tk
            label.pack()

        elif file_ext == 'csv':
            df = pd.read_csv(src_path)
            text = df.to_string()
            text_box = tk.Text(preview_window, wrap=tk.WORD)
            text_box.insert(tk.END, text)
            text_box.pack(expand=True, fill=tk.BOTH)

        elif file_ext == 'xlsx':
            df = pd.read_excel(src_path)
            text = df.to_string()
            text_box = tk.Text(preview_window, wrap=tk.WORD)
            text_box.insert(tk.END, text)
            text_box.pack(expand=True, fill=tk.BOTH)

        elif file_ext == 'docx':
            doc = Document(src_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
            text_box = tk.Text(preview_window, wrap=tk.WORD)
            text_box.insert(tk.END, text)
            text_box.pack(expand=True, fill=tk.BOTH)

        else:
            raise ValueError("Desteklenmeyen dosya formatı!")

        preview_window.update_idletasks()
        return preview_window


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dosya Yönetim Uygulaması")
        self.geometry("300x300")
        self.logged_in_user = None
        self.show_login_ui()

    def show_login_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Kullanıcı Adı:").pack(pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Şifre:").pack(pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self, text="Giriş Yap", command=self.login).pack(pady=5)
        tk.Button(self, text="Kayıt Ol", command=self.register).pack(pady=5)
        tk.Button(self, text="Face ID ile Giriş Yap", command=self.face_id_login).pack(pady=5)

    def show_main_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        tk.Button(self, text="Dosya Yükle", command=self.upload_file).pack(pady=5)
        tk.Button(self, text="Dosya İndir", command=self.download_file).pack(pady=5)
        tk.Button(self, text="Dosya Önizle", command=self.preview_file).pack(pady=5)
        tk.Button(self, text="Çıkış Yap", command=self.logout).pack(pady=5)
        tk.Button(self, text="Face ID Kayıt", command=self.register_face_id).pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            UserManager.login_user(username, password)
            self.logged_in_user = username
            self.show_main_ui()

            if not UserManager.get_user_data(username).get('face_id_registered', False):
                if messagebox.askyesno("Face ID Kayıt", "Face ID'nizi kaydetmek ister misiniz?"):
                    self.register_face_id()

        except ValueError as e:
            messagebox.showerror("Giriş Hatası", str(e))

    def face_id_login(self):
        username = self.username_entry.get()

        if not username:
            messagebox.showwarning("Giriş Hatası", "Kullanıcı adı girilmelidir!")
            return

        try:
            if FaceRecognitionManager.face_recognition(username):
                self.logged_in_user = username
                self.show_main_ui()
            else:
                messagebox.showerror("Giriş Hatası", "Face ID uyuşmadı!")

        except ValueError as e:
            messagebox.showerror("Hata", str(e))

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            UserManager.register_user(username, password)
            messagebox.showinfo("Kayıt Başarılı", "Kayıt işlemi başarılı!")
            self.show_login_ui()
        except ValueError as e:
            messagebox.showerror("Kayıt Hatası", str(e))

    def upload_file(self):
        if FileManager.upload_file():
            messagebox.showinfo("Başarı", "Dosya başarıyla yüklendi!")
        else:
            messagebox.showwarning("Uyarı", "Dosya yükleme işlemi başarısız!")

    def download_file(self):
        file_name = simpledialog.askstring("Dosya İndir", "İndirmek istediğiniz dosyanın adını girin:")
        if FileManager.download_file(file_name):
            messagebox.showinfo("Başarı", "Dosya başarıyla indirildi!")
        else:
            messagebox.showwarning("Uyarı", "Dosya indirilemedi!")

    def preview_file(self):
        file_name = simpledialog.askstring("Dosya Önizle", "Önizlemek istediğiniz dosyanın adını girin:")
        try:
            preview_window = FileManager.preview_file(file_name, self)
            preview_window.wait_window()  # Önizleme penceresi kapanana kadar bekle
        except (FileNotFoundError, ValueError) as e:
            messagebox.showerror("Hata", str(e))

    def logout(self):
        self.logged_in_user = None
        self.show_login_ui()

    def register_face_id(self):
        if not self.logged_in_user:
            messagebox.showwarning("Giriş Hatası", "Önce giriş yapmalısınız!")
            return

        try:
            FaceRecognitionManager.register_face_id(self.logged_in_user)
            messagebox.showinfo("Başarı", "Face ID başarıyla kaydedildi!")
        except (ValueError, IOError) as e:
            messagebox.showerror("Hata", str(e))


if __name__ == "__main__":
    app = Application()
    app.mainloop()
"""