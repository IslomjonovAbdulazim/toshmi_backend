from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.dependencies import require_admin
from app.schemas import *
from app.crud import *
from app.models import *
from app.utils.audit import log_action
import pandas as pd
import uuid
import io

router = APIRouter()


# BULK DELETE OPERATIONS
@router.delete("/students/bulk")
async def bulk_delete_students(
        student_ids: List[str],
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """Delete multiple students"""
    deleted_count = 0
    errors = []

    for student_id in student_ids:
        try:
            student = db.query(Student).filter(Student.id == student_id).first()
            if student:
                # Delete related records first
                db.query(HomeworkGrade).filter(HomeworkGrade.student_id == student_id).delete()
                db.query(ExamGrade).filter(ExamGrade.student_id == student_id).delete()
                db.query(Attendance).filter(Attendance.student_id == student_id).delete()
                db.query(Payment).filter(Payment.student_id == student_id).delete()

                # Delete student
                db.delete(student)
                deleted_count += 1
                await log_action(admin.id, "DELETE", "Student", student_id)
            else:
                errors.append(f"Student {student_id} not found")
        except Exception as e:
            errors.append(f"Error deleting {student_id}: {str(e)}")

    db.commit()
    return {"deleted": deleted_count, "errors": errors}


@router.delete("/users/bulk")
async def bulk_delete_users(
        user_ids: List[str],
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """Delete multiple users"""
    deleted_count = 0
    errors = []

    for user_id in user_ids:
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.role != "admin":  # Protect admin users
                # Delete user profile first
                if user.role == "student":
                    student = db.query(Student).filter(Student.user_id == user_id).first()
                    if student:
                        db.delete(student)
                elif user.role == "parent":
                    parent = db.query(Parent).filter(Parent.user_id == user_id).first()
                    if parent:
                        db.delete(parent)
                elif user.role == "teacher":
                    teacher = db.query(Teacher).filter(Teacher.user_id == user_id).first()
                    if teacher:
                        db.delete(teacher)

                db.delete(user)
                deleted_count += 1
                await log_action(admin.id, "DELETE", "User", user_id)
            else:
                errors.append(f"Cannot delete user {user_id}")
        except Exception as e:
            errors.append(f"Error deleting {user_id}: {str(e)}")

    db.commit()
    return {"deleted": deleted_count, "errors": errors}


@router.delete("/grades/bulk")
async def bulk_delete_grades(
        grade_ids: List[str],
        grade_type: str,  # "homework" or "exam"
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """Delete multiple grades"""
    deleted_count = 0

    if grade_type == "homework":
        db.query(HomeworkGrade).filter(HomeworkGrade.id.in_(grade_ids)).delete()
    elif grade_type == "exam":
        db.query(ExamGrade).filter(ExamGrade.id.in_(grade_ids)).delete()
    else:
        raise HTTPException(400, "Invalid grade type")

    deleted_count = len(grade_ids)
    db.commit()
    await log_action(admin.id, "BULK_DELETE", f"{grade_type}_grades", str(grade_ids))
    return {"deleted": deleted_count}


# BULK CREATE OPERATIONS
@router.post("/students/bulk-create-csv")
async def bulk_create_students_csv(
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        admin=Depends(require_admin)
):
    """Create students from CSV upload"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "File must be CSV")

    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))

        required_columns = ['full_name', 'phone', 'group_name', 'graduation_year', 'parent_phone']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(400, f"CSV must contain columns: {required_columns}")

        created_students = []
        errors = []

        for _, row in df.iterrows():
            try:
                # Find or create group
                group = db.query(Group).filter(Group.name == row['group_name']).first()
                if not group:
                    group = Group(id=str(uuid.uuid4()), name=row['group_name'])
                    db.add(group)
                    db.flush()

                # Create user
                from app.utils.password import hash_password
                user = User(
                    id=str(uuid.uuid4()),
                    role="student",
                    phone=int(row['phone']),
                    password_hash=hash_password("student123"),  # Default password
                    full_name=row['full_name']
                )
                db.add(user)
                db.flush()

                # Create student
                student = Student(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    group_id=group.id,
                    graduation_year=int(row['graduation_year'])
                )
                db.add(student)

                # Link to parent if exists
                parent_user = db.query(User).filter(
                    User.phone == int(row['parent_phone']),
                    User.role == "parent"
                ).first()

                if parent_user:
                    parent = db.query(Parent).filter(Parent.user_id == parent_user.id).first()
                    if parent:
                        # Add student to parent's children (many-to-many)
                        parent.students.append(student)

                created_students.append({
                    "name": row['full_name'],
                    "phone": row['phone'],
                    "student_id": student.id
                })

            except Exception as e:
                errors.append(f"Row {len(created_students) + len(errors) + 1}: {str(e)}")

        db.commit()
        await log_action(admin.id, "BULK_CREATE", "Students", f"Created {len(created_students)}")

        return {
            "created": len(created_students),
            "students": created_students,
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(400, f"Error processing CSV: {str(e)}")


@router.get("/students/csv-template")
async def download_csv_template():
    """Download CSV template for bulk student creation"""
    template_data = {
        'full_name': ['John Doe', 'Jane Smith'],
        'phone': [1234567890, 1234567891],
        'group_name': ['10A', '10B'],
        'graduation_year': [2025, 2025],
        'parent_phone': [9876543210, 9876543211]
    }

    df = pd.DataFrame(template_data)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    from fastapi.responses import Response
    return Response(
        csv_buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_template.csv"}
    )