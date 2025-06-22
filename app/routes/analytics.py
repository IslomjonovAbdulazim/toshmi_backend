from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_admin, require_teacher
from app.crud import get_class_report, get_payment_report

router = APIRouter()


@router.get("/overview")
def get_school_overview(db: Session = Depends(get_db), admin=Depends(require_admin)):
    from app.models import User, Student, Payment

    total_students = db.query(Student).count()
    total_teachers = db.query(User).filter(User.role == "teacher").count()
    total_parents = db.query(User).filter(User.role == "parent").count()

    # Recent payments
    import datetime
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


@router.get("/class-performance")
def get_class_performance(group_id: str, subject_id: str, db: Session = Depends(get_db),
                          teacher=Depends(require_teacher)):
    return get_class_report(db, group_id, subject_id)


@router.get("/payment-analytics")
def get_payment_analytics(month: int, year: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    return get_payment_report(db, month, year)