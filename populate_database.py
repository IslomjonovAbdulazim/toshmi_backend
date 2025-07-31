#!/usr/bin/env python3
"""
Database Population Script
Creates sample data for all tables in the education management system
"""

import psycopg2
import json
from datetime import datetime, date, time, timedelta

DATABASE_URL = "postgresql://postgres:tehVJTDHftcSszXtnggXfdYGsXPIHTwC@gondola.proxy.rlwy.net:54324/railway"

def create_all_tables(cursor):
    """Create all tables if they don't exist"""
    print("🏗️  Creating all database tables...")
    
    # Files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            filename VARCHAR NOT NULL,
            file_path VARCHAR NOT NULL,
            file_size INTEGER,
            uploaded_by INTEGER REFERENCES users(id),
            upload_date TIMESTAMP DEFAULT NOW(),
            related_id INTEGER,
            file_type VARCHAR
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);")
    
    # Subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            code VARCHAR UNIQUE NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_name ON subjects(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects(code);")
    
    # Group_subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_subjects (
            id SERIAL PRIMARY KEY,
            group_id INTEGER REFERENCES groups(id),
            subject_id INTEGER REFERENCES subjects(id),
            teacher_id INTEGER REFERENCES users(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_subjects_group ON group_subjects(group_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_subjects_subject ON group_subjects(subject_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_subjects_teacher ON group_subjects(teacher_id);")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_group_subject_unique ON group_subjects(group_id, subject_id);")
    
    # Schedules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id SERIAL PRIMARY KEY,
            group_subject_id INTEGER REFERENCES group_subjects(id),
            day INTEGER NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            room VARCHAR
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_group_subject ON schedules(group_subject_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedule_day_time ON schedules(day, start_time);")
    
    # Homework table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework (
            id SERIAL PRIMARY KEY,
            group_subject_id INTEGER REFERENCES group_subjects(id),
            title VARCHAR NOT NULL,
            description TEXT,
            due_date TIMESTAMP,
            max_points INTEGER DEFAULT 100,
            external_links JSON DEFAULT '[]',
            document_ids JSON DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_homework_group_subject ON homework(group_subject_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_homework_title ON homework(title);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_homework_due_date ON homework(due_date, group_subject_id);")
    
    # Exams table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id SERIAL PRIMARY KEY,
            group_subject_id INTEGER REFERENCES group_subjects(id),
            title VARCHAR NOT NULL,
            description TEXT,
            exam_date TIMESTAMP,
            max_points INTEGER DEFAULT 100,
            external_links JSON DEFAULT '[]',
            document_ids JSON DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exams_group_subject ON exams(group_subject_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exams_title ON exams(title);")
    
    # Homework_grades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS homework_grades (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            homework_id INTEGER REFERENCES homework(id),
            points INTEGER,
            comment TEXT DEFAULT '',
            graded_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_homework_grades_student ON homework_grades(student_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_homework_grades_homework ON homework_grades(homework_id);")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_homework_grade_unique ON homework_grades(student_id, homework_id);")
    
    # Exam_grades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam_grades (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            exam_id INTEGER REFERENCES exams(id),
            points INTEGER,
            comment TEXT DEFAULT '',
            graded_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_grades_student ON exam_grades(student_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_grades_exam ON exam_grades(exam_id);")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_exam_grade_unique ON exam_grades(student_id, exam_id);")
    
    # Attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            group_subject_id INTEGER REFERENCES group_subjects(id),
            date DATE NOT NULL,
            status VARCHAR NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_group_subject ON attendance(group_subject_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_attendance_unique ON attendance(student_id, group_subject_id, date);")
    
    # Payment_records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_records (
            id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(id),
            amount INTEGER NOT NULL,
            payment_date DATE NOT NULL,
            payment_method VARCHAR DEFAULT 'cash',
            description VARCHAR DEFAULT '',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_records_student ON payment_records(student_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_records_date ON payment_records(payment_date);")
    
    # News table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            content TEXT,
            author_id INTEGER REFERENCES users(id),
            external_links JSON DEFAULT '[]',
            image_ids JSON DEFAULT '[]',
            created_at TIMESTAMP DEFAULT NOW(),
            is_published BOOLEAN DEFAULT TRUE
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_title ON news(title);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_published ON news(is_published);")
    
    # Notifications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR NOT NULL,
            message TEXT,
            type VARCHAR,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_user_read ON notifications(user_id, is_read);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notification_type_date ON notifications(type, created_at);")
    
    print("✅ All tables created successfully!")

def populate_subjects(cursor):
    """Create sample subjects"""
    print("📚 Creating subjects...")
    
    subjects = [
        ("Matematika", "MATH"),
        ("Ingliz tili", "ENG"),
        ("Uzbek tili", "UZB"),
        ("Fizika", "PHY"),
        ("Kimyo", "CHEM"),
        ("Biologiya", "BIO"),
        ("Tarix", "HIST"),
        ("Geografiya", "GEO")
    ]
    
    subject_ids = []
    for name, code in subjects:
        cursor.execute("SELECT id FROM subjects WHERE code = %s", (code,))
        existing = cursor.fetchone()
        
        if existing:
            subject_ids.append(existing[0])
            continue
            
        cursor.execute("""
            INSERT INTO subjects (name, code) VALUES (%s, %s) RETURNING id
        """, (name, code))
        subject_id = cursor.fetchone()[0]
        subject_ids.append(subject_id)
        print(f"✅ Created subject: {name} ({code})")
    
    return subject_ids

def populate_group_subjects(cursor, group_id, subject_ids, teacher_id):
    """Assign subjects to group with teacher"""
    print("🎓 Creating group-subject assignments...")
    
    group_subject_ids = []
    for subject_id in subject_ids[:4]:  # Assign first 4 subjects
        cursor.execute("""
            SELECT id FROM group_subjects 
            WHERE group_id = %s AND subject_id = %s
        """, (group_id, subject_id))
        existing = cursor.fetchone()
        
        if existing:
            group_subject_ids.append(existing[0])
            continue
            
        cursor.execute("""
            INSERT INTO group_subjects (group_id, subject_id, teacher_id)
            VALUES (%s, %s, %s) RETURNING id
        """, (group_id, subject_id, teacher_id))
        gs_id = cursor.fetchone()[0]
        group_subject_ids.append(gs_id)
        print(f"✅ Assigned subject {subject_id} to group {group_id}")
    
    return group_subject_ids

def populate_schedules(cursor, group_subject_ids):
    """Create class schedules"""
    print("⏰ Creating schedules...")
    
    schedule_data = [
        (group_subject_ids[0], 1, time(9, 0), time(9, 45), "Room 101"),  # Monday Math
        (group_subject_ids[1], 1, time(10, 0), time(10, 45), "Room 102"), # Monday English
        (group_subject_ids[2], 2, time(9, 0), time(9, 45), "Room 103"),  # Tuesday Uzbek
        (group_subject_ids[3], 2, time(10, 0), time(10, 45), "Room 104"), # Tuesday Physics
    ]
    
    for gs_id, day, start_time, end_time, room in schedule_data:
        cursor.execute("""
            SELECT id FROM schedules 
            WHERE group_subject_id = %s AND day = %s AND start_time = %s
        """, (gs_id, day, start_time))
        existing = cursor.fetchone()
        
        if existing:
            continue
            
        cursor.execute("""
            INSERT INTO schedules (group_subject_id, day, start_time, end_time, room)
            VALUES (%s, %s, %s, %s, %s)
        """, (gs_id, day, start_time, end_time, room))
        print(f"✅ Created schedule for group_subject {gs_id} on day {day}")

def populate_homework(cursor, group_subject_ids):
    """Create homework assignments"""
    print("📝 Creating homework...")
    
    homework_list = [
        (group_subject_ids[0], "Algebra masalalar", "1-10 sahifadagi barcha masalalarni yeching", datetime.now() + timedelta(days=7), 100),
        (group_subject_ids[1], "English Essay", "Write an essay about your favorite book (200 words)", datetime.now() + timedelta(days=5), 50),
        (group_subject_ids[2], "Adabiyot tahlili", "Hamza asarlarini o'qib tahlil qiling", datetime.now() + timedelta(days=10), 75),
    ]
    
    homework_ids = []
    for gs_id, title, description, due_date, max_points in homework_list:
        cursor.execute("SELECT id FROM homework WHERE title = %s", (title,))
        existing = cursor.fetchone()
        
        if existing:
            homework_ids.append(existing[0])
            continue
            
        cursor.execute("""
            INSERT INTO homework (group_subject_id, title, description, due_date, max_points, created_at)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (gs_id, title, description, due_date, max_points, datetime.now()))
        hw_id = cursor.fetchone()[0]
        homework_ids.append(hw_id)
        print(f"✅ Created homework: {title}")
    
    return homework_ids

def populate_exams(cursor, group_subject_ids):
    """Create exams"""
    print("📊 Creating exams...")
    
    exam_list = [
        (group_subject_ids[0], "Matematika yarim yillik imtihoni", "Algebra va geometriya bo'yicha", datetime.now() + timedelta(days=30), 100),
        (group_subject_ids[1], "English Midterm", "Grammar and vocabulary test", datetime.now() + timedelta(days=25), 100),
    ]
    
    exam_ids = []
    for gs_id, title, description, exam_date, max_points in exam_list:
        cursor.execute("SELECT id FROM exams WHERE title = %s", (title,))
        existing = cursor.fetchone()
        
        if existing:
            exam_ids.append(existing[0])
            continue
            
        cursor.execute("""
            INSERT INTO exams (group_subject_id, title, description, exam_date, max_points, created_at)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """, (gs_id, title, description, exam_date, max_points, datetime.now()))
        exam_id = cursor.fetchone()[0]
        exam_ids.append(exam_id)
        print(f"✅ Created exam: {title}")
    
    return exam_ids

def populate_grades(cursor, student_id, homework_ids, exam_ids):
    """Create grades for homework and exams"""
    print("🎯 Creating grades...")
    
    # Homework grades
    for hw_id in homework_ids:
        cursor.execute("""
            SELECT id FROM homework_grades WHERE student_id = %s AND homework_id = %s
        """, (student_id, hw_id))
        existing = cursor.fetchone()
        
        if existing:
            continue
            
        cursor.execute("""
            INSERT INTO homework_grades (student_id, homework_id, points, comment, graded_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, hw_id, 85, "Yaxshi ish!", datetime.now()))
        print(f"✅ Created homework grade for homework {hw_id}")
    
    # Exam grades
    for exam_id in exam_ids:
        cursor.execute("""
            SELECT id FROM exam_grades WHERE student_id = %s AND exam_id = %s
        """, (student_id, exam_id))
        existing = cursor.fetchone()
        
        if existing:
            continue
            
        cursor.execute("""
            INSERT INTO exam_grades (student_id, exam_id, points, comment, graded_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, exam_id, 92, "A'lo natija!", datetime.now()))
        print(f"✅ Created exam grade for exam {exam_id}")

def populate_attendance(cursor, student_id, group_subject_ids):
    """Create attendance records"""
    print("📅 Creating attendance records...")
    
    # Create attendance for the last 7 days
    for i in range(7):
        attendance_date = date.today() - timedelta(days=i)
        
        for gs_id in group_subject_ids[:2]:  # First 2 subjects
            cursor.execute("""
                SELECT id FROM attendance 
                WHERE student_id = %s AND group_subject_id = %s AND date = %s
            """, (student_id, gs_id, attendance_date))
            existing = cursor.fetchone()
            
            if existing:
                continue
                
            status = "present" if i < 5 else "absent"  # Student was absent 2 days ago
            cursor.execute("""
                INSERT INTO attendance (student_id, group_subject_id, date, status)
                VALUES (%s, %s, %s, %s)
            """, (student_id, gs_id, attendance_date, status))
            print(f"✅ Created attendance: {status} for {attendance_date}")

def populate_payments(cursor, student_id):
    """Create payment records"""
    print("💰 Creating payment records...")
    
    payments = [
        (500000, date.today() - timedelta(days=30), "cash", "Oktyabr oyi to'lovi"),
        (500000, date.today() - timedelta(days=60), "card", "Sentyabr oyi to'lovi"),
        (500000, date.today() - timedelta(days=90), "cash", "Avgust oyi to'lovi"),
    ]
    
    for amount, payment_date, method, description in payments:
        cursor.execute("""
            SELECT id FROM payment_records 
            WHERE student_id = %s AND payment_date = %s AND amount = %s
        """, (student_id, payment_date, amount))
        existing = cursor.fetchone()
        
        if existing:
            continue
            
        cursor.execute("""
            INSERT INTO payment_records (student_id, amount, payment_date, payment_method, description, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (student_id, amount, payment_date, method, description, datetime.now()))
        print(f"✅ Created payment: {amount} som for {payment_date}")

def populate_news(cursor, admin_id):
    """Create news articles"""
    print("📰 Creating news...")
    
    news_articles = [
        ("Yangi o'quv yili boshlanishi", "Hurmatli o'quvchilar va ota-onalar! Yangi 2024-2025 o'quv yili 1-sentyabrdan boshlanadi.", []),
        ("Olimpiada e'lon qilinishi", "Matematika olimpiadasi 15-noyabrda o'tkaziladi. Ishtirok etmoqchi bo'lganlar ro'yxatdan o'tishlari kerak.", []),
        ("Bayram tabrigi", "Mustaqillik kuni munosabati bilan barcha o'quvchi va o'qituvchilarni tabriklaymiz!", []),
    ]
    
    for title, content, external_links in news_articles:
        cursor.execute("SELECT id FROM news WHERE title = %s", (title,))
        existing = cursor.fetchone()
        
        if existing:
            continue
            
        cursor.execute("""
            INSERT INTO news (title, content, author_id, external_links, created_at, is_published)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, content, admin_id, json.dumps(external_links), datetime.now(), True))
        print(f"✅ Created news: {title}")

def populate_notifications(cursor, user_ids):
    """Create notifications for users"""
    print("🔔 Creating notifications...")
    
    notifications = [
        ("Yangi vazifa", "Matematika fanidan yangi uy vazifasi berildi", "homework", False),
        ("Imtihon eslatmasi", "Ingliz tili imtihoni 1 hafta qoldi", "exam", False),
        ("To'lov eslatmasi", "Noyabr oyi uchun to'lov muddati yetib keldi", "payment", True),
        ("Yangi xabar", "Maktab yangiliklari bo'limida yangi post", "news", True),
    ]
    
    for user_id in user_ids:
        for title, message, notif_type, is_read in notifications:
            cursor.execute("""
                SELECT id FROM notifications 
                WHERE user_id = %s AND title = %s AND type = %s
            """, (user_id, title, notif_type))
            existing = cursor.fetchone()
            
            if existing:
                continue
                
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, title, message, notif_type, is_read, datetime.now()))
            print(f"✅ Created notification for user {user_id}: {title}")

def populate_files(cursor, admin_id):
    """Create sample files"""
    print("📁 Creating file records...")
    
    files = [
        ("homework_math_1.pdf", "/uploads/homework/homework_math_1.pdf", 245760, "homework"),
        ("exam_english_midterm.docx", "/uploads/exams/exam_english_midterm.docx", 128540, "exam"),
        ("news_image_1.jpg", "/uploads/news/news_image_1.jpg", 892340, "news"),
        ("profile_photo.jpg", "/uploads/profiles/profile_photo.jpg", 445678, "profile"),
    ]
    
    for filename, file_path, file_size, file_type in files:
        cursor.execute("SELECT id FROM files WHERE filename = %s", (filename,))
        existing = cursor.fetchone()
        
        if existing:
            continue
            
        cursor.execute("""
            INSERT INTO files (filename, file_path, file_size, uploaded_by, upload_date, file_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (filename, file_path, file_size, admin_id, datetime.now(), file_type))
        print(f"✅ Created file: {filename}")

def main():
    print("🗄️  Database Population Script Starting...")
    print("=" * 60)
    
    try:
        # Connect to database
        print("🔗 Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Database connection successful!")
        
        # Create all tables
        create_all_tables(cursor)
        
        # Get existing user IDs
        cursor.execute("SELECT id FROM users WHERE role = 'teacher' LIMIT 1")
        teacher_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        admin_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM students LIMIT 1")
        student_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM groups WHERE name = '10-A'")
        group_id = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM users")
        all_user_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Found: teacher_id={teacher_id}, admin_id={admin_id}, student_id={student_id}, group_id={group_id}")
        
        # Populate all tables
        subject_ids = populate_subjects(cursor)
        group_subject_ids = populate_group_subjects(cursor, group_id, subject_ids, teacher_id)
        populate_schedules(cursor, group_subject_ids)
        homework_ids = populate_homework(cursor, group_subject_ids)
        exam_ids = populate_exams(cursor, group_subject_ids)
        populate_grades(cursor, student_id, homework_ids, exam_ids)
        populate_attendance(cursor, student_id, group_subject_ids)
        populate_payments(cursor, student_id)
        populate_news(cursor, admin_id)
        populate_notifications(cursor, all_user_ids)
        populate_files(cursor, admin_id)
        
        # Summary
        print("\n📊 DATABASE POPULATION SUMMARY")
        print("=" * 50)
        
        tables = [
            "users", "students", "groups", "subjects", "group_subjects", 
            "schedules", "homework", "exams", "homework_grades", "exam_grades",
            "attendance", "payment_records", "news", "notifications", "files"
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📋 {table}: {count} records")
        
        print("\n✅ Database population completed successfully!")
        print("🎉 All tables now have sample data!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
        
    finally:
        cursor.close()
        conn.close()
        print("\n🔐 Database connection closed.")
    
    return 0

if __name__ == "__main__":
    exit(main())