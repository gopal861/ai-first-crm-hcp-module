from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# FORCE load env
load_dotenv(override=True)

# DEBUG PRINT
print("USING DB:", os.getenv("DB_NAME"))

# BUILD URL
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

print("FINAL URL:", DATABASE_URL)

# CREATE ENGINE (fresh every run)
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()