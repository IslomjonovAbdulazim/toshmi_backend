from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models.models import User, Student, Group, Subject, GroupSubject, PaymentRecord, News, Schedule
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
    if db.query(User).filter(User.phone == data.phone).first():
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
        if db.query(User).filter(User.phone == data.phone, User.id != user.id).first():
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
    students = db.query(Student).options(
        joinedload(Student.user),
        joinedload(Student.group)
    ).offset(skip).limit(limit).all()

    return [{
        "id": s.id,
        "user_id": s.user_id,
        "name": s.user.full_name,
        "phone": s.user.phone,
        "group_name": s.group.name,
        "parent_phone": s.parent_phone,
        "graduation_year": s.graduation_year,
        "is_active": s.user.is_active
    } for s in students]


@router.get("/students/{student_id}")
def get_student(student_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    student = db.query(Student).options(
        joinedload(Student.user),
        joinedload(Student.group)
    ).filter(Student.id == student_id).first()

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
    student = db.query(Student).options(joinedload(Student.user)).filter(Student.id == student_id).first()
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


@router.post("/teachers")
def create_teacher(request: CreateUserRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    user = create_user(request, "teacher", db)
    db.commit()
    return {"message": "Teacher created", "id": user.id}


@router.get("/teachers")
def list_teachers(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    teachers = db.query(User).filter(User.role == "teacher").all()
    return [{"id": t.id, "name": t.full_name, "phone": t.phone, "is_active": t.is_active} for t in teachers]


@router.get("/teachers/{teacher_id}")
def get_teacher(teacher_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    teacher = db.query(User).options(
        selectinload(User.group_subjects).joinedload(GroupSubject.group),
        selectinload(User.group_subjects).joinedload(GroupSubject.subject)
    ).filter(User.id == teacher_id, User.role == "teacher").first()

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "id": teacher.id,
        "name": teacher.full_name,
        "phone": teacher.phone,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "is_active": teacher.is_active,
        "assigned_subjects": [{
            "group_subject_id": gs.id,
            "group_name": gs.group.name,
            "subject_name": gs.subject.name
        } for gs in teacher.group_subjects]
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


@router.post("/parents")
def create_parent(request: CreateUserRequest, current_user: User = Depends(require_role(["admin"])),
                  db: Session = Depends(get_db)):
    user = create_user(request, "parent", db)
    db.commit()
    return {"message": "Parent created", "id": user.id}


@router.get("/parents")
def list_parents(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    parents = db.query(User).filter(User.role == "parent").all()
    return [{"id": p.id, "name": p.full_name, "phone": p.phone, "is_active": p.is_active} for p in parents]


@router.put("/parents/{parent_id}")
def update_parent(parent_id: int, request: UpdateUserRequest,
                  current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    parent = db.query(User).filter(User.id == parent_id, User.role == "parent").first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    update_user(parent, request, db)
    db.commit()
    return {"message": "Parent updated"}


@router.post("/groups")
def create_group(request: CreateGroupRequest, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    if db.query(Group).filter(Group.name == request.name).first():
        raise HTTPException(status_code=400, detail="Group name already exists")
    group = Group(name=request.name, academic_year=request.academic_year)
    db.add(group)
    db.commit()
    return {"message": "Group created", "id": group.id}


@router.get("/groups")
def list_groups(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    groups = db.query(Group).options(selectinload(Group.students)).all()
    return [{"id": g.id, "name": g.name, "academic_year": g.academic_year, "student_count": len(g.students)} for g in groups]


@router.get("/groups/{group_id}")
def get_group(group_id: int, current_user: User = Depends(require_role(["admin"])),
              db: Session = Depends(get_db)):
    group = db.query(Group).options(
        selectinload(Group.students).joinedload(Student.user)
    ).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    return {
        "id": group.id,
        "name": group.name,
        "academic_year": group.academic_year,
        "student_count": len(group.students),
        "students": [{"id": s.id, "name": s.user.full_name, "phone": s.user.phone} for s in group.students]
    }


@router.put("/groups/{group_id}")
def update_group(group_id: int, request: CreateGroupRequest,
                 current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if request.name != group.name and db.query(Group).filter(Group.name == request.name, Group.id != group_id).first():
        raise HTTPException(status_code=400, detail="Group name already exists")

    group.name = request.name
    group.academic_year = request.academic_year
    db.commit()
    return {"message": "Group updated"}


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    group = db.query(Group).options(selectinload(Group.students)).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if group.students:
        raise HTTPException(status_code=400, detail="Cannot delete group with students")
    db.delete(group)
    db.commit()
    return {"message": "Group deleted"}


@router.post("/subjects")
def create_subject(request: CreateSubjectRequest, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    if db.query(Subject).filter(Subject.code == request.code).first():
        raise HTTPException(status_code=400, detail="Subject code already exists")
    subject = Subject(name=request.name, code=request.code)
    db.add(subject)
    db.commit()
    return {"message": "Subject created", "id": subject.id}


@router.get("/subjects")
def list_subjects(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    return [{"id": s.id, "name": s.name, "code": s.code} for s in subjects]


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    subject = db.query(Subject).options(
        selectinload(Subject.group_subjects).joinedload(GroupSubject.group),
        selectinload(Subject.group_subjects).joinedload(GroupSubject.teacher)
    ).filter(Subject.id == subject_id).first()

    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    return {
        "id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "assignments": [{
            "group_subject_id": gs.id,
            "group_name": gs.group.name,
            "teacher_name": gs.teacher.full_name
        } for gs in subject.group_subjects]
    }


@router.put("/subjects/{subject_id}")
def update_subject(subject_id: int, request: CreateSubjectRequest,
                   current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if request.code != subject.code and db.query(Subject).filter(Subject.code == request.code, Subject.id != subject_id).first():
        raise HTTPException(status_code=400, detail="Subject code already exists")

    subject.name = request.name
    subject.code = request.code
    db.commit()
    return {"message": "Subject updated"}


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    subject = db.query(Subject).options(selectinload(Subject.group_subjects)).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.group_subjects:
        raise HTTPException(status_code=400, detail="Cannot delete subject with active assignments")
    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted"}


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
    return [{
        "id": n.id,
        "title": n.title,
        "content": n.content[:200] + "..." if len(n.content) > 200 else n.content,
        "created_at": n.created_at,
        "is_published": n.is_published
    } for n in news_list]


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


@router.get("/payments/summary")
def get_payments_summary(current_user: User = Depends(require_role(["admin"])),
                         db: Session = Depends(get_db)):
    """Get payment statistics and summary"""
    from sqlalchemy import func

    total_amount = db.query(func.sum(PaymentRecord.amount)).scalar() or 0
    total_payments = db.query(PaymentRecord).count()

    # Payment methods breakdown
    payment_methods = db.query(
        PaymentRecord.payment_method,
        func.sum(PaymentRecord.amount).label('total'),
        func.count(PaymentRecord.id).label('count')
    ).group_by(PaymentRecord.payment_method).all()

    # Recent payments
    recent_payments = db.query(PaymentRecord).options(
        joinedload(PaymentRecord.student).joinedload(Student.user)
    ).order_by(PaymentRecord.created_at.desc()).limit(5).all()

    return {
        "total_amount": total_amount,
        "total_payments": total_payments,
        "payment_methods": [{
            "method": pm.payment_method,
            "total_amount": pm.total,
            "count": pm.count
        } for pm in payment_methods],
        "recent_payments": [{
            "id": p.id,
            "student_name": p.student.user.full_name,
            "amount": p.amount,
            "payment_date": p.payment_date,
            "payment_method": p.payment_method
        } for p in recent_payments]
    }


@router.delete("/payments/{payment_id}")
def delete_payment(payment_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    """Delete payment record"""
    payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    db.delete(payment)
    db.commit()
    return {"message": "Payment deleted"}


def hard_delete_user_and_dependencies(user_id: int, db: Session):
    """Hard delete user and all related data"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # Delete student profile and related data if exists
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if student:
        # Delete student's homework grades, exam grades, attendance, payments
        from app.models.models import HomeworkGrade, ExamGrade, Attendance
        db.query(HomeworkGrade).filter(HomeworkGrade.student_id == student.id).delete()
        db.query(ExamGrade).filter(ExamGrade.student_id == student.id).delete()
        db.query(Attendance).filter(Attendance.student_id == student.id).delete()
        db.query(PaymentRecord).filter(PaymentRecord.student_id == student.id).delete()
        db.delete(student)

    # Delete teacher's assignments if exists
    if user.role == "teacher":
        # Only unassign, don't delete the group-subjects themselves
        assignments = db.query(GroupSubject).filter(GroupSubject.teacher_id == user_id).all()
        for assignment in assignments:
            assignment.teacher_id = None

    # Delete user's notifications
    from app.models.models import Notification
    db.query(Notification).filter(Notification.user_id == user_id).delete()

    # Delete user's files
    from app.models.models import File
    db.query(File).filter(File.uploaded_by == user_id).delete()

    # Finally delete the user
    db.delete(user)
    return True


# REPLACE the existing delete_student function with this:
@router.delete("/students/{student_id}")
def delete_student(student_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    student = db.query(Student).options(joinedload(Student.user)).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Hard delete the student and user
    if hard_delete_user_and_dependencies(student.user_id, db):
        db.commit()
        return {"message": "Student deleted completely"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete student")


# REPLACE the existing delete_teacher function with this:
@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Hard delete the teacher and unassign from subjects
    if hard_delete_user_and_dependencies(teacher_id, db):
        db.commit()
        return {"message": "Teacher deleted completely"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete teacher")


# REPLACE the existing delete_parent function with this:
@router.delete("/parents/{parent_id}")
def delete_parent(parent_id: int, current_user: User = Depends(require_role(["admin"])),
                  db: Session = Depends(get_db)):
    parent = db.query(User).filter(User.id == parent_id, User.role == "parent").first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    # Hard delete the parent
    if hard_delete_user_and_dependencies(parent_id, db):
        db.commit()
        return {"message": "Parent deleted completely"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete parent")


# ADD THESE NEW PAYMENT ENDPOINTS at the end of the file:

@router.get("/payments")
def list_all_payments(skip: int = 0, limit: int = 100, student_id: Optional[int] = None,
                      payment_method: Optional[str] = None,
                      current_user: User = Depends(require_role(["admin"])),
                      db: Session = Depends(get_db)):
    """Get all payment records with optional filtering"""
    query = db.query(PaymentRecord).options(
        joinedload(PaymentRecord.student).joinedload(Student.user),
        joinedload(PaymentRecord.student).joinedload(Student.group)
    )

    if student_id:
        query = query.filter(PaymentRecord.student_id == student_id)
    if payment_method:
        query = query.filter(PaymentRecord.payment_method == payment_method)

    payments = query.order_by(PaymentRecord.payment_date.desc()).offset(skip).limit(limit).all()

    return [{
        "id": p.id,
        "student_id": p.student_id,
        "student_name": p.student.user.full_name,
        "student_phone": p.student.user.phone,
        "group_name": p.student.group.name,
        "amount": p.amount,
        "payment_date": p.payment_date,
        "payment_method": p.payment_method,
        "description": p.description,
        "created_at": p.created_at
    } for p in payments]


@router.get("/payments/{payment_id}")
def get_payment(payment_id: int, current_user: User = Depends(require_role(["admin"])),
                db: Session = Depends(get_db)):
    """Get specific payment record"""
    payment = db.query(PaymentRecord).options(
        joinedload(PaymentRecord.student).joinedload(Student.user),
        joinedload(PaymentRecord.student).joinedload(Student.group)
    ).filter(PaymentRecord.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return {
        "id": payment.id,
        "student_id": payment.student_id,
        "student_name": payment.student.user.full_name,
        "student_phone": payment.student.user.phone,
        "group_name": payment.student.group.name,
        "amount": payment.amount,
        "payment_date": payment.payment_date,
        "payment_method": payment.payment_method,
        "description": payment.description,
        "created_at": payment.created_at
    }


@router.put("/payments/{payment_id}")
def update_payment(payment_id: int, request: PaymentRequest,
                   current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    """Update payment record"""
    payment = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.student_id = request.student_id
    payment.amount = request.amount
    payment.payment_date = request.payment_date
    payment.payment_method = request.payment_method
    payment.description = request.description

    db.commit()
    return {"message": "Payment updated"}