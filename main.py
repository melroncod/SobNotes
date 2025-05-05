import sys
import os
from PyQt5 import QtWidgets
from ui.main_window import MainWindow

def load_stylesheet(path: str) -> str:
    """
    Загрузить QSS-файл по указанному пути.
    Вернёт пустую строку, если файл не найден.
    """
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    # Создаём приложение
    app = QtWidgets.QApplication(sys.argv)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # --- Общий стиль ---
    style_path = os.path.join(base_dir, "assets", "style.qss")
    app.setStyleSheet(load_stylesheet(style_path))

    # --- Тема (light или dark) ---
    theme_name = os.environ.get("INTERVIEW_NOTE_THEME", "light").lower()
    theme_path = os.path.join(base_dir, "assets", "themes", f"{theme_name}.qss")
    app.setStyleSheet(app.styleSheet() + "\n" + load_stylesheet(theme_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
