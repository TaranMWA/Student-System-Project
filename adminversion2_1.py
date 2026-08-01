import tkinter as tk
from tkinter import ttk, messagebox
from backend import (
    count_students, count_courses, view_students, view_courses, view_enrollments,
    view_timetable, add_student, edit_student, remove_student, add_course,
    enrol_student, remove_enrollment, add_lesson, remove_lesson, mark_attendance,
    attendance_summary
)


def show_admin_dashboard():
    root = tk.Toplevel()
    root.title("Capital City College - Admin Dashboard")
    root.geometry("1100x650")
    root.configure(bg="#F5F5F5")

    topbar = tk.Frame(root, bg="white", height=60)
    topbar.pack(fill="x")

    for item in ["Dashboard", "Courses", "Timetable", "Admin"]:
        tk.Button(topbar, text=item, bg="white", fg="#333333", font=("Arial", 12), relief="flat").pack(side="left", padx=20, pady=10)

    tk.Button(topbar, text="Logout", bg="#FF6B6B", fg="white", font=("Arial", 12, "bold"), relief="flat", command=root.destroy).pack(side="right", padx=20, pady=10)

    sidebar = tk.Frame(root, width=220, bg="#D9D9D9")
    sidebar.pack(side="left", fill="y")
    tk.Label(sidebar, text="Admin Menu", bg="#D9D9D9", font=("Arial", 16, "bold")).pack(pady=20)

    main_frame = tk.Frame(root, bg="#F5F5F5")
    main_frame.pack(side="right", expand=True, fill="both")

    work = tk.Frame(main_frame, bg="#F5F5F5")
    work.pack(expand=True, fill="both")

    def clear():
        for widget in work.winfo_children():
            widget.destroy()

    def make_form(title, labels, submit_text, submit_cmd):
        clear()
        tk.Label(work, text=title, font=("Arial", 20, "bold"), bg="#F5F5F5").pack(pady=15)
        frm = tk.Frame(work, bg="white", padx=20, pady=20, highlightbackground="#CCCCCC", highlightthickness=1)
        frm.pack(pady=10)
        entries = []
        for i, label in enumerate(labels):
            tk.Label(frm, text=label, bg="white").grid(row=i, column=0, sticky="w")
            entry = tk.Entry(frm, width=35)
            entry.grid(row=i, column=1, padx=10, pady=4)
            entries.append(entry)
        tk.Button(frm, text=submit_text, command=lambda: submit_cmd(entries), bg="#A7C7E7").grid(row=len(labels), column=0, columnspan=2, pady=10)

    def show_students():
        clear()
        tk.Label(work, text="All Students", font=("Arial", 20, "bold"), bg="#F5F5F5").pack(pady=15)
        tree = ttk.Treeview(work, columns=("Name", "ID", "Age", "Gender", "Phone", "Email"), show="headings", height=14)
        for col in ("Name", "ID", "Age", "Gender", "Phone", "Email"):
            tree.heading(col, text=col)
        tree.pack(expand=True, fill="both", padx=15, pady=10)
        for row in view_students():
            tree.insert("", "end", values=row)

    def show_courses():
        clear()
        tk.Label(work, text="Courses", font=("Arial", 20, "bold"), bg="#F5F5F5").pack(pady=15)
        tree = ttk.Treeview(work, columns=("ID", "Course Name"), show="headings", height=14)
        for col in ("ID", "Course Name"):
            tree.heading(col, text=col)
        tree.pack(expand=True, fill="both", padx=15, pady=10)
        for row in view_courses():
            tree.insert("", "end", values=row)

    def show_enrollments():
        clear()
        tk.Label(work, text="Enrollments", font=("Arial", 20, "bold"), bg="#F5F5F5").pack(pady=15)
        tree = ttk.Treeview(work, columns=("Student Name", "Student ID", "Course", "Enrolled At"), show="headings", height=14)
        for col in ("Student Name", "Student ID", "Course", "Enrolled At"):
            tree.heading(col, text=col)
        tree.pack(expand=True, fill="both", padx=15, pady=10)
        for row in view_enrollments():
            tree.insert("", "end", values=row)

    def show_timetable():
        clear()
        tk.Label(work, text="Timetable", font=("Arial", 20, "bold"), bg="#F5F5F5").pack(pady=15)
        tree = ttk.Treeview(work, columns=("ID", "Course", "Day", "Time", "Room", "Instructor"), show="headings", height=14)
        for col in ("ID", "Course", "Day", "Time", "Room", "Instructor"):
            tree.heading(col, text=col)
        tree.pack(expand=True, fill="both", padx=15, pady=10)
        for row in view_timetable():
            tree.insert("", "end", values=row)

    def show_totals():
        clear()
        tk.Label(work, text="System Totals", font=("Arial", 20, "bold"), bg="#F5F5F5").pack(pady=15)
        tk.Label(work, text=f"Total Students: {count_students()}", font=("Arial", 16), bg="#F5F5F5").pack(pady=10)
        tk.Label(work, text=f"Total Courses: {count_courses()}", font=("Arial", 16), bg="#F5F5F5").pack(pady=10)

    def add_student_ui():
        def submit(entries):
            try:
                add_student(entries[0].get().strip().title(), int(entries[1].get().strip()), int(entries[2].get().strip()), entries[3].get().strip().upper(), entries[4].get().strip(), entries[5].get().strip())
                messagebox.showinfo("Success", "Student added")
                show_students()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Add Student", ["Name", "Student ID", "Age", "Gender (M/F)", "Phone", "Email"], "Save", submit)

    def edit_student_ui():
        def submit(entries):
            try:
                edit_student(int(entries[0].get().strip()), entries[1].get().strip().title(), int(entries[2].get().strip()), int(entries[3].get().strip()), entries[4].get().strip().upper(), entries[5].get().strip(), entries[6].get().strip())
                messagebox.showinfo("Success", "Student updated")
                show_students()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Edit Student", ["Current Student ID", "Name", "New Student ID", "Age", "Gender (M/F)", "Phone", "Email"], "Update", submit)

    def remove_student_ui():
        def submit(entries):
            try:
                remove_student(int(entries[0].get().strip()))
                messagebox.showinfo("Success", "Student removed")
                show_students()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Remove Student", ["Student ID"], "Remove", submit)

    def add_course_ui():
        def submit(entries):
            try:
                add_course(entries[0].get().strip().title())
                messagebox.showinfo("Success", "Course added")
                show_courses()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Add Course", ["Course Name"], "Save", submit)

    def enrol_ui():
        def submit(entries):
            try:
                enrol_student(int(entries[0].get().strip()), entries[1].get().strip().title())
                messagebox.showinfo("Success", "Student enrolled")
                show_enrollments()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Enroll Student", ["Student ID", "Course Name"], "Enroll", submit)

    def remove_enrol_ui():
        def submit(entries):
            try:
                n = remove_enrollment(int(entries[0].get().strip()), entries[1].get().strip().title())
                messagebox.showinfo("Result", "Removed" if n else "Enrollment not found")
                show_enrollments()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Remove Enrollment", ["Student ID", "Course Name"], "Remove", submit)

    def add_lesson_ui():
        def submit(entries):
            try:
                add_lesson(entries[0].get().strip().title(), entries[1].get().strip().title(), entries[2].get().strip(), entries[3].get().strip(), entries[4].get().strip())
                messagebox.showinfo("Success", "Lesson added")
                show_timetable()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Add Lesson", ["Course Name", "Day of Week", "Time Slot", "Room", "Instructor"], "Save", submit)

    def remove_lesson_ui():
        def submit(entries):
            try:
                n = remove_lesson(entries[0].get().strip().title(), entries[1].get().strip().title(), entries[2].get().strip())
                messagebox.showinfo("Result", "Lesson removed" if n else "Lesson not found")
                show_timetable()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Remove Lesson", ["Course Name", "Day of Week", "Time Slot"], "Remove", submit)

    def attendance_ui():
        def submit(entries):
            try:
                mark_attendance(int(entries[0].get().strip()), entries[1].get().strip().title(), entries[2].get().strip().title(), entries[3].get().strip(), entries[4].get().strip().lower() == "y")
                messagebox.showinfo("Success", "Attendance marked")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Mark Attendance", ["Student ID", "Course Name", "Day of Week", "Time Slot", "Present? (y/n)"], "Save", submit)

    def attendance_percent_ui():
        def submit(entries):
            try:
                row = attendance_summary(int(entries[0].get().strip()))
                if not row or row[1] == 0:
                    messagebox.showinfo("Attendance", "No attendance records found")
                    return
                name, total, present = row
                pct = (present / total * 100) if total else 0
                messagebox.showinfo("Attendance", f"{name}\nTotal Lessons: {total}\nPresent: {present}\nAttendance %: {pct:.1f}%")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        make_form("Attendance Percentage", ["Student ID"], "Check", submit)

    buttons = [
        ("Add Student", add_student_ui), ("Edit Student", edit_student_ui), ("Remove Student", remove_student_ui),
        ("View Students", show_students), ("Add Course", add_course_ui), ("View Courses", show_courses),
        ("Enroll Student", enrol_ui), ("Remove Enrollment", remove_enrol_ui), ("View Enrollments", show_enrollments),
        ("Add Lesson", add_lesson_ui), ("Remove Lesson", remove_lesson_ui), ("View Timetable", show_timetable),
        ("Mark Attendance", attendance_ui), ("Attendance %", attendance_percent_ui), ("Totals", show_totals)
    ]

    tk.Label(sidebar, text="Admin Menu", bg="#D9D9D9", font=("Arial", 16, "bold")).pack(pady=15)
    for text, func in buttons:
        tk.Button(sidebar, text=text, command=func, bg="white", relief="flat").pack(fill="x", padx=15, pady=3)

    show_totals()
