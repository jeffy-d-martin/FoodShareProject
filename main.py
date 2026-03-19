import sqlite3
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
import os
import uvicorn

app = FastAPI(title="Annapoorna Connect API")

DB_FILE = "account.db"

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            profile_image TEXT,
            gender TEXT,
            dob TEXT,
            profession TEXT,
            address TEXT
        )
    ''')
    # Migration: Add new columns if they don't exist
    new_columns = [
        ("profile_image", "TEXT"),
        ("gender", "TEXT"),
        ("dob", "TEXT"),
        ("profession", "TEXT"),
        ("address", "TEXT")
    ]
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass # Column already exists
            
    conn.commit()
    conn.close()

init_db()

DONATIONS_DB_FILE = "donations.db"

def init_donations_db():
    conn = sqlite3.connect(DONATIONS_DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            food_type TEXT NOT NULL,
            quantity TEXT NOT NULL,
            expiry_time TEXT NOT NULL,
            category TEXT NOT NULL,
            pickup_address TEXT NOT NULL,
            contact_name TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            food_image TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_donations_db()

# Pydantic Model for incoming registration
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str = Field(..., pattern=r"^[6-9]\d{9}$")

@app.post("/api/register")
def register_user(user: UserCreate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if phone number already exists
    try:
        cursor.execute("INSERT INTO users (name, email, password, phone) VALUES (?, ?, ?, ?)",
                       (user.name, user.email, user.password, user.phone))
        conn.commit()
        conn.close()
        return {"message": "Account created successfully!"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="An account with this phone number already exists.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/login")
def login_user(user: UserLogin):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, phone, profile_image, gender, dob, profession, address FROM users WHERE email = ? AND password = ?", (user.email, user.password))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "message": "Login successful", 
            "user": {
                "id": row[0], "name": row[1], "email": row[2], "phone": row[3], 
                "profile_image": row[4], "gender": row[5], "dob": row[6], 
                "profession": row[7], "address": row[8]
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

class IdentifierCheck(BaseModel):
    identifier: str

@app.post("/api/verify-identifier")
def verify_identifier(data: IdentifierCheck):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if it's a 10-digit number or email
    cursor.execute("SELECT id FROM users WHERE phone = ? OR email = ?", (data.identifier, data.identifier))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"exists": True}
    else:
        raise HTTPException(status_code=404, detail="No account found with this email or phone number.")

class PasswordReset(BaseModel):
    identifier: str
    new_password: str

@app.post("/api/reset-password")
def reset_password(data: PasswordReset):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Update password where phone or email matches
    cursor.execute("UPDATE users SET password = ? WHERE phone = ? OR email = ?", 
                   (data.new_password, data.identifier, data.identifier))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Account not found.")
        
    conn.commit()
    conn.close()
    return {"message": "Password updated successfully!"}

class ProfileUpdate(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str
    profile_image: str = None
    gender: str = None
    dob: str = None
    profession: str = None
    address: str = None

@app.post("/api/update-profile")
def update_profile(data: ProfileUpdate):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE users SET 
                name = ?, email = ?, phone = ?, profile_image = ?, 
                gender = ?, dob = ?, profession = ?, address = ? 
            WHERE id = ?
        """, (data.name, data.email, data.phone, data.profile_image, 
               data.gender, data.dob, data.profession, data.address, data.id))
        conn.commit()
        conn.close()
        return {"message": "Profile updated successfully!"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="This email or phone is already in use by another user.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

class DonationCreate(BaseModel):
    user_id: int
    food_name: str
    food_type: str
    quantity: str
    expiry_time: str
    category: str
    pickup_address: str
    contact_name: str
    contact_phone: str
    food_image: str = None

@app.post("/api/donate-food")
def donate_food(donation: DonationCreate):
    conn = sqlite3.connect(DONATIONS_DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO donations (
                user_id, food_name, food_type, quantity, expiry_time, 
                category, pickup_address, contact_name, contact_phone, food_image
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            donation.user_id, donation.food_name, donation.food_type, 
            donation.quantity, donation.expiry_time, donation.category, 
            donation.pickup_address, donation.contact_name, donation.contact_phone, 
            donation.food_image
        ))
        conn.commit()
        conn.close()
        return {"message": "Donation posted successfully!"}
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files to serve the frontend
# We mount the current directory at "/"
# So http://localhost:8000/signup.html will serve the signup page
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
