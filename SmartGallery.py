# New branch

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import imagehash

from pathlib import Path

import sqlite3

import os

from PIL import Image, ImageFile, ImageTk, ExifTags

import shutil

import tkinter
import tkinter.ttk
import tkinter.messagebox
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter import simpledialog, filedialog
from tkinter.constants import END
from tkinter import Tk, Toplevel, Label, Button, Frame, messagebox

# 1.1 Импортируем поддержку формата HEIC (с айфонов)
from pillow_heif import register_heif_opener

# 1.2 Регистрируем плагин в Pillow
register_heif_opener()

# Разрешаем Pillow читать поврежденные/недокачанные файлы
ImageFile.LOAD_TRUNCATED_IMAGES = True


class Application(tkinter.ttk.Frame):
    def __init__(self, master: Tk | None = None):
        super().__init__(master)
        self.master: Tk
        self.pack(fill="both", expand=True)

        self.archive_path_var = None
        self.directory_path_var = None
        self.progressbar = None
        self.tree = None
        self.value_var_prog = None

        self.create_widgets()
        self.master.title("Smart gallery")
        self.master.resizable(True, True)
        self.master.geometry("460x550+200+200")

    def create_widgets(self):
        archive_frame = tkinter.ttk.LabelFrame(self, text="Open DB")
        archive_frame.pack(fill="x", padx=10, pady=3)
        # Даем колонке 0 (где лежит Entry) вес 1.
        # По умолчанию вес (weight) всех колонок равен 0, поэтому ячейки сжимаются до минимально возможного размера
        archive_frame.columnconfigure(0, weight=1)

        self.archive_path_var = tkinter.StringVar()
        self.directory_path_var = tkinter.StringVar()

        archive_path_entry = tkinter.ttk.Entry(archive_frame, textvariable=self.archive_path_var, width=54,
                                               state="disabled")
        archive_path_entry.grid(column=0, row=0, padx=(0, 10), pady=(5, 15), sticky="ew")

        open_btn = tkinter.ttk.Button(archive_frame, text="Open")
        open_btn.bind("<ButtonRelease>", self.open_image_in_new_window)
        open_btn.grid(column=1, row=0, padx=(0, 10), pady=(5, 15))

        output_frame = tkinter.ttk.LabelFrame(self, text="Output Folder")
        output_frame.pack(fill="x", padx=10, pady=3)
        output_frame.columnconfigure(0, weight=1)

        directory_path_entry = tkinter.ttk.Entry(output_frame, textvariable=self.directory_path_var, width=54,
                                                 state="disabled")
        directory_path_entry.grid(column=0, row=0, padx=(0, 10), pady=(5, 15), sticky="ew")

        select_btn = tkinter.ttk.Button(output_frame, text="Select")
        select_btn.bind("<ButtonRelease>", self.select_folder)
        select_btn.grid(column=1, row=0, padx=(0, 10), pady=(5, 15))

        files_frame = tkinter.ttk.LabelFrame(self, text="File List")
        files_frame.pack(fill="both", expand=True, padx=10, pady=3)

        columns = ("name", "size")

        # 1. Создаем контейнер. Первым аргументом передаем его родителя — files_frame.
        table_container = tkinter.ttk.Frame(files_frame)
        table_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 2. Создаем таблицу. Её родитель теперь — table_container.
        self.tree = tkinter.ttk.Treeview(table_container, columns=columns, show="headings")
        self.tree.pack(side="left", fill="both", expand=True)

        # 3. Создаем скроллбар. Его родитель тоже — table_container.
        vs = tkinter.ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        vs.pack(side="right", fill="y")

        # 4. Привязываем скроллбар к таблице
        self.tree.configure(yscrollcommand=vs.set)

        # Определяем заголовки
        self.tree.heading("name", text="File name")
        self.tree.heading("size", text="Unpacked size")

        progress_frame = tkinter.ttk.LabelFrame(self, text="Progress")
        progress_frame.pack(fill="x", padx=10, pady=(3, 10))

        self.value_var_prog = tkinter.IntVar(value=0)

        self.progressbar = tkinter.ttk.Progressbar(orient="horizontal", variable=self.value_var_prog,
                                                   mode="determinate")
        self.progressbar.pack(fill="x", in_=progress_frame, padx=10, pady=(0, 10))

        # directory_path_entry = tkinter.ttk.Label(self, textvariable = self.value_var_prog)
        # directory_path_entry.pack(side = "left")

        # Кнопка Close (будет самой правой)
        close_btn = tkinter.ttk.Button(self)
        close_btn["text"] = "Close"
        close_btn["command"] = root.destroy
        close_btn.pack(side="right", padx=(0, 20), pady=15)

        # Кнопка Unzip (встанет левее кнопки Close)
        unzip_btn = tkinter.ttk.Button(self)
        unzip_btn.bind("<ButtonRelease>", self.unzip)
        unzip_btn["text"] = "Unzip"
        unzip_btn.pack(side="right", padx=(0, 10), pady=15)

    def open_image_in_new_window(self, evt=None):
        file_paths = filedialog.askopenfilenames(
            filetypes=(("Изображения", "*.jpg;*.jpeg;*.png"), ("Все файлы", "*.*"))
        )
        if not file_paths:
            return

        # Сбрасываем счетчик сетки в 0, чтобы окна всегда начинались с левого верхнего угла
        self.window_count = 0

        if len(file_paths) > 8:
            messagebox.showwarning(
                "Предупреждение",
                f"Выбрано {len(file_paths)} файлов.\nБудут открыты только первые 8."
            )

        for file_path in file_paths[:8]:
            self._create_image_window(file_path)

    def _get_exif_summary(self, img):
        """Извлекает дату съемки, модель камеры и параметры кадра из EXIF"""
        exif = img.getexif()
        if not exif:
            return "EXIF: нет данных"

        # Преобразуем числовые коды тегов в понятные названия
        data = {ExifTags.TAGS.get(tag, tag): val for tag, val in exif.items()}

        # 1. Дата и время съемки
        date_str = data.get("DateTimeOriginal") or data.get("DateTime")
        if date_str:
            # Меняем формат '2026:11:21 19:40:00' на более читаемый '2026-11-21 19:40'
            date_str = str(date_str).replace(":", "-", 2)[:16]

        # 2. Модель камеры или смартфона
        model = str(data.get("Model", "")).strip()

        # 3. Параметры съемки (ISO и выдержка)
        iso = data.get("ISOSpeedRatings")
        exp = data.get("ExposureTime")
        settings = []
        if iso:
            settings.append(f"ISO {iso}")
        if exp:
            # Если выдержка меньше 1 сек (например, 0.005), переводим в дробь 1/200
            exp_str = f"1/{round(1 / exp)}с" if 0 < exp < 1 else f"{exp}с"
            settings.append(exp_str)

        # Собираем всё в компактную строку
        parts = [p for p in [date_str, model, ", ".join(settings)] if p]
        return f"EXIF: {' | '.join(parts)}" if parts else "EXIF: базовые теги"

    def _create_image_window(self, file_path):
        new_window = Toplevel()
        new_window.title(os.path.basename(file_path))

        # --- НАСТРОЙКА ПОЗИЦИИ И РАЗМЕРА ОКНА (СЕТКА 4x2) ---
        if not hasattr(self, "window_count"):
            self.window_count = 0

        cols = 4
        rows = 2

        col = self.window_count % cols
        row = (self.window_count // cols) % rows

        screen_w = new_window.winfo_screenwidth()
        screen_h = new_window.winfo_screenheight() - 60  # Запас под панель задач снизу

        cell_w = screen_w // cols
        cell_h = screen_h // rows

        x = col * cell_w
        y = row * cell_h

        # Вычитаем толщину системных рамок (16px) и шапки окна (35px), чтобы окна не наезжали друг на друга
        win_w = cell_w - 16
        win_h = cell_h - 35

        # Задаем И размер (WxH), И координаты (+X+Y)
        new_window.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.window_count += 1
        # ----------------------------------------------------

        # 1. Загружаем ОРИГИНАЛ и сохраняем его в память (без блока with, чтобы объект жил пока открыто окно)
        orig_img = Image.open(file_path)
        orig_width, orig_height = orig_img.size
        img_format = orig_img.format
        file_size_kb = round(os.path.getsize(file_path) / 1024, 1)
        exif_line = self._get_exif_summary(orig_img)

        # 2. Создаем пустой Label для фото (саму картинку в него подставит функция ниже)
        img_label = Label(new_window)
        img_label.pack(side="top", expand=True, fill="both", padx=10, pady=(5, 5))

        # Запоминаем прошлый размер области, чтобы не перерисовывать картинку вхолостую
        last_size = [0, 0]

        def resize_image(event):
            # Вычитаем отступы (padx=10 с двух сторон = 20px, pady=5 сверху и снизу = 10px)
            avail_w = event.width - 20
            avail_h = event.height - 10

            # Игнорируем слишком мелкие размеры при инициализации и повторные вызовы с тем же размером
            if avail_w < 50 or avail_h < 50 or [avail_w, avail_h] == last_size:
                return
            last_size[0], last_size[1] = avail_w, avail_h

            # Делаем копию оригинала и подгоняем под текущий размер области (сохраняя пропорции)
            resized = orig_img.copy()
            resized.thumbnail((avail_w, avail_h), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized)

            img_label.config(image=photo)
            img_label.image = photo  # Обязательно обновляем ссылку

        # Привязываем перерисовку к изменению размеров области img_label
        img_label.bind("<Configure>", resize_image)



        # 2. Информация
        file_name = os.path.basename(file_path)
        short_file_name = file_name if len(file_name) < 75 else "..." + file_name[-72:]
        short_path = file_path if len(file_path) < 75 else "..." + file_path[-72:]
        info_text = (
            f"Файл: {short_file_name}\n"
            f"Путь: {short_path}\n"
            f"Размер: {orig_width}×{orig_height} px | {img_format} | {file_size_kb} КБ\n"
            f"{exif_line}"
        )

        info_label = Label(
            new_window,
            text=info_text,
            font=("Arial", 8),
            fg="#222222",
            justify="left",
            anchor="w",
            wraplength = win_w - 25
        )
        info_label.pack(fill="x", padx=10, pady=(0, 5))

        # 3. Функции для кнопок
        # Важно: передаем path=file_path по умолчанию, чтобы в цикле каждая кнопка помнила СВОЙ файл
        def move_file(path=file_path, win=new_window):
            target_dir = filedialog.askdirectory(title="Выберите папку", parent=win)
            if not target_dir:
                return
            orig_img.close()
            try:
                shutil.move(path, os.path.join(target_dir, os.path.basename(path)))
                win.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переместить:\n{e}", parent=win)

        def delete_file(path=file_path, win=new_window):
            if messagebox.askyesno("Подтверждение", f"Удалить {os.path.basename(path)}?", parent=win):
                orig_img.close()
                try:
                    os.remove(path)
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить:\n{e}", parent=win)

        # 4. Кнопки
        btn_frame = Frame(new_window)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 8))

        Button(btn_frame, text="Переместить", command=move_file, font=("Arial", 8), width=11).pack(side="left",
                                                                                                   padx=(0, 3))
        Button(btn_frame, text="Удалить", command=delete_file, font=("Arial", 8), width=8, fg="#b00020").pack(
            side="left", padx=3)
        Button(btn_frame, text="Закрыть", command=new_window.destroy, font=("Arial", 8), width=8).pack(side="right")





    def open_file(self, evt):
        my_path = askopenfilename(filetypes=(('.rar', '*.rar'), ('Any', '*')), multiple=True)
        if not my_path:
            return
        directory_path = os.path.dirname(my_path[0])
        directory_path = os.path.join(directory_path, "rar")
        directory_path = os.path.normpath(directory_path)
        print(self.directory_path_var)
        print(directory_path, my_path[0])
        self.directory_path_var.set(directory_path)
        self.archive_path_var.set(my_path[0])

        for i in my_path:
            file_size = os.path.getsize(i)
            self.tree.insert("", END, values=(i, file_size))

    def select_folder(self, evt):
        # Метод для кнопки Select — открывает диалог выбора папки
        selected_dir = askdirectory()
        if selected_dir:
            self.directory_path_var.set(os.path.normpath(selected_dir))

    def unzip(self, evt):
        self.progressbar['maximum'] = len(self.tree.get_children(''))
        for i, j in enumerate(self.tree.get_children('')):
            path = self.tree.item(j)["values"][0]
            print(path)


        tkinter.messagebox.showinfo("Info", "Done!")
        self.value_var_prog.set(0)


if __name__ == '__main__':
    root = Tk()
    app = Application(master=root)
    root.mainloop()

    """ 
        def heavy_work():
        print("Задача началась...")
        time.sleep(5)  # Имитация долгой работы
        print("Задача завершена!")
        # Останавливаем прогрессбар после завершения
        progress.stop()
        status_label.config(text="Готово!")
        btn.config(state=tk.NORMAL)
        """


