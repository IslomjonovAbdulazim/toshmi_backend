import os
import requests
from sqlalchemy import create_engine


def setup_ssl_cert():
    """Download and setup SSL certificate"""
    cert_dir = os.path.expanduser("~/.cloud-certs")
    cert_path = os.path.join(cert_dir, "root.crt")

    os.makedirs(cert_dir, exist_ok=True)

    if not os.path.exists(cert_path):
        print("Downloading SSL certificate...")
        # Common root certificate URL - may need adjustment
        cert_url = "https://www.postgresql.org/media/keys/ACCC4CF8.asc"
        try:
            response = requests.get(cert_url)
            with open(cert_path, 'w') as f:
                f.write(response.text)
            print(f"✅ Certificate saved to {cert_path}")
        except:
            print("❌ Could not download certificate")
            print("Manually place your SSL certificate at ~/.cloud-certs/root.crt")
            return None

    return cert_path


def test_ssl_connection():
    """Test SSL connection to remote PostgreSQL"""
    cert_path = setup_ssl_cert()

    # Set environment variable
    os.environ['PGSSLROOTCERT'] = cert_path or os.path.expanduser("~/.cloud-certs/root.crt")

    # Connection string with SSL
    db_url = "postgresql://gen_user:(8Ah)S$aY)lF6t@islomjonovabdulazim-toshmi-backend-0914.twc1.net:5432/default_db?sslmode=require&connect_timeout=30"

    try:
        print("Testing SSL connection...")
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            print("✅ SSL connection successful!")
            return db_url
    except Exception as e:
        print(f"❌ SSL connection failed: {e}")

        # Try without SSL verification
        db_url_no_verify = "postgresql://gen_user:(8Ah)S$aY)lF6t@3d7780415a2721a636acfe11.twc1.net:5432/default_db?sslmode=require"
        try:
            print("Trying without SSL verification...")
            engine = create_engine(db_url_no_verify)
            with engine.connect() as conn:
                result = conn.execute("SELECT version()")
                print("✅ Connection successful (no SSL verify)!")
                return db_url_no_verify
        except Exception as e2:
            print(f"❌ Connection failed: {e2}")
            return None


def update_env_file(database_url):
    """Update .env file with SSL connection"""
    env_content = """DATABASE_URL={}
JWT_SECRET=UgoxERiU-d3vFK8z-a9lU_mRrN12oWKcUu_zjn1CHZ0
JWT_EXPIRE_MINUTES=30
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
MAX_IMAGE_SIZE=3145728""".format(database_url)

    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ Updated .env file")


if __name__ == "__main__":
    print("🔐 Setting up SSL PostgreSQL connection...")

    db_url = test_ssl_connection()
    if db_url:
        update_env_file(db_url)
        print("\n🎉 Remote PostgreSQL configured!")
    else:
        print("\n❌ Setup failed")
        print("Manual steps:")
        print("1. Get SSL certificate from your provider")
        print("2. Save to ~/.cloud-certs/root.crt")
        print("3. export PGSSLROOTCERT=\"$HOME/.cloud-certs/root.crt\"")
        print("4. Test with psql")