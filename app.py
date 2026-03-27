import streamlit as st
import sqlite3
import pandas as pd
import os
from openai import OpenAI

# --------- OPENAI SETUP ---------
# Replace with your actual API key string from OpenAI dashboard
os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI()

def translate_text(text, target_language):
    try:
        prompt = f"Translate this into {target_language}: {text}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return ""

# --------- DATABASE SETUP ---------
conn = sqlite3.connect('lessons.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT, email TEXT UNIQUE, password TEXT, preferred_language TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS lessons
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             title TEXT, content_en TEXT, content_es TEXT, content_fr TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS progress
             (user_id INTEGER,
              lesson_id INTEGER,
              is_read INTEGER DEFAULT 0,
              PRIMARY KEY (user_id, lesson_id))''')

conn.commit()

# --------- SESSION ---------
if "user" not in st.session_state:
    st.session_state.user = None

# --------- FUNCTIONS ---------
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

def preload_lessons():
    c.execute("SELECT COUNT(*) FROM lessons")
    if c.fetchone()[0] == 0:
        sample = [
            ("Greetings", "Hello, how are you?", "Hola, ¿cómo estás?", "Bonjour, comment ça va?"),
            ("Introduction", "My name is John", "Me llamo Juan", "Je m'appelle Jean"),
            ("Food", "I like pizza", "Me gusta la pizza", "J'aime la pizza"),
            ("Travel", "Where is the station?", "¿Dónde está la estación?", "Où est la gare?")
        ]
        c.executemany('INSERT INTO lessons (title, content_en, content_es, content_fr) VALUES (?, ?, ?, ?)', sample)
        conn.commit()

def mark_as_read(user_id, lesson_id):
    c.execute('INSERT OR REPLACE INTO progress (user_id, lesson_id, is_read) VALUES (?, ?, 1)',
              (user_id, lesson_id))
    conn.commit()

def mark_as_unread(user_id, lesson_id):
    c.execute('DELETE FROM progress WHERE user_id=? AND lesson_id=?',
              (user_id, lesson_id))
    conn.commit()

def is_read(user_id, lesson_id):
    c.execute('SELECT is_read FROM progress WHERE user_id=? AND lesson_id=?',
              (user_id, lesson_id))
    return c.fetchone() is not None

# preload data
preload_lessons()

# --------- UI ---------
st.title("🌐 3 Language Barrier – AI Learning App")

menu = ["Home", "Register", "Login"]
choice = st.sidebar.selectbox("Menu", menu)

# --------- HOME ---------
if choice == "Home":
    st.subheader("📚 Available Lessons")
    lessons = get_lessons()

    if lessons:
        df = pd.DataFrame(lessons, columns=["ID","Title","English","Spanish","French"])
        st.dataframe(df[["Title","English","Spanish","French"]])
    else:
        st.info("No lessons available.")

# --------- REGISTER ---------
elif choice == "Register":
    st.subheader("📝 Register")
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    lang = st.selectbox("Preferred Language", ["en", "es", "fr"])

    if st.button("Register"):
        if register_user(name, email, password, lang):
            st.success("✅ Account created!")
        else:
            st.error("❌ User already exists")

# --------- LOGIN ---------
elif choice == "Login":
    st.subheader("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        user = login_user(email, password)
        if user:
            st.session_state.user = user
            st.success(f"Welcome {user[1]}!")
        else:
            st.error("Invalid credentials")

    if st.session_state.user:
        user = st.session_state.user
        user_id = user[0]

        # --------- ADD LESSON ---------
        st.subheader("➕ Add New Lesson")

        with st.form("lesson_form", clear_on_submit=True):
            title = st.text_input("Lesson Title")
            content_en = st.text_area("Content (English)")

            auto_translate = st.checkbox("🌍 Auto-translate")

            content_es = st.text_area("Content (Spanish)")
            content_fr = st.text_area("Content (French)")

            submitted = st.form_submit_button("Add Lesson")

            if submitted:
                if title and content_en:

                    if auto_translate:
                        with st.spinner("🤖 Translating..."):
                            content_es = translate_text(content_en, "Spanish")
                            content_fr = translate_text(content_en, "French")

                    add_lesson(title, content_en, content_es, content_fr)

                    st.success("✅ Lesson added!")
                    st.experimental_rerun()

                else:
                    st.warning("⚠️ Title & English required")

        # --------- VIEW LESSONS ---------
        st.subheader("📖 Learn")

        lessons = get_lessons()

        for lesson in lessons:
            lesson_id, title, en, es, fr = lesson

            st.markdown(f"### 📘 {title}")

            lang = st.selectbox("Language", ["English","Spanish","French"], key=f"lang_{lesson_id}")

            if lang == "English":
                st.write(en)
            elif lang == "Spanish":
                st.write(es)
            else:
                st.write(fr)

            st.caption("🤖 AI supported translations")

            if is_read(user_id, lesson_id):
                st.success("✅ Completed")
                if st.button(f"Mark Unread {lesson_id}", key=f"unread_{lesson_id}"):
                    mark_as_unread(user_id, lesson_id)
                    st.experimental_rerun()
            else:
                st.warning("❌ Not Completed")
                if st.button(f"Mark Read {lesson_id}", key=f"read_{lesson_id}"):
                    mark_as_read(user_id, lesson_id)
                    st.experimental_rerun()

            st.write("---")

        # --------- PROGRESS ---------
        total = len(lessons)
        done = sum([1 for l in lessons if is_read(user_id, l[0])])

        st.subheader("📊 Progress")
        st.progress(done/total if total else 0)
        st.write(f"{done}/{total} lessons completed")
