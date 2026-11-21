# New branch

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import os

from PIL import Image, ImageTk

import shutil

import tkinter
import tkinter.ttk
import tkinter.messagebox
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter import simpledialog, filedialog
from tkinter.constants import END
from tkinter import Tk, Toplevel, Label, Button, Frame, messagebox

# rarfile.UNRAR_TOOL = r"C:\Users\boris\PycharmProjects\Rar_extractor\.venv\UnRAR.exe"
#rarfile.UNRAR_TOOL = r"C:\Python313\UnRAR.exe"


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
        self.master.title("Unzip RAR")
        self.master.resizable(True, True)
        self.master.geometry("460x550+200+200")

    def create_widgets(self):
        archive_frame = tkinter.ttk.LabelFrame(self, text="RAR Archive")
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

        if len(file_paths) > 8:
            messagebox.showwarning(
                "Предупреждение",
                f"Выбрано {len(file_paths)} файлов.\nБудут открыты только первые 8."
            )

        for file_path in file_paths[:8]:
            self._create_image_window(file_path)

    def _create_image_window(self, file_path):
        new_window = Toplevel()
        new_window.title(os.path.basename(file_path))

        # --- НАСТРОЙКА ПОЗИЦИИ ОКНА (СЕТКА 4x2) ---
        if not hasattr(self, "window_count"):
            self.window_count = 0

        cols = 4
        rows = 2

        col = self.window_count % cols
        row = (self.window_count // cols) % rows

        screen_w = new_window.winfo_screenwidth()
        screen_h = new_window.winfo_screenheight() - 60

        cell_w = screen_w // cols
        cell_h = screen_h // rows

        x = col * cell_w
        y = row * cell_h

        new_window.geometry(f"+{x}+{y}")
        self.window_count += 1
        # -----------------------------------------

        # 1. Получаем данные и масштабируем фото под ячейку
        with Image.open(file_path) as img:
            orig_width, orig_height = img.size
            img_format = img.format
            file_size_kb = round(os.path.getsize(file_path) / 1024, 1)

            max_img_w = max(150, cell_w - 20)
            max_img_h = max(150, cell_h - 165)

            img.thumbnail((max_img_w, max_img_h))
            photo = ImageTk.PhotoImage(img)

        img_label = Label(new_window, image=photo)
        img_label.image = photo
        img_label.pack(padx=10, pady=(5, 5))

        # 2. Информация
        short_path = file_path if len(file_path) < 38 else "..." + file_path[-35:]
        info_text = (
            f"Файл: {os.path.basename(file_path)}\n"
            f"Путь: {short_path}\n"
            f"Размер: {orig_width}×{orig_height} px | {img_format} | {file_size_kb} КБ"
        )

        info_label = Label(
            new_window,
            text=info_text,
            font=("Arial", 8),
            fg="#222222",
            justify="left",
            anchor="w"
        )
        info_label.pack(fill="x", padx=10, pady=(0, 5))

        # 3. Функции для кнопок
        # Важно: передаем path=file_path по умолчанию, чтобы в цикле каждая кнопка помнила СВОЙ файл
        def move_file(path=file_path, win=new_window):
            target_dir = filedialog.askdirectory(title="Выберите папку", parent=win)
            if not target_dir:
                return
            try:
                shutil.move(path, os.path.join(target_dir, os.path.basename(path)))
                win.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переместить:\n{e}", parent=win)

        def delete_file(path=file_path, win=new_window):
            if messagebox.askyesno("Подтверждение", f"Удалить {os.path.basename(path)}?", parent=win):
                try:
                    os.remove(path)
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить:\n{e}", parent=win)

        # 4. Кнопки
        btn_frame = Frame(new_window)
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))

        Button(btn_frame, text="Переместить", command=move_file, font=("Arial", 8), width=11).pack(side="left",
                                                                                                   padx=(0, 3))
        Button(btn_frame, text="Удалить", command=delete_file, font=("Arial", 8), width=8, fg="#b00020").pack(
            side="left", padx=3)
        Button(btn_frame, text="Закрыть", command=new_window.destroy, font=("Arial", 8), width=8).pack(side="right")



    def open_image_in_new_window_v1(self, evt=None):
        file_path = filedialog.askopenfilename(
            filetypes=(("Изображения", "*.jpg;*.jpeg;*.png"), ("Все файлы", "*.*"))
        )
        if not file_path:
            return

        new_window = Toplevel()

        # В заголовок лучше вывести только имя файла
        # new_window.title(file_path)
        new_window.title(os.path.basename(file_path))


        # 1. Открываем фото и сразу собираем информацию об оригинале
        img = Image.open(file_path)

        orig_width, orig_height = img.size
        img_format = img.format
        img_mode = img.mode  # Цветовая модель (RGB, RGBA, L и т.д.)
        file_size_kb = round(os.path.getsize(file_path) / 1024, 1)

        # 2. Масштабируем для отображения
        img.thumbnail((800, 600))
        photo = ImageTk.PhotoImage(img)

        # 3. Выводим картинку
        label = Label(new_window, image=photo)
        label.image = photo  # Обязательно сохраняем ссылку, иначе картинка пропадет!
        label.pack(padx=10, pady=10)

        # 3. Формируем многострочный текст с помощью \n
        info_text = (
            f"Имя файла: {os.path.basename(file_path)}\n"
            f"Путь: {file_path}\n"
            f"Разрешение: {orig_width} × {orig_height} px\n"
            f"Формат и цвет: {img_format} ({img_mode})\n"
            f"Размер на диске: {file_size_kb} КБ"
        )

        # 4. Выводим текст: justify выравнивает строки между собой, anchor прижимает блок влево
        info_label = Label(
            new_window,
            text=info_text,
            font=("Arial", 10),
            fg="#222222",
            justify="left",  # Выравнивание текста внутри блока по левому краю
            anchor="w"  # Привязка самого текста к левой границе виджета
        )
        # fill="x" растягивает виджет на всю ширину окна, чтобы anchor="w" сработал
        info_label.pack(fill="x", padx=15, pady=(5, 15))

        # 4. Функции-обработчики для кнопок
        def move_file():
            # Открываем выбор новой папки (parent=new_window чтобы диалог не прятался за окном)
            target_dir = filedialog.askdirectory(title="Выберите папку для перемещения", parent=new_window)
            if not target_dir:
                return
            try:
                new_path = os.path.join(target_dir, os.path.basename(file_path))
                shutil.move(file_path, new_path)
                messagebox.showinfo("Готово", f"Файл перемещен в:\n{target_dir}", parent=new_window)
                new_window.destroy()  # Закрываем окно после перемещения
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переместить файл:\n{e}", parent=new_window)

        def delete_file():
            # Спрашиваем подтверждение перед удалением
            confirm = messagebox.askyesno(
                "Подтверждение",
                f"Точно удалить файл навсегда?\n{os.path.basename(file_path)}",
                parent=new_window
            )
            if confirm:
                try:
                    os.remove(file_path)
                    new_window.destroy()  # Закрываем окно после удаления
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{e}", parent=new_window)

        # 5. Контейнер (Frame) для кнопок, чтобы они встали в одну линию
        btn_frame = Frame(new_window)
        btn_frame.pack(fill="x", padx=15, pady=(5, 15))

        Button(btn_frame, text="Переместить", command=move_file, width=12).pack(side="left", padx=(0, 5))
        Button(btn_frame, text="Удалить", command=delete_file, width=12, fg="#b00020").pack(side="left", padx=5)
        Button(btn_frame, text="Закрыть", command=new_window.destroy, width=12).pack(side="right")

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


