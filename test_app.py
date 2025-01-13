import pytest
from PyQt6.QtWidgets import QApplication
from unittest.mock import patch, MagicMock
from App import SystemMonitor
import mongomock

@pytest.fixture
def app():
    """Создаёт экземпляр QApplication для тестов UI."""
    return QApplication([])

@pytest.fixture
def window(app):
    """Создаёт экземпляр окна для тестов."""
    win = SystemMonitor()
    return win

def test_init_db_success(window):
    """Тест успешной инициализации MongoDB."""
    with patch("App.MongoClient", return_value=mongomock.MongoClient()):
        window.init_db()
        assert window.mongo_client is not None
        assert window.db is not None
        assert window.collection is not None

def test_update_stats(window):
    """Тест обновления статистики системы."""
    with patch("App.psutil.cpu_percent", return_value=50):
        with patch("App.psutil.virtual_memory", return_value=MagicMock(total=8 * 1024**3, available=4 * 1024**3)):
            with patch("App.psutil.disk_usage", return_value=MagicMock(total=256 * 1024**3, free=128 * 1024**3)):
                window.update_stats()
                assert window.cpu_label.text() == "Загрузка ЦП: 50%"
                assert "ОЗУ: 4096.00/8192.00 MB" in window.memory_label.text()
                assert "ПЗУ: 128.00/256.00 GB" in window.disk_label.text()

def test_save_record_success(window):
    """Тест успешного сохранения записи в базу данных."""
    with patch("App.MongoClient", return_value=mongomock.MongoClient()):
        window.init_db()
        record = {
            "cpu": 50,
            "available_memory": 4096,
            "total_memory": 8192,
            "free_disk": 128,
            "total_disk": 256,
        }
        window.save_record(**record)
        saved_records = list(window.collection.find())
        assert len(saved_records) == 1
        assert saved_records[0]["cpu"] == 50

def test_toggle_recording(window):
    """Тест переключения записи."""
    assert not window.is_recording
    window.toggle_recording()
    assert window.is_recording
    window.toggle_recording()
    assert not window.is_recording

def test_change_interval(window):
    """Тест изменения интервала обновления."""
    window.change_interval(2000)
    assert window.update_interval == 2000
    assert window.data_timer.interval() == 2000


def test_close_event(window):
    """Тест закрытия окна."""
    with patch.object(window, "closeEvent", wraps=window.closeEvent) as mocked_close_event:
        window.close()
        mocked_close_event.assert_called_once()
