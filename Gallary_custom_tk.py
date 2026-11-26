import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

# Настройка базовой темы CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# Объединяем CTk с TkinterDnD для поддержки Drag & Drop
class TkDnDWindow(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class DropZoneWidget(ctk.CTkFrame):
    def __init__(self, master, on_folder_selected, **kwargs):
        super().__init__(
            master,
            fg_color="#18181B",
            border_width=2,
            border_color="#3F3F46",
            corner_radius=14,
            height=190,
            **kwargs
        )
        self.on_folder_selected = on_folder_selected
        self.pack_propagate(False)

        # Регистрация Drag & Drop
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<DropEnter>>", self.on_drag_enter)
        self.dnd_bind("<<DropLeave>>", self.on_drag_leave)
        self.dnd_bind("<<Drop>>", self.on_drop)

        # Внутренний контейнер для центрирования
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        title = ctk.CTkLabel(
            inner,
            text="Перетащите папку с фотографиями сюда",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#E4E4E7"
        )
        title.pack(pady=(0, 6))

        subtitle = ctk.CTkLabel(
            inner,
            text="Поддерживаются JPG, PNG, HEIC и RAW • ИИ автоматически найдёт дубли и смазы",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#A1A1AA"
        )
        subtitle.pack(pady=(0, 16))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack()

        btn_add = ctk.CTkButton(
            btn_frame,
            text="+ Выбрать папку",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            corner_radius=8,
            height=38,
            command=self.open_dialog
        )
        btn_add.pack(side="left", padx=(0, 12))

        btn_continue = ctk.CTkButton(
            btn_frame,
            text="Продолжить: Отпуск_2026 (65%)",
            fg_color="#27272A",
            hover_color="#3F3F46",
            border_width=1,
            border_color="#3F3F46",
            text_color="#E4E4E7",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            corner_radius=8,
            height=38
        )
        btn_continue.pack(side="left")

    def open_dialog(self):
        folder = filedialog.askdirectory(title="Выберите папку с фотографиями")
        if folder:
            self.on_folder_selected(folder)

    def on_drag_enter(self, event):
        self.configure(fg_color="#1E293B", border_color="#3B82F6")

    def on_drag_leave(self, event):
        self.configure(fg_color="#18181B", border_color="#3F3F46")

    def on_drop(self, event):
        self.configure(fg_color="#18181B", border_color="#3F3F46")
        # Очистка пути от фигурных скобок, если путь содержит пробелы в Windows
        raw_path = event.data.strip()
        if raw_path.startswith("{") and raw_path.endswith("}"):
            raw_path = raw_path[1:-1]
        if Path(raw_path).is_dir():
            self.on_folder_selected(raw_path)


class SmartGalleryStartWindow(TkDnDWindow):
    def __init__(self):
        super().__init__()
        self.title("SmartGallery — Умный разбор семейного архива")
        self.geometry("1120x740")
        self.configure(fg_color="#121214")

        # 1. Левая боковая панель
        sidebar = ctk.CTkFrame(
            self,
            fg_color="#18181B",
            width=240,
            corner_radius=0,
            border_width=1,
            border_color="#27272A"
        )
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = ctk.CTkLabel(
            sidebar,
            text="✦ SmartGallery",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#FFFFFF",
            anchor="w"
        )
        logo.pack(fill="x", padx=20, pady=(24, 16))

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
            lbl = ctk.CTkLabel(
                sidebar,
                text=section_title,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#71717A",
                anchor="w"
            )
            lbl.pack(fill="x", padx=22, pady=(14, 4))

            for text, active in items:
                btn = ctk.CTkButton(
                    sidebar,
                    text=text,
                    anchor="w",
                    height=38,
                    corner_radius=8,
                    font=ctk.CTkFont(
                        family="Segoe UI",
                        size=14,
                        weight="bold" if active else "normal"
                    ),
                    fg_color="#2563EB" if active else "transparent",
                    hover_color="#1D4ED8" if active else "#27272A",
                    text_color="#FFFFFF" if active else "#A1A1AA"
                )
                btn.configure(command=lambda b=btn: self.select_nav(b))
                btn.pack(fill="x", padx=16, pady=2)
                self.nav_buttons.append(btn)

        # Блок сэкономленного места внизу сайдбара
        stats_card = ctk.CTkFrame(
            sidebar,
            fg_color="#18181B",
            border_width=1,
            border_color="#27272A",
            corner_radius=12
        )
        stats_card.pack(side="bottom", fill="x", padx=16, pady=20)

        stats_title = ctk.CTkLabel(
            stats_card,
            text="Освобождено места",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A1A1AA",
            anchor="w"
        )
        stats_title.pack(fill="x", padx=14, pady=(12, 2))

        stats_val = ctk.CTkLabel(
            stats_card,
            text="4.2 ГБ (310 фото)",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color="#10B981",
            anchor="w"
        )
        stats_val.pack(fill="x", padx=14, pady=(0, 12))

        # 2. Правая рабочая область
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=28, pady=20)

        # Верхняя панель поиска
        top_bar = ctk.CTkFrame(content, fg_color="transparent")
        top_bar.pack(fill="x", pady=(0, 20))

        search = ctk.CTkEntry(
            top_bar,
            placeholder_text="Поиск по именам людей, тегам (например: «море», «кот») или году...",
            fg_color="#18181B",
            border_color="#27272A",
            border_width=1,
            text_color="#FFFFFF",
            placeholder_text_color="#71717A",
            corner_radius=8,
            height=38,
            font=ctk.CTkFont(family="Segoe UI", size=13)
        )
        search.pack(side="left", fill="x", expand=True)

        hotkeys_hint = ctk.CTkLabel(
            top_bar,
            text="Space: Оставить  •  Del: В корзину",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#71717A"
        )
        hotkeys_hint.pack(side="right", padx=(14, 0))

        # Зона Drag & Drop
        self.drop_zone = DropZoneWidget(content, self.handle_folder_selected)
        self.drop_zone.pack(fill="x", pady=(0, 20))

        # Умные подборки ИИ
        ai_header = ctk.CTkLabel(
            content,
            text="Умные подборки ИИ",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#E4E4E7",
            anchor="w"
        )
        ai_header.pack(fill="x", pady=(0, 10))

        ai_row = ctk.CTkFrame(content, fg_color="transparent")
        ai_row.pack(fill="x", pady=(0, 20))
        ai_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

        ai_cards_data = [
            ("35 серий похожих фото", "ИИ выбрал лучшие кадры в каждой серии", "#3B82F6"),
            ("Люди в архиве", "Распознано 14 человек • Нажмите для фильтра", "#8B5CF6"),
            ("Кандидаты на удаление", "48 смазанных и тёмных кадров • 320 МБ", "#EF4444"),
        ]
        for idx, (title_txt, desc_txt, accent) in enumerate(ai_cards_data):
            card = self.create_info_card(ai_row, title_txt, desc_txt, accent)
            padx = (0, 14) if idx < 2 else (0, 0)
            card.grid(row=0, column=idx, sticky="nsew", padx=padx)

        # Недавние сессии
        recent_header = ctk.CTkLabel(
            content,
            text="Недавние папки",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#E4E4E7",
            anchor="w"
        )
        recent_header.pack(fill="x", pady=(0, 10))

        recent_grid = ctk.CTkFrame(content, fg_color="transparent")
        recent_grid.pack(fill="x")
        recent_grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="sessions")

        sessions = [
            ("Отпуск_2026_Сочи", "500 фото • Оставлено 210", 0.65),
            ("День_рождения_Мамы", "184 фото • Разбор завершён", 1.00),
            ("Архив_телефона_Осень", "1 240 фото • Новая папка", 0.10),
            ]
        for idx, (folder_name, info, progress) in enumerate(sessions):
            session_card = self.create_session_card(recent_grid, folder_name, info, progress)
            padx = (0, 14) if idx < 2 else (0, 0)
            session_card.grid(row=0, column=idx, sticky="nsew", padx=padx)
        # Нижний статус-бар
        self.status_label = ctk.CTkLabel(
            content,
            text="Готов к работе • Перетащите папку выше, чтобы начать разбор",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#71717A",
            anchor="w"
            )
        self.status_label.pack(side="bottom", fill="x")
    def select_nav(self, active_btn):
        for btn in self.nav_buttons:
            is_active = (btn == active_btn)
            btn.configure(
            fg_color="#2563EB" if is_active else "transparent",
            hover_color="#1D4ED8" if is_active else "#27272A",
            text_color="#FFFFFF" if is_active else "#A1A1AA",
            font=ctk.CTkFont(
                family="Segoe UI",
                size=14,
                weight="bold" if is_active else "normal"
                )
            )
    def bind_card_hover(self, card):
        def on_enter(_):
            card.configure(fg_color="#1F1F23", border_color="#3F3F46")
        def on_leave(_):
            card.configure(fg_color="#18181B", border_color="#27272A")
            card.bind("", on_enter)
            card.bind("", on_leave)
            for child in card.winfo_children():
                child.bind("", on_enter)
                child.bind("", on_leave)
    def create_info_card(self, parent, title, desc, accent_color):
        card = ctk.CTkFrame(
            parent,
            fg_color="#18181B",
            border_width=1,
            border_color="#27272A",
            corner_radius=12,
            cursor="hand2"
            )
        badge = ctk.CTkLabel(
            card,
            text="● ИИ-анализ",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=accent_color,
            anchor="w"
            )
        badge.pack(fill="x", padx=16, pady=(14, 2))
        t = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#E4E4E7",
            anchor="w"
            )
        t.pack(fill="x", padx=16, pady=(0, 4))
        d = ctk.CTkLabel(
            card,
            text=desc,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A1A1AA",
            anchor="w",
            justify="left",
            wraplength=220
            )
        d.pack(fill="x", padx=16, pady=(0, 14))
        self.bind_card_hover(card)
        return card
    def create_session_card(self, parent, title, info, progress):
        card = ctk.CTkFrame(
            parent,
            fg_color="#18181B",
            border_width=1,
            border_color="#27272A",
            corner_radius=12,
            cursor="hand2"
            )
        t = ctk.CTkLabel(
            card,
            text="📁 " + title,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#E4E4E7",
            anchor="w"
            )
        t.pack(fill="x", padx=16, pady=(14, 4))
        i = ctk.CTkLabel(
            card,
            text=info,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#A1A1AA",
            anchor="w"
            )
        i.pack(fill="x", padx=16, pady=(0, 10))
        pbar = ctk.CTkProgressBar(
            card,
            height=6,
            corner_radius=4,
            fg_color="#27272A",
            progress_color="#10B981"
            )
        pbar.set(progress)
        pbar.pack(fill="x", padx=16, pady=(0, 14))
        self.bind_card_hover(card)
        return card
    def handle_folder_selected(self, folder_path):
        self.status_label.configure(
            text=f"Выбрана папка: {folder_path} — запуск сканирования...",
            text_color="#10B981",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
            )
if __name__ == "__main__":
    app = SmartGalleryStartWindow()
    app.mainloop()