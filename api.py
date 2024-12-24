from flask import Flask, request, jsonify
import base64
import os
from datetime import datetime
import logging
from PIL import Image  # Подключаем Pillow для работы с изображениями

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'train_project.settings')

# Инициализируем Django
import django
django.setup()

# Импортируем модели из Django после инициализации
from train_app.models import TrainDetail

# Настраиваем логирование
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Инициализация Flask приложения
app = Flask(__name__)

# Вспомогательная функция для проверки изображения
def check_image_properties(image_path):
    try:
        # Открываем изображение с помощью Pillow
        with Image.open(image_path) as img:
            logging.debug(f"Формат изображения: {img.format}")
            logging.debug(f"Размер изображения: {img.size}")
            logging.debug(f"Режим изображения: {img.mode}")
            return img.format, img.size, img.mode
    except Exception as e:
        logging.error(f"Ошибка при открытии изображения: {e}")
        return None, None, None

# Вспомогательная функция для конвертации изображения в base64
# Вспомогательная функция для конвертации изображения в base64
def image_to_base64(image_path):
    try:
        # Префикс пути к файлам изображений
        base_path = '/mnt/ks/Works/railcars/railcars_new/train_project/'

        # Объединяем базовый путь и путь изображения из базы данных
        full_image_path = os.path.join(base_path, image_path.lstrip('/'))

        # Проверяем, существует ли файл
        if not os.path.exists(full_image_path):
            logging.error(f"Файл не найден: {full_image_path}")
            return None
        
        # Проверяем свойства изображения перед кодированием
        format, size, mode = check_image_properties(full_image_path)
        if not format:
            logging.error(f"Файл не является изображением или поврежден: {full_image_path}")
            return None

        # Если все хорошо, кодируем в base64
        logging.debug(f"Чтение изображения из пути: {full_image_path}")
        with open(full_image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            logging.debug(f"Изображение успешно закодировано в base64. Длина строки: {len(image_data)} символов.")
            return image_data
    except Exception as e:
        logging.error(f"Ошибка при чтении изображения из файловой системы: {e}")
        return None


# Маршрут для получения информации о вагоне и изображения
@app.route('/api/get_train_image', methods=['POST'])
def get_wagon_image():
    data = request.get_json()

    # Проверяем наличие обязательных полей в запросе
    train_number = data.get("train_number")
    date_str = data.get("date")

    if not train_number or not date_str:
        logging.warning(f"Отсутствуют обязательные поля: train_number или date. Получено: train_number={train_number}, date={date_str}")
        return jsonify({"error": "Отсутствуют обязательные поля: train_number, date"}), 400

    try:
        # Преобразуем дату из строки в объект даты
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logging.warning(f"Неверный формат даты: {date_str}")
        return jsonify({"error": "Неверный формат даты. Используйте YYYY-MM-DD."}), 400

    try:
        # Запрос к базе данных для получения деталей вагона
        wagon_detail = TrainDetail.objects.filter(serial_number=train_number, train__date=date).first()

        if not wagon_detail:
            return jsonify({"error": "Вагон с указанным номером и датой не найден."}), 404

        # Получаем путь к изображению из базы данных
        image_path = wagon_detail.image_link

        # Конвертируем изображение в base64
        image_base64 = image_to_base64(image_path)

        if not image_base64:
            return jsonify({"error": "Невозможно получить изображение."}), 500

        logging.info(f"Изображение успешно получено и закодировано для номера поезда: {train_number}")
        return jsonify({
            "serial_number": train_number,
            "date": date_str,
            "train_image_base64": image_base64
        }), 200

    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")
        return jsonify({"error": "Произошла непредвиденная ошибка."}), 500

if __name__ == '__main__':
    logging.info("Запуск Flask приложения...")
    app.run(debug=True, host='0.0.0.0', port=5055)
