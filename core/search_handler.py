from PyQt5 import QtCore, QtWidgets

class SearchHandler(QtCore.QObject):
    """
    Обеспечивает автосброс строки поиска через заданное число секунд после последнего изменения.
    """

    def __init__(self, reset_seconds: int = 5, parent: QtCore.QObject | None = None):
        """
        :param reset_seconds: время (в секундах) бездействия, после которого поиск сбрасывается
        :param parent: родительский QObject
        """
        super().__init__(parent)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(reset_seconds * 1000)

    def attach_line_edit(self, line_edit: QtWidgets.QLineEdit):
        """
        Привязывает таймер к QLineEdit:
        - перезапуск таймера при каждом изменении текста
        - очистка поля по тайм-ауту
        """
        self._line_edit = line_edit
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._timer.timeout.connect(self._clear_search)

    def _on_text_changed(self, text: str):
        # при любом вводе — перезапускаем таймер
        if self._timer.isActive():
            self._timer.stop()
        self._timer.start()

    def _clear_search(self):
        # по истечении интервала очищаем строку поиска
        self._line_edit.clear()
