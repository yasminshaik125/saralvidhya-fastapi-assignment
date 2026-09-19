# Saralvidhya FastAPI – PDF OCR, Summary and Quiz API

A FastAPI-based backend application developed for the Saralvidhya internship assignment. The application provides user authentication, PDF upload, OCR-based text extraction, document summarization, and quiz generation from uploaded PDF materials.

## Features

- User registration
- Secure password hashing
- JWT-based authentication
- OAuth2 password flow
- Protected API endpoints
- SQLite database
- PDF upload
- OCR-based PDF text extraction using Tesseract
- Automatic document summary
- Quiz generation from extracted document content
- Interactive Swagger API documentation

## Tech Stack

- Python
- FastAPI
- SQLite
- SQLAlchemy
- JWT
- OAuth2
- Passlib
- Tesseract OCR
- PyMuPDF
- Uvicorn

## Project Structure

```text
saralvidhya-fastapi-assignment/
│
├── main.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
└── uploads/
```

The `uploads/`, virtual environment, SQLite database, and secret `.env` files are excluded from Git using `.gitignore`.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yasminshaik125/saralvidhya-fastapi-assignment.git
cd saralvidhya-fastapi-assignment
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

For Windows PowerShell:

```powershell
.\venv\Scripts\activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

## Tesseract OCR Setup

Tesseract OCR is required for extracting text from PDF documents.

For Windows, install Tesseract OCR and make sure the Tesseract installation directory is available in the system PATH.

Typical installation path:

```text
C:\Program Files\Tesseract-OCR
```

Verify the installation:

```bash
tesseract --version
```

## Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```text
SECRET_KEY=your-secret-key
```

Do not commit the `.env` file or any API keys or secrets to GitHub.

## Run the Application

Start the FastAPI server:

```bash
python -m uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### 1. Create User

```http
POST /users
```

Creates a new user account.

Example request:

```json
{
  "name": "Yasmin",
  "email": "yasmin@example.com",
  "password": "your-password"
}
```

### 2. Login

```http
POST /auth/login
```

Authenticates the user using OAuth2 password flow and returns a JWT access token.

The returned token is used as a Bearer token for protected endpoints.

### 3. Current User Profile

```http
GET /users/me
```

Returns details of the currently authenticated user.

Authentication required.

### 4. Upload PDF

```http
POST /materials/upload
```

Uploads a PDF document and stores its metadata in the SQLite database.

Authentication required.

Only PDF files are accepted.

### 5. Generate Material Summary

```http
POST /materials/{material_id}/summary
```

Processes the uploaded PDF using OCR and generates a summary from the extracted document content.

Authentication required.

Example:

```text
POST /materials/1/summary
```

### 6. Generate Quiz

```http
POST /materials/{material_id}/quiz
```

Processes the uploaded PDF and generates quiz questions and answers based on the extracted document content.

Authentication required.

Example:

```text
POST /materials/1/quiz
```

## Authentication Flow

The application uses OAuth2 Password Flow with JWT authentication.

```text
User Registration
       ↓
User Login
       ↓
JWT Access Token
       ↓
Authorize Swagger
       ↓
Protected API Endpoints
```

Protected material endpoints require a valid Bearer token.

## PDF Processing Pipeline

The main document processing workflow is:

```text
PDF Upload
     ↓
PDF Stored
     ↓
OCR using Tesseract
     ↓
Text Extraction
     ↓
Summary Generation
     ↓
Quiz Generation
```

## Database

SQLite is used as the application database with SQLAlchemy ORM.

The application stores user information including:

- User ID
- Name
- Email
- Hashed password

Material information includes:

- Material ID
- Original filename
- Stored file path
- User ID

## OCR

Tesseract OCR is used to extract text from uploaded PDF documents.

The extracted text is then passed to the application's summary and quiz generation workflow.

## Testing

The API was tested using FastAPI Swagger UI.

The following workflows were successfully tested:

- User registration
- User login
- JWT authentication
- Protected user profile endpoint
- PDF upload
- OCR-based text extraction
- Summary generation
- Quiz generation

The summary endpoint successfully returned a `200 OK` response after OCR processing.

The quiz endpoint successfully returned a `200 OK` response with questions generated from the uploaded document content.

## Security

The application includes the following security measures:

- Password hashing
- JWT-based authentication
- OAuth2 password flow
- Bearer token protection for protected endpoints
- PDF file-type validation
- Secrets excluded from Git
- Local database excluded from Git
- Uploaded files excluded from Git

## GitHub Repository

Source code:

https://github.com/yasminshaik125/saralvidhya-fastapi-assignment

## API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

The Swagger interface can be used to register a user, authenticate, upload a PDF, generate a summary, and generate a quiz.

## Author

**Yasmin Shaik**

B.Tech – Computer Science and Engineering
