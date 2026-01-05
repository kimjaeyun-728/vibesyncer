from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# .env 파일에 있는 내용을 불러옵니다.
load_dotenv()

# .env에서 DATABASE_URL 가져오기
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# DB 엔진 생성 (Supabase와 연결)
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 데이터베이스 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 모델(테이블)이 상속받을 기본 클래스
Base = declarative_base()

# API 요청 때마다 DB를 열고 닫아주는 함수 (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()