from .user_schemas import (
    UserBase, UserCreate, UserResponse,
    StudentBase, StudentCreate, StudentResponse,
    ParentBase, ParentCreate, ParentResponse,
    TeacherBase, TeacherCreate, TeacherResponse
)
from .academic_schemas import (
    GroupBase, GroupCreate, GroupResponse,
    SubjectBase, SubjectCreate, SubjectResponse,
    GroupSubjectBase, GroupSubjectCreate, GroupSubjectResponse,
    ScheduleBase, ScheduleCreate, ScheduleResponse
)
from .grade_schemas import (
    HomeworkBase, HomeworkCreate, HomeworkResponse,
    HomeworkGradeBase, HomeworkGradeCreate, HomeworkGradeResponse,
    ExamBase, ExamCreate, ExamResponse,
    ExamGradeBase, ExamGradeCreate, ExamGradeResponse
)
from .misc_schemas import (
    AttendanceBase, AttendanceCreate, AttendanceResponse,
    PaymentBase, PaymentCreate, PaymentResponse,
    NewsBase, NewsCreate, NewsResponse
)
from .auth_schemas import LoginRequest, Token, TokenData
from .bulk_grade_schemas import StudentGradeRow, HomeworkGradingTable, ExamGradingTable, BulkGradeSubmission
from .recent_grades_schemas import RecentGradeItem, RecentGradesResponse