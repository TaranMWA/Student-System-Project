import sqlite3 #importing SQLite module to handle databases
from datetime import datetime #import date and time to handle timetables

DB_NAME = "StudentManagementSystemVer1.sqlite"

#upon running code 5 tables will be created, each will link to each other, adding UNIQUE contraints stops duplicates
def create_tables():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # Students table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            name TEXT NOT NULL,
            student_id TEXT PRIMARY KEY,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE
        )
        """)
        
        # Courses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL UNIQUE
        )
        """)
        
        # Enrollments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            student_id TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
        )
        """)
        
        # Lessons table (timetable)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            lesson_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday','Tuesday','Wednesday','Thursday','Friday')),
            time_slot TEXT NOT NULL,  -- e.g., '09:00-10:00'
            room TEXT,
            instructor TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE
        )
        """)
        
        # Attendance table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            lesson_id INTEGER NOT NULL,
            present BOOLEAN NOT NULL DEFAULT 0,
            attendance_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id) ON DELETE CASCADE,
            UNIQUE(student_id, lesson_id)  -- One attendance per student per lesson
        )
        """)
#both these functions read the SQLite database and count all of the entries to find out total amount
def count_students():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        return cursor.fetchone()[0]

def count_courses():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM courses")
        return cursor.fetchone()[0]
#this is what user sees when system is loaded
def display_menu():
    print("=" * 50)
    print("         STUDENT MANAGEMENT SYSTEM")
    print("=" * 50)
    print("1. Add New Student")
    print("2. Remove Student")
    print("3. Edit Student")
    print("4. View All Students")
    print("5. Add Course")
    print("6. View All Courses")
    print("7. Enrol Student in Course")
    print("8. Remove Student from Course")
    print("9. View Student Enrollments")
    print("10. Add Lesson to Timetable")
    print("11. Remove Lesson")
    print("12. View Timetable")
    print("13. Mark Attendance")
    print("14. View Student Attendance %")
    print("15. Total Counts")
    print("16. Exit")
    print("-" * 50)

def add_student(): #allows user to input student data
    print("Enter Student Details:")
    print("-" * 20)
#formats data so inputs all are uniform
    name = input("Name: ").strip().title()
    student_id = input("Student ID: ").strip().upper()
    age_input = input("Age: ").strip()
    gender = input("Gender (M/F/Other): ").strip().upper()
    phone = input("Phone: ").strip()
    email = input("Email: ").strip()

    if not all([name, student_id, age_input, gender, phone, email]):
        print("All fields are required!") #ensures  all fields are populated
        return

    try:
        age = int(age_input)
        if age < 0 or age > 99:
            print("Age must be between 0-99!")#ensures a valid age
            return
    except ValueError:
        print("Age must be a number!")
        return

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO students (name, student_id, age, gender, phone, email) VALUES (?, ?, ?, ?, ?, ?)",
                          (name, student_id, age, gender, phone, email))#inserts data to the SQLite database
        print(f"Student '{name}' registered successfully!")
        print(f"Total students: {count_students()}")
    except sqlite3.IntegrityError:
        print("Student ID, phone, or email already exists!")#avoids duplicates

def view_students():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, student_id, age, gender, phone, email
            FROM students ORDER BY student_id
        """) #gets data from SQLite database
        students = cursor.fetchall()

    if not students:
        print("No students registered yet.")
        return

    print("REGISTERED STUDENTS:")
    print("-" * 50)
    print(f"{'Name':<15} {'Student ID':<12} {'Age':<5} {'Gender':<8} {'Phone':<15} {'Email':<25}")
    print("-" * 50)

    for name, student_id, age, gender, phone, email in students:
        print(f"{name:<15} {student_id:<12} {age:<5} {gender:<8} {phone:<15} {email:<25}")

    print(f"Total students: {len(students)}")

