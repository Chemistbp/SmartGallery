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

        output_frame = tkinter.ttk.LabelFrame(self, text="Папка с фотографиями")
        output_frame.pack(fill="x", padx=10, pady=3)
        output_frame.columnconfigure(0, weight=1)

        directory_path_entry = tkinter.ttk.Entry(output_frame, textvariable=self.directory_path_var, width=54,
                                                 state="disabled")
        directory_path_entry.grid(column=0, row=0, padx=(0, 10), pady=(5, 15), sticky="ew")

        select_btn = tkinter.ttk.Button(output_frame, text="Выбрать")
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
        close_btn["text"] = "Закрыть"
        close_btn["command"] = root.destroy
        close_btn.pack(side="right", padx=(0, 20), pady=15)

        # Кнопка "Сканировать" (встанет левее кнопки Close)
        scan_btn = tkinter.ttk.Button(self)
        scan_btn.bind("<ButtonRelease>", self.scan)
        scan_btn["text"] = "Сканировать"
        scan_btn.pack(side="right", padx=(0, 10), pady=15)

        # Кнопка "Поиск дублей" (встанет левее кнопки Сканировать)
        find_dupl_btn = tkinter.ttk.Button(self)
        find_dupl_btn.bind("<ButtonRelease>", self.find_dupl)
        find_dupl_btn["text"] = "Поиск дублей"
        find_dupl_btn.pack(side="right", padx=(0, 10), pady=15)

    def open_image_in_new_window(self, file_paths):
        #file_paths = filedialog.askopenfilenames(
        #    filetypes=(("Изображения", "*.jpg;*.jpeg;*.png;*.heic"), ("Все файлы", "*.*"))
        #)
        #if not file_paths:
        #    return

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

    def check_db_exists(self, folder_path):
        if not folder_path or not os.path.isdir(folder_path):
            return None
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".db"):
                return filename  # Возвращаем имя найденного файла
        return None

    def _ask_db_action(self, filename):
        """Создает кастомное окно с нужными кнопками и ждет выбора пользователя"""
        dialog = Toplevel(self.master)
        dialog.title("База данных уже существует")
        dialog.resizable(False, False)
        dialog.grab_set()  # Блокируем главное окно, пока пользователь не нажмет кнопку

        # Центрируем окно поверх главного
        x = self.master.winfo_x() + 50
        y = self.master.winfo_y() + 150
        dialog.geometry(f"+{x}+{y}")

        # Переменная для хранения результата нажатия
        user_choice = tkinter.StringVar(value="cancel")

        def choose(action):
            user_choice.set(action)
            dialog.destroy()

        # Текст сообщения
        Label(
            dialog,
            text=f"В этой папке уже найден файл:\n{filename}\n\nЧто вы хотите сделать?",
            justify="left",
            padx=20,
            pady=15
        ).pack()

        # Контейнер для кнопок
        btn_frame = Frame(dialog)
        btn_frame.pack(padx=15, pady=(0, 15))

        Button(
            btn_frame,
            text="Перезаписать",
            width=14,
            command=lambda: choose("overwrite")
        ).pack(side="left", padx=5)

        Button(
            btn_frame,
            text="Дополнить",
            width=14,
            command=lambda: choose("append")
        ).pack(side="left", padx=5)

        Button(
            btn_frame,
            text="Отмена",
            width=10,
            command=lambda: choose("cancel")
        ).pack(side="left", padx=5)

        # Ждем, пока окно не закроется
        self.master.wait_window(dialog)
        return user_choice.get()
    def make_db(self, folder_path):
        folder_path = Path(folder_path)
        db_path = folder_path / "SG.db"
        # Подключаемся к базе данных (если файла нет, он создастся автоматически)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Создаем таблицу для хранения путей и хэшей (если она еще не создана)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_hashes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE,
            image_hash TEXT
        )
        """)
        conn.commit()

        # Укажите путь к вашей папке (можно относительный или абсолютный)
        #folder_path = Path("/content")


        # Задаем кортеж нужных расширений (обязательно с точкой и в нижнем регистре)
        valid_extensions = ('.jpg', '.jpeg', '.png', '.heic')

        data_to_insert = []

        # Ищем все файлы и фильтруем их
        for file_path in folder_path.rglob('*'):
            if file_path.suffix.lower() in valid_extensions:
                print(f"Найден нужный файл: {file_path}")
                try:
                    with Image.open(file_path) as img:
                        # Считаем хэш и сразу переводим его в строку
                        h_str = str(imagehash.phash(img))

                        # Сохраняем абсолютный путь (строкой) и хэш-строку
                        data_to_insert.append((str(file_path.resolve()), h_str))

                except Exception as e:
                    print(f"Ошибка при обработке файла {file_path}: {e}")

        # 4. Массово записываем данные в базу данных
        # Используем INSERT OR IGNORE, чтобы не было ошибок, если файл уже есть в базе (благодаря UNIQUE)
        cursor.executemany("""
        INSERT OR IGNORE INTO file_hashes (file_path, image_hash)
        VALUES (?, ?)
        """, data_to_insert)

        # Подтверждаем изменения и закрываем соединение
        conn.commit()
        conn.close()

        print(f"Успешно обработано и сохранено записей: {len(data_to_insert)}")

    def find_exact_duplicates(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем, какие таблицы вообще есть в этом файле
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        print("Таблицы в базе:", cursor.fetchall())

        # Находим хэши, которые встречаются в таблице больше одного раза
        cursor.execute("""
           SELECT image_hash, GROUP_CONCAT(file_path, ' | ')
           FROM file_hashes
           GROUP BY image_hash
           HAVING COUNT(*) > 1
           """)

        results = cursor.fetchall()
        conn.close()

        # Превращаем результат в список групп путей
        duplicates = [paths.split(' | ') for _, paths in results]
        return duplicates
    def scan(self, evt):
        folder_path = self.directory_path_var.get()
        if not folder_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку с фотографиями!")
            return

        filename = self.check_db_exists(folder_path)

        if filename:
            # Вызываем наше окно с кнопками и получаем ответ
            action = self._ask_db_action(filename)

            if action == "overwrite":
                print(f"Удаляем старую {filename} и создаем заново...")
            elif action == "append":
                print(f"Открываем {filename} и дописываем новые фото...")
            else:
                print("Сканирование отменено пользователем.")
                return
        else:
            self.make_db(folder_path)
            messagebox.showinfo("Info", "Новая база создана!")
        #self.progressbar['maximum'] = len(self.tree.get_children(''))
        #for i, j in enumerate(self.tree.get_children('')):
            #path = self.tree.item(j)["values"][0]
            #print(path)
    def find_dupl(self, evt):
        folder_path = self.directory_path_var.get()
        if not folder_path:
            messagebox.showwarning("Внимание", "Сначала выберите папку с фотографиями!")
            return

        file_name = self.check_db_exists(folder_path)
        # Объединяем путь и имя файла
        full_path = Path(folder_path) / file_name
        print(full_path)
        if file_name:
            arr = self.find_exact_duplicates(full_path)

            print(arr)
            for i in arr:
                self.open_image_in_new_window(i)
                messagebox.showwarning("Вопрос", "Следующее фото?")





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


