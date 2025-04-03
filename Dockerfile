FROM python:3.11-slim

WORKDIR /app

# Копирование файлов
COPY requirements.txt .
COPY parser.py .
COPY links.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Запуск парсера при старте контейнера
CMD ["python", "parser.py"]