def view_student_enrollments():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name, s.student_id, c.course_name, e.enrolled_at
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            JOIN courses c ON e.course_id = c.course_id
            ORDER BY s.student_id, c.course_name
        """)
        enrollments = cursor.fetchall()

    if not enrollments:
        print("No enrollments found.")
        return

    print("STUDENT ENROLLMENTS:")
    print("-" * 50)
    print(f"{'Student Name':<20} {'Student ID':<12} {'Course':<20} {'Enrolled Date'}")
    print("-" * 50)

    for name, student_id, course, enrolled_at in enrollments:
        print(f"{name:<20} {student_id:<12} {course:<20} {enrolled_at}")

def view_courses():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT course_id, course_name FROM courses ORDER BY course_name")
        courses = cursor.fetchall()

    if not courses:
        print("No courses available.")
        return

    print("AVAILABLE COURSES:")
    print("-" * 50)
    print(f"{'ID':<5} {'Course Name'}")
    print("-" * 50)

    for course_id, course_name in courses:
        print(f"{course_id:<5} {course_name}")

    print(f"Total courses: {len(courses)}")

def add_course():
    course_name = input("Enter course name: ").strip().title() #works the same as previous functions
    
    if not course_name:
        print("Course name is required!")
        return

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO courses (course_name) VALUES (?)", (course_name,))
        print(f"Course '{course_name}' added successfully!")
        print(f"Total courses: {count_courses()}")
    except sqlite3.IntegrityError:
        print("Course already exists!")

def enrol_in_course():
    student_id = input("Enter Student ID: ").strip().upper()
    course_name = input("Enter Course Name: ").strip().title()

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
            student = cursor.fetchone()
            if not student:
                print("Student ID not found!")
                return

            cursor.execute("SELECT course_id FROM courses WHERE course_name = ?", (course_name,))
            course = cursor.fetchone()
            if not course:
                print("Course not found!")
                return

            course_id = course[0]

            cursor.execute("""
                SELECT 1 FROM enrollments
                WHERE student_id = ? AND course_id = ?
            """, (student_id, course_id))
            
            if cursor.fetchone():
                print("Student is already enrolled in this course!")
                return

            cursor.execute("""
                INSERT INTO enrollments (student_id, course_id)
                VALUES (?, ?)
            """, (student_id, course_id))

        print(f"Student '{student[0]}' enrolled in '{course_name}' successfully!")
    except sqlite3.IntegrityError:
        print("Enrollment failed - already enrolled!")

def remove_enrolled_course():
    student_id = input("Enter Student ID: ").strip().upper()
    course_name = input("Enter Course Name: ").strip().title()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT course_id FROM courses WHERE course_name = ?", (course_name,))
        course = cursor.fetchone()
        if not course:
            print("Course not found!")
            return

        course_id = course[0]

        cursor.execute("""
            DELETE FROM enrollments
            WHERE student_id = ? AND course_id = ?
        """, (student_id, course_id)) #deletes from SQLite database

        if cursor.rowcount == 0:
            print("Enrollment not found!")
        else:
            print("Student removed from course successfully!")

def add_lesson():
    print("Add Lesson to Timetable:")
    print("-" * 25)
    
    course_name = input("Lesson Name: ").strip().title()
    day_of_week = input("Day (Monday-Friday): ").strip().title()
    time_slot = input("Time Slot (e.g., 09:00-10:00): ").strip()
    room = input("Room (optional): ").strip()
    instructor = input("Instructor (optional): ").strip()

    if not all([course_name, day_of_week, time_slot]):
        print("Lesson, day, and time slot are required!")
        return

    # Validate day
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if day_of_week not in valid_days:
        print("Day must be Monday-Friday!")
        return

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT course_id FROM courses WHERE course_name = ?", (course_name,))
            course = cursor.fetchone()
            if not course:
                print("Lesson not found!")
                return

            course_id = course[0]

            cursor.execute("""
                INSERT INTO lessons (course_id, day_of_week, time_slot, room, instructor)
                VALUES (?, ?, ?, ?, ?)
            """, (course_id, day_of_week, time_slot, room or None, instructor or None))

        print("Lesson added to timetable successfully!")
    except sqlite3.IntegrityError:
        print("Lesson schedule conflict!")
        
def view_timetable():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.lesson_id, c.course_name, l.day_of_week, l.time_slot, l.room, l.instructor
            FROM lessons l
            JOIN courses c ON l.course_id = c.course_id
            ORDER BY l.day_of_week, l.time_slot
        """)
        lessons = cursor.fetchall()

    if not lessons:
        print("No lessons scheduled.")
        return

    print("TIMETABLE:")
    print("-" * 50)
    print(f"{'ID':<4} {'Course':<20} {'Day':<12} {'Time':<12} {'Room':<10} {'Instructor'}")
    print("-" * 50)

    for lesson_id, course, day, time_slot, room, instructor in lessons:
        room_display = room or "-"
        instructor_display = instructor or "-"
        print(f"{lesson_id:<4} {course:<20} {day:<12} {time_slot:<12} {room_display:<10} {instructor_display}")

