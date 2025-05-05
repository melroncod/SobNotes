import os
import asyncio
import traceback
from PyQt5 import QtWidgets, QtCore, QtGui
from core.storage import NoteStorage
from core.search_handler import SearchHandler
from core.gigachat import generate_note_with_gigachat
from ui.note_editor import NoteEditor
from core.models import Note


class GigachatWorker(QtCore.QThread):
    """
    Запускает асинхронную функцию generate_note_with_gigachat в отдельном потоке
    и по завершении отдаёт заголовок и тело заметки.
    """
    result_ready = QtCore.pyqtSignal(str, str)
    error = QtCore.pyqtSignal(str)

    def __init__(self, query: str, parent=None):
        super().__init__(parent)
        self.query = query

    def run(self):
        try:
            title, body = asyncio.run(generate_note_with_gigachat(self.query))
            self.result_ready.emit(title, body)
        except Exception:
            # Эмитим полный traceback для подробного разбора ошибки
            tb = traceback.format_exc()
            self.error.emit(tb)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SobNotes")
        self.setMinimumSize(900, 600)
        self.setWindowIcon(QtGui.QIcon(os.path.join("assets", "DarkIcon.png")))
        self.change_theme("dark")

        # 1) Меню
        self._create_menu()

        # 2) Данные
        self.storage = NoteStorage("data/notes.json")
        self.notes: list[Note] = self.storage.load_notes()

        # 3) Виджеты
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Поиск...")
        self.list_view = QtWidgets.QListWidget()
        self.list_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.on_context_menu)
        self.editor = NoteEditor()

        # 4) Поиск с автосбросом (5s)
        self.search_handler = SearchHandler(reset_seconds=5)
        self.search_handler.attach_line_edit(self.search_bar)
        self.search_bar.textChanged.connect(self.filter_notes)

        # 4.1) Таймер автозакрытия (3s) — открыть лучший матч
        self.open_timer = QtCore.QTimer(self)
        self.open_timer.setSingleShot(True)
        self.open_timer.setInterval(3000)
        self.open_timer.timeout.connect(self.open_top_match)
        self.search_bar.textChanged.connect(self._restart_open_timer)

        # 4.2) Enter в поиске — генерация через GigaChat
        self.search_bar.returnPressed.connect(self.on_search_enter)

        # 5) Сигналы
        self.list_view.itemClicked.connect(self.load_selected_note)
        self.editor.note_changed.connect(self.save_note)

        # 6) Кнопка новой заметки
        new_btn = QtWidgets.QPushButton("＋ Новая заметка")
        new_btn.clicked.connect(self.create_new_note)

        # 7) Компоновка левого блока
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(self.search_bar)
        left_layout.addWidget(new_btn)
        left_layout.addWidget(self.list_view)
        left_pane = QtWidgets.QWidget()
        left_pane.setLayout(left_layout)

        # 8) Сплиттер
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(left_pane)
        splitter.addWidget(self.editor)
        splitter.setSizes([250, 650])

        # 9) Центральный виджет
        container = QtWidgets.QWidget()
        hl = QtWidgets.QHBoxLayout(container)
        hl.addWidget(splitter)
        hl.setContentsMargins(4, 4, 4, 4)
        self.setCentralWidget(container)
        self.statusBar().showMessage("Готово")

        self.populate_note_list()

    # ———— Заполнение и фильтрация списка заметок —————

    def populate_note_list(self):
        self.list_view.clear()
        for note in self.notes:
            item = QtWidgets.QListWidgetItem(note.title)
            item.setData(QtCore.Qt.UserRole, note)
            self.list_view.addItem(item)

    def filter_notes(self, text: str):
        self.list_view.clear()
        tokens = [tok.lower() for tok in text.split() if tok.strip()]
        if not tokens:
            return self.populate_note_list()
        for note in self.notes:
            hay = " ".join([
                note.title.lower(),
                note.body.lower(),
                " ".join(tag.lower() for tag in note.tags)
            ])
            if any(tok in hay for tok in tokens):
                item = QtWidgets.QListWidgetItem(note.title)
                if hasattr(note, 'tags') and note.tags:
                    item.setToolTip("Теги: " + ", ".join(note.tags))
                item.setData(QtCore.Qt.UserRole, note)
                self.list_view.addItem(item)

    # ———— Авто‑открытие лучшей заметки —————

    def _restart_open_timer(self, text: str):
        if self.open_timer.isActive():
            self.open_timer.stop()
        if text.strip():
            self.open_timer.start()

    def open_top_match(self):
        if self.list_view.count() > 0:
            item = self.list_view.item(0)
            self.list_view.setCurrentItem(item)
            self.load_selected_note(item)

    # ———— Генерация заметки по Enter —————

    def on_search_enter(self):
        query = self.search_bar.text().strip()
        if not query:
            return
        # Останавливаем авто‑таймеры
        self.search_handler._timer.stop()
        self.open_timer.stop()
        # Запускаем GigaChatWorker
        self.statusBar().showMessage("Генерация заметки через GigaChat…")
        self._worker = GigachatWorker(query)
        self._worker.result_ready.connect(self.on_giga_result)
        self._worker.error.connect(self.on_giga_error)
        self._worker.start()

    def on_giga_result(self, title: str, body: str):
        note = Note(title=title, body=body)
        self.notes.append(note)
        self.storage.save_notes(self.notes)
        self.populate_note_list()
        # Открываем новую заметку
        items = self.list_view.findItems(title, QtCore.Qt.MatchExactly)
        if items:
            self.list_view.setCurrentItem(items[0])
            self.editor.load_note(note)
        self.statusBar().showMessage("Заметка сгенерирована и добавлена", 3000)
        self.search_bar.clear()
        QtCore.QTimer.singleShot(200, lambda: self.search_bar.setFocus())

    def on_giga_error(self, error_msg: str):
        dlg = QtWidgets.QMessageBox(self)
        dlg.setIcon(QtWidgets.QMessageBox.Warning)
        dlg.setWindowTitle("Ошибка GigaChat")
        dlg.setText("Произошла ошибка при генерации заметки.")
        dlg.setInformativeText("Нажмите «Подробнее», чтобы увидеть детали.")
        dlg.setDetailedText(error_msg)
        dlg.exec_()
        self.statusBar().showMessage("Не удалось сгенерировать заметку", 3000)
        QtCore.QTimer.singleShot(200, lambda: self.search_bar.setFocus())

    # ———— Работа с заметками —————

    def load_selected_note(self, item: QtWidgets.QListWidgetItem):
        note = item.data(QtCore.Qt.UserRole)
        self.editor.load_note(note)
        self.statusBar().showMessage(f"Открыта: {note.title}")
        QtCore.QTimer.singleShot(2000, lambda: self.search_bar.setFocus())

    def create_new_note(self):
        note = Note(title="Новая заметка", body="")
        self.notes.append(note)
        self.populate_note_list()
        self.editor.load_note(note)
        self.statusBar().showMessage("Создана новая заметка")

    def save_note(self, note: Note):
        self.storage.save_notes(self.notes)
        self.populate_note_list()
        self.statusBar().showMessage(f"Сохранено: {note.title}", 2000)

    # ———— Контекстное меню для заметок —————

    def on_context_menu(self, point: QtCore.QPoint):
        item = self.list_view.itemAt(point)
        if not item:
            return
        menu = QtWidgets.QMenu(self)
        copy_act = menu.addAction("Копировать")
        rename_act = menu.addAction("Переименовать")
        delete_act = menu.addAction("Удалить")
        action = menu.exec_(self.list_view.mapToGlobal(point))
        note = item.data(QtCore.Qt.UserRole)
        if action == copy_act:
            self.copy_note(note)
        elif action == rename_act:
            self.rename_note(note, item)
        elif action == delete_act:
            self.delete_note(note)

    def copy_note(self, note: Note):
        new = Note(title=note.title + " (копия)", body=note.body, tags=getattr(note, 'tags', []))
        self.notes.append(new)
        self.storage.save_notes(self.notes)
        self.populate_note_list()
        self.statusBar().showMessage(f"Скопировано: {note.title}", 2000)

    def rename_note(self, note: Note, item: QtWidgets.QListWidgetItem):
        text, ok = QtWidgets.QInputDialog.getText(
            self, "Переименовать заметку", "Новый заголовок:", text=note.title
        )
        if ok and text.strip():
            note.title = text.strip()
            self.storage.save_notes(self.notes)
            item.setText(note.title)
            self.statusBar().showMessage(f"Переименовано: {note.title}", 2000)

    def delete_note(self, note: Note):
        reply = QtWidgets.QMessageBox.question(
            self, "Удалить заметку",
            f"Вы уверены, что хотите удалить заметку «{note.title}»?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        if reply == QtWidgets.QMessageBox.Yes:
            self.notes.remove(note)
            self.storage.save_notes(self.notes)
            self.populate_note_list()
            self.editor.load_note(Note(title="", body="", tags=[]))
            self.statusBar().showMessage("Заметка удалена", 2000)

    # ———— Меню и тема —————

    def _create_menu(self):
        menubar = self.menuBar()
        settings = menubar.addMenu("Настройки")
        theme_menu = settings.addMenu("Тема")
        light_act = QtWidgets.QAction("Светлая", self)
        dark_act = QtWidgets.QAction("Тёмная", self)
        light_act.triggered.connect(lambda: self.change_theme("light"))
        dark_act.triggered.connect(lambda: self.change_theme("dark"))
        theme_menu.addAction(light_act)
        theme_menu.addAction(dark_act)

        help_menu = menubar.addMenu("Help")
        about_act = QtWidgets.QAction("О программе", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    def change_theme(self, theme_name: str):
        app = QtWidgets.QApplication.instance()
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # применяем QSS
        style = self._load_qss(os.path.join(base, "assets", "style.qss"))
        theme = self._load_qss(os.path.join(base, "assets", "themes", f"{theme_name}.qss"))
        app.setStyleSheet(style + "\n" + theme)

        # смена иконки окна
        icon_file = "LightIcon.png" if theme_name == "dark" else "DarkIcon.png"
        icon_path = os.path.join(base, "assets", icon_file)
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        self.statusBar().showMessage(f"Тема: {theme_name}", 1500)

    def _load_qss(self, path: str) -> str:
        if not os.path.exists(path):
            return ""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "О SobNotes",
            "SobNotes v1.0\n\n"
            "Личный блокнот для подготовки к техническим собеседованиям.\n"
            "Разработано на Python + PyQt5."
        )
