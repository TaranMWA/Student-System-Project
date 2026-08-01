import tkinter as tk
from tkinter import messagebox
from backend import register_user, authenticate


def open_dashboard(role, name, student_id=None):
    role = (role or '').lower()
    if role == 'admin':
        from adminversion2_1 import show_admin_dashboard
        show_admin_dashboard()
    elif role == 'teacher':
        from teacher_dashboard import show_teacher_dashboard
        show_teacher_dashboard(name)
    elif role == 'student':
        from student_dashboard import show_student_dashboard
        show_student_dashboard(name, student_id=student_id or '123456')
    else:
        messagebox.showerror('Error', 'Unknown role')


def show_login(on_success=open_dashboard):
    root = tk.Tk()
    root.title('Capital City College - Login')
    root.geometry('1200x700')
    root.configure(bg='#F5F5F5')

    topbar = tk.Frame(root, bg='white', height=60)
    topbar.pack(fill='x')

    for item in ['Dashboard', 'Courses', 'Timetable', 'Admin']:
        tk.Button(topbar, text=item, bg='white', fg='#333333', font=('Arial', 12), relief='flat').pack(side='left', padx=20, pady=10)

    tk.Button(topbar, text='Logout', bg='#FF6B6B', fg='white', font=('Arial', 12, 'bold'), relief='flat', command=root.destroy).pack(side='right', padx=20, pady=10)

    sidebar = tk.Frame(root, width=220, bg='#D9D9D9')
    sidebar.pack(side='left', fill='y')
    tk.Label(sidebar, text='Login Menu', bg='#D9D9D9', font=('Arial', 16, 'bold')).pack(pady=20)

    main_frame = tk.Frame(root, bg='#F5F5F5')
    main_frame.pack(side='right', expand=True, fill='both')

    form_frame = tk.Frame(main_frame, bg='white', highlightbackground='#CCCCCC', highlightthickness=1)
    form_frame.place(x=260, y=80, width=420, height=500)

    tk.Label(form_frame, text='Login / Register', bg='white', font=('Arial', 20, 'bold')).pack(pady=20)

    tk.Label(form_frame, text='Name', bg='white').pack(anchor='w', padx=30)
    e_name = tk.Entry(form_frame, width=35)
    e_name.pack(padx=30, pady=5)

    tk.Label(form_frame, text='Role (admin/teacher/student)', bg='white').pack(anchor='w', padx=30)
    e_role = tk.Entry(form_frame, width=35)
    e_role.pack(padx=30, pady=5)

    tk.Label(form_frame, text='Student ID (students only)', bg='white').pack(anchor='w', padx=30)
    e_sid = tk.Entry(form_frame, width=35)
    e_sid.pack(padx=30, pady=5)

    tk.Label(form_frame, text='Email', bg='white').pack(anchor='w', padx=30)
    e_email = tk.Entry(form_frame, width=35)
    e_email.pack(padx=30, pady=5)

    tk.Label(form_frame, text='Password', bg='white').pack(anchor='w', padx=30)
    e_pass = tk.Entry(form_frame, width=35, show='*')
    e_pass.pack(padx=30, pady=5)

    def do_login():
        name, role, student_id = authenticate(e_email.get().strip(), e_pass.get())
        if name:
            root.destroy()
            on_success(role, name, student_id)
        else:
            messagebox.showerror('Error', 'Invalid login')

    def do_register():
        try:
            sid = e_sid.get().strip()
            sid_val = int(sid) if sid else None
            register_user(e_name.get().strip().title(), e_role.get().strip().lower(), e_email.get().strip(), e_pass.get(), sid_val)
            messagebox.showinfo('Success', 'Registered')
        except Exception:
            messagebox.showerror('Error', 'Registration failed')

    btn_frame = tk.Frame(form_frame, bg='white')
    btn_frame.pack(pady=25)

    tk.Button(btn_frame, text='Login', command=do_login, bg='#A7C7E7', font=('Arial', 12), relief='flat', width=12).grid(row=0, column=0, padx=8)
    tk.Button(btn_frame, text='Register', command=do_register, bg='#B5EAD7', font=('Arial', 12), relief='flat', width=12).grid(row=0, column=1, padx=8)

    return root
