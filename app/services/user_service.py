# app/services/user_service.py
"""
User management service with passionate user experience!
Handles creation, updates, and management of all user types.
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from datetime import datetime

from ..models import User, Student, Parent, Teacher, Group
from ..utils.auth import hash_password, generate_secure_password
from ..utils.helpers import UserRole, sanitize_phone_number, clean_string
from ..schemas.users import (
    StudentCreate, ParentCreate, TeacherCreate,
    StudentUpdate, ParentUpdate, TeacherUpdate,
    UserSearchRequest, StudentSearchRequest
)


class UserManagementService:
    """
    Comprehensive user management service handling all user operations
    with robust validation and error handling!
    """

    def __init__(self, db: Session):
        self.db = db

    def create_student(self, student_data: StudentCreate, admin_id: str) -> Dict[str, Any]:
        """
        Create a new student with user account

        Args:
            student_data: Student creation data
            admin_id: Admin creating the student

        Returns:
            Created student information with credentials

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Sanitize phone number
            phone = sanitize_phone_number(student_data.phone)

            # Check if phone already exists for this role
            existing_user = self.db.query(User).filter(
                User.phone == phone,
                User.role == UserRole.STUDENT
            ).first()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Student with this phone number already exists"
                )

            # Validate group exists
            group = self.db.query(Group).filter(
                Group.id == student_data.group_id,
                Group.is_active == True
            ).first()

            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found or inactive"
                )

            # Validate parent exists if provided
            parent = None
            if student_data.parent_id:
                parent = self.db.query(Parent).filter(
                    Parent.id == student_data.parent_id
                ).first()

                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent not found"
                    )

            # Create user account
            user = User(
                role=UserRole.STUDENT,
                phone=phone,
                password_hash=hash_password(student_data.password),
                full_name=clean_string(student_data.full_name),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(user)
            self.db.flush()  # Get user ID

            # Create student profile
            student = Student(
                user_id=user.id,
                group_id=student_data.group_id,
                parent_id=student_data.parent_id,
                graduation_year=student_data.graduation_year,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(student)
            self.db.commit()

            return {
                "message": "Student created successfully",
                "user_id": user.id,
                "student_id": student.id,
                "credentials": {
                    "phone": phone,
                    "password": student_data.password,
                    "role": UserRole.STUDENT,
                    "full_name": user.full_name
                },
                "created_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Student creation error: {str(e)}"
            )

    def create_parent(self, parent_data: ParentCreate, admin_id: str) -> Dict[str, Any]:
        """
        Create a new parent with user account

        Args:
            parent_data: Parent creation data
            admin_id: Admin creating the parent

        Returns:
            Created parent information with credentials

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Sanitize phone number
            phone = sanitize_phone_number(parent_data.phone)

            # Check if phone already exists for this role
            existing_user = self.db.query(User).filter(
                User.phone == phone,
                User.role == UserRole.PARENT
            ).first()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent with this phone number already exists"
                )

            # Create user account
            user = User(
                role=UserRole.PARENT,
                phone=phone,
                password_hash=hash_password(parent_data.password),
                full_name=clean_string(parent_data.full_name),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(user)
            self.db.flush()  # Get user ID

            # Create parent profile
            parent = Parent(
                user_id=user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(parent)
            self.db.commit()

            return {
                "message": "Parent created successfully",
                "user_id": user.id,
                "parent_id": parent.id,
                "credentials": {
                    "phone": phone,
                    "password": parent_data.password,
                    "role": UserRole.PARENT,
                    "full_name": user.full_name
                },
                "created_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Parent creation error: {str(e)}"
            )

    def create_teacher(self, teacher_data: TeacherCreate, admin_id: str) -> Dict[str, Any]:
        """
        Create a new teacher with user account

        Args:
            teacher_data: Teacher creation data
            admin_id: Admin creating the teacher

        Returns:
            Created teacher information with credentials

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Sanitize phone number
            phone = sanitize_phone_number(teacher_data.phone)

            # Check if phone already exists for this role
            existing_user = self.db.query(User).filter(
                User.phone == phone,
                User.role == UserRole.TEACHER
            ).first()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Teacher with this phone number already exists"
                )

            # Create user account
            user = User(
                role=UserRole.TEACHER,
                phone=phone,
                password_hash=hash_password(teacher_data.password),
                full_name=clean_string(teacher_data.full_name),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(user)
            self.db.flush()  # Get user ID

            # Create teacher profile
            teacher = Teacher(
                user_id=user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(teacher)
            self.db.commit()

            return {
                "message": "Teacher created successfully",
                "user_id": user.id,
                "teacher_id": teacher.id,
                "credentials": {
                    "phone": phone,
                    "password": teacher_data.password,
                    "role": UserRole.TEACHER,
                    "full_name": user.full_name
                },
                "created_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Teacher creation error: {str(e)}"
            )

    def get_all_students(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """
        Get paginated list of all students

        Args:
            page: Page number
            size: Page size

        Returns:
            Paginated student list with metadata
        """
        try:
            offset = (page - 1) * size

            # Get students with user and group information
            students_query = self.db.query(Student).join(User).filter(User.is_active == True)

            total = students_query.count()
            students = students_query.offset(offset).limit(size).all()

            # Calculate pagination metadata
            total_pages = (total + size - 1) // size

            student_list = []
            for student in students:
                student_data = {
                    "id": student.id,
                    "user_id": student.user_id,
                    "group_id": student.group_id,
                    "parent_id": student.parent_id,
                    "graduation_year": student.graduation_year,
                    "created_at": student.created_at,
                    "updated_at": student.updated_at,
                    "user": {
                        "id": student.user.id,
                        "role": student.user.role,
                        "phone": student.user.phone,
                        "full_name": student.user.full_name,
                        "avatar_url": student.user.avatar_url,
                        "is_active": student.user.is_active
                    }
                }

                # Add group information if available
                if student.group:
                    student_data["group_name"] = student.group.name

                # Add parent information if available
                if student.parent and student.parent.user:
                    student_data["parent_name"] = student.parent.user.full_name

                student_list.append(student_data)

            return {
                "students": student_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": total_pages
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving students: {str(e)}"
            )

    def get_all_parents(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """
        Get paginated list of all parents with their children

        Args:
            page: Page number
            size: Page size

        Returns:
            Paginated parent list with metadata
        """
        try:
            offset = (page - 1) * size

            # Get parents with user information
            parents_query = self.db.query(Parent).join(User).filter(User.is_active == True)

            total = parents_query.count()
            parents = parents_query.offset(offset).limit(size).all()

            # Calculate pagination metadata
            total_pages = (total + size - 1) // size

            parent_list = []
            for parent in parents:
                # Get children for this parent
                children = self.db.query(Student).join(User).filter(
                    Student.parent_id == parent.id,
                    User.is_active == True
                ).all()

                parent_data = {
                    "id": parent.id,
                    "user_id": parent.user_id,
                    "created_at": parent.created_at,
                    "updated_at": parent.updated_at,
                    "user": {
                        "id": parent.user.id,
                        "role": parent.user.role,
                        "phone": parent.user.phone,
                        "full_name": parent.user.full_name,
                        "avatar_url": parent.user.avatar_url,
                        "is_active": parent.user.is_active
                    },
                    "children_count": len(children),
                    "children": [
                        {
                            "id": child.id,
                            "full_name": child.user.full_name,
                            "group_id": child.group_id,
                            "graduation_year": child.graduation_year
                        }
                        for child in children
                    ]
                }

                parent_list.append(parent_data)

            return {
                "parents": parent_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": total_pages
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving parents: {str(e)}"
            )

    def get_all_teachers(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """
        Get paginated list of all teachers

        Args:
            page: Page number
            size: Page size

        Returns:
            Paginated teacher list with metadata
        """
        try:
            offset = (page - 1) * size

            # Get teachers with user information
            teachers_query = self.db.query(Teacher).join(User).filter(User.is_active == True)

            total = teachers_query.count()
            teachers = teachers_query.offset(offset).limit(size).all()

            # Calculate pagination metadata
            total_pages = (total + size - 1) // size

            teacher_list = []
            for teacher in teachers:
                teacher_data = {
                    "id": teacher.id,
                    "user_id": teacher.user_id,
                    "created_at": teacher.created_at,
                    "updated_at": teacher.updated_at,
                    "user": {
                        "id": teacher.user.id,
                        "role": teacher.user.role,
                        "phone": teacher.user.phone,
                        "full_name": teacher.user.full_name,
                        "avatar_url": teacher.user.avatar_url,
                        "is_active": teacher.user.is_active
                    }
                }

                teacher_list.append(teacher_data)

            return {
                "teachers": teacher_list,
                "total": total,
                "page": page,
                "size": size,
                "pages": total_pages
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving teachers: {str(e)}"
            )

    def get_student_by_id(self, student_id: str) -> Dict[str, Any]:
        """
        Get student by ID with full details

        Args:
            student_id: Student ID

        Returns:
            Student details

        Raises:
            HTTPException: If student not found
        """
        try:
            student = self.db.query(Student).join(User).filter(
                Student.id == student_id,
                User.is_active == True
            ).first()

            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )

            student_data = {
                "id": student.id,
                "user_id": student.user_id,
                "group_id": student.group_id,
                "parent_id": student.parent_id,
                "graduation_year": student.graduation_year,
                "created_at": student.created_at,
                "updated_at": student.updated_at,
                "user": {
                    "id": student.user.id,
                    "role": student.user.role,
                    "phone": student.user.phone,
                    "full_name": student.user.full_name,
                    "avatar_url": student.user.avatar_url,
                    "is_active": student.user.is_active
                }
            }

            # Add group information
            if student.group:
                student_data["group"] = {
                    "id": student.group.id,
                    "name": student.group.name,
                    "description": student.group.description
                }

            # Add parent information
            if student.parent and student.parent.user:
                student_data["parent"] = {
                    "id": student.parent.id,
                    "full_name": student.parent.user.full_name,
                    "phone": student.parent.user.phone
                }

            return student_data

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving student: {str(e)}"
            )

    def assign_parent_to_student(self, student_id: str, parent_id: str, admin_id: str) -> Dict[str, Any]:
        """
        Assign parent to student

        Args:
            student_id: Student ID
            parent_id: Parent ID
            admin_id: Admin performing the assignment

        Returns:
            Success response

        Raises:
            HTTPException: If assignment fails
        """
        try:
            # Validate student exists
            student = self.db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )

            # Validate parent exists
            parent = self.db.query(Parent).filter(Parent.id == parent_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent not found"
                )

            # Update student's parent assignment
            student.parent_id = parent_id
            student.updated_at = datetime.utcnow()

            self.db.commit()

            return {
                "message": "Parent assigned to student successfully",
                "student_id": student_id,
                "parent_id": parent_id,
                "assigned_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Parent assignment error: {str(e)}"
            )

    def change_student_group(self, student_id: str, new_group_id: str, admin_id: str) -> Dict[str, Any]:
        """
        Change student's group

        Args:
            student_id: Student ID
            new_group_id: New group ID
            admin_id: Admin performing the change

        Returns:
            Success response

        Raises:
            HTTPException: If change fails
        """
        try:
            # Validate student exists
            student = self.db.query(Student).filter(Student.id == student_id).first()
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found"
                )

            # Validate new group exists and is active
            new_group = self.db.query(Group).filter(
                Group.id == new_group_id,
                Group.is_active == True
            ).first()
            if not new_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="New group not found or inactive"
                )

            old_group_id = student.group_id

            # Update student's group
            student.group_id = new_group_id
            student.updated_at = datetime.utcnow()

            self.db.commit()

            return {
                "message": "Student group changed successfully",
                "student_id": student_id,
                "old_group_id": old_group_id,
                "new_group_id": new_group_id,
                "changed_by": admin_id,
                "timestamp": datetime.utcnow()
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Group change error: {str(e)}"
            )

    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics for admin dashboard

        Returns:
            User statistics
        """
        try:
            stats = {
                "total_users": self.db.query(User).count(),
                "active_users": self.db.query(User).filter(User.is_active == True).count(),
                "total_students": self.db.query(User).filter(User.role == UserRole.STUDENT).count(),
                "total_teachers": self.db.query(User).filter(User.role == UserRole.TEACHER).count(),
                "total_parents": self.db.query(User).filter(User.role == UserRole.PARENT).count(),
                "active_students": self.db.query(User).filter(
                    User.role == UserRole.STUDENT,
                    User.is_active == True
                ).count(),
                "active_teachers": self.db.query(User).filter(
                    User.role == UserRole.TEACHER,
                    User.is_active == True
                ).count(),
                "active_parents": self.db.query(User).filter(
                    User.role == UserRole.PARENT,
                    User.is_active == True
                ).count()
            }

            return stats

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving user statistics: {str(e)}"
            )


# Service factory function
def get_user_service(db: Session) -> UserManagementService:
    """Create user management service instance"""
    return UserManagementService(db)