from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import uuid
import re
from io import BytesIO

# PDF and OCR libraries
from pypdf import PdfReader
import fitz
import pytesseract
from PIL import Image


# ==========================================
# FastAPI app
# ==========================================

app = FastAPI(title="Saralvidhya API")


# ==========================================
# Database
# ==========================================

DATABASE_URL = "sqlite:///./saralvidhya.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


# ==========================================
# User table
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)


# ==========================================
# Material table
# ==========================================

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)


# Create database tables
Base.metadata.create_all(bind=engine)


# ==========================================
# Password hashing
# ==========================================

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


# ==========================================
# JWT settings
# ==========================================

SECRET_KEY = "saralvidhya-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


# ==========================================
# Request model
# ==========================================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str


# ==========================================
# Home API
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Saralvidhya API is running!"
    }


# ==========================================
# Create User API
# ==========================================

@app.post("/users")
def create_user(user: UserCreate):

    db = SessionLocal()

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        db.close()

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = pwd_context.hash(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response = {
        "message": "User created successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }

    db.close()

    return response


# ==========================================
# Login API
# ==========================================

@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    db = SessionLocal()

    user = db.query(User).filter(
        User.email == form_data.username
    ).first()

    db.close()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not pwd_context.verify(
        form_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expire
    }

    access_token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ==========================================
# Get Current Logged-in User
# ==========================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        user_id = int(user_id)

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    db = SessionLocal()

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    db.close()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


# ==========================================
# Protected Profile API
# ==========================================

@app.get("/users/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):

    return {
        "user_id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }


# ==========================================
# PDF Upload API
# ==========================================

@app.post("/materials/upload")
def upload_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):

    # Check file extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Create uploads folder
    os.makedirs("uploads", exist_ok=True)

    # Create unique filename
    unique_filename = (
        str(uuid.uuid4()) + "_" + file.filename
    )

    file_path = os.path.join(
        "uploads",
        unique_filename
    )

    # Save PDF
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    # Save information in database
    db = SessionLocal()

    material = Material(
        filename=file.filename,
        file_path=file_path,
        user_id=current_user.id
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    material_id = material.id

    db.close()

    return {
        "message": "PDF uploaded successfully",
        "material_id": material_id,
        "filename": file.filename,
        "user_id": current_user.id
    }


# ==========================================
# Get Material
# ==========================================

def get_user_material(
    material_id: int,
    current_user: User
):

    db = SessionLocal()

    material = db.query(Material).filter(
        Material.id == material_id,
        Material.user_id == current_user.id
    ).first()

    db.close()

    if material is None:
        raise HTTPException(
            status_code=404,
            detail="Material not found"
        )

    if not os.path.exists(material.file_path):
        raise HTTPException(
            status_code=404,
            detail="PDF file not found"
        )

    return material


# ==========================================
# Extract text from PDF
# ==========================================

def extract_pdf_text(file_path: str):

    extracted_text = ""

    # First try normal PDF text extraction
    try:
        reader = PdfReader(file_path)

        for page in reader.pages:
            text = page.extract_text()

            if text:
                extracted_text += text + "\n"

    except Exception:
        extracted_text = ""

    # If PDF has little/no text, use OCR
    if len(extracted_text.strip()) < 50:

        try:
            document = fitz.open(file_path)

            ocr_text = ""

            for page in document:

                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2)
                )

                image_bytes = pixmap.tobytes("png")

                image = Image.open(
                    BytesIO(image_bytes)
                )

                page_text = pytesseract.image_to_string(
                    image
                )

                ocr_text += page_text + "\n"

            document.close()

            extracted_text = ocr_text

        except Exception as e:

            raise HTTPException(
                status_code=500,
                detail=f"OCR failed: {str(e)}"
            )

    if not extracted_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF"
        )

    return extracted_text.strip()


# ==========================================
# Clean extracted text
# ==========================================

def clean_text(text: str):

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    text = re.sub(
        r"\n+",
        "\n",
        text
    )

    return text.strip()


# ==========================================
# Generate Summary
# ==========================================

def generate_summary(text: str):

    text = clean_text(text)

    # Split text into sentences
    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip().split()) >= 5
    ]

    # Remove duplicate sentences
    unique_sentences = []

    for sentence in sentences:

        if sentence.lower() not in [
            item.lower()
            for item in unique_sentences
        ]:
            unique_sentences.append(sentence)

    # Take the first important sentences
    summary_sentences = unique_sentences[:5]

    if not summary_sentences:

        words = text.split()

        summary = " ".join(
            words[:100]
        )

    else:

        summary = " ".join(
            summary_sentences
        )

    return summary


# ==========================================
# Summary API
# ==========================================

@app.post("/materials/{material_id}/summary")
def generate_material_summary(
    material_id: int,
    current_user: User = Depends(get_current_user)
):

    material = get_user_material(
        material_id,
        current_user
    )

    text = extract_pdf_text(
        material.file_path
    )

    summary = generate_summary(text)

    return {
        "material_id": material.id,
        "filename": material.filename,
        "summary": summary
    }


# ==========================================
# Generate Quiz
# ==========================================

def generate_quiz(text: str):

    text = clean_text(text)

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.split()) >= 8
    ]

    quiz = []

    for index, sentence in enumerate(sentences[:5], start=1):

        words = sentence.split()

        if len(words) < 8:
            continue

        # Select a meaningful word
        answer_index = min(
            4,
            len(words) - 1
        )

        answer = re.sub(
            r"[^\w-]",
            "",
            words[answer_index]
        )

        if not answer:
            continue

        question_words = words.copy()

        question_words[answer_index] = "_____"

        question = " ".join(
            question_words
        )

        quiz.append({
            "question": question,
            "answer": answer
        })

    # Fallback question if PDF has very little text
    if not quiz:

        quiz.append({
            "question": "What is the main topic of the uploaded PDF?",
            "answer": "Refer to the uploaded study material."
        })

    return quiz


# ==========================================
# Quiz API
# ==========================================

@app.post("/materials/{material_id}/quiz")
def generate_material_quiz(
    material_id: int,
    current_user: User = Depends(get_current_user)
):

    material = get_user_material(
        material_id,
        current_user
    )

    text = extract_pdf_text(
        material.file_path
    )

    quiz = generate_quiz(text)

    return {
        "material_id": material.id,
        "filename": material.filename,
        "quiz": quiz
    }