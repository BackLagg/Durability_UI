# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем зависимости для PyQt6 и MongoDB
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libegl1 \
    libopengl0 \
    libx11-xcb1 \
    libxkbcommon-x11-0 \
    libglu1-mesa-dev \
    libxcb-glx0 \
    libfontconfig1 \
    libdbus-1-3 \
    libxcomposite1 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libssl-dev \
    libfreetype6 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем необходимые Python библиотеки
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем приложение в контейнер
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Запускаем тесты
CMD ["pytest"]
