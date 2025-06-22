from sqlalchemy.orm import Session
from app.models import Attendance, Payment, News
from app.schemas import AttendanceCreate, PaymentCreate, NewsCreate
import uuid
import json


def create_attendance(db: Session, attendance: AttendanceCreate):
    db_attendance = Attendance(
        id=str(uuid.uuid4()),
        student_id=attendance.student_id,
        group_subject_id=attendance.group_subject_id,
        date=attendance.date,
        status=attendance.status,
        comment=attendance.comment
    )
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    return db_attendance


def get_attendance_by_student(db: Session, student_id: str):
    return db.query(Attendance).filter(Attendance.student_id == student_id).all()


def get_attendance_by_group_subject_and_date(db: Session, group_subject_id: str, date: str):
    return db.query(Attendance).filter(
        Attendance.group_subject_id == group_subject_id,
        Attendance.date == date
    ).all()


def create_payment(db: Session, payment: PaymentCreate):
    db_payment = Payment(
        id=str(uuid.uuid4()),
        student_id=payment.student_id,
        month=payment.month,
        year=payment.year,
        amount_paid=payment.amount_paid,
        is_fully_paid=payment.is_fully_paid,
        comment=payment.comment
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def get_payments_by_student(db: Session, student_id: str):
    return db.query(Payment).filter(Payment.student_id == student_id).all()


def get_payments_by_month_year(db: Session, month: int, year: int):
    return db.query(Payment).filter(Payment.month == month, Payment.year == year).all()


def update_payment(db: Session, payment_id: str, is_fully_paid: bool, comment: str = None):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment:
        payment.is_fully_paid = is_fully_paid
        if comment:
            payment.comment = comment
        db.commit()
        db.refresh(payment)
    return payment


def create_news(db: Session, news: NewsCreate):
    # Convert lists to JSON strings for SQLite
    media_urls_json = json.dumps(news.media_urls) if news.media_urls else None
    links_json = json.dumps(news.links) if news.links else None

    db_news = News(
        id=str(uuid.uuid4()),
        title=news.title,
        body=news.body,
        media_urls=media_urls_json,
        links=links_json
    )
    db.add(db_news)
    db.commit()
    db.refresh(db_news)

    # Convert back to lists for response
    if db_news.media_urls:
        db_news.media_urls = json.loads(db_news.media_urls)
    if db_news.links:
        db_news.links = json.loads(db_news.links)

    return db_news


def get_all_news(db: Session):
    news_list = db.query(News).order_by(News.created_at.desc()).all()
    # Convert JSON strings back to lists
    for news in news_list:
        if news.media_urls:
            news.media_urls = json.loads(news.media_urls)
        if news.links:
            news.links = json.loads(news.links)
    return news_list


def get_news(db: Session, news_id: str):
    news = db.query(News).filter(News.id == news_id).first()
    if news:
        # Convert JSON strings back to lists
        if news.media_urls:
            news.media_urls = json.loads(news.media_urls)
        if news.links:
            news.links = json.loads(news.links)
    return news