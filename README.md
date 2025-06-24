# School Management System API Endpoints

## Authentication
- `POST /auth/login` - User login
- `PUT /auth/change-password` - Change password
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user profile

## Admin Endpoints

### Students (Full CRUD)
- `POST /admin/students` - Create student
- `GET /admin/students` - List all students
- `GET /admin/students/{student_id}` - Get student details
- `PUT /admin/students/{student_id}` - Update student
- `DELETE /admin/students/{student_id}` - Deactivate student

### Teachers (Full CRUD)
- `POST /admin/teachers` - Create teacher
- `GET /admin/teachers` - List all teachers
- `GET /admin/teachers/{teacher_id}` - Get teacher details
- `PUT /admin/teachers/{teacher_id}` - Update teacher
- `DELETE /admin/teachers/{teacher_id}` - Deactivate teacher

### Parents (Full CRUD)
- `POST /admin/parents` - Create parent
- `GET /admin/parents` - List all parents
- `PUT /admin/parents/{parent_id}` - Update parent
- `DELETE /admin/parents/{parent_id}` - Deactivate parent

### Groups (Full CRUD)
- `POST /admin/groups` - Create group
- `GET /admin/groups` - List all groups
- `GET /admin/groups/{group_id}` - Get group details
- `PUT /admin/groups/{group_id}` - Update group
- `DELETE /admin/groups/{group_id}` - Delete group (if no students)

### Subjects (Full CRUD)
- `POST /admin/subjects` - Create subject
- `GET /admin/subjects` - List all subjects
- `GET /admin/subjects/{subject_id}` - Get subject details
- `PUT /admin/subjects/{subject_id}` - Update subject
- `DELETE /admin/subjects/{subject_id}` - Delete subject (if no assignments)

### News (Full CRUD)
- `POST /admin/news` - Create news
- `GET /admin/news` - List all news
- `GET /admin/news/{news_id}` - Get news details
- `PUT /admin/news/{news_id}` - Update news
- `DELETE /admin/news/{news_id}` - Delete news

### Schedule (Full CRUD)
- `POST /admin/schedule` - Create schedule
- `GET /admin/schedule` - List all schedules
- `GET /admin/schedule/{schedule_id}` - Get schedule details
- `PUT /admin/schedule/{schedule_id}` - Update schedule
- `DELETE /admin/schedule/{schedule_id}` - Delete schedule

### Other Admin Operations
- `POST /admin/assign-teacher` - Assign teacher to group-subject
- `POST /admin/payments` - Record payment
- `PUT /admin/monthly-payment-status` - Update monthly payment status

## Teacher Endpoints

### Homework (Full CRUD)
- `POST /teacher/homework` - Create homework
- `GET /teacher/homework` - List my homework
- `PUT /teacher/homework/{homework_id}` - Update homework
- `DELETE /teacher/homework/{homework_id}` - Delete homework (if no grades)

### Exams (Full CRUD)
- `POST /teacher/exams` - Create exam
- `GET /teacher/exams` - List my exams
- `PUT /teacher/exams/{exam_id}` - Update exam
- `DELETE /teacher/exams/{exam_id}` - Delete exam (if no grades)

### Grading
- `GET /teacher/homework/{homework_id}/grading-table` - Get homework grading table
- `GET /teacher/exams/{exam_id}/grading-table` - Get exam grading table
- `POST /teacher/bulk-grade` - Submit bulk grades
- `POST /teacher/bulk-attendance` - Submit bulk attendance

### Other Teacher Operations
- `GET /teacher/groups/{group_id}/students` - Get students in group

## Student Endpoints (Read Only)
- `GET /student/homework` - Get my homework assignments
- `GET /student/exams` - Get my exams
- `GET /student/grades` - Get my grades
- `GET /student/attendance` - Get my attendance
- `GET /student/schedule` - Get my class schedule
- `GET /student/payments` - Get my payment records
- `GET /student/dashboard` - Get dashboard summary

## Parent Endpoints (Read Only)
- `GET /parent/children` - List my children
- `GET /parent/children/{child_id}/homework` - Get child's homework
- `GET /parent/children/{child_id}/grades` - Get child's grades
- `GET /parent/children/{child_id}/attendance` - Get child's attendance
- `GET /parent/children/{child_id}/payments` - Get child's payments
- `GET /parent/dashboard` - Get dashboard summary

## File Management
- `POST /files/profile-picture` - Upload profile picture
- `POST /files/homework/{homework_id}/upload` - Upload homework file
- `POST /files/exam/{exam_id}/upload` - Upload exam file
- `POST /files/news/{news_id}/upload-image` - Upload news image
- `GET /files/{file_id}` - Download file
- `DELETE /files/{file_id}` - Delete file

## System Endpoints
- `GET /` - API info
- `GET /health` - Health check
- `POST /init-db` - Initialize database
- `GET /stats` - System statistics

## Key Features

### Admin Password
- Admin password is stored in plain text (not hashed) as requested
- Can be configured via `ADMIN_PASSWORD` environment variable
- Default: `"sWk}X2<1#5[*"`

### CRUD Operations
- All major entities support full CRUD operations
- Soft deletes for users (deactivation)
- Hard deletes for system entities (groups, subjects, etc.)
- Validation prevents deletion when dependencies exist

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (admin, teacher, student, parent)
- Protected endpoints based on user roles

### File Management
- Profile pictures, homework documents, exam files
- Automatic file organization in folders
- File size limits and validation

### Data Relationships
- Proper SQLAlchemy relationships for efficient queries
- Automatic data loading via relationships
- Consistent data structure across endpoints