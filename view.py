from tkinter import *
from tkinter import ttk, messagebox, filedialog
from controller import Controller
from model import Database


class Paginator:
    def __init__(self, controller, records_per_page=5, current_page=1):
        self.controller = controller
        self.records_per_page = records_per_page
        self.current_page = current_page
        self.total_records = self.controller.get_total()

    def get_total_pages(self):
        return (self.total_records + self.records_per_page -
                1) // self.records_per_page

    def get_paginated_data(self):
        start_idx = (self.current_page - 1) * self.records_per_page
        return self.controller.get_paginated(self.records_per_page, start_idx)

    def first_page(self):
        self.current_page = 1

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1

    def next_page(self):
        if self.current_page < self.get_total_pages():
            self.current_page += 1

    def last_page(self):
        self.current_page = self.get_total_pages()

    def set_records_per_page(self, records_per_page):
        self.records_per_page = records_per_page
        self.current_page = 1

    def update_total_records(self):
        self.total_records = self.controller.get_total()


class TableView:
    def __init__(self, root, paginator):
        self.root = root
        self.paginator = paginator
        self.main_table_frame = Frame(self.root)
        self.main_table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        self.init_table_view()

    def init_table_view(self):
        h_scrollbar = ttk.Scrollbar(self.main_table_frame, orient=HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(self.main_table_frame, orient=VERTICAL)
        self.canvas = Canvas(
            self.main_table_frame,
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set)
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.table_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.table_frame, anchor=NW)

        def on_frame_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.table_frame.bind("<Configure>", on_frame_configure)

    def draw_table(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        ttk.Label(
            self.table_frame,
            text="ФИО студента",
            width=20).grid(
            row=1,
            column=0,
            padx=10,
            pady=5)
        ttk.Label(
            self.table_frame,
            text="Группа",
            width=10).grid(
            row=1,
            column=1,
            padx=5,
            pady=5)
        ttk.Label(
            self.table_frame,
            text="Экзамены").grid(
            row=0,
            column=2,
            columnspan=100,
            padx=100,
            sticky=W,
            pady=5)

        students = self.paginator.get_paginated_data()
        max_exams = max(len(student['exams'])
                        for student in students) if students else 0

        for exam_num in range(max_exams):
            col = 2 + exam_num
            ttk.Label(
                self.table_frame,
                text=f"Экз.{
                    exam_num +
                    1}").grid(
                row=1,
                column=col,
                padx=5,
                pady=5,
                sticky=N)

        for i, student in enumerate(students, start=2):
            ttk.Label(
                self.table_frame,
                text=student['fio'],
                width=20).grid(
                row=i,
                column=0,
                padx=10,
                sticky=W)
            ttk.Label(
                self.table_frame,
                text=student['group'],
                width=10).grid(
                row=i,
                column=1,
                padx=5,
                sticky=W)
            for exam_num, (subject, grade) in enumerate(
                    student['exams'].items()):
                col = 2 + exam_num
                ttk.Label(
                    self.table_frame,
                    text=subject,
                    wraplength=80).grid(
                    row=i,
                    column=col,
                    padx=25,
                    sticky=SW)
                ttk.Label(
                    self.table_frame,
                    text=str(grade)).grid(
                    row=i,
                    column=col,
                    sticky=SE)

    def pack(self):
        self.main_table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def pack_forget(self):
        self.main_table_frame.pack_forget()