def remove_lesson():
    course_name = input("Enter Lesson Name: ").strip().title()
    day_of_week = input("Enter Day (Monday-Friday): ").strip().title()
    time_slot = input("Enter Time Slot (e.g., 09:00-10:00): ").strip()

    if not all([course_name, day_of_week, time_slot]):
        print("Lesson name, day, and time slot are all required!")
        return

    # Validate day
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if day_of_week not in valid_days:
        print("Day must be Monday-Friday!")
        return

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            # Find the exact lesson match
            cursor.execute("""
                SELECT l.lesson_id, c.course_name, l.day_of_week, l.time_slot
                FROM lessons l 
                JOIN courses c ON l.course_id = c.course_id 
                WHERE c.course_name = ? AND l.day_of_week = ? AND l.time_slot = ?
            """, (course_name, day_of_week, time_slot))
            
            lesson = cursor.fetchone()
            
            if not lesson:
                print("No lesson found with that course, day, and time slot!")
                return

            lesson_id, course_name, day, time_slot = lesson
            
            # Confirm deletion
            print(f"\nFound lesson:")
            print(f"  Lesson: {course_name}")
            print(f"  Day: {day}")
            print(f"  Time: {time_slot}")
            confirm = input("Delete this lesson? (y/n): ").strip().lower()
            
            if confirm == 'y':
                cursor.execute("DELETE FROM lessons WHERE lesson_id = ?", (lesson_id,))
                print("Lesson removed successfully!")
            else:
                print("Lesson removal cancelled.")
                
    except sqlite3.Error as e:
        print("Database error occurred!")

def mark_attendance():
    student_id = input("Enter Student ID: ").strip().upper()
    course_name = input("Enter Course Name: ").strip().title()
    day_of_week = input("Enter Day (Monday-Friday): ").strip().title()
    time_slot = input("Enter Time Slot (e.g., 09:00-10:00): ").strip()
    present = input("Present? (y/n): ").strip().lower() == 'y'

    if not all([student_id, course_name, day_of_week, time_slot]):
        print("Student ID, course name, day, and time slot are all required!")
        return

    # Validate day
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    if day_of_week not in valid_days:
        print("Day must be Monday-Friday!")
        return

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Check student exists
            cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
            student = cursor.fetchone()
            if not student:
                print("Student not found!")
                return

            # Find exact lesson match
            cursor.execute("""
                SELECT l.lesson_id, c.course_name, l.day_of_week, l.time_slot
                FROM lessons l 
                JOIN courses c ON l.course_id = c.course_id 
                WHERE c.course_name = ? AND l.day_of_week = ? AND l.time_slot = ?
            """, (course_name, day_of_week, time_slot))
            
            lesson = cursor.fetchone()
            if not lesson:
                print("No lesson found with that course, day, and time slot!")
                return

            lesson_id, course_name, day, time_slot = lesson

            # Mark attendance (INSERT OR REPLACE handles updates)
            cursor.execute("""
                INSERT OR REPLACE INTO attendance (student_id, lesson_id, present)
                VALUES (?, ?, ?)
            """, (student_id, lesson_id, present))

        status = "Present" if present else "Absent"
        print(f"Marked '{student[0]}' as {status} for '{course_name}' on {day} {time_slot}!")
        
    except sqlite3.Error as e:
        print("Database error occurred!")

