import sqlite3
import json

class Database:
    def __init__(self, db_name="students.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_db()

    def __del__(self):
        self.conn.close()

    def create_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT NOT NULL,
                group_name TEXT NOT NULL
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                student_id INTEGER,
                exams_data TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')
        self.conn.commit()

    def add_student(self, fio, group, exams):
        self.cursor.execute('''
            INSERT INTO students (fio, group_name)
            VALUES (?, ?)
        ''', (fio, group))
        student_id = self.cursor.lastrowid
        
        self.cursor.execute('''
            INSERT INTO exams (student_id, exams_data)
            VALUES (?, ?)
        ''', (student_id, json.dumps(exams)))
        
        self.conn.commit()

    def get_all_students(self):
        self.cursor.execute('''
            SELECT s.id, s.fio, s.group_name, e.exams_data 
            FROM students s
            JOIN exams e ON s.id = e.student_id
        ''')
        students = []
        for row in self.cursor.fetchall():
            students.append({
                "id": row[0],
                "fio": row[1],
                "group": row[2],
                "exams": json.loads(row[3])
            })
        return students

    def delete_student(self, student_id):
        self.cursor.execute('DELETE FROM exams WHERE student_id = ?', (student_id,))
        self.cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        self.conn.commit()

    def clear_db(self):
        self.cursor.execute("DELETE FROM exams")
        self.cursor.execute("DELETE FROM students")
        self.conn.commit()

    def get_total_students(self):
        self.cursor.execute("SELECT COUNT(*) FROM students")
        return self.cursor.fetchone()[0]

    def get_paginated_students(self, limit, offset):
        self.cursor.execute('''
            SELECT s.id, s.fio, s.group_name, e.exams_data 
            FROM students s
            JOIN exams e ON s.id = e.student_id
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        students = []
        for row in self.cursor.fetchall():
            students.append({
                "id": row[0],
                "fio": row[1],
                "group": row[2],
                "exams": json.loads(row[3])
            })
        return students
    
    def get_total_items(self):
        self.cursor.execute("SELECT COUNT(*) FROM students")
        return self.cursor.fetchone()[0]