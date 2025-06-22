from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    """Hash a password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)