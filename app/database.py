from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Configure connection arguments based on environment
connect_args = {
    "connect_timeout": 10,
}

# Add SSL configuration for production/cloud databases
if "twc1.net" in settings.database_url or settings.environment == "production":
    connect_args["sslmode"] = "require"
else:
    connect_args["sslmode"] = "prefer"

# Create SQLAlchemy engine with proper configuration for production
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,  # Recycle connections every 5 minutes
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Additional connections allowed
    connect_args=connect_args
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Function to create tables
def create_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")

        # Import all models to ensure they're registered
        from . import models

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise


# Function to test database connection
def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False