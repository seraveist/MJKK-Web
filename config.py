from dotenv import load_dotenv
import os

load_dotenv()  # .env 파일의 설정을 로드

class Config:
    DEBUG = os.environ.get("DEBUG", False)
    DB_USER = os.environ.get("DB_USER", "defaultUser")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "defaultPassword")
    DB_URL = f"mongodb+srv://{os.environ.get('DB_USER', 'defaultUser')}:{os.environ.get('DB_PASSWORD', 'defaultPassword')}@cluster0.6nqoq8u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
