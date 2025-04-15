from tkinter import *
from tkinter import ttk, messagebox, filedialog
import json
import xml.sax
from xml.sax.handler import ContentHandler
from xml.dom import minidom
from xml.dom.minidom import Document
from model import Database
import sqlite3
import io
import os


class StudentHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.students = []
        self.current_student = None
        self.current_tag = None
        self.current_exam = None

    def startElement(self, tag, attrs):

        self.current_tag = tag
        if tag == "student":
            self.current_student = {"fio": "", "group": "", "exams": {}}
        elif tag == "exam":
            self.current_exam = attrs["subject"]

    def characters(self, content):
        if self.current_tag == "fio":
            self.current_student["fio"] += content.strip()
        elif self.current_tag == "group":
            self.current_student["group"] += content.strip()
        elif self.current_tag == "grade" and self.current_exam:
            self.current_student["exams"][self.current_exam] = int(
                content.strip())

    def endElement(self, tag):
        if tag == "student":
            self.students.append(self.current_student)
            self.current_student = None
        self.current_tag = None
        if tag == "exam":
            self.current_exam = None


class Controller:
    LEN = 6

    def __init__(self, db):
        self.db = db
        self.notes = self.db.get_all_students()

    def get_total(self):
        return self.db.get_total_items()

    def get_paginated(self, limit, ofset):
        return self.db.get_paginated_students(limit, ofset)

    def clear_db(self):
        try:
            self.db.clear_db()
            return True
        except Exception as e:
            return False

    def find_path(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("XML files", "*.xml")],
            title="Выберите XML файл"
        )
        return file_path

    def find_path_sql(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("SQL files", "*.sql"), ("All files", "*.*")],
            title="Выберите SQL файл для загрузки"
        )
        return file_path

    def save_to_sql(self, file_path):
        try:
            with io.open(file_path, 'w', encoding='utf-8') as f:
                for line in self.db.conn.iterdump():
                    f.write('%s\n' % line)
            return True
        except Exception as e:
            return False

    def load_from_sql(self, file_path):
        try:

            with io.open(file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            temp_conn = sqlite3.connect(':memory:')
            temp_cursor = temp_conn.cursor()

            temp_cursor.executescript(sql_script)

            temp_cursor.execute("SELECT * FROM students")
            students = temp_cursor.fetchall()

            temp_cursor.execute("SELECT * FROM exams")
            exams = temp_cursor.fetchall()

            self.db.cursor.execute("PRAGMA foreign_keys=OFF")

            for student in students:

                self.db.cursor.execute(
                    "SELECT id FROM students WHERE id=?", (student[0],))
                if not self.db.cursor.fetchone():
                    self.db.cursor.execute(
                        "INSERT INTO students (id, fio, group_name) VALUES (?, ?, ?)",
                        student
                    )

            for exam in exams:
                self.db.cursor.execute(
                    "SELECT student_id FROM exams WHERE student_id=?",
                    (exam[0],)
                )
                if not self.db.cursor.fetchone():
                    self.db.cursor.execute(
                        "INSERT INTO exams (student_id, exams_data) VALUES (?, ?)",
                        exam
                    )
            self.db.cursor.execute("PRAGMA foreign_keys=ON")
            self.db.conn.commit()
            temp_conn.close()

            return True
        except Exception as e:
            print(f"Ошибка при загрузке SQL-файла: {e}")
            self.db.conn.rollback()
            self.db.cursor.execute("PRAGMA foreign_keys=ON")
            if 'temp_conn' in locals():
                temp_conn.close()
            return False

    def load(self, file_path):
        try:

            handler = StudentHandler()
            parser = xml.sax.make_parser()
            parser.setContentHandler(handler)

            parser.parse(file_path)

            for student in handler.students:
                self.db.add_student(
                    student["fio"],
                    student["group"],
                    student["exams"]
                )
            return True
        except Exception as e:
            return False

    def validate_student_data(self, data):
        errors = []

        if not all(c.isalpha() or c.isspace() for c in data['fio']):
            errors.append("ФИО должно содержать только буквы и пробелы")
        if len(data['fio'].strip()) < 5:
            errors.append("ФИО слишком короткое (минимум 5 символов)")

        if not data['group'].isdigit() or len(data['group']) != self.LEN:
            errors.append(f"Номер группы должен состоять из {self.LEN} цифр")

        if not isinstance(data['exams'], dict):
            errors.append("Экзамены должны быть в формате словаря")
        else:
            for subject, grade in data['exams'].items():
                if not isinstance(subject, str) or not all(
                        c.isalpha() or c.isspace() for c in subject) or not subject.strip():
                    errors.append(
                        "Название предмета должно быть непустой строкой и содержать только буквы и пробелы")
                if not isinstance(grade, int) or grade < 1 or grade > 10:
                    errors.append(
                        f"Оценка по {subject} должна быть целым числом от 1 до 10")

        return errors

    def create(self, student_data):
        try:
            # Валидация данных
            errors = self.validate_student_data(student_data)
            if errors:
                return errors

            # Добавление в базу данных
            self.db.add_student(
                fio=student_data['fio'],
                group=student_data['group'],
                exams=student_data['exams']
            )

            # Успешное сообщение

            return True

        except Exception as e:
            return e

    def search_by_group(self, group):
        try:
            errors = []
            if not group or len(group) != self.LEN:
                errors.append(
                    f"Номер группы должен состоять из {
                        self.LEN} цифр"
                )
            if not group.isdigit():
                errors.append(f"Номер группы должен состоять из цифр")
            if errors:
                return str(errors)[1:-1]

            students = self.db.get_all_students()
            return [student for student in students if student['group'] == group]

        except Exception as e:
            return False

    def search_by_avg_grade(self, ex, min, max):
        try:
            students = self.db.get_all_students()
            result = []
            errors = []
            if not isinstance(ex, str) or not all(
                    c.isalpha() or c.isspace() for c in ex) or not ex.strip():
                errors.append(
                    "Название предмета должно быть непустой строкой и содержать только буквы и пробелы")

            if min < 1 or min > 10:
                errors.append(
                    f"Нижний Предел должен быть целым числом от 1 до 10")

            if max < 1 or max > 10:
                errors.append(
                    f"Верхний Предел должен быть целым числом от 1 до 10")

            if not max > min:
                errors.append(f"Верхний предел  должен быть больше нижнего")
            if errors:

                return str(errors)[1:-1]

            for student in students:
                if ex in student['exams']:
                    grades = list(student['exams'].values())
                    avg_grade = sum(grades) / len(grades) if grades else 0
                    if min <= avg_grade <= max:
                        student['avg_grade'] = round(avg_grade, 2)
                        result.append(student)
            return result
        except Exception as e:
            return False

    def search_by_exam_grade(self, ex, min, max):
        try:
            students = self.db.get_all_students()
            result = []
            errors = []
            if not isinstance(ex, str) or not all(
                    c.isalpha() or c.isspace() for c in ex) or not ex.strip():
                errors.append(
                    "Название предмета должно быть непустой строкой и содержать только буквы и пробелы")

            if min < 1 or min > 10:
                errors.append(f"Предел должен быть целым числом от 1 до 10")

            if max < 1 or max > 10:
                errors.append(f"Предел должен быть целым числом от 1 до 10")

            if not max > min:
                errors.append(f"Верхний предел  должен быть больше нижнего")

            if errors:
                return str(errors)[1:-1]

            for student in students:
                if ex in student['exams']:
                    grade = student['exams'][ex]
                    if min <= grade <= max:
                        result.append(student)
            return result

        except Exception as e:
            return False

    def delete(self, results):
        success = 0
        failed = 0
        for student in results:
            try:
                self.db.delete_student(student['id'])
                success += 1
            except Exception as e:
                failed += 1
        return success, failed

    def save_to_xml(self, file_path):

        try:
            students = self.db.get_all_students()
            doc = Document()
            root = doc.createElement('students')
            doc.appendChild(root)
            for student in students:
                student_elem = doc.createElement('student')
                root.appendChild(student_elem)
                fio_elem = doc.createElement('fio')
                fio_elem.appendChild(doc.createTextNode(student['fio']))
                student_elem.appendChild(fio_elem)

                group_elem = doc.createElement('group')
                group_elem.appendChild(doc.createTextNode(student['group']))
                student_elem.appendChild(group_elem)

                exams_elem = doc.createElement('exams')
                student_elem.appendChild(exams_elem)

                for subject, grade in student['exams'].items():
                    exam_elem = doc.createElement('exam')
                    exam_elem.setAttribute('subject', subject)

                    grade_elem = doc.createElement('grade')
                    grade_elem.appendChild(doc.createTextNode(str(grade)))
                    exam_elem.appendChild(grade_elem)

                    exams_elem.appendChild(exam_elem)

            xml_str = doc.toprettyxml(indent="  ", encoding='utf-8')

            with open(file_path, 'wb') as f:
                f.write(xml_str)

            return True
        except Exception as e:
            return False
