from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_admin
from app.schemas.schemas import *
from app.crud import *

router = APIRouter()


# USER MANAGEMENT
@router.post("/users", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_user(db, user)


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(user_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("/users", response_model=List[UserResponse])
def get_users_by_role_endpoint(
        role: str = None,
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    if role:
        users = get_users_by_role(db, role)
    else:
        users = get_users_by_role(db, "student")

    # Simple pagination
    start = (page - 1) * size
    end = start + size
    return users[start:end]


@router.patch("/users/{user_id}")
def update_user_profile_endpoint(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db),
                                 admin=Depends(require_admin)):
    return update_user_profile(db, user_id, user_update)


@router.delete("/users/{user_id}")
def delete_user_endpoint(user_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    db.delete(user)
    db.commit()
    return {"deleted": True}


# PASSWORD MANAGEMENT
@router.patch("/users/{user_id}/password")
def admin_change_user_password(
        user_id: str,
        password_data: AdminPasswordChange,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    from app.utils.password import hash_password

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    user.password_hash = hash_password(password_data.new_password)
    db.commit()

    return {"message": f"Password changed for {user.full_name}"}


@router.post("/users/{user_id}/reset-password")
def admin_reset_user_password(
        user_id: str,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    import secrets
    from app.utils.password import hash_password

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    temp_password = secrets.token_urlsafe(8)
    user.password_hash = hash_password(temp_password)
    db.commit()

    return {
        "message": f"Temporary password generated for {user.full_name}",
        "temporary_password": temp_password
    }


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
def create_group_subject_endpoint(group_subject: GroupSubjectCreate, db: Session = Depends(get_db),
                                  admin=Depends(require_admin)):
    return create_group_subject(db, group_subject)


@router.get("/group-subjects", response_model=List[GroupSubjectResponse])
def get_group_subjects_endpoint(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_all_group_subjects(db)


@router.patch("/group-subjects/{group_subject_id}", response_model=GroupSubjectResponse)
def update_group_subject_endpoint(group_subject_id: str, group_subject: GroupSubjectCreate,
                                  db: Session = Depends(get_db), admin=Depends(require_admin)):
    return update_group_subject(db, group_subject_id, group_subject)


@router.delete("/group-subjects/{group_subject_id}")
def delete_group_subject_endpoint(group_subject_id: str, db: Session = Depends(get_db), admin=Depends(require_admin)):
    result = delete_group_subject(db, group_subject_id)
    return {"deleted": result}


# STUDENT MANAGEMENT
@router.post("/students", response_model=StudentResponse)
def create_student_endpoint(student: StudentCreate, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return create_student(db, student)


@router.post("/students/enroll")
def enroll_student_endpoint(enrollment: StudentEnrollment, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return enroll_student_in_group(db, enrollment.student_id, enrollment.group_id)


@router.post("/students/transfer")
def transfer_students_endpoint(transfer: GroupTransfer, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return bulk_transfer_students(db, transfer.student_ids, transfer.from_group_id, transfer.to_group_id)


@router.post("/students/bulk-create")
def bulk_create_students_endpoint(bulk_data: BulkStudentCreate, db: Session = Depends(get_db),
                                  admin=Depends(require_admin)):
    return bulk_create_students(db, bulk_data.students)


@router.get("/students/search")
def search_students_endpoint(
        name: str = None,
        group_id: str = None,
        graduation_year: int = None,
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    return search_students(db, name, group_id, graduation_year)


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


# REPORTS
@router.get("/reports/class")
def get_class_report_endpoint(group_id: str, subject_id: str, db: Session = Depends(get_db),
                              admin=Depends(require_admin)):
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