from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mysql.connector
import bcrypt # <--- Our new clean import

from fastapi.middleware.cors import CORSMiddleware

# --- OUR NEW BCRYPT FUNCTIONS ---
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)


app = FastAPI(title="Student ERP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 2. Database Connection Helper
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",          # Replace with your MySQL username
            password="1234",  # Replace with your MySQL password
            database="students" # The DB you created
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# 3. Pydantic Models (Data Validation)
# These define exactly what data the frontend must send
class StudentSignup(BaseModel):
    username: str
    password: str
    security_q: str
    security_a: str
    total_fee: int

class StudentLogin(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    username: str

class PasswordReset(BaseModel):
    username: str
    security_a: str
    new_password: str

# 4. API Routes

@app.post("/signup")
def signup(student: StudentSignup):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if username already exists
        cursor.execute("SELECT * FROM Students WHERE username = %s", (student.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")

        # Insert new student (Note: In a real app, hash the password using bcrypt before saving!)
        # INSIDE @app.post("/signup")
        
        # Hash the password!
        hashed_password = get_password_hash(student.password)

        sql = """INSERT INTO Students (username, password_hash, security_q, security_a, total_fee, fee_paid) 
                 VALUES (%s, %s, %s, %s, %s, %s)"""
                 
        # Use hashed_password instead of student.password
        values = (student.username, hashed_password, student.security_q, student.security_a, student.total_fee, 0)
        
        cursor.execute(sql, values)
        conn.commit()
        
        return {"message": "Student registered successfully!"}
    
    finally:
        cursor.close()
        conn.close()

# --- FORGOT PASSWORD FLOW ---

@app.post("/forgot-password/question")
def get_security_question(req: ForgotPasswordRequest):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT security_q FROM Students WHERE username = %s", (req.username,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {"security_q": user['security_q']}
    finally:
        cursor.close()
        conn.close()

@app.post("/forgot-password/reset")
def reset_password(req: PasswordReset):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Verify the security answer (In a real app, answers should be case-insensitive or hashed)
        cursor.execute("SELECT id FROM Students WHERE username = %s AND security_a = %s", 
                       (req.username, req.security_a))
        if not cursor.fetchone():
            raise HTTPException(status_code=401, detail="Incorrect security answer")
        
        # Update the password
        hashed_new_password = get_password_hash(req.new_password)
        
        # Update the password in DB
        cursor.execute("UPDATE Students SET password_hash = %s WHERE username = %s", 
                       (hashed_new_password, req.username))
        conn.commit()
        
        return {"message": "Password reset successfully!"}
    finally:
        cursor.close()
        conn.close()

# --- DASHBOARD FLOW ---

@app.get("/dashboard/{student_id}")
def get_dashboard(student_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Get Fee Details & Calculate Remaining Fee
        cursor.execute("SELECT total_fee, fee_paid FROM Students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        remaining_fee = student['total_fee'] - student['fee_paid']

        # 2. Get Registered Subjects
        cursor.execute("SELECT subject_name FROM Subjects WHERE student_id = %s", (student_id,))
        subjects = [row['subject_name'] for row in cursor.fetchall()]

        # 3. Get Marks
        cursor.execute("SELECT subject_name, score FROM Marks WHERE student_id = %s", (student_id,))
        marks = cursor.fetchall()

        # Combine everything into one clean response for the frontend
        return {
            "fees": {
                "total": student['total_fee'],
                "paid": student['fee_paid'],
                "remaining": remaining_fee
            },
            "registered_subjects": subjects,
            "marks": marks
        }
    finally:
        cursor.close()
        conn.close()

@app.post("/login")
def login(student: StudentLogin):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Returns results as a dictionary
    
    try:
        # Find the user
        cursor.execute("SELECT id, username, password_hash FROM Students WHERE username = %s", (student.username,))
        user = cursor.fetchone()

        # Check if user exists and password matches
        if not user or not verify_password(student.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        # In a full app, you would return a JWT token here. 
        # For simple UI, returning the user ID is enough to fetch the dashboard later.
        return {
            "message": "Login successful", 
            "student_id": user['id']
        }
    
    finally:
        cursor.close()
        conn.close()
# --- ADMIN FLOW (FOR TESTING ONLY) ---

@app.get("/admin/users")
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetching the hashes so we can see them in the UI
        cursor.execute("SELECT id, username, password_hash FROM Students")
        users = cursor.fetchall()
        return {"users": users}
    finally:
        cursor.close()
        conn.close()