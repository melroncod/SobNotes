from PyQt5 import QtWidgets, QtCore
from core.models import Note

class NoteEditor(QtWidgets.QWidget):
    note_changed = QtCore.pyqtSignal(Note)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_note: Note | None = None

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

        # Тело
        self.body_edit = QtWidgets.QTextEdit()
        self.body_edit.setPlaceholderText("Текст заметки...")
        layout.addWidget(self.body_edit)

        # Сигналы
        self.title_edit.textChanged.connect(self._on_content_changed)
        self.tags_edit.textChanged.connect(self._on_content_changed)
        self.body_edit.textChanged.connect(self._on_content_changed)

    def _on_content_changed(self):
        if not self.current_note:
            return

        self.current_note.title = self.title_edit.text()
        self.current_note.body  = self.body_edit.toPlainText()
        # разделяем по запятой, удаляем пустые
        tags = [t.strip() for t in self.tags_edit.text().split(',')]
        self.current_note.tags = [t for t in tags if t]
        self.note_changed.emit(self.current_note)

    def load_note(self, note: Note):
        self.current_note = note
        # блокируем сигналы, чтобы не вызывать _on_content_changed
        for w in (self.title_edit, self.tags_edit, self.body_edit):
            w.blockSignals(True)

        self.title_edit.setText(note.title)
        self.tags_edit .setText(', '.join(note.tags))
        self.body_edit .setPlainText(note.body)

        for w in (self.title_edit, self.tags_edit, self.body_edit):
            w.blockSignals(False)
