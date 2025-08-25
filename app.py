from flask import Flask, render_template, Response, jsonify
from flask_cors import CORS
import cv2
import sys
import threading
import time

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для внешних запросов

# Камера 1 - Локальная веб-камера
camera1 = cv2.VideoCapture(0)
camera1_name = "Web Camera"

# Камера 2 - Внешняя камера (телефон)
camera2 = None
camera2_name = "Phone Camera"
camera2_url = "http://192.168.0.101:8080/videofeed"  # Замените на IP вашего телефона

def init_cameras():
    """Инициализация камер"""
    # Проверяем первую камеру
    if camera1.isOpened():
        print(f"✓ {camera1_name} подключена", file=sys.stderr)
    else:
        print(f"✗ {camera1_name} не доступна", file=sys.stderr)
    
    # Пробуем подключить вторую камеру
    try:
        global camera2
        camera2 = cv2.VideoCapture(camera2_url)
        if camera2.isOpened():
            print(f"✓ {camera2_name} подключена", file=sys.stderr)
        else:
            print(f"✗ {camera2_name} не доступна", file=sys.stderr)
            camera2 = None
    except Exception as e:
        print(f"✗ Ошибка подключения {camera2_name}: {e}", file=sys.stderr)
        camera2 = None

def generate_frames(camera_id):
    """Генерирует кадры для указанной камеры"""
    if camera_id == 1:
        camera = camera1
        camera_name = camera1_name
    elif camera_id == 2 and camera2 is not None:
        camera = camera2
        camera_name = camera2_name
    else:
        return
    
    while True:
        try:
            success, frame = camera.read()
            if not success:
                print(f"ОШИБКА: Не могу прочитать кадр с {camera_name}", file=sys.stderr)
                time.sleep(1)
                continue
            
            # Изменяем размер для оптимизации
            frame = cv2.resize(frame, (640, 480))
            
            # Конвертируем кадр в JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                print(f"ОШИБКА: Не могу конвертировать кадр с {camera_name}", file=sys.stderr)
                continue
            
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
        except Exception as e:
            print(f"ОШИБКА в камере {camera_id}: {e}", file=sys.stderr)
            time.sleep(1)

@app.route('/')
def index():
    """Главная страница с двумя камерами"""
    return render_template('index.html')

@app.route('/video_feed/<int:camera_id>')
def video_feed(camera_id):
    """Маршрут для видеострима конкретной камеры"""
    return Response(generate_frames(camera_id),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/cameras')
def get_cameras():
    """API для получения информации о камерах"""
    cameras = [
        {
            'id': 1,
            'name': camera1_name,
            'status': camera1.isOpened() if camera1 else False
        },
        {
            'id': 2,
            'name': camera2_name,
            'status': camera2.isOpened() if camera2 else False,
            'url': camera2_url
        }
    ]
    return jsonify(cameras)

@app.route('/health')
def health():
    """Проверка здоровья сервера"""
    status = f"Сервер работает! | Камера 1: {'✓' if camera1.isOpened() else '✗'}"
    if camera2:
        status += f" | Камера 2: {'✓' if camera2.isOpened() else '✗'}"
    return status

if __name__ == '__main__':
    print("=== ЗАПУСК СЕРВЕРА ===", file=sys.stderr)
    print("Инициализация камер...", file=sys.stderr)
    
    init_cameras()
    
    print("📺 Главная страница: http://localhost:5000", file=sys.stderr)
    print("🎥 Камера 1: http://localhost:5000/video_feed/1", file=sys.stderr)
    print("📱 Камера 2: http://localhost:5000/video_feed/2", file=sys.stderr)
    print("📊 API камер: http://localhost:5000/api/cameras", file=sys.stderr)
    print("❤ Проверка: http://localhost:5000/health", file=sys.stderr)
    print("⏹️ Для остановки: Ctrl+C", file=sys.stderr)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        print(f"❌ ОШИБКА: {e}", file=sys.stderr)
