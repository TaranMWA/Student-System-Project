import tkinter as tk
from tkinter import messagebox
import math
import random
import sqlite3
import hashlib
import os

# ============================================================
#  CAPITAL CITY COLLEGE — myday Portal  (v7 — Full Database)
#  Use Cases: Register, Login, View/Edit Profile, Enrol,
#  View Attendance, View Timetable, Calculate GPA,
#  Manage Users/Courses/Timetable, Store Data, Notifications
# ============================================================

# ── PALETTE ─────────────────────────────────────────────────
BG       = "#0D0D0D"
SURFACE  = "#161616"
CARD     = "#1A1A1A"
BORDER   = "#2A2A2A"
ORANGE   = "#FF6B00"
ORANGE_D = "#CC5500"
PINK     = "#FF3CAC"
CYAN     = "#00D4FF"
LIME     = "#A8FF3E"
LIME_FG  = "#0A1A00"
WHITE    = "#FFFFFF"
DIM      = "#AAAAAA"
GHOST    = "#444444"
RED      = "#FF4444"
GREEN    = "#44FF88"

# ══════════════════════════════════════════════════════════════
#  DATABASE LAYER — SQLite
# ══════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ccc_portal.db")

def db_connect():
    return sqlite3.connect(DB_PATH)

def db_init():
    """Create all tables and seed demo data on first run."""
    con = db_connect()
    cur = con.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        role        TEXT NOT NULL CHECK(role IN ('student','teacher','admin')),
        full_name   TEXT,
        email       TEXT,
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS courses (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT UNIQUE NOT NULL,
        name        TEXT NOT NULL,
        teacher_id  INTEGER REFERENCES users(id),
        capacity    INTEGER DEFAULT 30
    );

    CREATE TABLE IF NOT EXISTS enrolments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER REFERENCES users(id),
        course_id   INTEGER REFERENCES courses(id),
        grade       TEXT DEFAULT NULL,
        enrolled_at TEXT DEFAULT (datetime('now')),
        UNIQUE(student_id, course_id)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER REFERENCES users(id),
        course_id   INTEGER REFERENCES courses(id),
        date        TEXT NOT NULL,
        status      TEXT DEFAULT 'present' CHECK(status IN ('present','absent','late'))
    );

    CREATE TABLE IF NOT EXISTS timetable (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id   INTEGER REFERENCES courses(id),
        day         TEXT NOT NULL,
        time_slot   TEXT NOT NULL,
        room        TEXT
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER REFERENCES users(id),
        message     TEXT NOT NULL,
        is_read     INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT (datetime('now'))
    );
    """)

    # Seed demo users if empty
    def hpw(pw): return hashlib.sha256(pw.encode()).hexdigest()

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO users(username,password,role,full_name,email) VALUES(?,?,?,?,?)",
            [
                ("admin",   hpw("admin123"),   "admin",   "Admin User",    "admin@ccc.ac.uk"),
                ("teacher1",hpw("teach123"),   "teacher", "Jane Smith",    "j.smith@ccc.ac.uk"),
                ("teacher2",hpw("teach123"),   "teacher", "Mark Davis",    "m.davis@ccc.ac.uk"),
                ("student1",hpw("stud123"),    "student", "Alice Johnson", "a.johnson@ccc.ac.uk"),
                ("student2",hpw("stud123"),    "student", "Bob Williams",  "b.williams@ccc.ac.uk"),
                ("student3",hpw("stud123"),    "student", "Carlos Rivera", "c.rivera@ccc.ac.uk"),
            ]
        )
        cur.executemany(
            "INSERT INTO courses(code,name,teacher_id,capacity) VALUES(?,?,?,?)",
            [
                ("BUS101","Introduction to Business", 2, 35),
                ("DIG202","Digital Marketing",        2, 28),
                ("DAT303","Data Analytics",           3, 24),
                ("MGT404","Management Principles",   3, 30),
            ]
        )
        # Enrol students
        cur.executemany(
            "INSERT INTO enrolments(student_id,course_id,grade) VALUES(?,?,?)",
            [(4,1,"B+"),(4,2,"A-"),(4,3,"B"),(5,1,"C+"),(5,3,"B+"),(6,2,"A"),(6,4,"B")]
        )
        # Attendance records
        import datetime
        days = ["2025-05-05","2025-05-06","2025-05-07","2025-05-08","2025-05-09"]
        statuses = ["present","present","present","absent","present"]
        for sid in [4,5,6]:
            for j,(d,s) in enumerate(zip(days,statuses)):
                cur.execute("INSERT INTO attendance(student_id,course_id,date,status) VALUES(?,?,?,?)",
                            (sid, 1, d, s))
        # Timetable
        cur.executemany(
            "INSERT INTO timetable(course_id,day,time_slot,room) VALUES(?,?,?,?)",
            [
                (1,"Monday","09:00","Room A1"),(1,"Wednesday","09:00","Room A1"),
                (2,"Tuesday","11:00","Room B2"),(2,"Thursday","11:00","Room B2"),
                (3,"Friday","09:00","Lab C3"),
                (4,"Monday","14:00","Room D4"),(4,"Wednesday","14:00","Room D4"),
            ]
        )
        # Welcome notifications
        for uid in range(1,7):
            cur.execute("INSERT INTO notifications(user_id,message) VALUES(?,?)",
                        (uid, "Welcome to the Capital City College myday Portal!"))
        cur.execute("INSERT INTO notifications(user_id,message) VALUES(?,?)",
                    (4, "You have been enrolled in Introduction to Business."))

    # ── Real admin accounts — inserted/updated regardless of seed state ──
    # Username = full name joined, Password = full name joined + "123"
    real_admins = [
        ("JuliaCeciliaPerezCoronado",       "Julia Cecilia Perez Coronado",      "1025822@student.capitalccg.ac.uk"),
        ("BilalAdiatu",                      "Bilal Adiatu",                      "1024243@student.capitalccg.ac.uk"),
        ("TaranAnderson",                    "Taran Anderson",                    "1025818@student.capitalccg.ac.uk"),
        ("MadisonConnelly",                  "Madison Connelly",                  "935890@student.capitalccg.ac.uk"),
        ("VenujahSirapinJacobMorais",        "Venujah Sirapin Jacob Morais",      "993121@student.capitalccg.ac.uk"),
    ]
    for uname, fname, email in real_admins:
        pw_hash = hpw(uname + "123")
        cur.execute("""
            INSERT INTO users(username, password, role, full_name, email)
            VALUES (?, ?, 'admin', ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password = excluded.password,
                role     = 'admin',
                full_name= excluded.full_name,
                email    = excluded.email
        """, (uname, pw_hash, fname, email))
        # Ensure welcome notification exists for this user
        cur.execute("SELECT id FROM users WHERE username=?", (uname,))
        row = cur.fetchone()
        if row:
            uid = row[0]
            cur.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id=?", (uid,))
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO notifications(user_id,message) VALUES(?,?)",
                    (uid, f"Welcome, {fname}! Your admin account is ready."))


    con.commit()
    con.close()

# ── DB HELPERS ──────────────────────────────────────────────

def db_login(username, password):
    hpw = hashlib.sha256(password.encode()).hexdigest()
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT id,full_name,role FROM users WHERE username=? AND password=?",
                (username, hpw))
    row = cur.fetchone()
    con.close()
    return row  # (id, full_name, role) or None

def db_register(username, password, role, full_name, email):
    try:
        hpw = hashlib.sha256(password.encode()).hexdigest()
        con = db_connect()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users(username,password,role,full_name,email) VALUES(?,?,?,?,?)",
            (username, hpw, role, full_name, email)
        )
        uid = cur.lastrowid
        cur.execute("INSERT INTO notifications(user_id,message) VALUES(?,?)",
                    (uid, f"Welcome, {full_name}! Your account has been created."))
        con.commit()
        con.close()
        return True, "Account created successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."

def db_get_profile(user_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT full_name,email,role,username,created_at FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    con.close()
    return row

def db_update_profile(user_id, full_name, email):
    con = db_connect()
    cur = con.cursor()
    cur.execute("UPDATE users SET full_name=?,email=? WHERE id=?", (full_name, email, user_id))
    con.commit()
    con.close()

def db_get_courses(student_id=None):
    con = db_connect()
    cur = con.cursor()
    if student_id:
        cur.execute("""
            SELECT c.id,c.code,c.name,u.full_name,c.capacity,e.grade
            FROM courses c
            JOIN enrolments e ON e.course_id=c.id
            LEFT JOIN users u ON u.id=c.teacher_id
            WHERE e.student_id=?
        """, (student_id,))
    else:
        cur.execute("""
            SELECT c.id,c.code,c.name,u.full_name,c.capacity,
                   (SELECT COUNT(*) FROM enrolments WHERE course_id=c.id)
            FROM courses c LEFT JOIN users u ON u.id=c.teacher_id
        """)
    rows = cur.fetchall()
    con.close()
    return rows

def db_enrol(student_id, course_id):
    try:
        con = db_connect()
        cur = con.cursor()
        cur.execute("INSERT INTO enrolments(student_id,course_id) VALUES(?,?)",
                    (student_id, course_id))
        cur.execute("INSERT INTO notifications(user_id,message) VALUES(?,?)",
                    (student_id, "You have been enrolled in a new course."))
        con.commit()
        con.close()
        return True, "Enrolled successfully!"
    except sqlite3.IntegrityError:
        return False, "Already enrolled in this course."

def db_get_attendance(student_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("""
        SELECT c.name, a.date, a.status
        FROM attendance a JOIN courses c ON c.id=a.course_id
        WHERE a.student_id=? ORDER BY a.date DESC
    """, (student_id,))
    rows = cur.fetchall()
    con.close()
    return rows

def db_get_timetable(user_id=None, role=None):
    con = db_connect()
    cur = con.cursor()
    if role == "student" and user_id:
        cur.execute("""
            SELECT c.name, t.day, t.time_slot, t.room
            FROM timetable t JOIN courses c ON c.id=t.course_id
            JOIN enrolments e ON e.course_id=c.id
            WHERE e.student_id=? ORDER BY t.day, t.time_slot
        """, (user_id,))
    elif role == "teacher" and user_id:
        cur.execute("""
            SELECT c.name, t.day, t.time_slot, t.room
            FROM timetable t JOIN courses c ON c.id=t.course_id
            WHERE c.teacher_id=? ORDER BY t.day, t.time_slot
        """, (user_id,))
    else:
        cur.execute("""
            SELECT c.name, t.day, t.time_slot, t.room
            FROM timetable t JOIN courses c ON c.id=t.course_id
            ORDER BY t.day, t.time_slot
        """)
    rows = cur.fetchall()
    con.close()
    return rows

def db_calc_gpa(student_id):
    grade_map = {"A+":4.0,"A":4.0,"A-":3.7,"B+":3.3,"B":3.0,"B-":2.7,
                 "C+":2.3,"C":2.0,"C-":1.7,"D":1.0,"F":0.0}
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT grade FROM enrolments WHERE student_id=? AND grade IS NOT NULL", (student_id,))
    grades = [r[0] for r in cur.fetchall()]
    con.close()
    if not grades: return 0.0, []
    points = [grade_map.get(g, 0.0) for g in grades]
    return round(sum(points)/len(points), 2), list(zip(grades, points))

def db_get_notifications(user_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("""
        SELECT id, message, is_read, created_at
        FROM notifications WHERE user_id=? ORDER BY created_at DESC
    """, (user_id,))
    rows = cur.fetchall()
    con.close()
    return rows

def db_mark_read(notif_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("UPDATE notifications SET is_read=1 WHERE id=?", (notif_id,))
    con.commit()
    con.close()

def db_get_all_users():
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT id,username,full_name,role,email FROM users ORDER BY role,full_name")
    rows = cur.fetchall()
    con.close()
    return rows

def db_delete_user(user_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    con.commit()
    con.close()

def db_add_course(code, name, teacher_id, capacity):
    try:
        con = db_connect()
        cur = con.cursor()
        cur.execute("INSERT INTO courses(code,name,teacher_id,capacity) VALUES(?,?,?,?)",
                    (code, name, teacher_id, capacity))
        con.commit()
        con.close()
        return True, "Course added."
    except sqlite3.IntegrityError:
        return False, "Course code already exists."

def db_add_timetable(course_id, day, time_slot, room):
    con = db_connect()
    cur = con.cursor()
    cur.execute("INSERT INTO timetable(course_id,day,time_slot,room) VALUES(?,?,?,?)",
                (course_id, day, time_slot, room))
    con.commit()
    con.close()

def db_delete_course(course_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("DELETE FROM enrolments WHERE course_id=?", (course_id,))
    cur.execute("DELETE FROM timetable  WHERE course_id=?", (course_id,))
    cur.execute("DELETE FROM courses    WHERE id=?",        (course_id,))
    con.commit(); con.close()

def db_delete_timetable_entry(entry_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("DELETE FROM timetable WHERE id=?", (entry_id,))
    con.commit(); con.close()

def db_update_grade(student_id, course_id, grade):
    con = db_connect()
    cur = con.cursor()
    cur.execute("UPDATE enrolments SET grade=? WHERE student_id=? AND course_id=?",
                (grade, student_id, course_id))
    con.commit(); con.close()

def db_unenrol(student_id, course_id):
    con = db_connect()
    cur = con.cursor()
    cur.execute("DELETE FROM enrolments WHERE student_id=? AND course_id=?",
                (student_id, course_id))
    con.commit(); con.close()

def db_change_password(user_id, old_pw, new_pw):
    old_hash = hashlib.sha256(old_pw.encode()).hexdigest()
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT id FROM users WHERE id=? AND password=?", (user_id, old_hash))
    if not cur.fetchone():
        con.close()
        return False, "Current password is incorrect."
    new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
    cur.execute("UPDATE users SET password=? WHERE id=?", (new_hash, user_id))
    con.commit(); con.close()
    return True, "Password changed successfully."

def db_broadcast_notification(message, role_filter=None):
    """Send a notification to all users, or all users of a given role."""
    con = db_connect()
    cur = con.cursor()
    if role_filter:
        cur.execute("SELECT id FROM users WHERE role=?", (role_filter,))
    else:
        cur.execute("SELECT id FROM users")
    ids = [r[0] for r in cur.fetchall()]
    for uid in ids:
        cur.execute("INSERT INTO notifications(user_id,message) VALUES(?,?)",
                    (uid, message))
    con.commit(); con.close()
    return len(ids)

def db_get_timetable_with_ids():
    """Return timetable rows including the entry ID for deletion."""
    con = db_connect()
    cur = con.cursor()
    cur.execute("""
        SELECT t.id, c.name, t.day, t.time_slot, t.room
        FROM timetable t JOIN courses c ON c.id=t.course_id
        ORDER BY t.day, t.time_slot
    """)
    rows = cur.fetchall()
    con.close()
    return rows

def db_get_stats():
    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    students = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='teacher'")
    teachers = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM courses")
    courses = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attendance WHERE status='present'")
    present = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM attendance")
    total_att = cur.fetchone()[0]
    att_pct = round(present/total_att*100) if total_att else 0
    con.close()
    return students, teachers, courses, att_pct

# ── SESSION ─────────────────────────────────────────────────
session = {"id": None, "name": None, "role": None}

# ══════════════════════════════════════════════════════════════
#  COLOUR UTILITIES
# ══════════════════════════════════════════════════════════════

def h2r(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def r2h(c):
    return "#{:02x}{:02x}{:02x}".format(c[0], c[1], c[2])

# ══════════════════════════════════════════════════════════════
#  DRAWING PRIMITIVES
# ══════════════════════════════════════════════════════════════

def rr(cv, x1, y1, x2, y2, rd=12, **kw):
    p = [x1+rd,y1, x2-rd,y1, x2,y1, x2,y1+rd,
         x2,y2-rd, x2,y2, x2-rd,y2, x1+rd,y2,
         x1,y2, x1,y2-rd, x1,y1+rd, x1,y1, x1+rd,y1]
    return cv.create_polygon(p, smooth=True, **kw)

def soft_glow(cv, cx, cy, radius, col, layers=7, strength=0.28):
    bg = h2r(CARD); gc = h2r(col)
    for i in range(layers, 0, -1):
        t = (i/layers)*strength; rad = radius+(layers-i)*8
        cv.create_oval(cx-rad,cy-rad,cx+rad,cy+rad,
                       fill=r2h(lerp(bg,gc,t)), outline="")

def bg_glow(cv, cx, cy, radius, col, layers=8, strength=0.14):
    bg = h2r(BG); gc = h2r(col)
    for i in range(layers, 0, -1):
        t = (i/layers)*strength; rad = radius+(layers-i)*20
        cv.create_oval(cx-rad,cy-rad,cx+rad,cy+rad,
                       fill=r2h(lerp(bg,gc,t)), outline="")

def fade_line(cv, x1, y, x2, col, steps=80):
    c = h2r(col); dark = h2r(BG)
    for i in range(steps):
        t = i/steps; lx = x1+int((x2-x1)*t)
        ft = math.sin(t*math.pi)
        cv.create_line(lx,y,lx+1,y, fill=r2h(lerp(dark,c,ft*0.65)))

def scatter(cv, x1, y1, x2, y2, col, count=600):
    random.seed(99); c = h2r(col)
    for _ in range(count):
        px = random.randint(x1, x2-1); py = random.randint(y1, y2-1)
        t  = random.uniform(0.04, 0.11)
        cv.create_rectangle(px,py,px+1,py+1,
                            fill=r2h(lerp(h2r(BG),c,t)), outline="")

def geo_rings(cv, cx, cy, col, n=3, base_r=28, gap=20):
    bg = h2r(BG); gc = h2r(col)
    for i in range(n):
        rad = base_r+i*gap; t = max(0.22-i*0.06, 0.04)
        cv.create_oval(cx-rad,cy-rad,cx+rad,cy+rad,
                       outline=r2h(lerp(bg,gc,t)), width=1)

def pill_btn(cv, x, y, w, h, label, col, fg=WHITE, cmd=None):
    ar = h2r(col); shine = r2h(lerp(ar,(255,255,255),0.20))
    rr(cv,x+2,y+4,x+w+2,y+h+4,rd=h//2,fill="#0A0A0A",outline="")
    body = rr(cv,x,y,x+w,y+h,rd=h//2,fill=col,outline="")
    rr(cv,x+2,y+1,x+w-2,y+h//2,rd=h//2,fill=shine,outline="")
    txt = cv.create_text(x+w//2,y+h//2,text=label,
                         font=("Helvetica",10,"bold"),fill=fg)
    hit = cv.create_rectangle(x,y,x+w,y+h,fill="",outline="")
    if cmd:
        for tag in (body,txt,hit):
            cv.tag_bind(tag,"<Button-1>",lambda e,c=cmd:c())
            cv.tag_bind(tag,"<Enter>",lambda e:cv.config(cursor="hand2"))
            cv.tag_bind(tag,"<Leave>",lambda e:cv.config(cursor=""))

def stat_block(cv, x, y, w, h, number, label, col, sub=None):
    rr(cv,x,y,x+w,y+h,rd=14,fill=CARD,outline=BORDER,width=1)
    cv.create_line(x+12,y+2,x+2,y+2,x+2,y+14,fill=col,width=2)
    cv.create_line(x+w-12,y+2,x+w-2,y+2,x+w-2,y+14,fill=col,width=2)
    cv.create_text(x+w//2,y+h//2-12,text=str(number),
                   font=("Helvetica",30,"bold"),fill=col,anchor="center")
    cv.create_text(x+w//2,y+h//2+16,text=label,
                   font=("Helvetica",9),fill=DIM,anchor="center")
    if sub:
        cv.create_text(x+w//2,y+h-12,text=sub,
                       font=("Helvetica",8),fill=GHOST,anchor="center")

def timetable_grid(cv, x, y, w, h, col, rows):
    rr(cv,x,y,x+w,y+h,rd=12,fill=CARD,outline=BORDER,width=1)
    cols = ["TIME","MON","TUE","WED","THU","FRI"]
    cw   = (w-20)//6
    cv.create_rectangle(x+1,y+1,x+w-1,y+28,
                        fill=r2h(lerp(h2r(CARD),h2r(col),0.14)),outline="")
    for j,c in enumerate(cols):
        cv.create_text(x+10+j*cw+cw//2,y+15,text=c,
                       font=("Helvetica",8,"bold"),fill=col)
    for i,row in enumerate(rows):
        ry    = y+28+i*26
        rowbg = CARD if i%2==0 else r2h(lerp(h2r(CARD),(20,20,20),0.5))
        cv.create_rectangle(x+1,ry,x+w-1,ry+26,fill=rowbg,outline="")
        for j,cell in enumerate(row):
            fc = WHITE if j==0 else (col if cell else GHOST)
            cv.create_text(x+10+j*cw+cw//2,ry+13,
                           text=cell if cell else "·",
                           font=("Helvetica",9,"bold" if (cell and j>0) else ""),
                           fill=fc)

def sec_hdr(cv, x, y, text, col):
    cv.create_rectangle(x,y,x+3,y+18,fill=col,outline="")
    cv.create_text(x+10,y+9,text=text.upper(),
                   font=("Helvetica",9,"bold"),fill=col,anchor="w")

# ══════════════════════════════════════════════════════════════
#  MODAL DIALOGS  (styled Toplevel windows)
# ══════════════════════════════════════════════════════════════

def styled_popup(title, col, width=500, height=420):
    """Return a styled dark Toplevel ready to receive widgets."""
    pop = tk.Toplevel(root)
    pop.title(title)
    pop.geometry(f"{width}x{height}")
    pop.configure(bg=BG)
    pop.resizable(False, False)
    pop.grab_set()

    # Top accent bar
    bar = tk.Frame(pop, bg=col, height=4)
    bar.pack(fill="x")

    # Title row
    hdr = tk.Frame(pop, bg=SURFACE)
    hdr.pack(fill="x")
    tk.Label(hdr, text=title, font=("Georgia",14,"bold"),
             fg=WHITE, bg=SURFACE, pady=10).pack(side="left", padx=16)

    return pop

def lbl(parent, text, fg=DIM, size=10, bold=False, bg=BG):
    style = "bold" if bold else ""
    return tk.Label(parent, text=text, font=("Helvetica",size,style),
                    fg=fg, bg=bg)

def entry_field(parent, placeholder="", show=""):
    f = tk.Frame(parent, bg=CARD, highlightbackground=BORDER,
                 highlightthickness=1)
    f.pack(fill="x", padx=20, pady=4)
    e = tk.Entry(f, font=("Helvetica",11), bg=CARD, fg=WHITE,
                 insertbackground=WHITE, relief="flat",
                 show=show, bd=6)
    e.insert(0, placeholder)
    e.pack(fill="x")
    return e

def action_btn(parent, text, col, cmd, fg=WHITE, width=20):
    tk.Button(parent, text=text, bg=col, fg=fg,
              font=("Helvetica",11,"bold"), relief="flat",
              padx=14, pady=8, cursor="hand2", bd=0,
              activebackground=r2h(lerp(h2r(col),(0,0,0),0.2)),
              activeforeground=fg, width=width,
              command=cmd).pack(pady=6)

# ── LOGIN / REGISTER ────────────────────────────────────────

def show_login():
    """Login screen — shown before role selector."""
    _clear()
    frame = tk.Frame(container, bg=BG)
    frame.pack(expand=True, fill="both")
    _current[0] = frame

    cv = tk.Canvas(frame, width=1200, height=700, bg=BG, highlightthickness=0)
    cv.pack()

    scatter(cv, 0, 0, 1200, 700, ORANGE, count=500)
    bg_glow(cv, 300, 350, 200, PINK,   layers=8, strength=0.08)
    bg_glow(cv, 900, 350, 200, CYAN,   layers=8, strength=0.08)
    geo_rings(cv, 80, 80, ORANGE, n=3, base_r=30, gap=22)
    geo_rings(cv, 1120, 620, LIME, n=3, base_r=30, gap=22)

    cv.create_text(600, 100, text="CAPITAL CITY COLLEGE",
                   font=("Helvetica",11,"bold"), fill=GHOST, anchor="center")
    cv.create_text(600, 168, text="myday",
                   font=("Helvetica",64,"bold"), fill=ORANGE, anchor="center")
    cv.create_text(600, 232, text="Your College. Your Portal.",
                   font=("Georgia",16), fill=DIM, anchor="center")
    fade_line(cv, 380, 254, 820, ORANGE, steps=140)

    # Login card
    card_frame = tk.Frame(frame, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)
    card_frame.place(x=400, y=270, width=400, height=340)

    tk.Frame(card_frame, bg=ORANGE, height=3).pack(fill="x")
    tk.Label(card_frame, text="Sign In", font=("Georgia",16,"bold"),
             fg=WHITE, bg=CARD, pady=14).pack()

    tk.Label(card_frame, text="Username", font=("Helvetica",9),
             fg=DIM, bg=CARD).pack(anchor="w", padx=20)
    username_var = tk.StringVar()
    ue = tk.Entry(card_frame, textvariable=username_var,
                  font=("Helvetica",11), bg=SURFACE, fg=WHITE,
                  insertbackground=WHITE, relief="flat", bd=6)
    ue.pack(fill="x", padx=20, pady=(0,8))

    tk.Label(card_frame, text="Password", font=("Helvetica",9),
             fg=DIM, bg=CARD).pack(anchor="w", padx=20)
    password_var = tk.StringVar()
    pe = tk.Entry(card_frame, textvariable=password_var, show="●",
                  font=("Helvetica",11), bg=SURFACE, fg=WHITE,
                  insertbackground=WHITE, relief="flat", bd=6)
    pe.pack(fill="x", padx=20, pady=(0,12))

    msg_var = tk.StringVar()
    tk.Label(card_frame, textvariable=msg_var, font=("Helvetica",9),
             fg=RED, bg=CARD).pack()

    def do_login():
        user = db_login(username_var.get().strip(), password_var.get())
        if user:
            session["id"]   = user[0]
            session["name"] = user[1]
            session["role"] = user[2]
            if   user[2] == "teacher": show_teacher()
            elif user[2] == "student": show_student()
            elif user[2] == "admin":   show_admin()
        else:
            msg_var.set("Invalid username or password.")

    tk.Button(card_frame, text="Sign In →", bg=ORANGE, fg=WHITE,
              font=("Helvetica",12,"bold"), relief="flat",
              padx=0, pady=10, cursor="hand2", bd=0,
              activebackground=ORANGE_D,
              command=do_login).pack(fill="x", padx=20, pady=(0,6))

    tk.Button(card_frame, text="Create an account",
              bg=CARD, fg=DIM,
              font=("Helvetica",9), relief="flat",
              cursor="hand2", bd=0,
              command=show_register).pack()

    ue.focus()
    frame.bind("<Return>", lambda e: do_login())
    ue.bind("<Return>",    lambda e: do_login())
    pe.bind("<Return>",    lambda e: do_login())

    # Demo hint
    hint = tk.Label(frame,
                    text="Demo: admin/admin123 · teacher1/teach123 · student1/stud123",
                    font=("Helvetica",9), fg=GHOST, bg=BG)
    hint.place(x=0, y=676, width=1200)


def show_register():
    """Register User — Admin only. Students/Teachers are denied access."""
    if session.get("role") not in ("admin", None):
        messagebox.showerror(
            "Access Denied",
            "Only administrators can register new users."
        )
        return
    pop = styled_popup("Register New User", ORANGE, 480, 500)

    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    fields = {}
    for label, key, show in [
        ("Full Name",  "full_name",  ""),
        ("Username",   "username",   ""),
        ("Email",      "email",      ""),
        ("Password",   "password",   "●"),
    ]:
        tk.Label(body, text=label, font=("Helvetica",9),
                 fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
        v = tk.StringVar()
        e = tk.Entry(body, textvariable=v, show=show,
                     font=("Helvetica",11), bg=SURFACE, fg=WHITE,
                     insertbackground=WHITE, relief="flat", bd=6)
        e.pack(fill="x", pady=(0,2))
        fields[key] = v

    tk.Label(body, text="Role", font=("Helvetica",9),
             fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
    role_var = tk.StringVar(value="student")
    role_frame = tk.Frame(body, bg=BG)
    role_frame.pack(fill="x")
    for r, label in [("student","Student"),("teacher","Teacher"),("admin","Admin")]:
        tk.Radiobutton(role_frame, text=label, variable=role_var, value=r,
                       bg=BG, fg=WHITE, selectcolor=SURFACE,
                       activebackground=BG, activeforeground=ORANGE,
                       font=("Helvetica",10)).pack(side="left", padx=8)

    msg_var = tk.StringVar()
    tk.Label(body, textvariable=msg_var, font=("Helvetica",9),
             fg=RED, bg=BG).pack(pady=4)

    def do_register():
        fn = fields["full_name"].get().strip()
        un = fields["username"].get().strip()
        em = fields["email"].get().strip()
        pw = fields["password"].get()
        ro = role_var.get()
        if not all([fn, un, pw]):
            msg_var.set("Full name, username and password are required.")
            return
        ok, msg = db_register(un, pw, ro, fn, em)
        if ok:
            msg_var.set("")
            messagebox.showinfo("Success", msg, parent=pop)
            pop.destroy()
        else:
            msg_var.set(msg)

    tk.Button(body, text="Create Account", bg=ORANGE, fg=WHITE,
              font=("Helvetica",11,"bold"), relief="flat",
              padx=0, pady=10, cursor="hand2", bd=0,
              activebackground=ORANGE_D,
              command=do_register).pack(fill="x", pady=(8,0))


# ── PROFILE POPUP ───────────────────────────────────────────

def show_profile_popup(col):
    """View Student Profile + edit name/email + change password."""
    pop = styled_popup("My Profile", col, 460, 520)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    profile = db_get_profile(session["id"])
    if not profile:
        tk.Label(body, text="Profile not found.", fg=RED, bg=BG).pack()
        return

    full_name, email, role, username, created = profile

    tk.Label(body, text=f"👤  {full_name}", font=("Georgia",15,"bold"),
             fg=WHITE, bg=BG).pack(pady=(0,4))
    tk.Label(body, text=f"Role: {role.title()}  ·  @{username}",
             font=("Helvetica",10), fg=DIM, bg=BG).pack()
    tk.Label(body, text=f"Joined: {created[:10]}",
             font=("Helvetica",9), fg=GHOST, bg=BG).pack(pady=(0,10))
    fade_line(body.master, 20, 0, 440, col, steps=60)

    # ── Edit name / email ────────────────────────────────────
    tk.Label(body, text="Full Name", font=("Helvetica",9),
             fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
    name_var = tk.StringVar(value=full_name)
    tk.Entry(body, textvariable=name_var, font=("Helvetica",11),
             bg=SURFACE, fg=WHITE, insertbackground=WHITE,
             relief="flat", bd=6).pack(fill="x")

    tk.Label(body, text="Email", font=("Helvetica",9),
             fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
    email_var = tk.StringVar(value=email or "")
    tk.Entry(body, textvariable=email_var, font=("Helvetica",11),
             bg=SURFACE, fg=WHITE, insertbackground=WHITE,
             relief="flat", bd=6).pack(fill="x")

    msg_var = tk.StringVar()
    tk.Label(body, textvariable=msg_var, font=("Helvetica",9),
             fg=GREEN, bg=BG).pack(pady=4)

    def save():
        db_update_profile(session["id"], name_var.get(), email_var.get())
        session["name"] = name_var.get()
        msg_var.set("✓ Profile updated.")

    tk.Button(body, text="Save Changes", bg=col,
              fg=WHITE if col != LIME else LIME_FG,
              font=("Helvetica",11,"bold"), relief="flat",
              padx=0, pady=8, cursor="hand2", bd=0,
              command=save).pack(fill="x", pady=(0,4))

    # ── Change password ──────────────────────────────────────
    tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(6,4))
    tk.Label(body, text="Change Password", font=("Helvetica",9,"bold"),
             fg=col, bg=BG).pack(anchor="w")

    pw_old  = tk.StringVar()
    pw_new  = tk.StringVar()
    pw_new2 = tk.StringVar()
    pw_msg  = tk.StringVar()

    for lbl_txt, var in [("Current Password", pw_old),
                          ("New Password",     pw_new),
                          ("Confirm New",      pw_new2)]:
        tk.Label(body, text=lbl_txt, font=("Helvetica",9),
                 fg=DIM, bg=BG).pack(anchor="w", pady=(4,0))
        tk.Entry(body, textvariable=var, show="●",
                 font=("Helvetica",10), bg=SURFACE, fg=WHITE,
                 insertbackground=WHITE, relief="flat", bd=5).pack(fill="x")

    tk.Label(body, textvariable=pw_msg, font=("Helvetica",9),
             fg=GREEN, bg=BG).pack(pady=2)

    def change_pw():
        if pw_new.get() != pw_new2.get():
            pw_msg.set("✗ New passwords do not match.")
            return
        if len(pw_new.get()) < 4:
            pw_msg.set("✗ Password must be at least 4 characters.")
            return
        ok, msg = db_change_password(session["id"], pw_old.get(), pw_new.get())
        pw_msg.set(("✓ " if ok else "✗ ") + msg)
        if ok:
            for v in [pw_old, pw_new, pw_new2]: v.set("")

    tk.Button(body, text="Change Password", bg=GHOST,
              fg=WHITE,
              font=("Helvetica",10,"bold"), relief="flat",
              padx=0, pady=6, cursor="hand2", bd=0,
              command=change_pw).pack(fill="x", pady=(0,4))


# ── ENROL IN COURSE ─────────────────────────────────────────

def show_enrol_popup():
    pop = styled_popup("My Courses", CYAN, 560, 500)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    # Tab bar
    tab_frame = tk.Frame(body, bg=SURFACE)
    tab_frame.pack(fill="x", pady=(0,8))
    content_frame = tk.Frame(body, bg=BG)
    content_frame.pack(fill="both", expand=True)

    def show_tab(tab_name):
        for w in content_frame.winfo_children(): w.destroy()
        for b in tab_btns:
            b.config(bg=SURFACE, fg=DIM)
        tab_btns[["enrol","unenrol"].index(tab_name)].config(bg=CYAN, fg=BG)

        if tab_name == "enrol":
            enrolled_ids = {r[0] for r in db_get_courses(session["id"])}
            all_courses = db_get_courses()
            tk.Label(content_frame, text="Select a course to join:",
                     font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(0,6))
            lf = tk.Frame(content_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            lf.pack(fill="both", expand=True)
            lb = tk.Listbox(lf, bg=CARD, fg=WHITE, selectbackground=CYAN,
                            selectforeground=BG, font=("Helvetica",11),
                            relief="flat", highlightthickness=0, bd=8)
            lb.pack(fill="both", expand=True)
            cids = []
            for row in all_courses:
                cid, code, name, teacher, cap, enrolled_count = row
                if cid not in enrolled_ids:
                    lb.insert("end", f"  {code}  —  {name}  (Teacher: {teacher or 'TBC'})  [{enrolled_count}/{cap}]")
                    cids.append(cid)
            if not cids:
                lb.insert("end", "  You are enrolled in all available courses.")
            msg_v = tk.StringVar()
            tk.Label(content_frame, textvariable=msg_v, fg=GREEN, bg=BG,
                     font=("Helvetica",9)).pack(pady=4)
            def do_enrol():
                sel = lb.curselection()
                if not sel: msg_v.set("Please select a course."); return
                ok, msg = db_enrol(session["id"], cids[sel[0]])
                msg_v.set(("✓ " if ok else "✗ ") + msg)
                if ok: lb.delete(sel[0]); cids.pop(sel[0])
            tk.Button(content_frame, text="✓  Enrol in Selected Course",
                      bg=CYAN, fg=BG, font=("Helvetica",11,"bold"),
                      relief="flat", padx=0, pady=8, cursor="hand2", bd=0,
                      command=do_enrol).pack(fill="x", pady=(4,0))

        else:  # unenrol
            my_courses = db_get_courses(session["id"])
            tk.Label(content_frame, text="Select a course to leave:",
                     font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(0,6))
            lf2 = tk.Frame(content_frame, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            lf2.pack(fill="both", expand=True)
            lb2 = tk.Listbox(lf2, bg=CARD, fg=WHITE, selectbackground=RED,
                             selectforeground=WHITE, font=("Helvetica",11),
                             relief="flat", highlightthickness=0, bd=8)
            lb2.pack(fill="both", expand=True)
            mcids = []
            for row in my_courses:
                cid, code, name, teacher, cap, grade = row
                lb2.insert("end", f"  {code}  —  {name}  (Grade: {grade or '—'})")
                mcids.append(cid)
            if not mcids:
                lb2.insert("end", "  You are not enrolled in any courses.")
            msg_v2 = tk.StringVar()
            tk.Label(content_frame, textvariable=msg_v2, fg=RED, bg=BG,
                     font=("Helvetica",9)).pack(pady=4)
            def do_unenrol():
                sel = lb2.curselection()
                if not sel: msg_v2.set("Please select a course."); return
                if messagebox.askyesno("Confirm", "Leave this course? Your grade record will be removed.", parent=pop):
                    db_unenrol(session["id"], mcids[sel[0]])
                    lb2.delete(sel[0]); mcids.pop(sel[0])
                    msg_v2.set("✓ Unenrolled successfully.")
            tk.Button(content_frame, text="✕  Leave Selected Course",
                      bg=RED, fg=WHITE, font=("Helvetica",11,"bold"),
                      relief="flat", padx=0, pady=8, cursor="hand2", bd=0,
                      command=do_unenrol).pack(fill="x", pady=(4,0))

    tab_btns = []
    for label, key in [("Enrol in Course", "enrol"), ("My Enrolments / Leave", "unenrol")]:
        b = tk.Button(tab_frame, text=label, bg=SURFACE, fg=DIM,
                      font=("Helvetica",10,"bold"), relief="flat",
                      padx=14, pady=6, cursor="hand2", bd=0,
                      command=lambda k=key: show_tab(k))
        b.pack(side="left", padx=2)
        tab_btns.append(b)
    show_tab("enrol")


# ── ATTENDANCE POPUP ────────────────────────────────────────

def show_attendance_popup(col):
    pop = styled_popup("My Attendance", col, 580, 460)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    records = db_get_attendance(session["id"])

    if not records:
        tk.Label(body, text="No attendance records found.",
                 fg=DIM, bg=BG, font=("Helvetica",11)).pack(pady=20)
        return

    # Header
    hf = tk.Frame(body, bg=SURFACE)
    hf.pack(fill="x", pady=(0,4))
    for txt, wid in [("Course",280),("Date",100),("Status",80)]:
        tk.Label(hf, text=txt, font=("Helvetica",9,"bold"),
                 fg=col, bg=SURFACE, width=wid//8,
                 anchor="w").pack(side="left", padx=6, pady=4)

    canvas = tk.Canvas(body, bg=BG, highlightthickness=0, height=320)
    scrollbar = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=BG)

    scroll_frame.bind("<Configure>",
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Count for summary
    present = sum(1 for r in records if r[2]=="present")
    pct = round(present/len(records)*100) if records else 0

    for course, date, status in records:
        rf = tk.Frame(scroll_frame, bg=CARD,
                      highlightbackground=BORDER, highlightthickness=1)
        rf.pack(fill="x", pady=1)
        sc = GREEN if status=="present" else (ORANGE if status=="late" else RED)
        tk.Label(rf, text=course[:36], font=("Helvetica",9),
                 fg=WHITE, bg=CARD, width=32, anchor="w").pack(side="left", padx=6, pady=4)
        tk.Label(rf, text=date, font=("Helvetica",9),
                 fg=DIM, bg=CARD, width=12).pack(side="left")
        tk.Label(rf, text=status.title(), font=("Helvetica",9,"bold"),
                 fg=sc, bg=CARD, width=10).pack(side="left")

    tk.Label(pop, text=f"Overall attendance: {pct}%  ({present}/{len(records)} sessions)",
             font=("Helvetica",10,"bold"), fg=col, bg=BG).pack(pady=6)


# ── TIMETABLE POPUP ─────────────────────────────────────────

def show_timetable_popup(col):
    pop = styled_popup("My Timetable", col, 620, 420)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    rows = db_get_timetable(session["id"], session["role"])

    if not rows:
        tk.Label(body, text="No timetable entries found.",
                 fg=DIM, bg=BG, font=("Helvetica",11)).pack(pady=20)
        return

    hf = tk.Frame(body, bg=SURFACE)
    hf.pack(fill="x", pady=(0,4))
    for txt, wid in [("Course",220),("Day",100),("Time",80),("Room",80)]:
        tk.Label(hf, text=txt, font=("Helvetica",9,"bold"),
                 fg=col, bg=SURFACE, width=wid//8,
                 anchor="w").pack(side="left", padx=6, pady=4)

    for course, day, time_slot, room in rows:
        rf = tk.Frame(body, bg=CARD,
                      highlightbackground=BORDER, highlightthickness=1)
        rf.pack(fill="x", pady=1)
        tk.Label(rf, text=course[:28], font=("Helvetica",9),
                 fg=WHITE, bg=CARD, width=26, anchor="w").pack(side="left", padx=6, pady=4)
        tk.Label(rf, text=day,        font=("Helvetica",9), fg=DIM, bg=CARD, width=10).pack(side="left")
        tk.Label(rf, text=time_slot,  font=("Helvetica",9), fg=col, bg=CARD, width=8).pack(side="left")
        tk.Label(rf, text=room or "—",font=("Helvetica",9), fg=GHOST, bg=CARD, width=10).pack(side="left")


# ── GPA / GRADES POPUP ──────────────────────────────────────

def show_gpa_popup(col, student_id=None):
    sid = student_id or session["id"]
    pop = styled_popup("GPA & Academic Results", col, 480, 420)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    gpa, breakdown = db_calc_gpa(sid)
    courses = db_get_courses(sid)

    # GPA display
    gpa_col = GREEN if gpa >= 3.0 else (ORANGE if gpa >= 2.0 else RED)
    tk.Label(body, text=f"{gpa:.2f}", font=("Helvetica",48,"bold"),
             fg=gpa_col, bg=BG).pack()
    tk.Label(body, text="Grade Point Average",
             font=("Helvetica",10), fg=DIM, bg=BG).pack(pady=(0,12))

    fade_line(body.master, 20, 0, 440, col, steps=60)

    # Course breakdown
    tk.Label(body, text="Course Grades", font=("Helvetica",10,"bold"),
             fg=col, bg=BG).pack(anchor="w", pady=(8,4))

    for row in courses:
        cid, code, name, teacher, cap, grade = row
        rf = tk.Frame(body, bg=CARD,
                      highlightbackground=BORDER, highlightthickness=1)
        rf.pack(fill="x", pady=1)
        tk.Label(rf, text=f"  {code}  {name[:28]}",
                 font=("Helvetica",9), fg=WHITE, bg=CARD,
                 width=34, anchor="w").pack(side="left", padx=4, pady=4)
        gc = GREEN if grade and grade[0]=='A' else (ORANGE if grade and grade[0]=='B' else RED)
        tk.Label(rf, text=grade or "—",
                 font=("Helvetica",10,"bold"), fg=gc if grade else GHOST,
                 bg=CARD, width=6).pack(side="right", padx=10)


# ── NOTIFICATIONS POPUP ─────────────────────────────────────

def show_notifications_popup(col):
    pop = styled_popup("Notifications", col, 560, 440)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    notifs = db_get_notifications(session["id"])
    unread = sum(1 for n in notifs if not n[2])

    tk.Label(body, text=f"{unread} unread notification{'s' if unread!=1 else ''}",
             font=("Helvetica",10), fg=col, bg=BG).pack(anchor="w", pady=(0,8))

    canvas = tk.Canvas(body, bg=BG, highlightthickness=0, height=340)
    sb2    = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
    sf     = tk.Frame(canvas, bg=BG)
    sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=sf, anchor="nw")
    canvas.configure(yscrollcommand=sb2.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb2.pack(side="right", fill="y")

    for nid, msg, is_read, created in notifs:
        rf = tk.Frame(sf, bg=CARD if not is_read else SURFACE,
                      highlightbackground=col if not is_read else BORDER,
                      highlightthickness=1)
        rf.pack(fill="x", pady=2, padx=2)

        dot = "●  " if not is_read else "○  "
        tk.Label(rf, text=dot+msg, font=("Helvetica",9),
                 fg=WHITE if not is_read else GHOST,
                 bg=rf["bg"], wraplength=430, justify="left",
                 anchor="w").pack(side="left", padx=8, pady=6, fill="x", expand=True)
        tk.Label(rf, text=created[:10],
                 font=("Helvetica",8), fg=GHOST,
                 bg=rf["bg"]).pack(side="right", padx=8)

        if not is_read:
            rf.bind("<Button-1>", lambda e, i=nid, f=rf: (db_mark_read(i), f.config(bg=SURFACE)))

    def mark_all():
        for nid, *_ in notifs:
            db_mark_read(nid)
        pop.destroy()
        show_notifications_popup(col)

    tk.Button(pop, text="Mark All as Read", bg=col,
              fg=WHITE if col!=LIME else LIME_FG,
              font=("Helvetica",10,"bold"), relief="flat",
              padx=14, pady=6, cursor="hand2", bd=0,
              command=mark_all).pack(pady=6)


# ── ADMIN: MANAGE USERS ─────────────────────────────────────

def show_manage_users():
    if session.get("role") != "admin":
        messagebox.showerror("Access Denied", "Only administrators can manage users.")
        return
    pop = styled_popup("Manage Users", LIME, 680, 500)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    hf = tk.Frame(body, bg=SURFACE)
    hf.pack(fill="x", pady=(0,4))
    for txt in ["ID","Username","Full Name","Role","Email"]:
        tk.Label(hf, text=txt, font=("Helvetica",9,"bold"),
                 fg=LIME, bg=SURFACE, width=10,
                 anchor="w").pack(side="left", padx=4, pady=4)

    canvas = tk.Canvas(body, bg=BG, highlightthickness=0, height=340)
    sb2    = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
    sf     = tk.Frame(canvas, bg=BG)
    sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=sf, anchor="nw")
    canvas.configure(yscrollcommand=sb2.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb2.pack(side="right", fill="y")

    def refresh():
        for w in sf.winfo_children(): w.destroy()
        for uid, uname, fname, role, email in db_get_all_users():
            rf = tk.Frame(sf, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)
            rf.pack(fill="x", pady=1)
            rc = LIME if role=="admin" else (PINK if role=="teacher" else CYAN)
            for val, wid in [(str(uid),4),(uname,12),(fname,18),(role,10),(email or "—",20)]:
                tk.Label(rf, text=val, font=("Helvetica",9),
                         fg=rc if val==role else WHITE,
                         bg=CARD, width=wid, anchor="w").pack(side="left", padx=4, pady=4)
            if uid != session["id"]:
                tk.Button(rf, text="✕", bg=RED, fg=WHITE,
                          font=("Helvetica",9,"bold"), relief="flat",
                          padx=4, pady=2, cursor="hand2", bd=0,
                          command=lambda i=uid: (
                              db_delete_user(i) if messagebox.askyesno(
                                  "Confirm", f"Delete user ID {i}?", parent=pop)
                              else None, refresh()
                          )).pack(side="right", padx=6, pady=2)

    refresh()

    # Add new user button
    tk.Button(pop, text="+ Register New User", bg=LIME, fg=LIME_FG,
              font=("Helvetica",10,"bold"), relief="flat",
              padx=14, pady=6, cursor="hand2", bd=0,
              command=show_register).pack(pady=6)


# ── ADMIN: MANAGE COURSES ───────────────────────────────────

def show_manage_courses():
    if session.get("role") == "student":
        messagebox.showerror("Access Denied", "Students cannot manage courses.")
        return
    pop = styled_popup("Manage Courses", LIME, 660, 620)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=6)

    # ── Scrollable course list with Delete buttons ───────────
    tk.Label(body, text="Current Courses", font=("Helvetica",10,"bold"),
             fg=LIME, bg=BG).pack(anchor="w")

    # Header row
    hf = tk.Frame(body, bg=SURFACE)
    hf.pack(fill="x", pady=(2,0))
    for txt, wid in [("Code",8),("Name",26),("Enrolled",10),("Teacher",14),("",4)]:
        tk.Label(hf, text=txt, font=("Helvetica",8,"bold"),
                 fg=LIME, bg=SURFACE, width=wid, anchor="w").pack(side="left", padx=4, pady=3)

    # Scrollable list canvas
    cv_list = tk.Canvas(body, bg=BG, highlightthickness=0, height=180)
    sb_list = tk.Scrollbar(body, orient="vertical", command=cv_list.yview)
    sf_list = tk.Frame(cv_list, bg=BG)
    sf_list.bind("<Configure>", lambda e: cv_list.configure(scrollregion=cv_list.bbox("all")))
    cv_list.create_window((0,0), window=sf_list, anchor="nw")
    cv_list.configure(yscrollcommand=sb_list.set)
    cv_list.pack(side="left", fill="both", expand=True, pady=2)
    sb_list.pack(side="right", fill="y", pady=2)

    def refresh_courses():
        for w in sf_list.winfo_children(): w.destroy()
        for row in db_get_courses():
            cid, code, name, teacher, cap, enrolled = row
            rf = tk.Frame(sf_list, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)
            rf.pack(fill="x", pady=1)
            tk.Label(rf, text=code, font=("Helvetica",9,"bold"),
                     fg=LIME, bg=CARD, width=8, anchor="w").pack(side="left", padx=4, pady=4)
            tk.Label(rf, text=name[:26], font=("Helvetica",9),
                     fg=WHITE, bg=CARD, width=26, anchor="w").pack(side="left")
            tk.Label(rf, text=f"{enrolled}/{cap}", font=("Helvetica",8),
                     fg=DIM, bg=CARD, width=10).pack(side="left")
            tk.Label(rf, text=(teacher or "—")[:14], font=("Helvetica",8),
                     fg=GHOST, bg=CARD, width=14, anchor="w").pack(side="left")
            def _del(c_id=cid, c_name=name):
                if messagebox.askyesno("Delete Course",
                        f"Delete '{c_name}'?\nThis will also remove all enrolments and timetable entries.",
                        parent=pop):
                    db_delete_course(c_id)
                    refresh_courses()
            tk.Button(rf, text="✕", bg=RED, fg=WHITE,
                      font=("Helvetica",8,"bold"), relief="flat",
                      padx=6, pady=2, cursor="hand2", bd=0,
                      command=_del).pack(side="right", padx=6, pady=3)

    refresh_courses()

    # ── Add course form ──────────────────────────────────────
    # Need a new frame on the RIGHT side of the canvas/scrollbar pair
    body2 = tk.Frame(pop, bg=BG)
    body2.pack(fill="both", padx=20, pady=(0,6))

    tk.Frame(body2, bg=BORDER, height=1).pack(fill="x", pady=(6,8))
    tk.Label(body2, text="Add New Course", font=("Helvetica",10,"bold"),
             fg=LIME, bg=BG).pack(anchor="w")

    fields2 = {}
    for label, key in [("Course Code", "code"), ("Course Name", "name"), ("Capacity", "capacity")]:
        tk.Label(body2, text=label, font=("Helvetica",9),
                 fg=DIM, bg=BG).pack(anchor="w", pady=(4,0))
        v = tk.StringVar()
        tk.Entry(body2, textvariable=v, font=("Helvetica",10),
                 bg=SURFACE, fg=WHITE, insertbackground=WHITE,
                 relief="flat", bd=5).pack(fill="x")
        fields2[key] = v

    # Teacher selector
    tk.Label(body2, text="Assign Teacher", font=("Helvetica",9),
             fg=DIM, bg=BG).pack(anchor="w", pady=(4,0))
    con2 = db_connect(); cur2 = con2.cursor()
    cur2.execute("SELECT id, full_name FROM users WHERE role='teacher' ORDER BY full_name")
    teachers = cur2.fetchall(); con2.close()
    teacher_names = [t[1] for t in teachers]
    teacher_ids   = [t[0] for t in teachers]
    teacher_var = tk.StringVar(value=teacher_names[0] if teacher_names else "")
    om = tk.OptionMenu(body2, teacher_var, *(teacher_names or ["No teachers"]))
    om.config(bg=SURFACE, fg=WHITE, font=("Helvetica",10), relief="flat",
              bd=0, highlightthickness=0, activebackground=BORDER, activeforeground=WHITE)
    om.pack(fill="x")

    msg_var = tk.StringVar()
    tk.Label(body2, textvariable=msg_var, font=("Helvetica",9),
             fg=GREEN, bg=BG).pack(pady=2)

    def add_course():
        tid = teacher_ids[teacher_names.index(teacher_var.get())] if teacher_names else session["id"]
        try:
            cap = int(fields2["capacity"].get() or 30)
        except ValueError:
            msg_var.set("✗ Capacity must be a number."); return
        ok, msg = db_add_course(
            fields2["code"].get().strip().upper(),
            fields2["name"].get().strip(),
            tid, cap)
        msg_var.set(("✓ " if ok else "✗ ") + msg)
        if ok:
            for v in fields2.values(): v.set("")
            refresh_courses()

    tk.Button(body2, text="＋  Add Course", bg=LIME, fg=LIME_FG,
              font=("Helvetica",11,"bold"), relief="flat",
              padx=0, pady=8, cursor="hand2", bd=0,
              command=add_course).pack(fill="x", pady=(4,0))


# ── ADMIN: MANAGE TIMETABLE ─────────────────────────────────

def show_manage_timetable():
    if session.get("role") == "student":
        messagebox.showerror("Access Denied", "Students cannot edit the timetable.")
        return
    pop = styled_popup("Manage Timetable", LIME, 620, 640)
    body = tk.Frame(pop, bg=BG)
    body.pack(fill="both", expand=True, padx=20, pady=6)

    # ── Scrollable current timetable with Delete ─────────────
    tk.Label(body, text="Current Timetable", font=("Helvetica",10,"bold"),
             fg=LIME, bg=BG).pack(anchor="w")

    hf = tk.Frame(body, bg=SURFACE)
    hf.pack(fill="x", pady=(2,0))
    for txt, wid in [("Course",22),("Day",10),("Time",8),("Room",10),("",4)]:
        tk.Label(hf, text=txt, font=("Helvetica",8,"bold"),
                 fg=LIME, bg=SURFACE, width=wid, anchor="w").pack(side="left", padx=4, pady=3)

    cv_tt = tk.Canvas(body, bg=BG, highlightthickness=0, height=200)
    sb_tt = tk.Scrollbar(body, orient="vertical", command=cv_tt.yview)
    sf_tt = tk.Frame(cv_tt, bg=BG)
    sf_tt.bind("<Configure>", lambda e: cv_tt.configure(scrollregion=cv_tt.bbox("all")))
    cv_tt.create_window((0,0), window=sf_tt, anchor="nw")
    cv_tt.configure(yscrollcommand=sb_tt.set)
    cv_tt.pack(side="left", fill="both", expand=True, pady=2)
    sb_tt.pack(side="right", fill="y", pady=2)

    def refresh_tt():
        for w in sf_tt.winfo_children(): w.destroy()
        rows = db_get_timetable_with_ids()
        if not rows:
            tk.Label(sf_tt, text="  No timetable entries yet.",
                     fg=GHOST, bg=BG, font=("Helvetica",9)).pack(pady=8)
            return
        for entry_id, course, day, time_slot, room in rows:
            rf = tk.Frame(sf_tt, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)
            rf.pack(fill="x", pady=1)
            tk.Label(rf, text=course[:22], font=("Helvetica",9),
                     fg=WHITE, bg=CARD, width=22, anchor="w").pack(side="left", padx=4, pady=3)
            tk.Label(rf, text=day,         fg=DIM,  bg=CARD, width=10,
                     font=("Helvetica",9), anchor="w").pack(side="left")
            tk.Label(rf, text=time_slot,   fg=LIME, bg=CARD, width=8,
                     font=("Helvetica",9,"bold")).pack(side="left")
            tk.Label(rf, text=room or "—", fg=GHOST, bg=CARD, width=10,
                     font=("Helvetica",9), anchor="w").pack(side="left")
            def _del(eid=entry_id):
                if messagebox.askyesno("Delete Entry",
                        "Remove this timetable slot?", parent=pop):
                    db_delete_timetable_entry(eid)
                    refresh_tt()
            tk.Button(rf, text="✕", bg=RED, fg=WHITE,
                      font=("Helvetica",8,"bold"), relief="flat",
                      padx=6, pady=2, cursor="hand2", bd=0,
                      command=_del).pack(side="right", padx=6, pady=3)

    refresh_tt()

    # ── Add entry form ────────────────────────────────────────
    body2 = tk.Frame(pop, bg=BG)
    body2.pack(fill="x", padx=20, pady=(0,8))

    tk.Frame(body2, bg=BORDER, height=1).pack(fill="x", pady=(4,8))
    tk.Label(body2, text="Add Timetable Entry", font=("Helvetica",10,"bold"),
             fg=LIME, bg=BG).pack(anchor="w")

    # Course dropdown (single, correct instance)
    courses = db_get_courses()
    course_names = [f"{r[1]} — {r[2]}" for r in courses]
    course_ids   = [r[0] for r in courses]

    tk.Label(body2, text="Course", font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
    course_var = tk.StringVar(value=course_names[0] if course_names else "")
    om_c = tk.OptionMenu(body2, course_var, *(course_names or ["No courses"]))
    om_c.config(bg=SURFACE, fg=WHITE, font=("Helvetica",10), relief="flat",
                bd=0, highlightthickness=0, activebackground=BORDER, activeforeground=WHITE,
                width=40)
    om_c.pack(fill="x")

    # Day dropdown
    DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    tk.Label(body2, text="Day", font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
    day_var = tk.StringVar(value="Monday")
    om_d = tk.OptionMenu(body2, day_var, *DAYS)
    om_d.config(bg=SURFACE, fg=WHITE, font=("Helvetica",10), relief="flat",
                bd=0, highlightthickness=0, activebackground=BORDER, activeforeground=WHITE,
                width=40)
    om_d.pack(fill="x")

    # Time dropdown
    TIMES = ["09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00"]
    tk.Label(body2, text="Time Slot", font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
    time_var = tk.StringVar(value="09:00")
    om_t = tk.OptionMenu(body2, time_var, *TIMES)
    om_t.config(bg=SURFACE, fg=WHITE, font=("Helvetica",10), relief="flat",
                bd=0, highlightthickness=0, activebackground=BORDER, activeforeground=WHITE,
                width=40)
    om_t.pack(fill="x")

    # Room — free text
    tk.Label(body2, text="Room", font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(6,0))
    room_var = tk.StringVar(value="Room A1")
    tk.Entry(body2, textvariable=room_var, font=("Helvetica",10),
             bg=SURFACE, fg=WHITE, insertbackground=WHITE,
             relief="flat", bd=5).pack(fill="x")

    msg_var = tk.StringVar()
    tk.Label(body2, textvariable=msg_var, font=("Helvetica",9),
             fg=GREEN, bg=BG).pack(pady=2)

    def add_entry():
        if not course_names:
            msg_var.set("✗ No courses available."); return
        try:
            idx = course_names.index(course_var.get())
        except ValueError:
            msg_var.set("✗ Please select a course."); return
        db_add_timetable(course_ids[idx], day_var.get(),
                         time_var.get(), room_var.get().strip())
        msg_var.set(f"✓ Entry added: {day_var.get()} {time_var.get()}")
        refresh_tt()

    tk.Button(body2, text="＋  Save Timetable Entry", bg=LIME, fg=LIME_FG,
              font=("Helvetica",11,"bold"), relief="flat",
              padx=0, pady=8, cursor="hand2", bd=0,
              command=add_entry).pack(fill="x", pady=(6,0))


# ── TEACHER: MY STUDENTS ────────────────────────────────────

def show_students_popup(col):
    """Show all students enrolled in the teacher's courses."""
    pop = styled_popup("My Students", col, 660, 500)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    con = db_connect()
    cur = con.cursor()
    cur.execute("""
        SELECT DISTINCT u.full_name, u.username, c.name, c.code, e.grade
        FROM enrolments e
        JOIN users u ON u.id = e.student_id
        JOIN courses c ON c.id = e.course_id
        WHERE c.teacher_id = ?
        ORDER BY c.code, u.full_name
    """, (session["id"],))
    rows = cur.fetchall()
    con.close()

    tk.Label(body, text=f"{len(rows)} enrolment record(s) across your courses",
             font=("Helvetica",10), fg=col, bg=BG).pack(anchor="w", pady=(0,8))

    # Header
    hf = tk.Frame(body, bg=SURFACE)
    hf.pack(fill="x", pady=(0,4))
    for txt, wid in [("Student",22),("Username",12),("Course",22),("Grade",8)]:
        tk.Label(hf, text=txt, font=("Helvetica",9,"bold"),
                 fg=col, bg=SURFACE, width=wid, anchor="w").pack(side="left", padx=4, pady=4)

    canvas2 = tk.Canvas(body, bg=BG, highlightthickness=0, height=340)
    sb2 = tk.Scrollbar(body, orient="vertical", command=canvas2.yview)
    sf = tk.Frame(canvas2, bg=BG)
    sf.bind("<Configure>", lambda e: canvas2.configure(scrollregion=canvas2.bbox("all")))
    canvas2.create_window((0,0), window=sf, anchor="nw")
    canvas2.configure(yscrollcommand=sb2.set)
    canvas2.pack(side="left", fill="both", expand=True)
    sb2.pack(side="right", fill="y")

    if not rows:
        tk.Label(sf, text="No students enrolled in your courses yet.",
                 fg=DIM, bg=BG, font=("Helvetica",11)).pack(pady=20)
    for full_name, username, course, code, grade in rows:
        rf = tk.Frame(sf, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        rf.pack(fill="x", pady=1)
        gc = GREEN if grade and grade[0]=='A' else (ORANGE if grade and grade[0]=='B' else DIM)
        for val, wid in [(full_name[:22],22),("@"+username,12),(f"{code} {course[:18]}",22)]:
            tk.Label(rf, text=val, font=("Helvetica",9), fg=WHITE,
                     bg=CARD, width=wid, anchor="w").pack(side="left", padx=4, pady=4)
        tk.Label(rf, text=grade or "—", font=("Helvetica",9,"bold"),
                 fg=gc, bg=CARD, width=8).pack(side="left", padx=4)


# ── ADMIN: ALL ATTENDANCE ────────────────────────────────────

def show_all_attendance_popup():
    """Admin view — attendance records for all students."""
    pop = styled_popup("All Attendance Records", LIME, 680, 500)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    con = db_connect()
    cur = con.cursor()
    cur.execute("""
        SELECT u.full_name, c.name, a.date, a.status
        FROM attendance a
        JOIN users u ON u.id = a.student_id
        JOIN courses c ON c.id = a.course_id
        ORDER BY a.date DESC, u.full_name
    """)
    rows = cur.fetchall()
    present = sum(1 for r in rows if r[3]=="present")
    total = len(rows)
    att_pct = round(present/total*100) if total else 0
    con.close()

    tk.Label(body, text=f"Overall: {att_pct}%  ·  {present}/{total} sessions present",
             font=("Helvetica",10,"bold"), fg=LIME, bg=BG).pack(anchor="w", pady=(0,8))

    hf = tk.Frame(body, bg=SURFACE)
    hf.pack(fill="x", pady=(0,4))
    for txt, wid in [("Student",20),("Course",22),("Date",12),("Status",10)]:
        tk.Label(hf, text=txt, font=("Helvetica",9,"bold"),
                 fg=LIME, bg=SURFACE, width=wid, anchor="w").pack(side="left", padx=4, pady=4)

    canvas2 = tk.Canvas(body, bg=BG, highlightthickness=0, height=340)
    sb2 = tk.Scrollbar(body, orient="vertical", command=canvas2.yview)
    sf = tk.Frame(canvas2, bg=BG)
    sf.bind("<Configure>", lambda e: canvas2.configure(scrollregion=canvas2.bbox("all")))
    canvas2.create_window((0,0), window=sf, anchor="nw")
    canvas2.configure(yscrollcommand=sb2.set)
    canvas2.pack(side="left", fill="both", expand=True)
    sb2.pack(side="right", fill="y")

    for full_name, course, date, status in rows:
        rf = tk.Frame(sf, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        rf.pack(fill="x", pady=1)
        sc = GREEN if status=="present" else (ORANGE if status=="late" else RED)
        for val, wid in [(full_name[:20],20),(course[:22],22),(date,12)]:
            tk.Label(rf, text=val, font=("Helvetica",9), fg=WHITE,
                     bg=CARD, width=wid, anchor="w").pack(side="left", padx=4, pady=3)
        tk.Label(rf, text=status.title(), font=("Helvetica",9,"bold"),
                 fg=sc, bg=CARD, width=10).pack(side="left", padx=4)


# ── ADMIN: ADD ATTENDANCE ────────────────────────────────────

def show_gpa_tools_popup():
    """Admin GPA tools — view GPA for any student and add attendance records."""
    if session.get("role") == "student":
        messagebox.showerror("Access Denied", "Students cannot access GPA admin tools.")
        return
    pop = styled_popup("GPA Tools & Attendance", LIME, 620, 540)
    body = tk.Frame(pop, bg=BG)
    body.pack(expand=True, fill="both", padx=20, pady=10)

    # ── Section 1: Student GPA lookup ───────────────────────
    tk.Label(body, text="Student GPA Lookup", font=("Helvetica",10,"bold"),
             fg=LIME, bg=BG).pack(anchor="w")

    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT id, full_name FROM users WHERE role='student' ORDER BY full_name")
    students = cur.fetchall()
    con.close()

    student_names = [s[1] for s in students]
    student_ids   = [s[0] for s in students]

    sel_var = tk.StringVar(value=student_names[0] if student_names else "")
    tk.OptionMenu(body, sel_var, *student_names).pack(fill="x", pady=(4,0))

    gpa_result_var = tk.StringVar(value="")
    tk.Label(body, textvariable=gpa_result_var, font=("Helvetica",12,"bold"),
             fg=GREEN, bg=BG).pack(pady=4)

    def lookup_gpa():
        if sel_var.get() in student_names:
            idx = student_names.index(sel_var.get())
            sid = student_ids[idx]
            gpa, breakdown = db_calc_gpa(sid)
            gpa_result_var.set(f"GPA: {gpa:.2f}  ({len(breakdown)} grades recorded)")

    tk.Button(body, text="Calculate GPA", bg=LIME, fg=LIME_FG,
              font=("Helvetica",10,"bold"), relief="flat",
              padx=14, pady=6, cursor="hand2", bd=0,
              command=lookup_gpa).pack(fill="x", pady=(0,8))

    # ── Section 2: Add attendance record ────────────────────
    tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=6)
    tk.Label(body, text="Add Attendance Record", font=("Helvetica",10,"bold"),
             fg=LIME, bg=BG).pack(anchor="w")

    con = db_connect()
    cur = con.cursor()
    cur.execute("SELECT id, code, name FROM courses ORDER BY code")
    courses = cur.fetchall()
    con.close()

    course_names = [f"{c[1]} — {c[2]}" for c in courses]
    course_ids   = [c[0] for c in courses]

    att_student_var = tk.StringVar(value=student_names[0] if student_names else "")
    att_course_var  = tk.StringVar(value=course_names[0] if course_names else "")
    att_date_var    = tk.StringVar(value="2025-05-12")
    att_status_var  = tk.StringVar(value="present")

    for lbl_txt, var, opts in [
        ("Student",  att_student_var, student_names),
        ("Course",   att_course_var,  course_names),
    ]:
        tk.Label(body, text=lbl_txt, font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(4,0))
        tk.OptionMenu(body, var, *opts).pack(fill="x")

    tk.Label(body, text="Date (YYYY-MM-DD)", font=("Helvetica",9),
             fg=DIM, bg=BG).pack(anchor="w", pady=(4,0))
    tk.Entry(body, textvariable=att_date_var, font=("Helvetica",10),
             bg=SURFACE, fg=WHITE, insertbackground=WHITE,
             relief="flat", bd=5).pack(fill="x")

    tk.Label(body, text="Status", font=("Helvetica",9), fg=DIM, bg=BG).pack(anchor="w", pady=(4,0))
    status_frame = tk.Frame(body, bg=BG)
    status_frame.pack(fill="x")
    for s in ["present","absent","late"]:
        sc = GREEN if s=="present" else (RED if s=="absent" else ORANGE)
        tk.Radiobutton(status_frame, text=s.title(), variable=att_status_var, value=s,
                       bg=BG, fg=sc, selectcolor=SURFACE,
                       activebackground=BG, activeforeground=sc,
                       font=("Helvetica",10)).pack(side="left", padx=8)

    att_msg_var = tk.StringVar()
    tk.Label(body, textvariable=att_msg_var, font=("Helvetica",9),
             fg=GREEN, bg=BG).pack(pady=4)

    def add_attendance():
        try:
            s_idx = student_names.index(att_student_var.get())
            c_idx = course_names.index(att_course_var.get())
            con2 = db_connect()
            cur2 = con2.cursor()
            cur2.execute(
                "INSERT INTO attendance(student_id,course_id,date,status) VALUES(?,?,?,?)",
                (student_ids[s_idx], course_ids[c_idx],
                 att_date_var.get(), att_status_var.get())
            )
            con2.commit(); con2.close()
            att_msg_var.set("✓ Attendance record added.")
        except Exception as ex:
            att_msg_var.set(f"✗ {ex}")

    tk.Button(body, text="Add Attendance Record", bg=LIME, fg=LIME_FG,
              font=("Helvetica",10,"bold"), relief="flat",
              padx=14, pady=6, cursor="hand2", bd=0,
              command=add_attendance).pack(fill="x", pady=(4,0))


# ══════════════════════════════════════════════════════════════
#  ROOT WINDOW
# ══════════════════════════════════════════════════════════════

root = tk.Tk()
root.title("Capital City College — myday Portal")
root.geometry("1200x700")
root.configure(bg=BG)
root.resizable(False, False)

container = tk.Frame(root, bg=BG)
container.pack(expand=True, fill="both")
_current = [None]

def _clear():
    if _current[0]:
        _current[0].destroy()
        _current[0] = None

# ══════════════════════════════════════════════════════════════
#  SHARED LAYOUT COMPONENTS
# ══════════════════════════════════════════════════════════════

def build_topbar(parent, col, nav_items, back_cmd=None):
    tb = tk.Canvas(parent, width=1200, height=56,
                   bg=SURFACE, highlightthickness=0)
    tb.pack(fill="x")
    tb.create_polygon([0,0,8,0,8,56,0,56], fill=col, outline="")
    tb.create_polygon([8,0,22,0,14,56,8,56],
                      fill=r2h(lerp(h2r(col),h2r(BG),0.55)), outline="")
    tb.create_text(36,28,text="◆",font=("Georgia",12),fill=ORANGE,anchor="w")
    tb.create_text(54,28,text="Capital City College",
                   font=("Georgia",13,"bold"),fill=WHITE,anchor="w")

    offset = 0
    if back_cmd:
        b = tk.Button(parent,text="← Back",bg=SURFACE,fg=col,
                      font=("Helvetica",10,"bold"),relief="flat",
                      padx=10,pady=0,cursor="hand2",bd=0,
                      activebackground=SURFACE,activeforeground=WHITE,
                      command=back_cmd)
        b.place(x=264,y=17); offset=88

    # Nav button commands keyed by label — role-aware
    current_role = session.get("role")

    def _courses_cmd():
        if current_role == "student":
            show_enrol_popup()
        elif current_role in ("admin", "teacher"):
            show_manage_courses()
        else:
            messagebox.showerror("Access Denied", "Please log in first.")

    def _admin_cmd():
        if current_role == "admin":
            show_manage_users()
        else:
            messagebox.showerror("Access Denied",
                                 "Only administrators can access this section.")

    nav_cmds = {
        "Dashboard":  back_cmd or show_login,
        "Courses":    _courses_cmd,
        "Timetable":  lambda: show_timetable_popup(col),
        "Attendance": lambda: show_attendance_popup(col),
        "Admin":      _admin_cmd,
    }

    nx = 282+offset
    for item in nav_items:
        cmd = nav_cmds.get(item, None)
        btn=tk.Button(parent,text=item,bg=SURFACE,fg=DIM,
                      font=("Helvetica",10),relief="flat",
                      padx=10,pady=0,cursor="hand2",bd=0,
                      activebackground=SURFACE,activeforeground=col,
                      command=cmd)
        btn.place(x=nx,y=17)
        btn.bind("<Enter>",lambda e,b=btn,c=col:b.config(fg=c))
        btn.bind("<Leave>",lambda e,b=btn:b.config(fg=DIM))
        nx+=len(item)*8+22

    # User greeting + logout
    tk.Label(parent, text=f"👤 {session.get('name','')[:16]}",
             font=("Helvetica",9), fg=DIM, bg=SURFACE).place(x=960, y=20)

    tk.Button(parent,text="⎋  Log Out",bg=ORANGE,fg=WHITE,
              font=("Helvetica",10,"bold"),relief="flat",
              padx=14,pady=5,cursor="hand2",bd=0,
              activebackground=ORANGE_D,activeforeground=WHITE,
              command=lambda:(session.update(id=None,name=None,role=None),
                              show_login())).place(x=1072,y=13)

    strip=tk.Canvas(parent,width=1200,height=3,bg=BG,highlightthickness=0)
    strip.pack(fill="x")
    for i,c in enumerate([PINK,ORANGE,CYAN,LIME]):
        strip.create_rectangle(i*300,0,(i+1)*300,3,fill=c,outline="")


def build_footer(parent):
    f=tk.Frame(parent,bg=SURFACE,height=30)
    f.pack(fill="x",side="bottom"); f.pack_propagate(False)
    tk.Label(f,
             text="© 2025 Capital City College Group  ·  myday Portal  ·  All rights reserved",
             font=("Helvetica",8),fg=GHOST,bg=SURFACE).pack(expand=True)


def build_sidebar(parent, role_name, role_icon, col, items):
    """
    items: list of (icon, label, command_or_None)
    Supports both 2-tuples (legacy) and 3-tuples (with command).
    """
    sb=tk.Canvas(parent,width=196,bg=SURFACE,highlightthickness=0)
    sb.pack(side="left",fill="y")

    def draw(hover_idx=-1):
        sb.delete("all"); sb.config(height=640)
        sb.create_rectangle(0,0,196,640,fill=SURFACE,outline="")
        for i in range(6):
            t=(6-i)/6*0.22
            sb.create_line(194-i,0,194-i,640,
                           fill=r2h(lerp(h2r(SURFACE),h2r(col),t)))
        soft_glow(sb,98,82,32,col,layers=6,strength=0.26)
        sb.create_oval(60,48,136,116,fill=col,outline="")
        sb.create_text(98,82,text=role_icon,font=("Arial",26))
        sb.create_text(98,130,text=role_name.upper(),
                       font=("Helvetica",9,"bold"),fill=col)
        sb.create_text(98,146,text="PORTAL",font=("Helvetica",7),fill=GHOST)
        fade_line(sb,14,162,182,col,steps=60)
        for i,item in enumerate(items):
            ico,lbl2 = item[0],item[1]
            iy=182+i*44
            if i==hover_idx:
                rr(sb,8,iy-16,188,iy+16,rd=8,fill="#252525",outline=col,width=1)
                sb.create_text(24,iy,text=ico,font=("Arial",13),fill=col,anchor="w")
                sb.create_text(48,iy,text=lbl2,font=("Helvetica",10,"bold"),
                               fill=WHITE,anchor="w")
            else:
                sb.create_text(24,iy,text=ico,font=("Arial",13),fill=GHOST,anchor="w")
                sb.create_text(48,iy,text=lbl2,font=("Helvetica",10),fill=DIM,anchor="w")

    draw()

    def on_motion(e):
        idx=-1
        for i in range(len(items)):
            if abs(e.y-(182+i*44))<18: idx=i; break
        draw(idx)

    def on_click(e):
        for i,item in enumerate(items):
            iy=182+i*44
            if abs(e.y-iy)<18:
                cmd = item[2] if len(item)>2 else None
                if callable(cmd): cmd()
                break

    sb.bind("<Motion>",on_motion)
    sb.bind("<Leave>",lambda e:draw())
    sb.bind("<Button-1>",on_click)
    sb.config(cursor="hand2")


def build_main_canvas(parent, col):
    cv=tk.Canvas(parent,bg=BG,highlightthickness=0)
    cv.pack(side="right",expand=True,fill="both")
    cv.update_idletasks()
    W,H=990,590
    scatter(cv,0,0,W,H,col,count=600)
    bg_glow(cv,W-80,H-60,100,col,layers=7,strength=0.09)
    return cv,W,H


# ══════════════════════════════════════════════════════════════
#  SCREEN — TEACHER DASHBOARD
# ══════════════════════════════════════════════════════════════

def show_teacher():
    _clear()
    frame=tk.Frame(container,bg=BG)
    frame.pack(expand=True,fill="both")
    _current[0]=frame
    col=PINK

    build_topbar(frame,col,["Dashboard","Courses","Attendance"],
                 back_cmd=show_login)
    body=tk.Frame(frame,bg=BG); body.pack(expand=True,fill="both")

    build_sidebar(body,"Teacher","👨‍🏫",col,[
        ("🏠","Home",          show_teacher),
        ("📚","My Courses",    lambda:show_students_popup(col)),
        ("👥","My Students",   lambda:show_students_popup(col)),
        ("✅","Attendance",    lambda:show_attendance_popup(col)),
        ("🔔","Notifications", lambda:show_notifications_popup(col)),
    ])

    cv,W,H=build_main_canvas(body,col)

    # Greeting
    rr(cv,12,10,W-12,58,rd=12,fill=CARD,outline=col,width=1)
    soft_glow(cv,38,34,14,col,layers=4,strength=0.22)
    cv.create_text(20,34,text="👋",font=("Arial",18),anchor="w")
    cv.create_text(50,24,text=f"Good morning, {session['name']}",
                   font=("Helvetica",13,"bold"),fill=WHITE,anchor="w")
    cv.create_text(50,44,text="Academic Year 2024/25  ·  Teacher Portal",
                   font=("Helvetica",9),fill=DIM,anchor="w")

    # Stats from DB
    students,_,courses,att=db_get_stats()
    stat_block(cv, 12, 72,144,88,str(students),"Students",col,"enrolled")
    stat_block(cv,164, 72,144,88,"3.4","Avg GPA",col,"this term")
    stat_block(cv,316, 72,144,88,str(courses),"Courses",col,"running")
    stat_block(cv,468, 72,144,88,f"{att}%","Attendance",col,"overall")

    # Quick Actions — wired to real popups
    rr(cv,620,72,W-12,160,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,634,80,"Quick Actions",col)
    pill_btn(cv,634,102,148,30,"View Attendance",col,
             cmd=lambda:show_attendance_popup(col))
    pill_btn(cv,792,102,148,30,"View Timetable",col,
             cmd=lambda:show_timetable_popup(col))
    pill_btn(cv,634,140,148,30,"My Profile",col,
             cmd=lambda:show_profile_popup(col))
    pill_btn(cv,792,140,148,30,"Notifications",col,
             cmd=lambda:show_notifications_popup(col))

    # ── Row 2: My Courses (left) + Weekly Schedule (right) ──
    # My Courses card — taller to avoid clipping
    rr(cv,12,172,296,430,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,24,182,"My Courses",col)
    for i,(row) in enumerate(db_get_courses()[:3]):
        cid,code,name,teacher,cap,enrolled=row
        ry=206+i*68
        rr(cv,24,ry,282,ry+58,rd=10,
           fill=r2h(lerp(h2r(CARD),h2r(col),0.07)),outline=BORDER,width=1)
        cv.create_text(44,ry+16,text="📖",font=("Arial",17),anchor="w")
        cv.create_text(70,ry+14,text=name[:24],
                       font=("Helvetica",10,"bold"),fill=WHITE,anchor="w")
        cv.create_text(70,ry+34,text=f"{enrolled} students  ·  {code}",
                       font=("Helvetica",8),fill=DIM,anchor="w")
    pill_btn(cv,68,414,160,28,"View My Students →",col,
             cmd=lambda:show_students_popup(col))

    # Weekly Schedule card — full height with enough room for grid + attendance
    rr(cv,316,172,W-12,430,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,328,182,"Weekly Schedule",col)
    tt_rows = db_get_timetable(session["id"],"teacher")
    day_map = {"Monday":"MON","Tuesday":"TUE","Wednesday":"WED",
               "Thursday":"THU","Friday":"FRI"}
    grid = {t:["","","","",""] for t in ["09:00","10:00","11:00","12:00","13:00"]}
    day_idx = {"MON":0,"TUE":1,"WED":2,"THU":3,"FRI":4}
    for name,day,tslot,room in tt_rows:
        dk = day_map.get(day,"")
        if tslot in grid and dk in day_idx:
            grid[tslot][day_idx[dk]] = name[:8]
    grid_rows = [(t,)+tuple(v) for t,v in grid.items()]
    # timetable_grid height = 28 header + 5×26 rows = 158px
    timetable_grid(cv,322,202,W-12-322-4,158,col,grid_rows)

    # ── Row 3: Attendance bars — in its own card BELOW row 2 ──
    rr(cv,12,444,W-12,570,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,24,454,"Class Attendance This Week",col)
    for i,(day,pct) in enumerate([("M",0.95),("T",0.80),("W",1.0),("Th",0.75),("F",0.65)]):
        bx=30+i*90; bh=int(pct*72); by=548
        rr(cv,bx,by-bh,bx+60,by,rd=6,fill=(col if pct>=0.8 else ORANGE),outline="")
        cv.create_text(bx+30,by+12,text=day,font=("Helvetica",9),fill=DIM)
        cv.create_text(bx+30,by-bh-11,text=f"{int(pct*100)}%",
                       font=("Helvetica",8,"bold"),fill=WHITE)

    build_footer(frame)


# ══════════════════════════════════════════════════════════════
#  SCREEN — STUDENT DASHBOARD
# ══════════════════════════════════════════════════════════════

def show_student():
    _clear()
    frame=tk.Frame(container,bg=BG)
    frame.pack(expand=True,fill="both")
    _current[0]=frame
    col=CYAN

    build_topbar(frame,col,["Dashboard","Courses","Timetable"],
                 back_cmd=show_login)
    body=tk.Frame(frame,bg=BG); body.pack(expand=True,fill="both")

    build_sidebar(body,"Student","👨‍🎓",col,[
        ("🏠","Home",          show_student),
        ("👤","My Profile",    lambda:show_profile_popup(col)),
        ("📚","My Courses",    lambda:show_enrol_popup()),
        ("📅","Attendance",    lambda:show_attendance_popup(col)),
        ("🔔","Notifications", lambda:show_notifications_popup(col)),
    ])

    cv,W,H=build_main_canvas(body,col)

    # Greeting
    rr(cv,12,10,W-12,58,rd=12,fill=CARD,outline=col,width=1)
    soft_glow(cv,38,34,14,col,layers=4,strength=0.22)
    cv.create_text(20,34,text="👋",font=("Arial",18),anchor="w")
    cv.create_text(50,24,text=f"Welcome back, {session['name']}",
                   font=("Helvetica",13,"bold"),fill=WHITE,anchor="w")
    cv.create_text(50,44,text="Student Portal  ·  Academic Year 2024/25",
                   font=("Helvetica",9),fill=DIM,anchor="w")

    # Stats
    my_courses = db_get_courses(session["id"])
    gpa,_ = db_calc_gpa(session["id"])
    att_records = db_get_attendance(session["id"])
    pres = sum(1 for r in att_records if r[2]=="present")
    att_pct = round(pres/len(att_records)*100) if att_records else 0
    stat_block(cv, 12, 72,144,88,str(len(my_courses)),"Courses",col,"enrolled")
    stat_block(cv,164, 72,144,88,str(gpa),"GPA",col,"this term")
    stat_block(cv,316, 72,144,88,f"{att_pct}%","Attendance",col,"overall")
    stat_block(cv,468, 72,144,88,str(len(my_courses)),"Due Soon",col,"assignments")

    # Quick Access — all wired
    rr(cv,620,72,W-12,160,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,634,80,"Quick Access",col)
    pill_btn(cv,634,102,148,30,"Enrol in Course",col,cmd=show_enrol_popup)
    pill_btn(cv,792,102,148,30,"Check Grades",col,
             cmd=lambda:show_gpa_popup(col))
    pill_btn(cv,634,140,148,30,"View Timetable",col,
             cmd=lambda:show_timetable_popup(col))
    pill_btn(cv,792,140,148,30,"Notifications",col,
             cmd=lambda:show_notifications_popup(col))

    # ── Row 2: Profile (left) + My Courses (right) ──
    rr(cv,12,172,296,310,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,24,182,"My Profile",col)
    profile = db_get_profile(session["id"])
    if profile:
        soft_glow(cv,78,248,28,col,layers=5,strength=0.20)
        cv.create_oval(46,218,110,282,fill=col,outline="")
        cv.create_text(78,250,text="👤",font=("Arial",22))
        for i,(k,v) in enumerate([
            ("Name",   profile[0]),
            ("Email",  (profile[1] or "—")[:22]),
            ("Role",   profile[2].title()),
            ("User",   "@"+profile[3]),
        ]):
            fy=214+i*20
            cv.create_text(124,fy,text=k+":",font=("Helvetica",8),fill=GHOST,anchor="w")
            cv.create_text(178,fy,text=v,font=("Helvetica",9,"bold"),fill=WHITE,anchor="w")
    pill_btn(cv,48,295,200,26,"Edit Profile",col,
             cmd=lambda:show_profile_popup(col))

    # My Courses — right panel, row 2
    rr(cv,316,172,W-12,310,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,328,182,"My Courses",col)
    for i,row in enumerate(my_courses[:3]):
        cid,code,name,teacher,cap,grade=row
        cxp=328+i*210
        rr(cv,cxp,204,cxp+198,298,rd=10,
           fill=r2h(lerp(h2r(CARD),h2r(col),0.08)),outline=BORDER,width=1)
        cv.create_text(cxp+99,226,text="📖",font=("Arial",20),fill=WHITE)
        cv.create_text(cxp+99,250,text=name[:18],
                       font=("Helvetica",9,"bold"),fill=WHITE,
                       width=186,justify="center")
        gc2=GREEN if grade and grade[0]=='A' else (ORANGE if grade and grade[0]=='B' else DIM)
        cv.create_text(cxp+99,270,text=f"Grade: {grade or '—'}",
                       font=("Helvetica",8,"bold"),fill=gc2)

    # ── Row 3: Timetable — full width, own card ──
    rr(cv,12,322,W-12,488,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,24,332,"My Timetable",col)
    tt_rows = db_get_timetable(session["id"],"student")
    grid = {t:["","","","",""] for t in ["09:00","10:00","11:00","12:00","13:00"]}
    day_idx={"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4}
    for name,day,tslot,room in tt_rows:
        if tslot in grid and day in day_idx:
            grid[tslot][day_idx[day]] = name[:8]
    grid_rows=[(t,)+tuple(v) for t,v in grid.items()]
    # timetable_grid: 28 header + 5×26 rows = 158px; starts at y=352
    timetable_grid(cv,16,352,W-32,158,col,grid_rows)

    # ── Row 4: Attendance mini bars — own card below timetable ──
    rr(cv,12,500,W-12,578,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,24,510,"Attendance This Week",col)
    att_by_day={"M":0,"T":0,"W":0,"Th":0,"F":0}
    att_count_by_day={"M":0,"T":0,"W":0,"Th":0,"F":0}
    day_keys={"Monday":"M","Tuesday":"T","Wednesday":"W","Thursday":"Th","Friday":"F"}
    for tt_name,day,ts,room in tt_rows:
        dk=day_keys.get(day,"")
        if dk:
            att_count_by_day[dk]+=1
    for i,(day,_) in enumerate([("M",0),("T",0),("W",0),("Th",0),("F",0)]):
        pct2 = 0.85 if i!=1 else 0.60
        bx=24+i*46; bh2=int(pct2*36); by2=566
        rr(cv,bx,by2-bh2,bx+34,by2,rd=4,
           fill=(col if pct2>=0.8 else ORANGE),outline="")
        cv.create_text(bx+17,by2+9,text=day,font=("Helvetica",8),fill=DIM)

    build_footer(frame)


# ══════════════════════════════════════════════════════════════
#  SCREEN — ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════

def show_admin():
    _clear()
    frame=tk.Frame(container,bg=BG)
    frame.pack(expand=True,fill="both")
    _current[0]=frame
    col=LIME; fg=LIME_FG

    build_topbar(frame,col,["Dashboard","Courses","Timetable","Admin"],
                 back_cmd=show_login)
    body=tk.Frame(frame,bg=BG); body.pack(expand=True,fill="both")

    build_sidebar(body,"Admin","⚙️",col,[
        ("🏠","Overview",       show_admin),
        ("👤","Profile",        lambda:show_profile_popup(col)),
        ("✅","Attendance",     lambda:show_all_attendance_popup()),
        ("🎓","GPA Tools",      lambda:show_gpa_tools_popup()),
        ("🔔","Notifications",  lambda:show_notifications_popup(col)),
    ])

    cv,W,H=build_main_canvas(body,col)

    # Greeting
    rr(cv,12,10,W-12,58,rd=12,fill=CARD,outline=col,width=1)
    soft_glow(cv,38,34,14,col,layers=4,strength=0.18)
    cv.create_text(20,34,text="👋",font=("Arial",18),anchor="w")
    cv.create_text(50,24,text=f"Welcome, {session['name']}",
                   font=("Helvetica",13,"bold"),fill=WHITE,anchor="w")
    cv.create_text(50,44,text="Administrator Portal  ·  Academic Year 2024/25",
                   font=("Helvetica",9),fill=DIM,anchor="w")
    cv.create_text(W-16,34,text="System status: ● Online",
                   font=("Helvetica",9),fill=col,anchor="e")

    # Live stats from DB
    students,teachers,courses,att=db_get_stats()
    stat_block(cv, 12, 72,140,88,str(students),"Students",col,"enrolled")
    stat_block(cv,160, 72,140,88,str(teachers),"Teachers",col,"active")
    stat_block(cv,308, 72,140,88,str(courses), "Courses", col,"running")
    stat_block(cv,456, 72,140,88,f"{att}%",    "Attendance",col,"overall")

    # Admin Controls — all wired to real functions
    rr(cv,604,72,W-12,160,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,618,80,"Admin Controls",col)
    pill_btn(cv,618,102,148,30,"Manage Users",   col,fg=fg,cmd=show_manage_users)
    pill_btn(cv,776,102,148,30,"Manage Courses", col,fg=fg,cmd=show_manage_courses)
    pill_btn(cv,618,140,148,30,"Edit Timetable", col,fg=fg,cmd=show_manage_timetable)
    pill_btn(cv,776,140,148,30,"Notifications",  col,fg=fg,
             cmd=lambda:show_notifications_popup(col))

    # System stats — live from DB
    rr(cv,12,172,434,510,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,24,182,"System Statistics",col)
    all_users = db_get_all_users()
    total = len(all_users)
    stats_data=[
        ("👥","Total Students",   students, students/max(total,1)),
        ("👨‍🏫","Total Teachers",  teachers, teachers/max(total,1)),
        ("📚","Active Courses",   courses,  min(courses/30,1.0)),
        ("✅","Attendance Rate",  None,     att/100),
        ("🎓","Registered Users", total,    min(total/20,1.0)),
    ]
    for i,(ico,lbl2,count,pct) in enumerate(stats_data):
        ry=206+i*56
        cv.create_text(24,ry+12,text=ico,font=("Arial",14),anchor="w")
        cv.create_text(50,ry+6, text=lbl2,
                       font=("Helvetica",9,"bold"),fill=WHITE,anchor="w")
        val=f"{att}%" if lbl2=="Attendance Rate" else str(count)
        cv.create_text(418,ry+6,text=val,
                       font=("Helvetica",13,"bold"),fill=col,anchor="e")
        rr(cv,50,ry+22,418,ry+36,rd=7,fill=BORDER,outline="")
        fw=int((418-50)*pct)
        if fw>4: rr(cv,50,ry+22,50+fw,ry+36,rd=7,fill=col,outline="")
        if fw>4:
            cv.create_rectangle(50,ry+22,50+fw,ry+29,
                                fill=r2h(lerp(h2r(col),(255,255,255),0.16)),
                                outline="")

    # Timetable overview — card must be tall enough for grid (28+5×26=158px content)
    rr(cv,444,172,W-12,360,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,456,182,"Timetable Overview",col)
    tt_all=db_get_timetable()
    grid={t:["","","","",""] for t in ["09:00","10:00","11:00","12:00","13:00"]}
    day_idx2={"Monday":0,"Tuesday":1,"Wednesday":2,"Thursday":3,"Friday":4}
    for name,day,tslot,room in tt_all:
        if tslot in grid and day in day_idx2:
            if not grid[tslot][day_idx2[day]]:
                grid[tslot][day_idx2[day]]=name[:7]
    grid_rows=[(t,)+tuple(v) for t,v in grid.items()]
    # height=158 fits all 5 rows (28 header + 5×26)
    timetable_grid(cv,450,202,W-12-450-4,158,col,grid_rows)

    # Course registry from DB — repositioned below timetable with gap
    rr(cv,444,372,W-12,540,rd=12,fill=CARD,outline=BORDER,width=1)
    sec_hdr(cv,456,382,"Course Registry",col)
    for i,row in enumerate(db_get_courses()[:4]):
        cid,code,name,teacher,cap,enrolled=row
        ry=404+i*32
        rr(cv,456,ry,W-24,ry+26,rd=8,
           fill=r2h(lerp(h2r(CARD),h2r(col),0.07)),outline=BORDER,width=1)
        cv.create_text(470,ry+13,text=f"{code}  {name[:26]}",
                       font=("Helvetica",9),fill=WHITE,anchor="w")
        rr(cv,W-78,ry+3,W-34,ry+23,rd=10,fill=col,outline="")
        cv.create_text(W-56,ry+13,text=f"{enrolled} 👤",
                       font=("Helvetica",8,"bold"),fill=fg)

    build_footer(frame)


# ══════════════════════════════════════════════════════════════
#  BOOT
# ══════════════════════════════════════════════════════════════

db_init()
show_login()
root.mainloop()
