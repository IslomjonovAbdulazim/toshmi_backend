from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models.models import User, Student, Group, Subject, GroupSubject, PaymentRecord, MonthlyPayment, News, \
    Schedule, Homework, Exam
from app.core.security import require_role, hash_password

router = APIRouter()


class CreateUserRequest(BaseModel):
    phone: str
    password: str
    first_name: str
    last_name: str


class CreateStudentRequest(CreateUserRequest):
    group_id: int
    parent_phone: str
    graduation_year: int


class CreateGroupRequest(BaseModel):
    name: str
    academic_year: str


class CreateSubjectRequest(BaseModel):
    name: str
    code: str


class AssignTeacherRequest(BaseModel):
    group_id: int
    subject_id: int
    teacher_id: int


class PaymentRequest(BaseModel):
    student_id: int
    amount: int
    payment_date: date
    payment_method: str = "cash"
    description: str = ""


class MonthlyPaymentRequest(BaseModel):
    student_id: int
    month: int
    year: int
    is_completed: bool
    due_date: date


class NewsRequest(BaseModel):
    title: str
    content: str
    external_links: List[str] = []
    is_published: bool = True


class ScheduleRequest(BaseModel):
    group_subject_id: int
    day: int
    start_time: str
    end_time: str
    room: str


@router.post("/students")
def create_student(request: CreateStudentRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    user = User(
        phone=request.phone,
        password_hash=hash_password(request.password),
        role="student",
        first_name=request.first_name,
        last_name=request.last_name
    )
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        group_id=request.group_id,
        parent_phone=request.parent_phone,
        graduation_year=request.graduation_year
    )
    db.add(student)
    db.commit()
    return {"message": "Student created", "id": student.id}


@router.post("/teachers")
def create_teacher(request: CreateUserRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    user = User(
        phone=request.phone,
        password_hash=hash_password(request.password),
        role="teacher",
        first_name=request.first_name,
        last_name=request.last_name
    )
    db.add(user)
    db.commit()
    return {"message": "Teacher created", "id": user.id}


@router.post("/parents")
def create_parent(request: CreateUserRequest, current_user: User = Depends(require_role(["admin"])),
                  db: Session = Depends(get_db)):
    user = User(
        phone=request.phone,
        password_hash=hash_password(request.password),
        role="parent",
        first_name=request.first_name,
        last_name=request.last_name
    )
    db.add(user)
    db.commit()
    return {"message": "Parent created", "id": user.id}


@router.post("/groups")
def create_group(request: CreateGroupRequest, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    group = Group(name=request.name, academic_year=request.academic_year)
    db.add(group)
    db.commit()
    return {"message": "Group created", "id": group.id}


@router.post("/subjects")
def create_subject(request: CreateSubjectRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    subject = Subject(name=request.name, code=request.code)
    db.add(subject)
    db.commit()
    return {"message": "Subject created", "id": subject.id}


@router.post("/assign-teacher")
def assign_teacher(request: AssignTeacherRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    assignment = GroupSubject(
        group_id=request.group_id,
        subject_id=request.subject_id,
        teacher_id=request.teacher_id
    )
    db.add(assignment)
    db.commit()
    return {"message": "Teacher assigned"}


@router.post("/payments")
def record_payment(request: PaymentRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    payment = PaymentRecord(
        student_id=request.student_id,
        amount=request.amount,
        payment_date=request.payment_date,
        payment_method=request.payment_method,
        description=request.description
    )
    db.add(payment)
    db.commit()
    return {"message": "Payment recorded", "id": payment.id}


@router.put("/monthly-payment-status")
def update_monthly_payment(request: MonthlyPaymentRequest, current_user: User = Depends(require_role(["admin"])),
                           db: Session = Depends(get_db)):
    monthly = db.query(MonthlyPayment).filter(
        MonthlyPayment.student_id == request.student_id,
        MonthlyPayment.month == request.month,
        MonthlyPayment.year == request.year
    ).first()

    if not monthly:
        monthly = MonthlyPayment(
            student_id=request.student_id,
            month=request.month,
            year=request.year,
            due_date=request.due_date
        )
        db.add(monthly)

    monthly.is_completed = request.is_completed
    db.commit()
    return {"message": "Monthly payment updated"}


@router.post("/news")
def create_news(request: NewsRequest, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    news = News(
        title=request.title,
        content=request.content,
        author_id=current_user.id,
        external_links=request.external_links,
        is_published=request.is_published
    )
    db.add(news)
    db.commit()
    return {"message": "News created", "id": news.id}


@router.post("/schedule")
def create_schedule(request: ScheduleRequest, current_user: User = Depends(require_role(["admin"])),
                    db: Session = Depends(get_db)):
    from datetime import time
    schedule = Schedule(
        group_subject_id=request.group_subject_id,
        day=request.day,
        start_time=time.fromisoformat(request.start_time),
        end_time=time.fromisoformat(request.end_time),
        room=request.room
    )
    db.add(schedule)
    db.commit()
    return {"message": "Schedule created"}


@router.get("/students")
def list_students(skip: int = 0, limit: int = 100, current_user: User = Depends(require_role(["admin"])),
                  db: Session = Depends(get_db)):
    students = db.query(Student).join(User).offset(skip).limit(limit).all()
    return [
        {
            "id": s.id,
            "name": f"{s.user.first_name} {s.user.last_name}",
            "phone": s.user.phone,
            "group_id": s.group_id,
            "parent_phone": s.parent_phone
        } for s in students
    ]


@router.get("/teachers")
def list_teachers(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    teachers = db.query(User).filter(User.role == "teacher").all()
    return [
        {
            "id": t.id,
            "name": f"{t.first_name} {t.last_name}",
            "phone": t.phone
        } for t in teachers
    ]