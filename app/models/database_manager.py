from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.models.models import Base, User, Group, Subject
from app.core.security import hash_password
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:

    @staticmethod
    def drop_all_tables():
        """Drop all existing tables in the database"""
        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            if existing_tables:
                logger.info(f"Found {len(existing_tables)} existing tables: {existing_tables}")

                with engine.connect() as conn:
                    # For PostgreSQL, use CASCADE to handle foreign keys
                    for table_name in existing_tables:
                        conn.execute(text(f"DROP TABLE IF EXISTS \"{table_name}\" CASCADE;"))
                        logger.info(f"Dropped table: {table_name}")

                    conn.commit()

                logger.info("All existing tables dropped successfully")
            else:
                logger.info("No existing tables found")

        except Exception as e:
            logger.error(f"Error dropping tables: {str(e)}")
            # Alternative PostgreSQL approach
            try:
                with engine.connect() as conn:
                    # Get all table names from information_schema
                    result = conn.execute(text("""
                                               SELECT tablename
                                               FROM pg_tables
                                               WHERE schemaname = 'public'
                                               """))
                    tables = [row[0] for row in result]

                    if tables:
                        logger.info(f"Found {len(tables)} PostgreSQL tables: {tables}")

                        # Drop all tables with CASCADE
                        for table in tables:
                            conn.execute(text(f"DROP TABLE IF EXISTS \"{table}\" CASCADE;"))
                            logger.info(f"Dropped PostgreSQL table: {table}")

                        conn.commit()
                        logger.info("All PostgreSQL tables dropped successfully")
                    else:
                        logger.info("No PostgreSQL tables found")

            except Exception as pg_error:
                logger.error(f"PostgreSQL drop error: {str(pg_error)}")
                raise

    @staticmethod
    def create_all_tables():
        """Create all tables defined in models"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

    @staticmethod
    def create_initial_admin():
        """Create initial admin user"""
        db = next(get_db())
        try:
            # Check if admin already exists
            existing_admin = db.query(User).filter(User.role == "admin").first()
            if existing_admin:
                logger.info("Admin user already exists")
                return existing_admin

            # Create admin user
            admin_user = User(
                phone="+998901234567",
                password_hash=hash_password("admin123"),
                role="admin",
                first_name="System",
                last_name="Administrator",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            logger.info(f"Admin user created with ID: {admin_user.id}")
            return admin_user

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating admin user: {str(e)}")
            raise
        finally:
            db.close()

    @staticmethod
    def create_sample_data():
        """Create sample groups and subjects for testing"""
        db = next(get_db())
        try:
            # Create sample groups
            groups_data = [
                {"name": "10-A", "academic_year": "2024-2025"},
                {"name": "10-B", "academic_year": "2024-2025"},
                {"name": "11-A", "academic_year": "2024-2025"},
                {"name": "11-B", "academic_year": "2024-2025"},
            ]

            for group_data in groups_data:
                existing_group = db.query(Group).filter(Group.name == group_data["name"]).first()
                if not existing_group:
                    group = Group(**group_data)
                    db.add(group)
                    logger.info(f"Created group: {group_data['name']}")

            # Create sample subjects
            subjects_data = [
                {"name": "Matematika", "code": "MATH"},
                {"name": "Fizika", "code": "PHYS"},
                {"name": "Kimyo", "code": "CHEM"},
                {"name": "Biologiya", "code": "BIO"},
                {"name": "Ingliz tili", "code": "ENG"},
                {"name": "O'zbek tili", "code": "UZB"},
                {"name": "Tarix", "code": "HIST"},
                {"name": "Geografiya", "code": "GEO"},
            ]

            for subject_data in subjects_data:
                existing_subject = db.query(Subject).filter(Subject.code == subject_data["code"]).first()
                if not existing_subject:
                    subject = Subject(**subject_data)
                    db.add(subject)
                    logger.info(f"Created subject: {subject_data['name']}")

            db.commit()
            logger.info("Sample data created successfully")

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating sample data: {str(e)}")
            raise
        finally:
            db.close()

    @staticmethod
    def get_database_stats():
        """Get current database statistics"""
        db = next(get_db())
        try:
            stats = {}

            # Get table counts
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            stats["total_tables"] = len(tables)
            stats["table_names"] = tables

            # Get record counts for main tables
            try:
                stats["users"] = db.query(User).count()
                stats["groups"] = db.query(Group).count()
                stats["subjects"] = db.query(Subject).count()
            except:
                stats["users"] = 0
                stats["groups"] = 0
                stats["subjects"] = 0

            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {"error": str(e)}
        finally:
            db.close()

    @staticmethod
    def reset_database():
        """Complete database reset - drop all tables and recreate"""
        try:
            logger.info("Starting complete database reset...")

            # Step 1: Drop all existing tables
            DatabaseManager.drop_all_tables()

            # Step 2: Create all tables fresh
            DatabaseManager.create_all_tables()

            # Step 3: Create initial admin user
            admin_user = DatabaseManager.create_initial_admin()

            # Step 4: Create sample data
            DatabaseManager.create_sample_data()

            logger.info("Database reset completed successfully")

            return {
                "success": True,
                "message": "Database reset completed",
                "admin_user": {
                    "id": admin_user.id,
                    "phone": admin_user.phone,
                    "role": admin_user.role
                },
                "stats": DatabaseManager.get_database_stats()
            }

        except Exception as e:
            logger.error(f"Database reset failed: {str(e)}")
            raise Exception(f"Database reset failed: {str(e)}")


def verify_database_connection():
    """Verify database connection is working"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False