# New branch

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import os

from PIL import Image, ImageTk

import tkinter
import tkinter.ttk
import tkinter.messagebox
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter import simpledialog, filedialog
from tkinter.constants import END
from tkinter import Tk, Toplevel, Label

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
        file_path = filedialog.askopenfilename(
            filetypes=(("Изображения", "*.jpg;*.jpeg;*.png"), ("Все файлы", "*.*"))
        )
        if not file_path:
            return

        new_window = Toplevel()
        new_window.title(file_path)

        # Открываем и масштабируем фото, чтобы оно поместилось на экран
        img = Image.open(file_path)
        img.thumbnail((800, 600))
        photo = ImageTk.PhotoImage(img)

        label = Label(new_window, image=photo)
        label.image = photo  # Обязательно сохраняем ссылку, иначе картинка пропадет!
        label.pack(padx=10, pady=10)

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


