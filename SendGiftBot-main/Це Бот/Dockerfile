# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем зависимости проекта
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Команда для запуска бота
CMD ["python", "main.py"]