class TreeView:
    def __init__(self, root, paginator):
        self.root = root
        self.paginator = paginator
        self.tree_frame = Frame(self.root)
        self.init_tree_view()

    def init_tree_view(self):
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree["columns"] = ("group", "exams")
        self.tree.column("#0", width=200, minwidth=200, stretch=NO)
        self.tree.column("group", width=100, minwidth=100, stretch=NO)
        self.tree.column("exams", width=400, minwidth=200)
        self.tree.heading("#0", text="ФИО студента", anchor=W)
        self.tree.heading("group", text="Группа", anchor=W)
        self.tree.heading("exams", text="Экзамены", anchor=W)
        scrollbar = ttk.Scrollbar(
            self.tree_frame,
            orient="vertical",
            command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

    def show_tree_view(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        students = self.paginator.get_paginated_data()
        for i, student in enumerate(students):
            student_id = f"student_{i}"
            exams_str = ", ".join(
                f"{k}:{v}" for k,
                v in student['exams'].items())
            self.tree.insert(
                "",
                "end",
                iid=student_id,
                text=student['fio'],
                values=(
                    student['group'],
                    exams_str))
            for subject, grade in student['exams'].items():
                exam_id = f"{student_id}_{subject}"
                self.tree.insert(
                    student_id,
                    "end",
                    iid=exam_id,
                    text=subject,
                    values=(
                        "",
                        str(grade)))

    def pack(self):
        self.tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def pack_forget(self):
        self.tree_frame.pack_forget()


class Main:
    def __init__(self, controller):
        self.root = Tk()
        self.controller = controller
        self.root.title('Students_base')
        self.root.geometry("800x400")
        self.root.resizable(False, False)
        self.view_mode = "table"

        self.Menu()
        self.paginator = Paginator(self.controller)
        self.createPaginationControls()
        self.createViewToggle()
        self.table_view = TableView(self.root, self.paginator)
        self.tree_view = TreeView(self.root, self.paginator)

        self.update_view()
        self.root.mainloop()

    def create_note(self):
        self.window = Toplevel()
        self.window.title("Создание записи о студенте")
        self.window.geometry("500x400")

        main_frame = Frame(self.window)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        canvas = Canvas(main_frame)
        scrollbar = ttk.Scrollbar(
            main_frame,
            orient=VERTICAL,
            command=canvas.yview)
        scrollable_frame = Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(scrollable_frame, text="ФИО студента:").pack(pady=(5, 0))
        self.fio_entry = ttk.Entry(scrollable_frame, width=40)
        self.fio_entry.pack(pady=(0, 10))

        ttk.Label(scrollable_frame, text="Номер группы:").pack()
        self.group_entry = ttk.Entry(scrollable_frame, width=40)
        self.group_entry.pack(pady=(0, 15))

        self.exams_frame = LabelFrame(scrollable_frame, text="Экзамены")
        self.exams_frame.pack(fill=X, pady=5)

        ttk.Button(
            scrollable_frame,
            text="Добавить экзамен",
            command=self.add_exam_field).pack(
            pady=5)
        self.exam_entries = []
        self.add_exam_field()

        buttons_frame = Frame(scrollable_frame)
        buttons_frame.pack(pady=10)

        ttk.Button(
            buttons_frame,
            text="Сохранить",
            command=self.save_student).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            buttons_frame,
            text="Отмена",
            command=self.window.destroy).pack(
            side=LEFT,
            padx=5)

    def add_exam_field(self):
        exam_frame = Frame(self.exams_frame)
        exam_frame.pack(fill=X, pady=2)

        ttk.Label(exam_frame, text="Предмет:").pack(side=LEFT, padx=(0, 5))
        subject_entry = ttk.Entry(exam_frame, width=20)
        subject_entry.pack(side=LEFT)

        ttk.Label(exam_frame, text="Оценка:").pack(side=LEFT, padx=(10, 5))
        grade_entry = ttk.Entry(exam_frame, width=5)
        grade_entry.pack(side=LEFT)

        ttk.Button(
            exam_frame,
            text="✕",
            width=3,
            command=lambda f=exam_frame: self.remove_exam_field(f)).pack(
            side=RIGHT,
            padx=(
                5,
                0))
        self.exam_entries.append((subject_entry, grade_entry))

    def remove_exam_field(self, frame):
        for entry_pair in self.exam_entries:
            if entry_pair[0].master == frame:
                self.exam_entries.remove(entry_pair)
                break
        frame.destroy()

    def save_student(self):
        fio = self.fio_entry.get().strip()
        group = self.group_entry.get().strip()
        exams = {}
        for subject_entry, grade_entry in self.exam_entries:
            subject = subject_entry.get().strip()
            grade = grade_entry.get().strip()
            if not subject:
                messagebox.showerror("Ошибка", "Введите название экзамена")
                return
            if not grade:
                messagebox.showerror("Ошибка", "Введите балл за экзамен")
                return
            try:
                exams[subject] = int(grade)
            except ValueError:
                messagebox.showerror(
                    "Ошибка", f"Некорректная оценка для предмета '{subject}'")
                return

        if not fio or not group or not exams:
            messagebox.showerror(
                "Ошибка", "Заполните все поля и добавьте хотя бы один экзамен")
            return

        student_data = {'fio': fio, 'group': group, 'exams': exams}
        if self.controller.create(student_data) == True:
            messagebox.showinfo(
                "Успешно", f"Студент {
                    student_data['fio']} успешно добавлен!")
            self.window.destroy()
            self.refresh_data()
        else:
            messagebox.showerror(
                "Ошибка ввода данных", "\n".join(
                    self.controller.create(student_data)))

    def refresh_data(self):
        self.paginator.update_total_records()
        self.paginator.first_page()
        self.update_view()

    def find_note(self):
        self.search_window = Toplevel()
        self.search_window.title("Поиск студентов")
        self.search_window.resizable(False, False)

        search_frame = Frame(self.search_window)
        search_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        search_criteria_frame = LabelFrame(
            search_frame, text="Критерии поиска")
        search_criteria_frame.pack(fill=X, pady=5)

        self.search_mode = StringVar(value="group")
        search_options = [
            ("По номеру группы", "group"),
            ("По среднему баллу студента и наличию экзамена", "avg_grade"),
            ("По баллу за конкретный экзамен", "exam_grade")
        ]

        for i, (text, mode) in enumerate(search_options):
            rb = Radiobutton(search_criteria_frame, text=text, variable=self.search_mode,
                             value=mode, command=self.toggle_search_fields)
            rb.grid(row=0, column=i, padx=5, pady=5, sticky=W)

        self.search_input_frame = Frame(search_criteria_frame)
        self.search_input_frame.grid(
            row=1, column=0, columnspan=3, sticky=EW, pady=5)

        search_btn = Button(
            search_criteria_frame,
            text="Найти",
            command=self.perform_search)
        search_btn.grid(row=2, column=0, columnspan=3, pady=10)

        results_frame = LabelFrame(search_frame, text="Результаты поиска")
        results_frame.pack(fill=BOTH, expand=True, pady=5)

        self.results_tree = ttk.Treeview(results_frame, columns=(
            "fio", "group", "exams", "avg_grade"), show="headings")
        self.results_tree.heading("fio", text="ФИО")
        self.results_tree.heading("group", text="Группа")
        self.results_tree.heading("exams", text="Экзамены")
        self.results_tree.heading("avg_grade", text="Ср. балл")
        self.results_tree.column("fio", width=200, anchor=W)
        self.results_tree.column("group", width=100, anchor=CENTER)
        self.results_tree.column("exams", width=300, anchor=W)
        self.results_tree.column("avg_grade", width=80, anchor=CENTER)

        scroll_y = ttk.Scrollbar(
            results_frame,
            orient=VERTICAL,
            command=self.results_tree.yview)
        scroll_x = ttk.Scrollbar(
            results_frame,
            orient=HORIZONTAL,
            command=self.results_tree.xview)
        self.results_tree.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set)

        self.results_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)
        self.toggle_search_fields()

    def toggle_search_fields(self):
        for widget in self.search_input_frame.winfo_children():
            widget.destroy()

        mode = self.search_mode.get()
        if mode == "group":
            self.group_label = Label(
                self.search_input_frame,
                text="Номер группы:")
            self.group_entry = Entry(self.search_input_frame, width=20)
            self.group_label.grid(row=0, column=0, padx=5, pady=5, sticky=E)
            self.group_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        elif mode == "avg_grade":
            self.avg_min_label = Label(
                self.search_input_frame,
                text="Средний балл от:")
            self.avg_min_entry = Entry(self.search_input_frame, width=5)
            self.avg_max_label = Label(self.search_input_frame, text="до:")
            self.avg_max_entry = Entry(self.search_input_frame, width=5)
            self.exam1_name_label = Label(
                self.search_input_frame, text="Название экзамена:")
            self.exam1_name_entry = Entry(self.search_input_frame, width=20)
            self.avg_min_label.grid(row=1, column=0, padx=5, pady=5, sticky=E)
            self.avg_min_entry.grid(row=1, column=1, padx=5, pady=5, sticky=W)
            self.avg_max_label.grid(row=1, column=2, padx=5, pady=5, sticky=E)
            self.avg_max_entry.grid(row=1, column=3, padx=5, pady=5, sticky=W)
            self.exam1_name_label.grid(
                row=0, column=0, padx=5, pady=5, sticky=E)
            self.exam1_name_entry.grid(
                row=0, column=1, padx=5, pady=5, sticky=W)
        elif mode == "exam_grade":
            self.exam_name_label = Label(
                self.search_input_frame,
                text="Название экзамена:")
            self.exam_name_entry = Entry(self.search_input_frame, width=20)
            self.exam_min_label = Label(
                self.search_input_frame, text="Балл от:")
            self.exam_min_entry = Entry(self.search_input_frame, width=5)
            self.exam_max_label = Label(self.search_input_frame, text="до:")
            self.exam_max_entry = Entry(self.search_input_frame, width=5)
            self.exam_name_label.grid(
                row=0, column=0, padx=5, pady=5, sticky=E)
            self.exam_name_entry.grid(
                row=0, column=1, padx=5, pady=5, sticky=W)
            self.exam_min_label.grid(row=1, column=0, padx=5, pady=5, sticky=E)
            self.exam_min_entry.grid(row=1, column=1, padx=5, pady=5, sticky=W)
            self.exam_max_label.grid(row=1, column=2, padx=5, pady=5, sticky=E)
            self.exam_max_entry.grid(row=1, column=3, padx=5, pady=5, sticky=W)

    def perform_search(self):
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        mode = self.search_mode.get()
        try:
            if mode == "group":
                group = self.group_entry.get().strip()
                if not group:
                    messagebox.showwarning("Ошибка", "Введите номер группы")
                    return
                result = self.controller.search_by_group(group)
                if isinstance(result, list):
                    self.results = result
                    self.display_results()
                else:
                    messagebox.showerror("Ошибка ввода данных", result)
                    self.results = []
            elif mode == "avg_grade":
                exam_name1 = self.exam1_name_entry.get().strip()
                if not exam_name1 or not self.avg_min_entry.get() or not self.avg_max_entry.get():
                    messagebox.showwarning("Ошибка", "Заполните все поля")
                    return
                min_avg = int(self.avg_min_entry.get())
                max_avg = int(self.avg_max_entry.get())
                result = self.controller.search_by_avg_grade(
                    exam_name1, min_avg, max_avg)
                if isinstance(result, list):
                    self.results = result
                    self.display_results()
                else:
                    messagebox.showerror("Ошибка ввода данных", result)
                    self.results = []
            elif mode == "exam_grade":
                exam_name = self.exam_name_entry.get().strip()
                if not exam_name or not self.exam_min_entry.get() or not self.exam_max_entry.get():
                    messagebox.showwarning("Ошибка", "Заполните все поля")
                    return
                min_grade = float(self.exam_min_entry.get())
                max_grade = float(self.exam_max_entry.get())
                result = self.controller.search_by_exam_grade(
                    exam_name, min_grade, max_grade)
                if isinstance(result, list):
                    self.results = result
                    self.display_results()
                else:
                    messagebox.showerror("Ошибка ввода данных", result)
                    self.results = []
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный формат данных")

    def display_results(self):
        if not self.results:
            messagebox.showinfo("Результаты", "Студенты не найдены")
            return
        found_students = 0
        for student in self.results:
            found_students += 1
            exams_str = ", ".join(
                [f"{subject}: {grade}" for subject, grade in student['exams'].items()])
            self.results_tree.insert(
                "",
                "end",
                values=(
                    student['fio'],
                    student['group'],
                    exams_str,
                    student.get(
                        'avg_grade',
                        '')))
        messagebox.showinfo("Результаты",
                            f"Студентов найдено: {found_students}")

    def delete_note(self):
        self.deletion_window = Toplevel()
        self.deletion_window.title("Удаление студентов")
        self.deletion_window.resizable(False, False)

        deletion_frame = Frame(self.deletion_window)
        deletion_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        search_criteria_frame = LabelFrame(
            deletion_frame, text="Критерии поиска")
        search_criteria_frame.pack(fill=X, pady=5)

        self.search_mode = StringVar(value="group")
        search_options = [
            ("По номеру группы", "group"),
            ("По среднему баллу студента и наличию экзамена", "avg_grade"),
            ("По баллу за конкретный экзамен", "exam_grade")
        ]

        for i, (text, mode) in enumerate(search_options):
            rb = Radiobutton(search_criteria_frame, text=text, variable=self.search_mode,
                             value=mode, command=self.toggle_search_fields)
            rb.grid(row=0, column=i, padx=5, pady=5, sticky=W)

        self.search_input_frame = Frame(search_criteria_frame)
        self.search_input_frame.grid(
            row=1, column=0, columnspan=3, sticky=EW, pady=5)

        search_btn = Button(
            search_criteria_frame,
            text="Найти и удалить",
            command=self.perform_search_for_deletion)
        search_btn.grid(row=2, column=0, columnspan=3, pady=10)

        results_frame = LabelFrame(
            deletion_frame,
            text="Результаты: записи, которые были удалены")
        results_frame.pack(fill=BOTH, expand=True, pady=5)

        self.results_tree = ttk.Treeview(results_frame, columns=(
            "fio", "group", "exams", "avg_grade"), show="headings")
        self.results_tree.heading("fio", text="ФИО")
        self.results_tree.heading("group", text="Группа")
        self.results_tree.heading("exams", text="Экзамены")
        self.results_tree.heading("avg_grade", text="Ср. балл")
        self.results_tree.column("fio", width=200, anchor=W)
        self.results_tree.column("group", width=100, anchor=CENTER)
        self.results_tree.column("exams", width=300, anchor=W)
        self.results_tree.column("avg_grade", width=80, anchor=CENTER)

        scroll_y = ttk.Scrollbar(
            results_frame,
            orient=VERTICAL,
            command=self.results_tree.yview)
        scroll_x = ttk.Scrollbar(
            results_frame,
            orient=HORIZONTAL,
            command=self.results_tree.xview)
        self.results_tree.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set)

        self.results_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)
        self.toggle_search_fields()

    def perform_search_for_deletion(self):
        self.results = []
        self.perform_search()
        if self.results:
            success, failed = self.controller.delete(self.results)
            messagebox.showinfo(
                "Удаление", f"Удалено успешно: {success}, неудач: {failed}")
            self.refresh_data()

    def clear_db(self):
        if self.controller.clear_db():
            messagebox.showinfo("Успех", "База данных успешно очищена")
            self.refresh_data()
        else:
            messagebox.showerror("Ошибка", "Не удалось очистить базу данных")

    def load_state(self):
        file_path = self.controller.find_path()
        if not file_path:
            return
        if messagebox.askyesno(
                "Подтверждение", "Очистить текущую базу данных перед загрузкой?"):
            self.clear_db()
        if self.controller.load(file_path):
            messagebox.showinfo("Успех", "Данные успешно загружены из файла")
            self.refresh_data()
        else:
            messagebox.showerror(
                "Ошибка", "Не удалось загрузить данные из файла")

    def save_data(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xml", filetypes=[
                ("XML files", "*.xml")], title="Сохранить базу данных")
        if file_path:
            if self.controller.save_to_xml(file_path):
                messagebox.showinfo("Успех", "База данных успешно сохранена")
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить данные")

    def save_to_sql(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[(
            "SQL files", "*.sql"), ("All files", "*.*")], title="Сохранить базу данных как SQL")
        if file_path:
            if self.controller.save_to_sql(file_path):
                messagebox.showinfo(
                    "Успех", "База данных успешно экспортирована в SQL")
            else:
                messagebox.showerror(
                    "Ошибка", "Не удалось экспортировать данные")

    def load_from_sql(self):
        file_path = self.controller.find_path_sql()
        if not file_path:
            return
        if messagebox.askyesno(
                "Подтверждение", "Очистить текущую базу данных перед загрузкой?"):
            self.clear_db()
        if self.controller.load_from_sql(file_path):
            messagebox.showinfo("Успех", "Данные успешно загружены из SQL")
            self.refresh_data()
        else:
            messagebox.showerror("Ошибка", "Ошибка загрузки SQL файла")

    def Menu(self):
        btn_frame = Frame(self.root)
        btn_frame.pack(fill=X, padx=5, pady=5)
        ttk.Button(
            btn_frame,
            text="Создать запись",
            command=self.create_note).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            btn_frame,
            text="Удалить запись",
            command=self.delete_note).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            btn_frame,
            text="Найти запись",
            command=self.find_note).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            btn_frame,
            text="Загрузить из XML",
            command=self.load_state).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            btn_frame,
            text="Сохранить в XML",
            command=self.save_data).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            btn_frame,
            text="Загрузить из БД",
            command=self.load_from_sql).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            btn_frame,
            text="Сохранить в БД",
            command=self.save_to_sql).pack(
            side=LEFT,
            padx=5)

    def createViewToggle(self):
        toggle_frame = Frame(self.root)
        toggle_frame.pack(fill=X, padx=5, pady=2)
        self.view_var = StringVar(value="table")
        ttk.Radiobutton(
            toggle_frame,
            text="Таблица",
            variable=self.view_var,
            value="table",
            command=self.toggle_view).pack(
            side=LEFT,
            padx=5)
        ttk.Radiobutton(
            toggle_frame,
            text="Дерево",
            variable=self.view_var,
            value="tree",
            command=self.toggle_view).pack(
            side=LEFT,
            padx=5)

    def toggle_view(self):
        self.view_mode = self.view_var.get()
        if self.view_mode == "table":
            self.tree_view.pack_forget()
            self.table_view.pack()
        else:
            self.table_view.pack_forget()
            self.tree_view.pack()
        self.update_view()

    def createPaginationControls(self):
        pagination_frame = Frame(self.root)
        pagination_frame.pack(fill=X, padx=5, pady=5)

        ttk.Label(
            pagination_frame,
            text="Записей на странице:").pack(
            side=LEFT,
            padx=5)
        self.records_var = StringVar(
            value=str(self.paginator.records_per_page))
        records_combo = ttk.Combobox(
            pagination_frame, textvariable=self.records_var, values=[
                1, 5, 10, 15, 20, 25, 50], width=5)
        records_combo.pack(side=LEFT, padx=5)
        records_combo.bind(
            "<<ComboboxSelected>>",
            self.change_records_per_page)

        ttk.Button(
            pagination_frame,
            text="<< Первая",
            command=self.first_page).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            pagination_frame,
            text="< Предыдущая",
            command=self.prev_page).pack(
            side=LEFT,
            padx=5)

        self.page_info_frame = Frame(pagination_frame)
        self.page_info_frame.pack(side=LEFT, padx=5)

        self.page_label = ttk.Label(
            self.page_info_frame, text=f"Страница {
                self.paginator.current_page} из {
                self.paginator.get_total_pages()}")
        self.page_label.pack()

        self.total_records_label = ttk.Label(
            self.page_info_frame, text=f"Всего записей: {
                self.paginator.total_records}")
        self.total_records_label.pack()

        ttk.Button(
            pagination_frame,
            text="Следующая >",
            command=self.next_page).pack(
            side=LEFT,
            padx=5)
        ttk.Button(
            pagination_frame,
            text="Последняя >>",
            command=self.last_page).pack(
            side=LEFT,
            padx=5)

    def update_pagination_info(self):
        self.page_label.config(
            text=f"Страница {
                self.paginator.current_page} из {
                self.paginator.get_total_pages()}")
        self.total_records_label.config(
            text=f"Всего записей: {
                self.paginator.total_records}")

    def change_records_per_page(self, event):
        self.paginator.set_records_per_page(int(self.records_var.get()))
        self.update_view()

    def first_page(self):
        self.paginator.first_page()
        self.update_view()

    def prev_page(self):
        self.paginator.prev_page()
        self.update_view()

    def next_page(self):
        self.paginator.next_page()
        self.update_view()

    def last_page(self):
        self.paginator.last_page()
        self.update_view()

    def update_view(self):
        if self.view_mode == "table":
            self.table_view.draw_table()
        else:
            self.tree_view.show_tree_view()
        self.update_pagination_info()
