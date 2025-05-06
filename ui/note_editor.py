# ui/note_editor.py

from PyQt5 import QtWidgets, QtCore
from core.models import Note
from ui.markdown_editor import MarkdownEditor

class NoteEditor(QtWidgets.QWidget):
    """
    Виджет для создания и редактирования заметки:
    - QLineEdit для заголовка
    - QLineEdit для тегов
    - MarkdownEditor (raw + preview) для тела заметки
    Эмитит сигнал note_changed при любом изменении.
    """
    note_changed = QtCore.pyqtSignal(Note)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_note: Note | None = None

        # Основной layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Заголовок
        self.title_edit = QtWidgets.QLineEdit()
        self.title_edit.setPlaceholderText("Заголовок заметки")
        layout.addWidget(self.title_edit)

        # Теги
        self.tags_edit = QtWidgets.QLineEdit()
        self.tags_edit.setPlaceholderText("Теги (через запятую)")
        layout.addWidget(self.tags_edit)

        # Тело заметки — комбинированный Markdown‑редактор
        self.body_edit = MarkdownEditor()
        # Устанавливаем placeholder в raw‑режиме
        self.body_edit.raw.setPlaceholderText("Текст заметки (Markdown)...")
        layout.addWidget(self.body_edit)

        # Подключаем сигналы изменений
        self.title_edit.textChanged.connect(self._on_content_changed)
        self.tags_edit.textChanged.connect(self._on_content_changed)
        self.body_edit.raw.textChanged.connect(self._on_content_changed)

    def _on_content_changed(self):
        """
        При любом изменении полей обновляем current_note и эмитим сигнал.
        """
        if not self.current_note:
            return

        # Заголовок
        self.current_note.title = self.title_edit.text()
        # Тело заметки — из MarkdownEditor
        self.current_note.body = self.body_edit.toPlainText()
        # Теги
        tags = [t.strip() for t in self.tags_edit.text().split(',')]
        self.current_note.tags = [t for t in tags if t]
        # Эмитим обновлённую заметку
        self.note_changed.emit(self.current_note)

    def load_note(self, note: Note):
        """
        Загружает данные из Note в виджет.
        Блокируем сигналы, чтобы избежать лишних emit-ов при setText/ setPlainText.
        """
        self.current_note = note

        # Блокируем сигналы
        self.title_edit.blockSignals(True)
        self.tags_edit.blockSignals(True)
        self.body_edit.raw.blockSignals(True)

        # Устанавливаем значения
        self.title_edit.setText(note.title)
        self.tags_edit.setText(', '.join(note.tags))
        self.body_edit.setPlainText(note.body)

        # Снимаем блокировку сигналов
        self.title_edit.blockSignals(False)
        self.tags_edit.blockSignals(False)
        self.body_edit.raw.blockSignals(False)
