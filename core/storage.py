import json
import os
from typing import List
from core.models import Note
from dataclasses import asdict

class NoteStorage:
    """
    Отвечает за загрузку и сохранение списка заметок в JSON-файл.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_notes(self) -> List[Note]:
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        notes: List[Note] = []
        for item in data:
            title = item.get('title', '')
            body = item.get('body', '')
            tags = item.get('tags', [])  # <- вот эта строка
            notes.append(Note(title=title, body=body, tags=tags))
        return notes

    def save_notes(self, notes: List[Note]) -> None:
        # Гарантируем существование директории
        directory = os.path.dirname(self.file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        data = [asdict(note) for note in notes]
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
