import sys
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QLineEdit, QFileDialog, QGridLayout,
    QProgressBar, QSpacerItem, QSizePolicy
)

DARK_STYLESHEET = """
QMainWindow, QWidget#MainContainer {
    background-color: #121214;
    color: #E4E4E7;
    font-family: "Segoe UI", Arial, sans-serif;
}
QFrame#Sidebar {
    background-color: #18181B;
    border-right: 1px solid #27272A;
}
QPushButton#NavBtn {
    background-color: transparent;
    color: #A1A1AA;
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 14px;
    border: none;
}
QPushButton#NavBtn:hover {
    background-color: #27272A;
    color: #FFFFFF;
}
QPushButton#NavBtn:checked {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: bold;
}
QLineEdit#SearchBar {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 8px;
    padding: 8px 14px;
    color: #FFFFFF;
    font-size: 13px;
}
QLineEdit#SearchBar:focus {
    border: 1px solid #3B82F6;
}
QFrame#DropZone {
    background-color: #18181B;
    border: 2px dashed #3F3F46;
    border-radius: 14px;
}
QFrame#DropZone[dragOver="true"] {
    background-color: #1E293B;
    border: 2px dashed #3B82F6;
}
QPushButton#PrimaryBtn {
    background-color: #2563EB;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 14px;
    border: none;
}
QPushButton#PrimaryBtn:hover {
    background-color: #1D4ED8;
}
QPushButton#SecondaryBtn {
    background-color: #27272A;
    color: #E4E4E7;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    border: 1px solid #3F3F46;
}
QPushButton#SecondaryBtn:hover {
    background-color: #3F3F46;
}
QFrame#Card {
    background-color: #18181B;
    border: 1px solid #27272A;
    border-radius: 12px;
}
QFrame#Card:hover {
    border: 1px solid #3F3F46;
    background-color: #1F1F23;
}
QProgressBar {
    background-color: #27272A;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #10B981;
    border-radius: 4px;
}
"""


