from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models.models import User, Student, Group, Subject, GroupSubject, PaymentRecord, News, Schedule
from app.core.security import require_role, hash_password
from app.models.models import Schedule
from datetime import time
router = APIRouter()


def validate_phone_number(phone: str) -> bool:
    """
    Validate Uzbekistan phone number format: +998XXXXXXXXX
    Must be exactly 13 characters starting with +998
    """
    if not phone:
        return False
    
    # Check length (must be exactly 13 characters)
    if len(phone) != 13:
        return False
    
    # Check format: +998 followed by 9 digits
    if not phone.startswith("+998"):
        return False
    
    # Check that the remaining 9 characters are digits
    if not phone[4:].isdigit():
        return False
    
    return True


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
    parent_phone: Optional[str] = None
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
    # Validate phone number format
    if not validate_phone_number(data.phone):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid phone number format. Must be in format +998XXXXXXXXX (13 digits total). Example: +998990330919"
        )
    
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
        # Validate phone number format
        if not validate_phone_number(data.phone):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid phone number format. Must be in format +998XXXXXXXXX (13 digits total). Example: +998990330919"
            )
        
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
    # Validate parent phone number format only if provided
    if request.parent_phone and not validate_phone_number(request.parent_phone):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid parent phone number format. Must be in format +998XXXXXXXXX (13 digits total). Example: +998990330919"
        )
    
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
def list_students(skip: int = 0, limit: int = 500, current_user: User = Depends(require_role(["admin"])),
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
        "group_id": s.group_id,  # Added this field for frontend filtering
        "group_name": s.group.name if s.group else "No Group",
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
        "group_name": student.group.name if student.group else "No Group",
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
    if request.parent_phone is not None:
        # Validate parent phone number format only if provided (not empty)
        if request.parent_phone and not validate_phone_number(request.parent_phone):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid parent phone number format. Must be in format +998XXXXXXXXX (13 digits total). Example: +998990330919"
            )
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
        "is_published": n.is_published,
        "external_links": n.external_links,
        "image_ids": n.image_ids
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
    """Hard delete user and all related data - Students blocked only if they have payments"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    # Check for student profile and payments
    student = db.query(Student).filter(Student.user_id == user_id).first()
    if student:
        # Check payment records - block deletion if payments exist
        payment_count = db.query(PaymentRecord).filter(PaymentRecord.student_id == student.id).count()
        if payment_count > 0:
            return False  # Cannot delete student with payment history
        
        # No payments - safe to delete student data
        from app.models.models import HomeworkGrade, ExamGrade, Attendance
        db.query(HomeworkGrade).filter(HomeworkGrade.student_id == student.id).delete()
        db.query(ExamGrade).filter(ExamGrade.student_id == student.id).delete()
        db.query(Attendance).filter(Attendance.student_id == student.id).delete()
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
def list_all_payments(skip: int = 0, limit: int = 500, student_id: Optional[int] = None,
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
        "group_name": p.student.group.name if p.student.group else "No Group",
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
        "group_name": payment.student.group.name if payment.student.group else "No Group",
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


# Add these endpoints to app/api/admin.py after the existing assign-teacher endpoint

class ChangeTeacherRequest(BaseModel):
    new_teacher_id: int


class ChangeSubjectRequest(BaseModel):
    new_subject_id: int


class RemoveAssignmentByParamsRequest(BaseModel):
    group_id: int
    subject_id: int


@router.delete("/assignments/{group_subject_id}")
def remove_assignment(group_subject_id: int, current_user: User = Depends(require_role(["admin"])),
                      db: Session = Depends(get_db)):
    """Remove teacher assignment from a group-subject combination"""
    assignment = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject),
        joinedload(GroupSubject.teacher)
    ).filter(GroupSubject.id == group_subject_id).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check if there are any dependent records (homework, exams, grades, etc.)
    from app.models.models import Homework, Exam, HomeworkGrade, ExamGrade, Attendance

    homework_count = db.query(Homework).filter(Homework.group_subject_id == group_subject_id).count()
    exam_count = db.query(Exam).filter(Exam.group_subject_id == group_subject_id).count()
    grade_count = db.query(HomeworkGrade).join(Homework).filter(Homework.group_subject_id == group_subject_id).count()
    exam_grade_count = db.query(ExamGrade).join(Exam).filter(Exam.group_subject_id == group_subject_id).count()
    attendance_count = db.query(Attendance).filter(Attendance.group_subject_id == group_subject_id).count()

    if homework_count > 0 or exam_count > 0 or grade_count > 0 or exam_grade_count > 0 or attendance_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove assignment. Active records: {homework_count} homework, {exam_count} exams, {grade_count + exam_grade_count} grades, {attendance_count} attendance records."
        )

    # Get assignment details for response
    group_name = assignment.group.name
    subject_name = assignment.subject.name
    teacher_name = assignment.teacher.full_name if assignment.teacher else "Unassigned"

    # Delete the assignment
    db.delete(assignment)
    db.commit()

    return {
        "message": "Assignment removed successfully",
        "details": {
            "group": group_name,
            "subject": subject_name,
            "teacher": teacher_name
        }
    }


@router.delete("/assignments/by-params")
def remove_assignment_by_params(request: RemoveAssignmentByParamsRequest,
                                current_user: User = Depends(require_role(["admin"])),
                                db: Session = Depends(get_db)):
    """Remove assignment by group_id and subject_id"""
    assignment = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject),
        joinedload(GroupSubject.teacher)
    ).filter(
        GroupSubject.group_id == request.group_id,
        GroupSubject.subject_id == request.subject_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check for dependent records
    from app.models.models import Homework, Exam, HomeworkGrade, ExamGrade, Attendance

    homework_count = db.query(Homework).filter(Homework.group_subject_id == assignment.id).count()
    exam_count = db.query(Exam).filter(Exam.group_subject_id == assignment.id).count()
    grade_count = db.query(HomeworkGrade).join(Homework).filter(Homework.group_subject_id == assignment.id).count()
    exam_grade_count = db.query(ExamGrade).join(Exam).filter(Exam.group_subject_id == assignment.id).count()
    attendance_count = db.query(Attendance).filter(Attendance.group_subject_id == assignment.id).count()

    if homework_count > 0 or exam_count > 0 or grade_count > 0 or exam_grade_count > 0 or attendance_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot remove assignment. Active records: {homework_count} homework, {exam_count} exams, {grade_count + exam_grade_count} grades, {attendance_count} attendance records."
        )

    # Get assignment details for response
    group_name = assignment.group.name
    subject_name = assignment.subject.name
    teacher_name = assignment.teacher.full_name if assignment.teacher else "Unassigned"

    # Delete the assignment
    db.delete(assignment)
    db.commit()

    return {
        "message": "Assignment removed successfully",
        "details": {
            "group": group_name,
            "subject": subject_name,
            "teacher": teacher_name
        }
    }


@router.put("/assignments/{group_subject_id}/teacher")
def change_assignment_teacher(group_subject_id: int, request: ChangeTeacherRequest,
                              current_user: User = Depends(require_role(["admin"])),
                              db: Session = Depends(get_db)):
    """Change teacher for an existing assignment"""
    assignment = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject),
        joinedload(GroupSubject.teacher)
    ).filter(GroupSubject.id == group_subject_id).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify new teacher exists and is active
    new_teacher = db.query(User).filter(
        User.id == request.new_teacher_id,
        User.role == "teacher",
        User.is_active == True
    ).first()

    if not new_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or inactive")

    old_teacher_name = assignment.teacher.full_name if assignment.teacher else "Unassigned"

    # Update teacher
    assignment.teacher_id = request.new_teacher_id
    db.commit()

    return {
        "message": "Teacher changed successfully",
        "details": {
            "group": assignment.group.name,
            "subject": assignment.subject.name,
            "old_teacher": old_teacher_name,
            "new_teacher": new_teacher.full_name
        }
    }


@router.put("/assignments/{group_subject_id}/subject")
def change_assignment_subject(group_subject_id: int, request: ChangeSubjectRequest,
                              current_user: User = Depends(require_role(["admin"])),
                              db: Session = Depends(get_db)):
    """Change subject for an existing assignment"""
    assignment = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject),
        joinedload(GroupSubject.teacher)
    ).filter(GroupSubject.id == group_subject_id).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify new subject exists
    new_subject = db.query(Subject).filter(Subject.id == request.new_subject_id).first()
    if not new_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check if this group-subject combination already exists
    existing = db.query(GroupSubject).filter(
        GroupSubject.group_id == assignment.group_id,
        GroupSubject.subject_id == request.new_subject_id,
        GroupSubject.id != group_subject_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="This group already has this subject assigned")

    # Check if there are dependent records that might be affected
    from app.models.models import Homework, Exam
    homework_count = db.query(Homework).filter(Homework.group_subject_id == group_subject_id).count()
    exam_count = db.query(Exam).filter(Exam.group_subject_id == group_subject_id).count()

    if homework_count > 0 or exam_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change subject. There are {homework_count} homework(s) and {exam_count} exam(s) for this assignment. Remove them first."
        )

    old_subject_name = assignment.subject.name

    # Update subject
    assignment.subject_id = request.new_subject_id
    db.commit()

    return {
        "message": "Subject changed successfully",
        "details": {
            "group": assignment.group.name,
            "teacher": assignment.teacher.full_name if assignment.teacher else "Unassigned",
            "old_subject": old_subject_name,
            "new_subject": new_subject.name
        }
    }


@router.put("/assignments/{group_subject_id}/unassign-teacher")
def unassign_teacher_from_assignment(group_subject_id: int,
                                     current_user: User = Depends(require_role(["admin"])),
                                     db: Session = Depends(get_db)):
    """Unassign teacher from assignment (set teacher to None)"""
    assignment = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject),
        joinedload(GroupSubject.teacher)
    ).filter(GroupSubject.id == group_subject_id).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if not assignment.teacher_id:
        raise HTTPException(status_code=400, detail="No teacher is currently assigned")

    teacher_name = assignment.teacher.full_name
    assignment.teacher_id = None
    db.commit()

    return {
        "message": "Teacher unassigned successfully",
        "details": {
            "group": assignment.group.name,
            "subject": assignment.subject.name,
            "unassigned_teacher": teacher_name
        }
    }



@router.post("/schedule")
def create_schedule(request: ScheduleRequest, current_user: User = Depends(require_role(["admin"])),
                    db: Session = Depends(get_db)):
    """Create a new schedule entry"""
    # Verify group_subject exists
    group_subject = db.query(GroupSubject).filter(GroupSubject.id == request.group_subject_id).first()
    if not group_subject:
        raise HTTPException(status_code=404, detail="Group-subject assignment not found")

    # Validate day (0-6)
    if not 0 <= request.day <= 6:
        raise HTTPException(status_code=400, detail="Day must be between 0 (Monday) and 6 (Sunday)")

    # Parse time strings
    try:
        start_time = time.fromisoformat(request.start_time)
        end_time = time.fromisoformat(request.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM (e.g., '09:00')")

    # Validate time logic
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time")

    # Check for schedule conflicts (same group, same day, overlapping times)
    existing_schedules = db.query(Schedule).join(GroupSubject).filter(
        GroupSubject.group_id == group_subject.group_id,
        Schedule.day == request.day
    ).all()

    for existing in existing_schedules:
        if (start_time < existing.end_time and end_time > existing.start_time):
            raise HTTPException(
                status_code=400,
                detail=f"Schedule conflict with existing class from {existing.start_time} to {existing.end_time}"
            )

    # Create schedule
    schedule = Schedule(
        group_subject_id=request.group_subject_id,
        day=request.day,
        start_time=start_time,
        end_time=end_time,
        room=request.room
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return {"message": "Schedule created", "id": schedule.id}


@router.get("/schedule")
def list_schedules(current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    """List all schedules with proper error handling"""
    try:
        schedules = db.query(Schedule).options(
            joinedload(Schedule.group_subject).joinedload(GroupSubject.group),
            joinedload(Schedule.group_subject).joinedload(GroupSubject.subject),
            joinedload(Schedule.group_subject).joinedload(GroupSubject.teacher)
        ).all()

        result = []
        for s in schedules:
            # Safety checks for missing data
            if not s.group_subject or not s.group_subject.group or not s.group_subject.subject:
                continue  # Skip schedules with missing group/subject data
                
            schedule_data = {
                "id": s.id,
                "group_subject_id": s.group_subject_id,
                "group_name": s.group_subject.group.name,
                "subject_name": s.group_subject.subject.name,
                "teacher_name": s.group_subject.teacher.full_name if s.group_subject.teacher else "No teacher assigned",
                "day": s.day,
                "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][s.day],
                "start_time": s.start_time,
                "end_time": s.end_time,
                "room": s.room
            }
            result.append(schedule_data)
        
        return result
    except Exception as e:
        # Log the error and return empty array instead of crashing
        import logging
        logging.error(f"Error loading schedules: {str(e)}")
        return []


@router.get("/schedule/{schedule_id}")
def get_schedule(schedule_id: int, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    """Get specific schedule details"""
    schedule = db.query(Schedule).options(
        joinedload(Schedule.group_subject).joinedload(GroupSubject.group),
        joinedload(Schedule.group_subject).joinedload(GroupSubject.subject),
        joinedload(Schedule.group_subject).joinedload(GroupSubject.teacher)
    ).filter(Schedule.id == schedule_id).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return {
        "id": schedule.id,
        "group_subject_id": schedule.group_subject_id,
        "group_name": schedule.group_subject.group.name,
        "subject_name": schedule.group_subject.subject.name,
        "teacher_name": schedule.group_subject.teacher.full_name if schedule.group_subject.teacher else "No teacher assigned",
        "day": schedule.day,
        "day_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][schedule.day],
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "room": schedule.room
    }


@router.put("/schedule/{schedule_id}")
def update_schedule(schedule_id: int, request: ScheduleRequest,
                    current_user: User = Depends(require_role(["admin"])), db: Session = Depends(get_db)):
    """Update schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Verify group_subject exists
    group_subject = db.query(GroupSubject).filter(GroupSubject.id == request.group_subject_id).first()
    if not group_subject:
        raise HTTPException(status_code=404, detail="Group-subject assignment not found")

    # Validate day (0-6)
    if not 0 <= request.day <= 6:
        raise HTTPException(status_code=400, detail="Day must be between 0 (Monday) and 6 (Sunday)")

    # Parse time strings
    try:
        start_time = time.fromisoformat(request.start_time)
        end_time = time.fromisoformat(request.end_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM (e.g., '09:00')")

    # Validate time logic
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="Start time must be before end time")

    # Check for schedule conflicts (excluding current schedule)
    existing_schedules = db.query(Schedule).join(GroupSubject).filter(
        GroupSubject.group_id == group_subject.group_id,
        Schedule.day == request.day,
        Schedule.id != schedule_id
    ).all()

    for existing in existing_schedules:
        if (start_time < existing.end_time and end_time > existing.start_time):
            raise HTTPException(
                status_code=400,
                detail=f"Schedule conflict with existing class from {existing.start_time} to {existing.end_time}"
            )

    # Update schedule
    schedule.group_subject_id = request.group_subject_id
    schedule.day = request.day
    schedule.start_time = start_time
    schedule.end_time = end_time
    schedule.room = request.room

    db.commit()
    return {"message": "Schedule updated"}


