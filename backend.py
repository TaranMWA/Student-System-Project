import sqlite3

DB_NAME = "StudentManagementSystemVer1.sqlite"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    with get_connection() as conn:
        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
            student_id INTEGER,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            name TEXT NOT NULL,
            student_id INTEGER PRIMARY KEY,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
            phone TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL UNIQUE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday','Tuesday','Wednesday','Thursday','Friday')),
            time_slot TEXT NOT NULL,
            room TEXT,
            instructor TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            present BOOLEAN NOT NULL DEFAULT 0,
            attendance_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id) ON DELETE CASCADE,
            UNIQUE(student_id, lesson_id)
        )
        """)


def register_user(name, role, email, password, student_id=None):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (name, role, student_id, email, password) VALUES (?, ?, ?, ?, ?)",
            (name, role, student_id, email, password)
        )


def authenticate(email, password):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT name, role, student_id, password FROM users WHERE email=?",
            (email,)
        ).fetchone()

    if row and row[3] == password:
        return row[0], row[1], row[2]
    return None, None, None


def count_students():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]


def count_courses():
    with get_connection() as conn:
        return conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]


def add_student(name, student_id, age, gender, phone, email):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO students VALUES (?, ?, ?, ?, ?, ?)",
            (name, student_id, age, gender, phone, email)
        )


def edit_student(old_student_id, name, new_student_id, age, gender, phone, email):
    with get_connection() as conn:
        conn.execute(
            "UPDATE students SET name=?, student_id=?, age=?, gender=?, phone=?, email=? WHERE student_id=?",
            (name, new_student_id, age, gender, phone, email, old_student_id)
        )


def remove_student(student_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM students WHERE student_id=?", (student_id,))


def view_students():
    with get_connection() as conn:
        return conn.execute(
            "SELECT name, student_id, age, gender, phone, email FROM students ORDER BY student_id"
        ).fetchall()


def add_course(course_name):
    with get_connection() as conn:
        conn.execute("INSERT INTO courses (course_name) VALUES (?)", (course_name,))


def view_courses():
    with get_connection() as conn:
        return conn.execute(
            "SELECT course_id, course_name FROM courses ORDER BY course_name"
        ).fetchall()


def enrol_student(student_id, course_name):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT course_id FROM courses WHERE course_name=?", (course_name,))
        course = c.fetchone()
        if not course:
            raise ValueError("Course not found")
        c.execute(
            "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
            (student_id, course[0])
        )


def remove_enrollment(student_id, course_name):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT course_id FROM courses WHERE course_name=?", (course_name,))
        course = c.fetchone()
        if not course:
            raise ValueError("Course not found")
        c.execute(
            "DELETE FROM enrollments WHERE student_id=? AND course_id=?",
            (student_id, course[0])
        )
        return c.rowcount


def view_enrollments():
    with get_connection() as conn:
        return conn.execute("""
            SELECT s.name, s.student_id, c.course_name, e.enrolled_at
            FROM students s
            JOIN enrollments e ON s.student_id=e.student_id
            JOIN courses c ON e.course_id=c.course_id
            ORDER BY s.student_id, c.course_name
        """).fetchall()


def add_lesson(course_name, day_of_week, time_slot, room, instructor):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT course_id FROM courses WHERE course_name=?", (course_name,))
        course = c.fetchone()
        if not course:
            raise ValueError("Course not found")
        c.execute("""
            INSERT INTO lessons (course_id, day_of_week, time_slot, room, instructor)
            VALUES (?, ?, ?, ?, ?)
        """, (course[0], day_of_week, time_slot, room or None, instructor or None))


def remove_lesson(course_name, day_of_week, time_slot):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT l.lesson_id
            FROM lessons l
            JOIN courses c ON l.course_id=c.course_id
            WHERE c.course_name=? AND l.day_of_week=? AND l.time_slot=?
        """, (course_name, day_of_week, time_slot))
        row = c.fetchone()
        if not row:
            return 0
        c.execute("DELETE FROM lessons WHERE lesson_id=?", (row[0],))
        return c.rowcount


def view_timetable():
    with get_connection() as conn:
        return conn.execute("""
            SELECT l.lesson_id, c.course_name, l.day_of_week, l.time_slot, l.room, l.instructor
            FROM lessons l
            JOIN courses c ON l.course_id=c.course_id
            ORDER BY l.day_of_week, l.time_slot
        """).fetchall()


def mark_attendance(student_id, course_name, day_of_week, time_slot, present):
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT l.lesson_id
            FROM lessons l
            JOIN courses c ON l.course_id=c.course_id
            WHERE c.course_name=? AND l.day_of_week=? AND l.time_slot=?
        """, (course_name, day_of_week, time_slot))
        lesson = c.fetchone()
        if not lesson:
            raise ValueError("Lesson not found")
        c.execute("""
            INSERT INTO attendance (student_id, lesson_id, present)
            VALUES (?, ?, ?)
            ON CONFLICT(student_id, lesson_id) DO UPDATE SET present=excluded.present
        """, (student_id, lesson[0], int(present)))


def attendance_summary(student_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT s.name,
                   COUNT(a.attendance_id),
                   SUM(CASE WHEN a.present=1 THEN 1 ELSE 0 END)
            FROM students s
            LEFT JOIN attendance a ON s.student_id=a.student_id
            WHERE s.student_id=?
            GROUP BY s.student_id
        """, (student_id,)).fetchone()
