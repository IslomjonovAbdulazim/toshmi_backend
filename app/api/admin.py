from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time
from app.database import get_db
from app.models.models import User, Student, Group, Subject, GroupSubject, PaymentRecord, MonthlyPayment, News, Schedule
from app.core.security import require_role, hash_password

router = APIRouter()


class CreateUserRequest(BaseModel):
    phone: str
    password: str
    first_name: str
    last_name: str


class UpdateUserRequest(BaseModel):
    phone: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None


class CreateStudentRequest(CreateUserRequest):
    group_id: int
    parent_phone: str
    graduation_year: int


class UpdateStudentRequest(BaseModel):
    user_data: Optional[UpdateUserRequest] = None
    group_id: Optional[int] = None
    parent_phone: Optional[str] = None
    graduation_year: Optional[int] = None


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


def create_user(data: CreateUserRequest, role: str, db: Session):
    existing = db.query(User).filter(User.phone == data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    user = User(
        phone=data.phone,
        password_hash=hash_password(data.password),
        role=role,
        first_name=data.first_name,
        last_name=data.last_name
    )
    db.add(user)
    db.flush()
    return user


def update_user(user: User, data: UpdateUserRequest, db: Session):
    if data.phone and data.phone != user.phone:
        existing = db.query(User).filter(User.phone == data.phone, User.id != user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Phone number already exists")
        user.phone = data.phone

    if data.password:
        user.password_hash = hash_password(data.password)
    if data.first_name:
        user.first_name = data.first_name
    if data.last_name:
        user.last_name = data.last_name
    if data.is_active is not None:
        user.is_active = data.is_active


# STUDENT CRUD
@router.post("/students")
def create_student(request: CreateStudentRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    user = create_user(request, "student", db)

    student = Student(
        user_id=user.id,
        group_id=request.group_id,
        parent_phone=request.parent_phone,
        graduation_year=request.graduation_year
    )
    db.add(student)
    db.commit()
    return {"message": "Student created", "id": student.id, "user_id": user.id}


@router.get("/students")
def list_students(skip: int = 0, limit: int = 100, current_user: User = Depends(require_role(["admin"])),
                  db: Session = Depends(get_db)):
    students = db.query(Student).offset(skip).limit(limit).all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "name": s.user.full_name,
            "phone": s.user.phone,
            "group_name": s.group.name,
            "parent_phone": s.parent_phone,
            "graduation_year": s.graduation_year,
            "is_active": s.user.is_active
        } for s in students
    ]


@router.get("/students/{student_id}")
def get_student(student_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "id": student.id,
        "user_id": student.user_id,
        "name": student.user.full_name,
        "phone": student.user.phone,
        "group_id": student.group_id,
        "group_name": student.group.name,
        "parent_phone": student.parent_phone,
        "graduation_year": student.graduation_year,
        "is_active": student.user.is_active
    }


@router.put("/students/{student_id}")
def update_student(student_id: int, request: UpdateStudentRequest,
                   current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if request.user_data:
        update_user(student.user, request.user_data, db)

    if request.group_id:
        student.group_id = request.group_id
    if request.parent_phone:
        student.parent_phone = request.parent_phone
    if request.graduation_year:
        student.graduation_year = request.graduation_year

    db.commit()
    return {"message": "Student updated"}


@router.delete("/students/{student_id}")
def delete_student(student_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.user.is_active = False
    db.commit()
    return {"message": "Student deactivated"}


# TEACHER CRUD
@router.post("/teachers")
def create_teacher(request: CreateUserRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    user = create_user(request, "teacher", db)
    db.commit()
    return {"message": "Teacher created", "id": user.id}


@router.get("/teachers")
def list_teachers(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    teachers = db.query(User).filter(User.role == "teacher").all()
    return [
        {
            "id": t.id,
            "name": t.full_name,
            "phone": t.phone,
            "is_active": t.is_active
        } for t in teachers
    ]


@router.get("/teachers/{teacher_id}")
def get_teacher(teacher_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "id": teacher.id,
        "name": teacher.full_name,
        "phone": teacher.phone,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "is_active": teacher.is_active,
        "assigned_subjects": [
            {
                "group_subject_id": gs.id,
                "group_name": gs.group.name,
                "subject_name": gs.subject.name
            } for gs in teacher.group_subjects
        ]
    }


@router.put("/teachers/{teacher_id}")
def update_teacher(teacher_id: int, request: UpdateUserRequest,
                   current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    update_user(teacher, request, db)
    db.commit()
    return {"message": "Teacher updated"}


@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    teacher.is_active = False
    db.commit()
    return {"message": "Teacher deactivated"}


# PARENT CRUD
@router.post("/parents")
def create_parent(request: CreateUserRequest, current_user: User = Depends(require_role(["admin"])),
                  db: Session = Depends(get_db)):
    user = create_user(request, "parent", db)
    db.commit()
    return {"message": "Parent created", "id": user.id}


@router.get("/parents")
def list_parents(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    parents = db.query(User).filter(User.role == "parent").all()
    return [
        {
            "id": p.id,
            "name": p.full_name,
            "phone": p.phone,
            "is_active": p.is_active
        } for p in parents
    ]


@router.put("/parents/{parent_id}")
def update_parent(parent_id: int, request: UpdateUserRequest,
                  current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    parent = db.query(User).filter(User.id == parent_id, User.role == "parent").first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    update_user(parent, request, db)
    db.commit()
    return {"message": "Parent updated"}


@router.delete("/parents/{parent_id}")
def delete_parent(parent_id: int, current_user: User = Depends(require_role(["admin"])),
                  db: Session = Depends(get_db)):
    parent = db.query(User).filter(User.id == parent_id, User.role == "parent").first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    parent.is_active = False
    db.commit()
    return {"message": "Parent deactivated"}


# GROUP CRUD
@router.post("/groups")
def create_group(request: CreateGroupRequest, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    existing = db.query(Group).filter(Group.name == request.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")

    group = Group(name=request.name, academic_year=request.academic_year)
    db.add(group)
    db.commit()
    return {"message": "Group created", "id": group.id}


@router.get("/groups")
def list_groups(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    return [
        {
            "id": g.id,
            "name": g.name,
            "academic_year": g.academic_year,
            "student_count": len(g.students)
        } for g in groups
    ]


@router.get("/groups/{group_id}")
def get_group(group_id: int, current_user: User = Depends(require_role(["admin"])),
              db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return {
        "id": group.id,
        "name": group.name,
        "academic_year": group.academic_year,
        "student_count": len(group.students),
        "students": [
            {
                "id": s.id,
                "name": s.user.full_name,
                "phone": s.user.phone
            } for s in group.students
        ]
    }


@router.put("/groups/{group_id}")
def update_group(group_id: int, request: CreateGroupRequest,
                 current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if request.name != group.name:
        existing = db.query(Group).filter(Group.name == request.name, Group.id != group_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Group name already exists")

    group.name = request.name
    group.academic_year = request.academic_year
    db.commit()
    return {"message": "Group updated"}


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if group.students:
        raise HTTPException(status_code=400, detail="Cannot delete group with students")

    db.delete(group)
    db.commit()
    return {"message": "Group deleted"}


# SUBJECT CRUD
@router.post("/subjects")
def create_subject(request: CreateSubjectRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    existing = db.query(Subject).filter(Subject.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject code already exists")

    subject = Subject(name=request.name, code=request.code)
    db.add(subject)
    db.commit()
    return {"message": "Subject created", "id": subject.id}


@router.get("/subjects")
def list_subjects(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "code": s.code
        } for s in subjects
    ]


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    return {
        "id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "assignments": [
            {
                "group_subject_id": gs.id,
                "group_name": gs.group.name,
                "teacher_name": gs.teacher.full_name
            } for gs in subject.group_subjects
        ]
    }


@router.put("/subjects/{subject_id}")
def update_subject(subject_id: int, request: CreateSubjectRequest,
                   current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if request.code != subject.code:
        existing = db.query(Subject).filter(Subject.code == request.code, Subject.id != subject_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Subject code already exists")

    subject.name = request.name
    subject.code = request.code
    db.commit()
    return {"message": "Subject updated"}


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if subject.group_subjects:
        raise HTTPException(status_code=400, detail="Cannot delete subject with active assignments")

    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted"}


# NEWS CRUD
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


@router.get("/news")
def list_news(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    news_list = db.query(News).all()
    return [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content[:200] + "..." if len(n.content) > 200 else n.content,
            "author_name": n.author.full_name,
            "created_at": n.created_at,
            "is_published": n.is_published
        } for n in news_list
    ]


@router.get("/news/{news_id}")
def get_news(news_id: int, current_user: User = Depends(require_role(["admin"])),
             db: Session = Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "author_name": news.author.full_name,
        "external_links": news.external_links,
        "image_ids": news.image_ids,
        "created_at": news.created_at,
        "is_published": news.is_published
    }


@router.put("/news/{news_id}")
def update_news(news_id: int, request: NewsRequest,
                current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    news.title = request.title
    news.content = request.content
    news.external_links = request.external_links
    news.is_published = request.is_published
    db.commit()
    return {"message": "News updated"}


@router.delete("/news/{news_id}")
def delete_news(news_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    db.delete(news)
    db.commit()
    return {"message": "News deleted"}


# SCHEDULE CRUD
@router.post("/schedule")
def create_schedule(request: ScheduleRequest, current_user: User = Depends(require_role(["admin"])),
                    db: Session = Depends(get_db)):
    schedule = Schedule(
        group_subject_id=request.group_subject_id,
        day=request.day,
        start_time=time.fromisoformat(request.start_time),
        end_time=time.fromisoformat(request.end_time),
        room=request.room
    )
    db.add(schedule)
    db.commit()
    return {"message": "Schedule created", "id": schedule.id}


@router.get("/schedule")
def list_schedules(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    schedules = db.query(Schedule).all()
    return [
        {
            "id": s.id,
            "group_name": s.group_subject.group.name,
            "subject_name": s.group_subject.subject.name,
            "teacher_name": s.group_subject.teacher.full_name,
            "day": s.day,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "room": s.room
        } for s in schedules
    ]


@router.get("/schedule/{schedule_id}")
def get_schedule(schedule_id: int, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {
        "id": schedule.id,
        "group_subject_id": schedule.group_subject_id,
        "group_name": schedule.group_subject.group.name,
        "subject_name": schedule.group_subject.subject.name,
        "teacher_name": schedule.group_subject.teacher.full_name,
        "day": schedule.day,
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "room": schedule.room
    }


@router.put("/schedule/{schedule_id}")
def update_schedule(schedule_id: int, request: ScheduleRequest,
                    current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.group_subject_id = request.group_subject_id
    schedule.day = request.day
    schedule.start_time = time.fromisoformat(request.start_time)
    schedule.end_time = time.fromisoformat(request.end_time)
    schedule.room = request.room
    db.commit()
    return {"message": "Schedule updated"}


@router.delete("/schedule/{schedule_id}")
def delete_schedule(schedule_id: int, current_user: User = Depends(require_role(["admin"])),
                    db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted"}


# OTHER OPERATIONS
@router.post("/assign-teacher")
def assign_teacher(request: AssignTeacherRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    existing = db.query(GroupSubject).filter(
        GroupSubject.group_id == request.group_id,
        GroupSubject.subject_id == request.subject_id
    ).first()

    if existing:
        existing.teacher_id = request.teacher_id
    else:
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