@router.delete("/schedule/{schedule_id}")
def delete_schedule(schedule_id: int, current_user: User = Depends(require_role(["admin"])),
                    db: Session = Depends(get_db)):
    """Delete schedule"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted"}


# Fix for get_all_assignments function (around line 980)
@router.get("/assignments")
def get_all_assignments(current_user: User = Depends(require_role(["admin"])),
                        db: Session = Depends(get_db)):
    """Get all assignments with full details"""
    # Filter out assignments with NULL group_id or subject_id
    assignments = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject),
        joinedload(GroupSubject.teacher)
    ).filter(
        GroupSubject.group_id.is_not(None),
        GroupSubject.subject_id.is_not(None)
    ).all()

    result = []
    for assignment in assignments:
        # Additional safety check
        if assignment.group is None or assignment.subject is None:
            continue

        assignment_data = {
            "id": assignment.id,
            "group_subject_id": assignment.id,
            "group": {
                "id": assignment.group.id,
                "name": assignment.group.name,
                "academic_year": assignment.group.academic_year
            },
            "subject": {
                "id": assignment.subject.id,
                "name": assignment.subject.name,
                "code": assignment.subject.code
            },
            "teacher": {
                "id": assignment.teacher.id,
                "name": assignment.teacher.full_name,
                "phone": assignment.teacher.phone,
                "is_active": assignment.teacher.is_active
            } if assignment.teacher else None,
            "has_teacher": assignment.teacher_id is not None
        }
        result.append(assignment_data)

    return result


# Fix for get_unassigned_subjects function (around line 1012)
@router.get("/assignments/unassigned")
def get_unassigned_subjects(current_user: User = Depends(require_role(["admin"])),
                            db: Session = Depends(get_db)):
    """Get all group-subject combinations without teachers"""
    # Filter out assignments with NULL group_id, subject_id, and where teacher_id is NULL
    unassigned = db.query(GroupSubject).options(
        joinedload(GroupSubject.group),
        joinedload(GroupSubject.subject)
    ).filter(
        GroupSubject.teacher_id.is_(None),
        GroupSubject.group_id.is_not(None),
        GroupSubject.subject_id.is_not(None)
    ).all()

    result = []
    for assignment in unassigned:
        # Additional safety check
        if assignment.group is None or assignment.subject is None:
            continue

        assignment_data = {
            "id": assignment.group.id,
            "name": assignment.group.name,
            "academic_year": assignment.group.academic_year,
            "subject": {
                "id": assignment.subject.id,
                "name": assignment.subject.name,
                "code": assignment.subject.code
            },
            "group_subject_id": assignment.id
        }
        result.append(assignment_data)

    return result


# Add a maintenance endpoint to clean up orphaned records
@router.post("/maintenance/cleanup-orphaned-records")
def cleanup_orphaned_records(current_user: User = Depends(require_role(["admin"])),
                             db: Session = Depends(get_db)):
    """Clean up orphaned records in the database"""
    from app.models.models import Schedule, Homework, Exam, HomeworkGrade, ExamGrade, Attendance

    cleanup_report = {
        "orphaned_group_subjects": 0,
        "orphaned_schedules": 0,
        "orphaned_homework": 0,
        "orphaned_exams": 0
    }

    # Clean up group_subjects with NULL group_id or subject_id
    orphaned_gs = db.query(GroupSubject).filter(
        or_(GroupSubject.group_id.is_(None), GroupSubject.subject_id.is_(None))
    ).all()

    for gs in orphaned_gs:
        # Clean up related records first
        db.query(Schedule).filter(Schedule.group_subject_id == gs.id).delete()
        db.query(Homework).filter(Homework.group_subject_id == gs.id).delete()
        db.query(Exam).filter(Exam.group_subject_id == gs.id).delete()
        db.query(Attendance).filter(Attendance.group_subject_id == gs.id).delete()
        db.delete(gs)
        cleanup_report["orphaned_group_subjects"] += 1

    # Clean up schedules referencing non-existent group_subjects
    valid_gs_ids = [gs.id for gs in db.query(GroupSubject.id).all()]
    orphaned_schedules = db.query(Schedule).filter(
        ~Schedule.group_subject_id.in_(valid_gs_ids)
    ).all()

    for schedule in orphaned_schedules:
        db.delete(schedule)
        cleanup_report["orphaned_schedules"] += 1

    db.commit()
    return {
        "message": "Cleanup completed successfully",
        "report": cleanup_report
    }


# Replace these functions in your admin.py file

@router.delete("/teachers/{teacher_id}")
def delete_teacher(teacher_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    """Delete teacher only if they have no active assignments"""
    teacher = db.query(User).filter(User.id == teacher_id, User.role == "teacher").first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Check for active group-subject assignments
    active_assignments = db.query(GroupSubject).filter(GroupSubject.teacher_id == teacher_id).all()

    if active_assignments:
        # Get details of assignments for error message
        assignment_details = []
        for assignment in active_assignments:
            if assignment.group and assignment.subject:  # Safety check
                assignment_details.append(f"{assignment.group.name} - {assignment.subject.name}")

        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete teacher. They are assigned to {len(active_assignments)} subjects: {', '.join(assignment_details[:3])}{'...' if len(assignment_details) > 3 else ''}"
        )

    # Safe to delete - no active assignments
    # Delete teacher's notifications first
    from app.models.models import Notification
    db.query(Notification).filter(Notification.user_id == teacher_id).delete()

    # Delete teacher's uploaded files
    from app.models.models import File
    db.query(File).filter(File.uploaded_by == teacher_id).delete()

    # Delete the teacher
    db.delete(teacher)
    db.commit()

    return {"message": f"Teacher {teacher.full_name} deleted successfully"}


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, current_user: User = Depends(require_role(["admin"])),
                 db: Session = Depends(get_db)):
    """Delete group only if it has no students. Clean up related data automatically."""
    group = db.query(Group).options(
        selectinload(Group.students)
    ).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Only check for students - this is the main constraint
    if group.students:
        student_names = [s.user.full_name for s in group.students[:3]]
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete group. It has {len(group.students)} students: {', '.join(student_names)}{'...' if len(group.students) > 3 else ''}"
        )

    # Clean up related data before deleting the group
    from app.models.models import Schedule, Homework, Exam, HomeworkGrade, ExamGrade, Attendance
    
    # Get all group subjects for this group
    group_subjects = db.query(GroupSubject).filter(GroupSubject.group_id == group_id).all()
    
    for gs in group_subjects:
        # Clean up schedules
        db.query(Schedule).filter(Schedule.group_subject_id == gs.id).delete()
        
        # Clean up homework and related grades
        homeworks = db.query(Homework).filter(Homework.group_subject_id == gs.id).all()
        for hw in homeworks:
            db.query(HomeworkGrade).filter(HomeworkGrade.homework_id == hw.id).delete()
        db.query(Homework).filter(Homework.group_subject_id == gs.id).delete()
        
        # Clean up exams and related grades
        exams = db.query(Exam).filter(Exam.group_subject_id == gs.id).all()
        for exam in exams:
            db.query(ExamGrade).filter(ExamGrade.exam_id == exam.id).delete()
        db.query(Exam).filter(Exam.group_subject_id == gs.id).delete()
        
        # Clean up attendance records
        db.query(Attendance).filter(Attendance.group_subject_id == gs.id).delete()
        
        # Delete the group subject assignment
        db.delete(gs)
    
    # Now safe to delete the group
    db.delete(group)
    db.commit()
    return {"message": f"Group '{group.name}' deleted successfully with all related data cleaned up"}


@router.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    """Delete subject only if it has no active assignments"""
    subject = db.query(Subject).options(
        selectinload(Subject.group_subjects)
    ).filter(Subject.id == subject_id).first()

    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check for active assignments
    if subject.group_subjects:
        group_names = []
        for gs in subject.group_subjects:
            if gs.group:  # Safety check
                teacher_info = f" (Teacher: {gs.teacher.full_name})" if gs.teacher else " (No teacher)"
                group_names.append(f"{gs.group.name}{teacher_info}")

        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete subject. It's assigned to {len(subject.group_subjects)} groups: {', '.join(group_names[:3])}{'...' if len(group_names) > 3 else ''}"
        )

    # Safe to delete
    db.delete(subject)
    db.commit()
    return {"message": f"Subject {subject.name} deleted successfully"}


@router.delete("/students/{student_id}")
def delete_student(student_id: int, current_user: User = Depends(require_role(["admin"])),
                   db: Session = Depends(get_db)):
    """Delete student only if they have no payment records"""
    student = db.query(Student).options(joinedload(Student.user)).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check for payment records - this is what blocks deletion
    payment_records = db.query(PaymentRecord).filter(PaymentRecord.student_id == student_id).count()

    if payment_records > 0:
        # Block deletion if payments exist
        raise HTTPException(
            status_code=403,
            detail=f"Cannot delete student '{student.user.full_name}' because they have {payment_records} payment records. Students with payment history cannot be deleted to maintain financial records integrity."
        )

    # No payments - safe to delete
    # Get other data for confirmation message
    from app.models.models import HomeworkGrade, ExamGrade, Attendance
    homework_grades = db.query(HomeworkGrade).filter(HomeworkGrade.student_id == student_id).count()
    exam_grades = db.query(ExamGrade).filter(ExamGrade.student_id == student_id).count()
    attendance_records = db.query(Attendance).filter(Attendance.student_id == student_id).count()

    user_id = student.user_id
    student_name = student.user.full_name

    # Delete all student-related data
    db.query(HomeworkGrade).filter(HomeworkGrade.student_id == student_id).delete()
    db.query(ExamGrade).filter(ExamGrade.student_id == student_id).delete()
    db.query(Attendance).filter(Attendance.student_id == student_id).delete()

    # Delete student record
    db.delete(student)

    # Delete user record and related data
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        # Delete user's notifications
        from app.models.models import Notification
        db.query(Notification).filter(Notification.user_id == user_id).delete()

        # Delete user's files
        from app.models.models import File
        db.query(File).filter(File.uploaded_by == user_id).delete()

        db.delete(user)

    db.commit()
    
    return {
        "message": f"Student '{student_name}' deleted successfully",
        "deleted_data": {
            "homework_grades": homework_grades,
            "exam_grades": exam_grades,
            "attendance_records": attendance_records,
            "payment_records": 0
        }
    }

