import tkinter as tk
from tkinter import ttk, messagebox
from backend import view_enrollments, view_timetable, attendance_summary, enrol_student


def show_student_dashboard(student_name="Student Name", student_id="123456"):
    root = tk.Toplevel()
    root.title("Capital City College - Student Dashboard")
    root.geometry("1200x700")
    root.configure(bg="#F5F5F5")

    topbar = tk.Frame(root, bg="white", height=60)
    topbar.pack(fill="x")

    for item in ["Dashboard", "Courses", "Timetable", "Admin"]:
        tk.Button(topbar, text=item, bg="white", fg="#333333", font=("Arial", 12), relief="flat").pack(side="left", padx=20, pady=10)

    tk.Button(topbar, text="Logout", bg="#FF6B6B", fg="white", font=("Arial", 12, "bold"), relief="flat", command=root.destroy).pack(side="right", padx=20, pady=10)

    sidebar = tk.Frame(root, width=220, bg="#D9D9D9")
    sidebar.pack(side="left", fill="y")
    tk.Label(sidebar, text="Student Menu", bg="#D9D9D9", font=("Arial", 16, "bold")).pack(pady=20)

    main_frame = tk.Frame(root, bg="#F5F5F5")
    main_frame.pack(side="right", expand=True, fill="both")

    courses_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    courses_frame.place(x=40, y=40, width=350, height=200)
    tk.Label(courses_frame, text="My Courses", bg="white", font=("Arial", 14, "bold")).pack(pady=10)

    course_box = tk.Listbox(courses_frame, height=5)
    course_box.pack(fill="both", padx=15, pady=5, expand=True)
    enrollments = view_enrollments()
    student_courses = [course for name, sid, course, enrolled_at in enrollments if str(sid) == str(student_id)]
    if student_courses:
        for c in student_courses:
            course_box.insert("end", c)
    else:
        course_box.insert("end", "No enrolled courses yet")

    tk.Label(courses_frame, text="View All Courses", fg="#4A90E2", bg="white", font=("Arial", 11, "underline")).pack(pady=10)

    timetable_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    timetable_frame.place(x=420, y=40, width=700, height=200)
    tk.Label(timetable_frame, text="My Timetable", bg="white", font=("Arial", 14, "bold")).pack(pady=10)

    columns = ("Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    tree = ttk.Treeview(timetable_frame, columns=columns, show="headings", height=4)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack()

    lessons = view_timetable()
    times = ["9:00", "10:00", "11:00"]
    for i, time in enumerate(times):
        row = ["", "", "", "", ""]
        if i < len(lessons):
            _, course, day, slot, room, instructor = lessons[i]
            day_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
            if day in day_map:
                row[day_map[day]] = course
        tree.insert("", "end", values=(time, *row))

    profile_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    profile_frame.place(x=40, y=270, width=350, height=150)
    tk.Label(profile_frame, text="My Profile", bg="white", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(profile_frame, text=f"Name: {student_name}", bg="white", font=("Arial", 12)).pack(pady=5)
    tk.Label(profile_frame, text=f"ID: {student_id}", bg="white", font=("Arial", 12)).pack(pady=5)

    links_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    links_frame.place(x=420, y=270, width=700, height=150)
    tk.Label(links_frame, text="Quick Links", bg="white", font=("Arial", 14, "bold")).pack(pady=10)

    def enrol_popup():
        win = tk.Toplevel(root)
        win.title("Enrol in Course")
        win.geometry("360x180")
        tk.Label(win, text="Course Name").pack(pady=5)
        entry = tk.Entry(win, width=30)
        entry.pack(pady=5)
        def save():
            try:
                enrol_student(int(student_id), entry.get().strip().title())
                messagebox.showinfo("Success", "Enrolled successfully")
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        tk.Button(win, text="Enrol", command=save, bg="#A7C7E7").pack(pady=15)

    def grades_popup():
        row = attendance_summary(int(student_id))
        if not row or row[1] == 0:
            messagebox.showinfo("Grades", "No attendance records yet")
            return
        name, total, present = row
        pct = (present / total * 100) if total else 0
        messagebox.showinfo("Grades", f"Attendance proxy for {name}: {pct:.1f}%")

    tk.Button(links_frame, text="Enrol in Course", bg="#A7C7E7", font=("Arial", 12), relief="flat", command=enrol_popup).pack(pady=5)
    tk.Button(links_frame, text="Check Grades", bg="#A7C7E7", font=("Arial", 12), relief="flat", command=grades_popup).pack(pady=5)

    return root
