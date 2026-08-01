import tkinter as tk
from tkinter import ttk, messagebox
from backend import view_courses, view_timetable, mark_attendance


def show_teacher_dashboard(teacher_name="Teacher"):
    root = tk.Toplevel()
    root.title("Capital City College - Teacher Dashboard")
    root.geometry("1200x700")
    root.configure(bg="#F5F5F5")

    topbar = tk.Frame(root, bg="white", height=60)
    topbar.pack(fill="x")

    for item in ["Dashboard", "Courses", "Attendance", "Admin"]:
        tk.Button(topbar, text=item, bg="white", fg="#333333", font=("Arial", 12), relief="flat").pack(side="left", padx=20, pady=10)

    tk.Button(topbar, text="Logout", bg="#FF6B6B", fg="white", font=("Arial", 12, "bold"), relief="flat", command=root.destroy).pack(side="right", padx=20, pady=10)

    sidebar = tk.Frame(root, width=220, bg="#D9D9D9")
    sidebar.pack(side="left", fill="y")
    tk.Label(sidebar, text="Teacher Menu", bg="#D9D9D9", font=("Arial", 16, "bold")).pack(pady=20)

    main_frame = tk.Frame(root, bg="#F5F5F5")
    main_frame.pack(side="right", expand=True, fill="both")

    courses_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    courses_frame.place(x=40, y=40, width=350, height=200)
    tk.Label(courses_frame, text="My Courses", bg="white", font=("Arial", 14, "bold")).pack(pady=10)

    course_box = tk.Listbox(courses_frame, height=5)
    course_box.pack(fill="both", padx=15, pady=5, expand=True)
    course_rows = view_courses()
    if course_rows:
        for _, course_name in course_rows:
            course_box.insert("end", course_name)
    else:
        course_box.insert("end", "No courses found")

    tk.Button(courses_frame, text="Manage Courses", bg="#A7C7E7", font=("Arial", 12), relief="flat").pack(pady=10)

    classes_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    classes_frame.place(x=420, y=40, width=700, height=200)
    tk.Label(classes_frame, text="Today's Classes", bg="white", font=("Arial", 14, "bold")).pack(pady=10)

    columns = ("Time", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
    tree = ttk.Treeview(classes_frame, columns=columns, show="headings", height=4)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)
    tree.pack()

    lessons = view_timetable()
    rows = {}
    for _, course, day, time_slot, room, instructor in lessons:
        rows.setdefault(time_slot, ["", "", "", "", ""])
        idx = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}.get(day)
        if idx is not None:
            rows[time_slot][idx] = course

    if rows:
        for time_slot, vals in sorted(rows.items()):
            tree.insert("", "end", values=(time_slot, *vals))
    else:
        tree.insert("", "end", values=("9:00", "", "Course A", "", "", ""))
        tree.insert("", "end", values=("10:00", "", "", "Course B", "", ""))
        tree.insert("", "end", values=("11:00", "", "", "", "Course C", ""))

    performance_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    performance_frame.place(x=40, y=270, width=350, height=150)
    tk.Label(performance_frame, text="Student Performance", bg="white", font=("Arial", 14, "bold")).pack(pady=10)
    tk.Label(performance_frame, text="Avg. GPA: 3.4", bg="white", font=("Arial", 12)).pack(pady=5)
    tk.Label(performance_frame, text="Pending Assignments: 2", bg="white", font=("Arial", 12)).pack(pady=5)

    actions_frame = tk.Frame(main_frame, bg="white", highlightbackground="#CCCCCC", highlightthickness=1)
    actions_frame.place(x=420, y=270, width=700, height=150)
    tk.Label(actions_frame, text="Quick Actions", bg="white", font=("Arial", 14, "bold")).pack(pady=10)

    def take_attendance_popup():
        win = tk.Toplevel(root)
        win.title("Take Attendance")
        win.geometry("420x260")
        fields = ["Student ID", "Course Name", "Day of Week", "Time Slot", "Present? (y/n)"]
        entries = []
        for i, f in enumerate(fields):
            tk.Label(win, text=f).grid(row=i, column=0, sticky="w", padx=10, pady=4)
            e = tk.Entry(win, width=30)
            e.grid(row=i, column=1, padx=10, pady=4)
            entries.append(e)
        def save():
            try:
                mark_attendance(int(entries[0].get().strip()), entries[1].get().strip().title(), entries[2].get().strip().title(), entries[3].get().strip(), entries[4].get().strip().lower() == "y")
                messagebox.showinfo("Success", "Attendance marked")
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        tk.Button(win, text="Save", command=save, bg="#B5EAD7").grid(row=len(fields), column=0, columnspan=2, pady=12)

    def grade_assignments_popup():
        messagebox.showinfo("Grade Assignments", "This section can be connected to your grading table next.")

    tk.Button(actions_frame, text="Take Attendance", bg="#B5EAD7", font=("Arial", 12), relief="flat", command=take_attendance_popup).pack(pady=5)
    tk.Button(actions_frame, text="Grade Assignments", bg="#B5EAD7", font=("Arial", 12), relief="flat", command=grade_assignments_popup).pack(pady=5)

    return root
