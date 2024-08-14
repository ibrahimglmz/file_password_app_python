import cv2
import uuid
import os
import time




#TODO Kamera testi



def capture_images_from_camera(user_name, num_images=10, delay=1):
    """Kameradan belirli sayıda fotoğraf çeker ve kaydeder."""
    cap = cv2.VideoCapture(0)  # Varsayılan kamera kullanılır
    if not cap.isOpened():
        print("Kamera açılamadı.")
        return None

    # Kullanıcı adı için bir klasör oluştur
    face_id_folder = os.path.join('face_id_data', user_name)
    if not os.path.exists(face_id_folder):
        os.makedirs(face_id_folder)

    file_paths = []
    for i in range(num_images):
        try:
            ret, frame = cap.read()
            if not ret:
                print(f"Görüntü alınamadı ({i+1}/{num_images}).")
                continue

            # Her fotoğraf için benzersiz bir dosya adı oluştur
            file_path = os.path.join(face_id_folder, f'image_{uuid.uuid4().hex}.jpg')
            cv2.imwrite(file_path, frame)
            file_paths.append(file_path)
            print(f"Fotoğraf kaydedildi: {file_path}")

            # Belirtilen süre kadar bekle
            time.sleep(delay)

        except Exception as e:
            print(f"Fotoğraf çekme hatası: {e}")

    cap.release()
    return file_paths
