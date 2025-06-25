from sqlalchemy.orm import Session
from app.models.models import Notification, Student, User


class NotificationService:

    @staticmethod
    def create_notification(db: Session, user_id: int, title: str, message: str, notification_type: str):
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type
        )
        db.add(notification)
        db.flush()
        return notification

    @staticmethod
    def notify_homework_created(db: Session, group_id: int, homework_title: str, due_date, subject_name: str):
        students = db.query(Student).filter(Student.group_id == group_id).all()
        for student in students:
            NotificationService.create_notification(
                db, student.user_id,
                "Yangi vazifa",
                f"{subject_name} fanidan '{homework_title}' vazifasi berildi. Muddati: {due_date.strftime('%d.%m.%Y %H:%M')}",
                "homework"
            )

    @staticmethod
    def notify_exam_created(db: Session, group_id: int, exam_title: str, exam_date, subject_name: str):
        students = db.query(Student).filter(Student.group_id == group_id).all()
        for student in students:
            NotificationService.create_notification(
                db, student.user_id,
                "Yangi imtihon",
                f"{subject_name} fanidan '{exam_title}' imtihoni belgilandi. Sana: {exam_date.strftime('%d.%m.%Y %H:%M')}",
                "exam"
            )

    @staticmethod
    def notify_homework_graded(db: Session, student_id: int, homework_title: str, points: int, max_points: int,
                               subject_name: str):
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            NotificationService.create_notification(
                db, student.user_id,
                "Vazifa baholandi",
                f"{subject_name} fanidan '{homework_title}' vazifangiz baholandi. Ball: {points}/{max_points}",
                "grade"
            )

            if student.parent_phone:
                parent = db.query(User).filter(User.phone == student.parent_phone, User.role == "parent").first()
                if parent:
                    NotificationService.create_notification(
                        db, parent.id,
                        "Farzandingiz vazifasi baholandi",
                        f"{student.user.full_name}ning {subject_name} fanidan '{homework_title}' vazifasi baholandi. Ball: {points}/{max_points}",
                        "grade"
                    )

    @staticmethod
    def notify_exam_graded(db: Session, student_id: int, exam_title: str, points: int, max_points: int,
                           subject_name: str):
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            NotificationService.create_notification(
                db, student.user_id,
                "Imtihon baholandi",
                f"{subject_name} fanidan '{exam_title}' imtihoni baholandi. Ball: {points}/{max_points}",
                "grade"
            )

            if student.parent_phone:
                parent = db.query(User).filter(User.phone == student.parent_phone, User.role == "parent").first()
                if parent:
                    NotificationService.create_notification(
                        db, parent.id,
                        "Farzandingiz imtihoni baholandi",
                        f"{student.user.full_name}ning {subject_name} fanidan '{exam_title}' imtihoni baholandi. Ball: {points}/{max_points}",
                        "grade"
                    )

    @staticmethod
    def notify_attendance_marked(db: Session, student_id: int, date, status: str, subject_name: str):
        student = db.query(Student).filter(Student.id == student_id).first()
        if student and status in ["absent", "late"]:
            status_uz = {"absent": "yo'q", "late": "kech kelgan"}[status]
            NotificationService.create_notification(
                db, student.user_id,
                "Davomat belgilandi",
                f"{date.strftime('%d.%m.%Y')} kuni {subject_name} darsida {status_uz} deb belgilandi",
                "attendance"
            )

            if student.parent_phone:
                parent = db.query(User).filter(User.phone == student.parent_phone, User.role == "parent").first()
                if parent:
                    NotificationService.create_notification(
                        db, parent.id,
                        "Farzandingiz davomati",
                        f"{student.user.full_name} {date.strftime('%d.%m.%Y')} kuni {subject_name} darsida {status_uz} deb belgilandi",
                        "attendance"
                    )

    @staticmethod
    def notify_payment_recorded(db: Session, student_id: int, amount: int, payment_date, description: str):
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            NotificationService.create_notification(
                db, student.user_id,
                "To'lov qabul qilindi",
                f"{payment_date.strftime('%d.%m.%Y')} kuni {amount:,} so'm to'lov qabul qilindi. {description}",
                "payment"
            )

            if student.parent_phone:
                parent = db.query(User).filter(User.phone == student.parent_phone, User.role == "parent").first()
                if parent:
                    NotificationService.create_notification(
                        db, parent.id,
                        "To'lov qabul qilindi",
                        f"{student.user.full_name} uchun {payment_date.strftime('%d.%m.%Y')} kuni {amount:,} so'm to'lov qabul qilindi. {description}",
                        "payment"
                    )

    @staticmethod
    def notify_file_uploaded(db: Session, related_id: int, file_type: str, filename: str):
        if file_type == "homework":
            from app.models.models import Homework
            homework = db.query(Homework).filter(Homework.id == related_id).first()
            if homework:
                students = db.query(Student).filter(Student.group_id == homework.group_subject.group_id).all()
                for student in students:
                    NotificationService.create_notification(
                        db, student.user_id,
                        "Vazifa fayli yuklandi",
                        f"'{homework.title}' vazifasiga fayl qo'shildi: {filename}",
                        "homework"
                    )

        elif file_type == "exam":
            from app.models.models import Exam
            exam = db.query(Exam).filter(Exam.id == related_id).first()
            if exam:
                students = db.query(Student).filter(Student.group_id == exam.group_subject.group_id).all()
                for student in students:
                    NotificationService.create_notification(
                        db, student.user_id,
                        "Imtihon fayli yuklandi",
                        f"'{exam.title}' imtihoniga fayl qo'shildi: {filename}",
                        "exam"
                    )