import streamlit as st
import sqlite3
import pandas as pd

# --------- DATABASE SETUP ---------
conn = sqlite3.connect('lessons.db', check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT, email TEXT UNIQUE, password TEXT, preferred_language TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS lessons
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             title TEXT, content_en TEXT, content_es TEXT, content_fr TEXT)''')

# --------- HELPER FUNCTIONS ---------
def register_user(name, email, password, preferred_language="en"):
    try:
        c.execute('INSERT INTO users (name, email, password, preferred_language) VALUES (?, ?, ?, ?)',
                  (name, email, password, preferred_language))
        conn.commit()
        return True
    except:
        return False

def login_user(email, password):
    c.execute('SELECT * FROM users WHERE email=? AND password=?', (email, password))
    return c.fetchone()

def add_lesson(title, en, es, fr):
    c.execute('INSERT INTO lessons (title, content_en, content_es, content_fr) VALUES (?, ?, ?, ?)',
              (title, en, es, fr))
    conn.commit()

def get_lessons():
    c.execute('SELECT * FROM lessons')
    return c.fetchall()

# --------- STREAMLIT APP ---------
st.title("🌐 3 Language Barrier – Multilingual Learning App")

menu = ["Home", "Register", "Login"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Home":
    st.subheader("Welcome to 3 Language Barrier App")
    lessons = get_lessons()
    if lessons:
        st.write("### Available Lessons")
        df = pd.DataFrame(lessons, columns=["ID","Title","English","Spanish","French"])
        st.dataframe(df[["Title","English","Spanish","French"]])
    else:
        st.info("No lessons available. Please register or login to add lessons.")

elif choice == "Register":
    st.subheader("Create a New Account")
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    preferred_language = st.selectbox("Preferred Language", ["en", "es", "fr"])
    if st.button("Register"):
        if register_user(name, email, password, preferred_language):
            st.success("Account created! Please login.")
        else:
            st.error("User already exists.")

elif choice == "Login":
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    if st.button("Login"):
        user = login_user(email, password)
        if user:
            st.success(f"Welcome {user[1]}!")
            st.subheader("Add New Lesson")
            title = st.text_input("Lesson Title")
            content_en = st.text_area("Content (English)")
            content_es = st.text_area("Content (Spanish)")
            content_fr = st.text_area("Content (French)")
            if st.button("Add Lesson"):
                if title and (content_en or content_es or content_fr):
                    add_lesson(title, content_en, content_es, content_fr)
                    st.success("Lesson added successfully!")
                else:
                    st.warning("Please enter at least one language content.")

            st.subheader("Available Lessons")
            lessons = get_lessons()
            df = pd.DataFrame(lessons, columns=["ID","Title","English","Spanish","French"])
            st.dataframe(df[["Title","English","Spanish","French"]])
        else:
            st.error("Invalid credentials")