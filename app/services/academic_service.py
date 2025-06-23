# app/services/academic_service.py
"""
Academic operations service with passionate educational excellence!
Handles homework, exams, grades, and attendance with comprehensive validation.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
from datetime import datetime, date

from ..models import (
    Homework, Exam, Grade, Attendance, Student, Teacher,
    Group, Subject, GroupSubject, User
)
from ..utils.helpers import (
    AttendanceStatus, serialize_external_links, parse_external_links,
    calculate_grade_percentage, get_attendance_percentage
)
from ..schemas.academic import (
    HomeworkCreate, ExamCreate, GradeCreate, AttendanceCreate,
    BulkGradeRequest, BulkAttendanceRequest
)


class AcademicService:
    """
    Comprehensive academic service handling all educational operations
    with passionate attention to student success!
    """

    def __init__(self, db: Session):
        self.db = db

    # Homework Management

    def create_homework(self, homework_data: HomeworkCreate, teacher_id: str) -> Dict[str, Any]:
        """
        Create new homework assignment

        Args:
            homework_data: Homework creation data
            teacher_id: Teacher creating the homework

        Returns:
            Created homework information

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Validate teacher has access to this group-subject
            group_subject = self.db.query(GroupSubject).filter(
                GroupSubject.group_id == homework_data.group_id,
                GroupSubject.subject_id == homework_data.subject_id,
                GroupSubject.teacher_id == teacher_id
            ).first()

            if not group_subject:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to create homework for this group-subject"
                )

            # Create homework
            homework = Homework(
                group_id=homework_data.group_id,
                subject_id=homework_data.subject_id,
                teacher_id=teacher_id,
                title=homework_data.title.strip(),
                description=homework_data.description.strip() if homework_data.description else None,
                external_links=serialize_external_links(homework_data.external_links or []),
                due_date=homework_data.due_date,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(homework)
            self.db.commit()
            self.db.refresh(homework)

            # Create notifications for students in the group
            self._create_homework_notifications(homework.id, homework_data.group_id, homework.title)

            return {
                "id": homework.id,
                "group_id": homework.group_id,
                "subject_id": homework.subject_id,
                "teacher_id": homework.teacher_id,
                "title": homework.title,
                "description": homework.description,
                "external_links": parse_external_links(homework.external_links),
                "due_date": homework.due_date,
                "created_at": homework.created_at,
                "message": "Homework created successfully"
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Homework creation error: {str(e)}"
            )

    def get_teacher_homework(self, teacher_id: str, group_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get homework assignments created by teacher

        Args:
            teacher_id: Teacher ID
            group_id: Optional group filter

        Returns:
            List of homework assignments
        """
        try:
            query = self.db.query(Homework).filter(Homework.teacher_id == teacher_id)

            if group_id:
                query = query.filter(Homework.group_id == group_id)

            homework_list = query.order_by(desc(Homework.created_at)).all()

            result = []
            for homework in homework_list:
                # Get grade statistics
                total_students = self.db.query(Student).filter(Student.group_id == homework.group_id).count()
                graded_students = self.db.query(Grade).filter(
                    Grade.homework_id == homework.id
                ).count()

                homework_data = {
                    "id": homework.id,
                    "group_id": homework.group_id,
                    "subject_id": homework.subject_id,
                    "title": homework.title,
                    "description": homework.description,
                    "external_links": parse_external_links(homework.external_links),
                    "due_date": homework.due_date,
                    "created_at": homework.created_at,
                    "grading_stats": {
                        "total_students": total_students,
                        "graded_students": graded_students,
                        "pending_grades": total_students - graded_students
                    }
                }

                result.append(homework_data)

            return result

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving homework: {str(e)}"
            )

    def get_student_homework(self, student_id: str, include_completed: bool = True) -> List[Dict[str, Any]]:
        """
        Get homework assignments for student

        Args:
            student_id: Student ID
            include_completed: Include completed homework

        Returns:
            List of homework assignments with grades
        """
        try:
            # Get student's group
            student = self.db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )

            # Get homework for student's group
            homework_query = self.db.query(Homework).filter(Homework.group_id == student.group_id)

            if not include_completed:
                # Only include homework without grades for this student
                graded_homework_ids = self.db.query(Grade.homework_id).filter(
                    Grade.student_id == student_id,
                    Grade.homework_id.isnot(None)
                ).subquery()

                homework_query = homework_query.filter(
                    ~Homework.id.in_(graded_homework_ids)
                )

            homework_list = homework_query.order_by(desc(Homework.due_date)).all()

            result = []
            for homework in homework_list:
                # Get grade if exists
                grade = self.db.query(Grade).filter(
                    Grade.student_id == student_id,
                    Grade.homework_id == homework.id
                ).first()

                homework_data = {
                    "id": homework.id,
                    "title": homework.title,
                    "description": homework.description,
                    "external_links": parse_external_links(homework.external_links),
                    "due_date": homework.due_date,
                    "subject_name": homework.subject.name,
                    "teacher_name": homework.teacher.user.full_name,
                    "is_overdue": homework.due_date < datetime.utcnow(),
                    "grade": None
                }

                if grade:
                    homework_data["grade"] = {
                        "grade": grade.grade,
                        "max_grade": grade.max_grade,
                        "percentage": calculate_grade_percentage(grade.grade, grade.max_grade),
                        "comment": grade.comment,
                        "graded_at": grade.graded_at
                    }

                result.append(homework_data)

            return result

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving student homework: {str(e)}"
            )

    # Exam Management

    def create_exam(self, exam_data: ExamCreate, teacher_id: str) -> Dict[str, Any]:
        """
        Create new exam

        Args:
            exam_data: Exam creation data
            teacher_id: Teacher creating the exam

        Returns:
            Created exam information

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Validate teacher has access to this group-subject
            group_subject = self.db.query(GroupSubject).filter(
                GroupSubject.group_id == exam_data.group_id,
                GroupSubject.subject_id == exam_data.subject_id,
                GroupSubject.teacher_id == teacher_id
            ).first()

            if not group_subject:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to create exams for this group-subject"
                )

            # Create exam
            exam = Exam(
                group_id=exam_data.group_id,
                subject_id=exam_data.subject_id,
                teacher_id=teacher_id,
                title=exam_data.title.strip(),
                description=exam_data.description.strip() if exam_data.description else None,
                external_links=serialize_external_links(exam_data.external_links or []),
                exam_date=exam_data.exam_date,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(exam)
            self.db.commit()
            self.db.refresh(exam)

            # Create notifications for students in the group
            self._create_exam_notifications(exam.id, exam_data.group_id, exam.title)

            return {
                "id": exam.id,
                "group_id": exam.group_id,
                "subject_id": exam.subject_id,
                "teacher_id": exam.teacher_id,
                "title": exam.title,
                "description": exam.description,
                "external_links": parse_external_links(exam.external_links),
                "exam_date": exam.exam_date,
                "created_at": exam.created_at,
                "message": "Exam created successfully"
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Exam creation error: {str(e)}"
            )

    # Grade Management

    def create_bulk_grades(self, grade_request: BulkGradeRequest, teacher_id: str) -> Dict[str, Any]:
        """
        Create grades in bulk for homework or exam

        Args:
            grade_request: Bulk grading request
            teacher_id: Teacher creating the grades

        Returns:
            Bulk grading results

        Raises:
            HTTPException: If grading fails
        """
        try:
            # Validate homework or exam belongs to teacher
            if grade_request.homework_id:
                homework = self.db.query(Homework).filter(
                    Homework.id == grade_request.homework_id,
                    Homework.teacher_id == teacher_id
                ).first()

                if not homework:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Homework not found or access denied"
                    )

                group_id = homework.group_id
                subject_id = homework.subject_id

            elif grade_request.exam_id:
                exam = self.db.query(Exam).filter(
                    Exam.id == grade_request.exam_id,
                    Exam.teacher_id == teacher_id
                ).first()

                if not exam:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Exam not found or access denied"
                    )

                group_id = exam.group_id
                subject_id = exam.subject_id
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either homework_id or exam_id must be provided"
                )

            # Validate all students belong to the group
            student_ids = [grade.student_id for grade in grade_request.grades]
            valid_students = self.db.query(Student.id).filter(
                Student.id.in_(student_ids),
                Student.group_id == group_id
            ).all()

            valid_student_ids = {student.id for student in valid_students}
            invalid_students = set(student_ids) - valid_student_ids

            if invalid_students:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid students for this group: {list(invalid_students)}"
                )

            # Delete existing grades for this homework/exam
            if grade_request.homework_id:
                self.db.query(Grade).filter(
                    Grade.homework_id == grade_request.homework_id,
                    Grade.student_id.in_(student_ids)
                ).delete(synchronize_session=False)
            else:
                self.db.query(Grade).filter(
                    Grade.exam_id == grade_request.exam_id,
                    Grade.student_id.in_(student_ids)
                ).delete(synchronize_session=False)

            # Create new grades
            grades_created = 0
            current_time = datetime.utcnow()

            for grade_item in grade_request.grades:
                grade = Grade(
                    student_id=grade_item.student_id,
                    group_id=group_id,
                    subject_id=subject_id,
                    homework_id=grade_request.homework_id,
                    exam_id=grade_request.exam_id,
                    teacher_id=teacher_id,
                    grade=grade_item.grade,
                    max_grade=grade_request.max_grade,
                    comment=grade_item.comment,
                    graded_at=current_time,
                    created_at=current_time
                )

                self.db.add(grade)
                grades_created += 1

            self.db.commit()

            # Create notifications for students
            self._create_grade_notifications(student_ids, subject_id,
                                             "homework" if grade_request.homework_id else "exam")

            return {
                "message": "Bulk grading completed successfully",
                "grades_created": grades_created,
                "homework_id": grade_request.homework_id,
                "exam_id": grade_request.exam_id,
                "max_grade": grade_request.max_grade,
                "graded_by": teacher_id,
                "timestamp": current_time
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk grading error: {str(e)}"
            )

    def get_homework_grading_table(self, homework_id: str, teacher_id: str) -> Dict[str, Any]:
        """
        Get grading table for homework

        Args:
            homework_id: Homework ID
            teacher_id: Teacher ID

        Returns:
            Grading table with students and current grades
        """
        try:
            # Validate homework belongs to teacher
            homework = self.db.query(Homework).filter(
                Homework.id == homework_id,
                Homework.teacher_id == teacher_id
            ).first()

            if not homework:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Homework not found or access denied"
                )

            # Get students in the group
            students = self.db.query(Student).join(User).filter(
                Student.group_id == homework.group_id,
                User.is_active == True
            ).all()

            # Get existing grades for this homework
            existing_grades = self.db.query(Grade).filter(
                Grade.homework_id == homework_id
            ).all()

            grade_dict = {grade.student_id: grade for grade in existing_grades}

            # Build grading table
            student_list = []
            for student in students:
                grade = grade_dict.get(student.id)

                student_data = {
                    "student_id": student.id,
                    "student_name": student.user.full_name,
                    "current_grade": grade.grade if grade else None,
                    "current_comment": grade.comment if grade else None
                }

                student_list.append(student_data)

            return {
                "homework_id": homework.id,
                "homework_title": homework.title,
                "max_grade": 100.0,  # Default max grade
                "students": student_list
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving grading table: {str(e)}"
            )

    # Attendance Management

    def create_bulk_attendance(self, attendance_request: BulkAttendanceRequest, teacher_id: str) -> Dict[str, Any]:
        """
        Record attendance in bulk for a group-subject

        Args:
            attendance_request: Bulk attendance request
            teacher_id: Teacher recording attendance

        Returns:
            Bulk attendance results

        Raises:
            HTTPException: If recording fails
        """
        try:
            # Validate teacher has access to this group-subject
            group_subject = self.db.query(GroupSubject).filter(
                GroupSubject.group_id == attendance_request.group_id,
                GroupSubject.subject_id == attendance_request.subject_id,
                GroupSubject.teacher_id == teacher_id
            ).first()

            if not group_subject:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to record attendance for this group-subject"
                )

            # Validate all students belong to the group
            student_ids = [att.student_id for att in attendance_request.attendance]
            valid_students = self.db.query(Student.id).filter(
                Student.id.in_(student_ids),
                Student.group_id == attendance_request.group_id
            ).all()

            valid_student_ids = {student.id for student in valid_students}
            invalid_students = set(student_ids) - valid_student_ids

            if invalid_students:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid students for this group: {list(invalid_students)}"
                )

            # Delete existing attendance for this date
            self.db.query(Attendance).filter(
                Attendance.group_id == attendance_request.group_id,
                Attendance.subject_id == attendance_request.subject_id,
                Attendance.date == attendance_request.date,
                Attendance.student_id.in_(student_ids)
            ).delete(synchronize_session=False)

            # Create new attendance records
            attendance_created = 0
            current_time = datetime.utcnow()

            for att_item in attendance_request.attendance:
                attendance = Attendance(
                    student_id=att_item.student_id,
                    group_id=attendance_request.group_id,
                    subject_id=attendance_request.subject_id,
                    teacher_id=teacher_id,
                    date=attendance_request.date,
                    status=att_item.status,
                    notes=att_item.notes,
                    created_at=current_time,
                    updated_at=current_time
                )

                self.db.add(attendance)
                attendance_created += 1

            self.db.commit()

            return {
                "message": "Bulk attendance recorded successfully",
                "attendance_created": attendance_created,
                "group_id": attendance_request.group_id,
                "subject_id": attendance_request.subject_id,
                "date": attendance_request.date,
                "recorded_by": teacher_id,
                "timestamp": current_time
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk attendance error: {str(e)}"
            )

    def get_student_academic_summary(self, student_id: str) -> Dict[str, Any]:
        """
        Get comprehensive academic summary for student

        Args:
            student_id: Student ID

        Returns:
            Academic summary with grades, attendance, and statistics
        """
        try:
            # Validate student exists
            student = self.db.query(Student).join(User).filter(
                Student.id == student_id,
                User.is_active == True
            ).first()

            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )

            # Get recent grades
            recent_grades = self.db.query(Grade).filter(
                Grade.student_id == student_id
            ).order_by(desc(Grade.graded_at)).limit(10).all()

            # Get recent attendance
            recent_attendance = self.db.query(Attendance).filter(
                Attendance.student_id == student_id
            ).order_by(desc(Attendance.date)).limit(10).all()

            # Calculate statistics
            total_grades = len(recent_grades)
            average_grade = sum(grade.grade for grade in recent_grades) / total_grades if total_grades > 0 else 0

            present_count = len([att for att in recent_attendance if att.status == AttendanceStatus.PRESENT])
            total_attendance = len(recent_attendance)
            attendance_percentage = get_attendance_percentage(present_count, total_attendance)

            # Get pending homework
            pending_homework = self.get_student_homework(student_id, include_completed=False)

            return {
                "student_id": student_id,
                "student_name": student.user.full_name,
                "group_name": student.group.name,
                "summary": {
                    "total_grades": total_grades,
                    "average_grade": round(average_grade, 2),
                    "attendance_percentage": attendance_percentage,
                    "pending_homework": len(pending_homework)
                },
                "recent_grades": [
                    {
                        "id": grade.id,
                        "subject_name": grade.homework.subject.name if grade.homework else grade.exam.subject.name,
                        "type": "homework" if grade.homework_id else "exam",
                        "title": grade.homework.title if grade.homework else grade.exam.title,
                        "grade": grade.grade,
                        "max_grade": grade.max_grade,
                        "percentage": calculate_grade_percentage(grade.grade, grade.max_grade),
                        "graded_at": grade.graded_at
                    }
                    for grade in recent_grades
                ],
                "recent_attendance": [
                    {
                        "id": att.id,
                        "subject_name": att.subject.name if att.subject else None,
                        "date": att.date,
                        "status": att.status,
                        "notes": att.notes
                    }
                    for att in recent_attendance
                ],
                "pending_homework": pending_homework[:5]  # Latest 5 pending
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving academic summary: {str(e)}"
            )

    # Helper methods for notifications

    def _create_homework_notifications(self, homework_id: str, group_id: str, title: str):
        """Create notifications for new homework"""
        # This would integrate with notification service
        # For now, we'll skip the implementation
        pass

    def _create_exam_notifications(self, exam_id: str, group_id: str, title: str):
        """Create notifications for new exam"""
        # This would integrate with notification service
        # For now, we'll skip the implementation
        pass

    def _create_grade_notifications(self, student_ids: List[str], subject_id: str, type: str):
        """Create notifications for new grades"""
        # This would integrate with notification service
        # For now, we'll skip the implementation
        pass


# Service factory function
def get_academic_service(db: Session) -> AcademicService:
    """Create academic service instance"""
    return AcademicService(db)