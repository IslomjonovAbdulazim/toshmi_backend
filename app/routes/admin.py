# app/routes/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_admin
from app.schemas import *
from app.crud import *

router = APIRouter()


# STUDENT MANAGEMENT
@router.post("/students", response_model=StudentResponse)
def create_student_endpoint(student: StudentCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_student(db, student)


@router.get("/students", response_model=List[StudentResponse])
def get_students_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_students(db)


@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student_endpoint(student_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    student = get_student(db, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    return student


@router.delete("/students/{student_id}")
def delete_student_endpoint(student_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    if delete_student(db, student_id):
        return {"deleted": True}
    raise HTTPException(404, "Student not found")


# PARENT MANAGEMENT
@router.post("/parents", response_model=ParentResponse)
def create_parent_endpoint(parent: ParentCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_parent(db, parent)


@router.get("/parents", response_model=List[ParentResponse])
def get_parents_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_parents(db)


@router.get("/parents/{parent_id}", response_model=ParentResponse)
def get_parent_endpoint(parent_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    parent = get_parent(db, parent_id)
    if not parent:
        raise HTTPException(404, "Parent not found")
    return parent


@router.delete("/parents/{parent_id}")
def delete_parent_endpoint(parent_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    if delete_parent(db, parent_id):
        return {"deleted": True}
    raise HTTPException(404, "Parent not found")


# TEACHER MANAGEMENT
@router.post("/teachers", response_model=TeacherResponse)
def create_teacher_endpoint(teacher: TeacherCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_teacher(db, teacher)


@router.get("/teachers", response_model=List[TeacherResponse])
def get_teachers_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_teachers(db)


@router.get("/teachers/{teacher_id}", response_model=TeacherResponse)
def get_teacher_endpoint(teacher_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    teacher = get_teacher(db, teacher_id)
    if not teacher:
        raise HTTPException(404, "Teacher not found")
    return teacher


@router.delete("/teachers/{teacher_id}")
def delete_teacher_endpoint(teacher_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    if delete_teacher(db, teacher_id):
        return {"deleted": True}
    raise HTTPException(404, "Teacher not found")


# GROUP MANAGEMENT
@router.post("/groups", response_model=GroupResponse)
def create_group_endpoint(group: GroupCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_group(db, group)


@router.get("/groups", response_model=List[GroupResponse])
def get_groups_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_groups(db)


@router.get("/groups/{group_id}", response_model=GroupResponse)
def get_group_endpoint(group_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    group = get_group(db, group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    return group


@router.delete("/groups/{group_id}")
def delete_group_endpoint(group_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    group = get_group(db, group_id)
    if not group:
        raise HTTPException(404, "Group not found")
    db.delete(group)
    db.commit()
    return {"deleted": True}


# SUBJECT MANAGEMENT
@router.post("/subjects", response_model=SubjectResponse)
def create_subject_endpoint(subject: SubjectCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_subject(db, subject)


@router.get("/subjects", response_model=List[SubjectResponse])
def get_subjects_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_subjects(db)


@router.delete("/subjects/{subject_id}")
def delete_subject_endpoint(subject_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    from app.models import Subject
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(404, "Subject not found")
    db.delete(subject)
    db.commit()
    return {"deleted": True}


# GROUP-SUBJECT MANAGEMENT
@router.post("/group-subjects", response_model=GroupSubjectResponse)
def create_group_subject_endpoint(group_subject: GroupSubjectCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_group_subject(db, group_subject)


@router.get("/group-subjects", response_model=List[GroupSubjectResponse])
def get_group_subjects_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_group_subjects(db)


@router.delete("/group-subjects/{group_subject_id}")
def delete_group_subject_endpoint(group_subject_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    result = delete_group_subject(db, group_subject_id)
    return {"deleted": result}


# PAYMENT MANAGEMENT
@router.post("/payments", response_model=PaymentResponse)
def create_payment_endpoint(payment: PaymentCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_payment(db, payment)


@router.patch("/payments/{payment_id}")
def update_payment_endpoint(
        payment_id: str,
        is_fully_paid: bool,
        comment: str = None,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    return update_payment(db, payment_id, is_fully_paid, comment)


@router.get("/payments")
def get_payments_endpoint(
        month: int = None,
        year: int = None,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    if month and year:
        return get_payments_by_month_year(db, month, year)
    return []


# NEWS MANAGEMENT
@router.post("/news", response_model=NewsResponse)
def create_news_endpoint(news: NewsCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_news(db, news)


@router.get("/news", response_model=List[NewsResponse])
def get_news_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_news(db)


@router.delete("/news/{news_id}")
def delete_news_endpoint(news_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    news = get_news(db, news_id)
    if not news:
        raise HTTPException(404, "News not found")
    db.delete(news)
    db.commit()
    return {"deleted": True}


# REPORTS (keeping these as requested)
@router.get("/reports/class")
def get_class_report_endpoint(group_id: str, subject_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_class_report(db, group_id, subject_id)


@router.get("/reports/payments")
def get_payment_report_endpoint(month: int, year: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_payment_report(db, month, year)


@router.get("/reports/overview")
def get_school_overview(db: Session = Depends(get_db), admin=Depends(require_admin)):
    from app.models import Student, User, Payment
    import datetime

    total_students = db.query(Student).count()
    total_teachers = db.query(User).filter(User.role == "teacher").count()
    total_parents = db.query(User).filter(User.role == "parent").count()

    current_month = datetime.datetime.now().month
    current_year = datetime.datetime.now().year
    monthly_payments = db.query(Payment).filter(
        Payment.month == current_month,
        Payment.year == current_year
    ).count()

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_parents": total_parents,
        "monthly_payments": monthly_payments
    }