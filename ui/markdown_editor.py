from PyQt5.QtWidgets import (
    QWidget, QStackedWidget, QPlainTextEdit, QTextEdit, QVBoxLayout
)
from PyQt5.QtCore import Qt

class MarkdownEditor(QWidget):
    """
    Комбинированный виджет: в режиме preview показывает отрендеренный Markdown,
    а когда фокус попадает в него — переключается на raw‑редактор.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # 1) Собираем стек из двух виджетов
        self.stack = QStackedWidget(self)
        self.raw   = QPlainTextEdit()
        self.raw.setTabStopDistance(4 * self.raw.fontMetrics().horizontalAdvance(' '))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        self.stack.addWidget(self.preview)   # индекс 0
        self.stack.addWidget(self.raw)       # индекс 1

        # 2) Слойlayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.stack)

        # 3) События переключения
        self.raw.focusInEvent   = self._on_raw_focus_in
        self.raw.focusOutEvent  = self._on_raw_focus_out
        self.preview.mousePressEvent = self._on_preview_click

        # 4) Обновление превью при изменении текста
        self.raw.textChanged.connect(self._update_preview)

        # Изначально показываем preview
        self.stack.setCurrentIndex(0)
        self._update_preview()

    def _on_preview_click(self, event):
        # При клике в превью — переключаем на raw‑режим и даём фокус
        self.stack.setCurrentIndex(1)
        self.raw.setFocus()
        event.accept()

    def _on_raw_focus_in(self, event):
        # фокус в raw — ничего дополнительно не делаем
        QPlainTextEdit.focusInEvent(self.raw, event)

    def _on_raw_focus_out(self, event):
        # уходим из raw — переключаем обратно в preview
        QPlainTextEdit.focusOutEvent(self.raw, event)
        self._update_preview()
        self.stack.setCurrentIndex(0)

    def _update_preview(self):
        md = self.raw.toPlainText()
        # Qt ≥5.14 умеет напрямую рендерить Markdown:
        self.preview.setMarkdown(md)

    def toPlainText(self) -> str:
        """Позволяет получить текущий Markdown."""
        return self.raw.toPlainText()

    def setPlainText(self, text: str):
        """Установить Markdown‑текст в raw‑виджете."""
        self.raw.blockSignals(True)
        self.raw.setPlainText(text)
        self.raw.blockSignals(False)
        self._update_preview()