class DropZoneWidget(QFrame):
    def __init__(self, on_folder_selected):
        super().__init__()
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.on_folder_selected = on_folder_selected
        self.setMinimumHeight(190)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        title = QLabel("Перетащите папку с фотографиями сюда")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Поддерживаются JPG, PNG, HEIC и RAW • ИИ автоматически найдёт дубли и смазы")
        subtitle.setStyleSheet("color: #A1A1AA; font-size: 13px;")
        subtitle.setAlignment(Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_add = QPushButton("+ Выбрать папку")
        btn_add.setObjectName("PrimaryBtn")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self.open_dialog)

        btn_continue = QPushButton("Продолжить: Отпуск_2026 (65%)")
        btn_continue.setObjectName("SecondaryBtn")
        btn_continue.setCursor(Qt.PointingHandCursor)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_continue)
        btn_layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addLayout(btn_layout)

    def open_dialog(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с фотографиями")
        if folder:
            self.on_folder_selected(folder)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragOver", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if Path(path).is_dir():
                self.on_folder_selected(path)


class SmartGalleryStartWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartGallery — Умный разбор семейного архива")
        self.resize(1120, 740)
        self.setStyleSheet(DARK_STYLESHEET)

        main_widget = QWidget()
        main_widget.setObjectName("MainContainer")
        self.setCentralWidget(main_widget)

        root_layout = QHBoxLayout(main_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Левая боковая панель
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 20, 16, 20)
        side_layout.setSpacing(6)

        logo = QLabel("✦ SmartGallery")
        logo.setFont(QFont("Segoe UI", 16, QFont.Bold))
        logo.setStyleSheet("color: #FFFFFF; margin-bottom: 12px;")
        side_layout.addWidget(logo)

        self.nav_buttons = []
        sections = [
            ("АРХИВ", [
                ("Все фотографии", True),
                ("Люди и лица", False),
                ("События по датам", False),
            ]),
            ("УМНАЯ ОЧИСТКА", [
                ("Дубликаты (124)", False),
                ("Размытые кадры (48)", False),
                ("Скриншоты и чеки (19)", False),
            ])
        ]

        for section_title, items in sections:
            lbl = QLabel(section_title)
            lbl.setStyleSheet("color: #71717A; font-size: 11px; font-weight: bold; margin-top: 12px; margin-left: 6px;")
            side_layout.addWidget(lbl)
            for text, active in items:
                btn = QPushButton(text)
                btn.setObjectName("NavBtn")
                btn.setCheckable(True)
                btn.setChecked(active)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda checked, b=btn: self.select_nav(b))
                side_layout.addWidget(btn)
                self.nav_buttons.append(btn)

        side_layout.addStretch()

        # Блок сэкономленного места
        stats_card = QFrame()
        stats_card.setObjectName("Card")
        stats_layout = QVBoxLayout(stats_card)
        stats_title = QLabel("Освобождено места")
        stats_title.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        stats_val = QLabel("4.2 ГБ (310 фото)")
        stats_val.setFont(QFont("Segoe UI", 13, QFont.Bold))
        stats_val.setStyleSheet("color: #10B981;")
        stats_layout.addWidget(stats_title)
        stats_layout.addWidget(stats_val)
        side_layout.addWidget(stats_card)

        root_layout.addWidget(sidebar)

        # 2. Правая рабочая область
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(28, 20, 28, 20)
        content_layout.setSpacing(20)

        # Верхняя панель поиска
        top_bar = QHBoxLayout()
        search = QLineEdit()
        search.setObjectName("SearchBar")
        search.setPlaceholderText("Поиск по именам людей, тегам (например: «море», «кот») или году...")
        top_bar.addWidget(search)

        hotkeys_hint = QLabel("Space: Оставить  •  Del: В корзину")
        hotkeys_hint.setStyleSheet("color: #71717A; font-size: 12px; margin-left: 12px;")
        top_bar.addWidget(hotkeys_hint)
        content_layout.addLayout(top_bar)

        # Зона Drag & Drop
        self.drop_zone = DropZoneWidget(self.handle_folder_selected)
        content_layout.addWidget(self.drop_zone)

        # Умные подборки ИИ
        ai_header = QLabel("Умные подборки ИИ")
        ai_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        content_layout.addWidget(ai_header)

        ai_row = QHBoxLayout()
        ai_row.setSpacing(14)
        ai_cards_data = [
            ("35 серий похожих фото", "ИИ выбрал лучшие кадры в каждой серии", "#3B82F6"),
            ("Люди в архиве", "Распознано 14 человек • Нажмите для фильтра", "#8B5CF6"),
            ("Кандидаты на удаление", "48 смазанных и тёмных кадров • 320 МБ", "#EF4444"),
        ]
        for title_txt, desc_txt, accent in ai_cards_data:
            card = self.create_info_card(title_txt, desc_txt, accent)
            ai_row.addWidget(card)
        content_layout.addLayout(ai_row)

        # Недавние сессии
        recent_header = QLabel("Недавние папки")
        recent_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        content_layout.addWidget(recent_header)

        recent_grid = QGridLayout()
        recent_grid.setSpacing(14)
        sessions = [
            ("Отпуск_2026_Сочи", "500 фото • Оставлено 210", 65),
            ("День_рождения_Мамы", "184 фото • Разбор завершён", 100),
            ("Архив_телефона_Осень", "1 240 фото • Новая папка", 10),
        ]
        for idx, (folder_name, info, progress) in enumerate(sessions):
            session_card = self.create_session_card(folder_name, info, progress)
            recent_grid.addWidget(session_card, 0, idx)
        content_layout.addLayout(recent_grid)

        content_layout.addStretch()

        # Нижний статус-бар
        self.status_label = QLabel("Готов к работе • Перетащите папку выше, чтобы начать разбор")
        self.status_label.setStyleSheet("color: #71717A; font-size: 12px;")
        content_layout.addWidget(self.status_label)
        root_layout.addWidget(content_widget)

    def select_nav(self, active_btn):
        for btn in self.nav_buttons:
            btn.setChecked(btn == active_btn)

    def create_info_card(self, title, desc, accent_color):
        card = QFrame()

        card.setObjectName("Card")
        card.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        badge = QLabel("● ИИ-анализ")
        badge.setStyleSheet(f"color: {accent_color}; font-size: 11px; font-weight: bold;")
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 12, QFont.Bold))
        d = QLabel(desc)
        d.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        d.setWordWrap(True)
        layout.addWidget(badge)
        layout.addWidget(t)
        layout.addWidget(d)
        return card

    def create_session_card(self, title, info, progress):
        card = QFrame()

        card.setObjectName("Card")
        card.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        t = QLabel("📁 " + title)
        t.setFont(QFont("Segoe UI", 12, QFont.Bold))
        i = QLabel(info)
        i.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        pbar = QProgressBar()
        pbar.setValue(progress)
        pbar.setTextVisible(False)
        layout.addWidget(t)
        layout.addWidget(i)
        layout.addWidget(pbar)
        return card

    def handle_folder_selected(self, folder_path):
        self.status_label.setText(f"Выбрана папка: {folder_path} — запуск сканирования...")

        self.status_label.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold;")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SmartGalleryStartWindow()
    window.show()
    sys.exit(app.exec())