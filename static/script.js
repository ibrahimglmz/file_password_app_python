// JavaScript kodu için tamamlanmış dosya
const registerBtn = document.getElementById('registerBtn');
const loginBtn = document.getElementById('loginBtn');
const uploadButton = document.getElementById('uploadButton');
const fileInput = document.getElementById('fileUpload');
const fileList = document.getElementById('fileList');

const registerVideo = document.getElementById('registerVideo');
const loginVideo = document.getElementById('loginVideo');

let mediaStream;

// Kamera başlatma işlevi
const startCamera = (videoElement) => {
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            mediaStream = stream;
            videoElement.srcObject = stream;
        })
        .catch(err => console.error('Kamera başlatılamadı:', err));
};

// Fotoğraf çekme işlevi
const capturePhoto = (videoElement) => {
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/png');
};

// Kayıt işlemi
const register = () => {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const image = capturePhoto(registerVideo);

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${username}&password=${password}&image=${encodeURIComponent(image)}`
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.success) {
            window.location.href = '/file_management'; // Yönlendirme ekleyin
        }
    })
    .catch(err => console.error('Kayıt hatası:', err))
    .finally(() => {
        mediaStream.getTracks().forEach(track => track.stop());
    });
};

// Giriş işlemi
const login = () => {
    const username = document.getElementById('loginUsername').value;
    const image = capturePhoto(loginVideo);

    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `username=${username}&image=${encodeURIComponent(image)}`
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.success) {
            window.location.href = '/file_management'; // Yönlendirme ekleyin
        }
    })
    .catch(err => console.error('Giriş hatası:', err))
    .finally(() => {
        mediaStream.getTracks().forEach(track => track.stop());
    });
};

// Dosya yükleme işlemi
const uploadFile = () => {
    const file = fileInput.files[0];
    if (!file) {
        alert('Lütfen bir dosya seçin.');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.success) {
            listFiles(); // Dosya listesini güncelleyin
        }
    })
    .catch(err => console.error('Dosya yükleme hatası:', err));
};

// Dosya listesi getirme ve güncelleme işlemi
const listFiles = () => {
    fetch('/files')
        .then(response => response.json())
        .then(data => {
            fileList.innerHTML = ''; // Listeyi temizle
            data.files.forEach(file => {
                const listItem = document.createElement('li');
                const fileLink = document.createElement('a');
                fileLink.href = `/download/${file}`; // Dosya indirme URL'si
                fileLink.textContent = file;
                fileLink.target = '_blank'; // Yeni sekmede açılacak
                listItem.appendChild(fileLink);
                fileList.appendChild(listItem);
            });
        })
        .catch(err => console.error('Dosya listesi getirme hatası:', err));
};

// Olay dinleyiciler
registerBtn.addEventListener('click', () => {
    startCamera(registerVideo);
    setTimeout(register, 1000); // 1 saniye bekle
});

loginBtn.addEventListener('click', () => {
    startCamera(loginVideo);
    setTimeout(login, 1000); // 1 saniye bekle
});

uploadButton.addEventListener('click', uploadFile);

// Sayfa yüklendiğinde dosyaları listele
document.addEventListener('DOMContentLoaded', listFiles);
