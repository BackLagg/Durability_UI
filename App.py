import os
import sys
import time
from datetime import datetime
from PyQt6.QtCore import QTimer, QTime, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSpinBox, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QMessageBox
)
import psutil
from pymongo import MongoClient, errors
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Системный монитор")
        self.setGeometry(100, 100, 500, 300)

        # Настройка MongoDB
        self.mongo_client = None
        self.db = None
        self.collection = None
        self.init_db()

        # Флаг для записи
        self.is_recording = False
        self.record_start_time = None
        self.timer_time = QTime(0, 0, 0)

        # Интервал обновления
        self.update_interval = 1000  # мс

        # Инициализация UI
        self.init_ui()

        # Таймер для обновления данных
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.update_stats)
        self.data_timer.start(self.update_interval)

        # Таймер записи
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.update_record_timer)

    def init_ui(self):
        # Главный виджет и макет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        # Метки для отображения информации
        self.cpu_label = QLabel("Загрузка ЦП: 0%", self)
        self.memory_label = QLabel("ОЗУ: 0/0 MB", self)
        self.disk_label = QLabel("ПЗУ: 0/0 GB", self)

        self.layout.addWidget(self.cpu_label)
        self.layout.addWidget(self.memory_label)
        self.layout.addWidget(self.disk_label)

        # Поле для изменения интервала обновления
        self.interval_layout = QHBoxLayout()
        self.interval_label = QLabel("Интервал обновления (мс):")
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(500, 10000)
        self.interval_spinbox.setValue(self.update_interval)
        self.interval_spinbox.valueChanged.connect(self.change_interval)

        self.interval_layout.addWidget(self.interval_label)
        self.interval_layout.addWidget(self.interval_spinbox)
        self.layout.addLayout(self.interval_layout)

        # Кнопка записи
        self.record_button = QPushButton("Начать запись")
        self.record_button.clicked.connect(self.toggle_recording)
        self.layout.addWidget(self.record_button)

        # Таймер записи
        self.record_timer_label = QLabel("Время записи: 00:00:00")
        self.record_timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.record_timer_label.hide()
        self.layout.addWidget(self.record_timer_label)

        # Кнопка истории
        self.history_button = QPushButton("Просмотреть историю")
        self.history_button.clicked.connect(self.view_history)
        self.layout.addWidget(self.history_button)

        self.central_widget.setLayout(self.layout)

    def init_db(self):
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27117")
            mongo_db = os.getenv("MONGO_DB", "system_monitor")
            mongo_collection = os.getenv("MONGO_COLLECTION", "records")

            self.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.mongo_client[mongo_db]
            self.collection = self.db[mongo_collection]
        except errors.ServerSelectionTimeoutError:
            self.mongo_client = None
            print("Ошибка подключения к MongoDB. Проверьте настройки подключения.")

    def update_stats(self):
        # Получение данных о загрузке системы
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Форматирование данных
        total_memory = memory.total / (1024 ** 2)  # MB
        available_memory = memory.available / (1024 ** 2)  # MB
        total_disk = disk.total / (1024 ** 3)  # GB
        free_disk = disk.free / (1024 ** 3)  # GB

        # Обновление меток
        self.cpu_label.setText(f"Загрузка ЦП: {cpu_usage}%")
        self.memory_label.setText(f"ОЗУ: {available_memory:.2f}/{total_memory:.2f} MB")
        self.disk_label.setText(f"ПЗУ: {free_disk:.2f}/{total_disk:.2f} GB")

        # Если запись активна, сохраняем данные
        if self.is_recording:
            self.save_record(cpu_usage, available_memory, total_memory, free_disk, total_disk)

    def save_record(self, cpu, available_memory, total_memory, free_disk, total_disk):
        record = {
            "timestamp": datetime.now().isoformat(),
            "cpu": cpu,
            "available_memory": available_memory,
            "total_memory": total_memory,
            "free_disk": free_disk,
            "total_disk": total_disk,
        }

        if self.mongo_client:
            try:
                self.collection.insert_one(record)
            except errors.PyMongoError:
                QMessageBox.warning(self, "Ошибка записи", "Не удалось сохранить запись в MongoDB.")

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_start_time = time.time()
        self.timer_time = QTime(0, 0, 0)
        self.record_timer.start(1000)
        self.record_button.setText("Остановить запись")
        self.record_timer_label.show()

    def stop_recording(self):
        self.is_recording = False
        self.record_timer.stop()
        self.record_button.setText("Начать запись")
        self.record_timer_label.hide()

    def update_record_timer(self):
        elapsed = time.time() - self.record_start_time
        self.timer_time = QTime(0, 0, 0).addSecs(int(elapsed))
        self.record_timer_label.setText(f"Время записи: {self.timer_time.toString('hh:mm:ss')}")

    def fetch_history(self):
        """Получение записей из базы данных."""
        if not self.mongo_client:
            raise ConnectionError("Подключение к базе данных отсутствует.")

        try:
            records = list(self.collection.find({}, {"_id": 0}))
        except errors.PyMongoError as e:
            raise RuntimeError(f"Не удалось загрузить записи из MongoDB: {e}")

        return records
    def view_history(self):
        """Отображение истории записей в диалоговом окне."""
        try:
            records = self.fetch_history()
        except ConnectionError:
            QMessageBox.warning(self, "Ошибка", "Подключение к базе данных отсутствует.")
            return
        except RuntimeError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("История записей")
        dialog.resize(600, 400)

        layout = QVBoxLayout()
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Время", "ЦП (%)", "ОЗУ (Доступно)", "ОЗУ (Всего)", "ПЗУ (Свободно)", "ПЗУ (Всего)"])

        try:
            records = list(self.collection.find({}, {"_id": 0}))
        except errors.PyMongoError:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить записи из MongoDB.")
            records = []

        table.setRowCount(len(records))

        for row, record in enumerate(records):
            table.setItem(row, 0, QTableWidgetItem(record["timestamp"]))
            table.setItem(row, 1, QTableWidgetItem(str(record["cpu"])))
            table.setItem(row, 2, QTableWidgetItem(f"{record['available_memory']:.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"{record['total_memory']:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"{record['free_disk']:.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{record['total_disk']:.2f}"))

        layout.addWidget(table)
        dialog.setLayout(layout)
        dialog.exec()

    def change_interval(self, value):
        try:
            self.update_interval = int(value)
            self.data_timer.setInterval(self.update_interval)
        except ValueError:
            self.update_interval = 1000
            self.interval_spinbox.setValue(self.update_interval)

    def closeEvent(self, event):
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec())