def view_attendance_percentage():
    student_id = input("Enter Student ID: ").strip().upper()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.name, 
                   COUNT(a.attendance_id) as total_lessons,
                   SUM(CASE WHEN a.present = 1 THEN 1 ELSE 0 END) as present_count
            FROM students s
            LEFT JOIN attendance a ON s.student_id = a.student_id
            WHERE s.student_id = ?
            GROUP BY s.student_id
        """, (student_id,))
        
        result = cursor.fetchone()
        
        if not result or result[1] == 0:
            print("No attendance records found for this student.")
            return

        name, total, present = result
        percentage = (present / total * 100) if total > 0 else 0 #formula to calculate percentage 
        
        print(f"\n{name}'s Attendance Summary:")
        print("-" * 50)
        print(f"Total Lessons: {total}")
        print(f"Present: {present}")
        print(f"Attendance %: {percentage:.1f}%")

def edit_student():
    student_id = input("Enter Student ID to edit: ").strip().upper()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, student_id, age, gender, phone, email
            FROM students WHERE student_id = ?
        """, (student_id,))
        student = cursor.fetchone()

        if not student:
            print("Student ID not found!")
            return

        print("\nCurrent details:")
        print(f"1. Name: {student[0]}")
        print(f"2. Student ID: {student[1]}")
        print(f"3. Age: {student[2]}")
        print(f"4. Gender: {student[3]}")
        print(f"5. Phone: {student[4]}")
        print(f"6. Email: {student[5]}")

        print("\nEnter new values. Press Enter to keep current value.")

        name = input("New Name: ").strip().title() or student[0]
        new_student_id = input("New Student ID: ").strip().upper() or student[1]
        age_input = input("New Age: ").strip()
        gender = input("New Gender: ").strip().upper() or student[3]
        phone = input("New Phone: ").strip() or student[4]
        email = input("New Email: ").strip() or student[5]

        age = int(age_input) if age_input else student[2]
        if age_input and (age < 0 or age > 120):
            print("Age must be between 0-120!")
            return

        try:
            cursor.execute("""
                SELECT 1 FROM students
                WHERE (student_id = ? OR phone = ? OR email = ?)
                AND student_id != ?
            """, (new_student_id, phone, email, student_id))

            if cursor.fetchone():
                print("Student ID, phone, or email already belongs to another student!")
                return

            cursor.execute("""
                UPDATE students
                SET name = ?, student_id = ?, age = ?, gender = ?, phone = ?, email = ?
                WHERE student_id = ?
            """, (name, new_student_id, age, gender, phone, email, student_id))

            print("Student updated successfully!")
        except sqlite3.IntegrityError:
            print("Update failed - ID, phone, or email conflict!")

def remove_student():
    student_id = input("Enter Student ID to remove: ").strip().upper()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()

        if not student:
            print("Student ID not found!")
            return

        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))

    print(f"Student '{student[0]}' removed successfully (all data cleared)!")
    print(f"Total students: {count_students()}")

def main():
    create_tables()
    print(f"Database initialized: {DB_NAME}")

    while True:
        display_menu()
        choice = input("Enter your choice (1-16): ").strip() #allows user to select an option which calls a function

        if choice == "1":
            add_student()
        elif choice == "2":
            remove_student()
        elif choice == "3":
            edit_student()
        elif choice == "4":
            view_students()
        elif choice == "5":
            add_course()
        elif choice == "6":
            view_courses()
        elif choice == "7":
            enrol_in_course()        
        elif choice == "8":
            remove_enrolled_course()
        elif choice == "9":
            view_student_enrollments()
        elif choice == "10":
            add_lesson()
        elif choice == "11":
            remove_lesson()
        elif choice == "12":
            view_timetable()
        elif choice == "13":
            mark_attendance()
        elif choice == "14":
            view_attendance_percentage()
        elif choice == "15":
            print(f"Total students: {count_students()}")
            print(f"Total courses: {count_courses()}")
        elif choice == "16":
            print("Thank you for using the Student Management System!")
            print(f"Data saved to '{DB_NAME}'")
            break
        else:
            print("Invalid choice! Please enter 1-16.")

        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
