import psycopg2
import smtplib
import random

from flask import render_template, request, url_for, redirect, session
from flask_login import login_user, login_required, logout_user, current_user

from connection import get_postgresql_connection
from app import app, login_manager
from ..models import User


@login_manager.user_loader
def load_user(user_id):
    curs, conn = get_postgresql_connection()
    curs.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = curs.fetchone()
    conn.close()
    curs.close()
    if user:
        return User(id=user[0], username=user[1], gmail=user[2], password=user[3], email_verified=user[4])
    return None


@app.get("/login/")
def get_login():
    return render_template("login.html")


@app.post("/login/")
def post_login():
    username = request.form["username"]
    password = request.form["password"]
    gmail = request.form["gmail"]

    if username == "admin" and password == "@dm1n" and gmail == "hktnadm@gmail.com":
        curs, conn = get_postgresql_connection()
        curs.execute("SELECT * FROM users WHERE username = %s", (username,))
        admin_user = curs.fetchone()
        conn.close()
        curs.close()

        if admin_user:
            admin_obj = User(id=admin_user[0], username=admin_user[1], gmail=admin_user[2], password=admin_user[3],
                             email_verified=admin_user[4])
            login_user(admin_obj)
            return render_template("admin_page.html")

    curs, conn = get_postgresql_connection()
    curs.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = curs.fetchone()
    conn.close()
    curs.close()

    if user:
        if user[1] == username and user[2] == gmail and user[3] == password:
            if user[4]:
                user_obj = User(id=user[0], username=user[1], gmail=user[2], password=user[3], email_verified=user[4])
                login_user(user_obj)
                return redirect(url_for("menu_page"))
            else:
                error_message = "Please verify your email before logging in."
                return render_template("login.html", error_message=error_message)

    error_message = "Invalid username, gmail or password"
    return render_template("login.html", error_message=error_message)


@app.get("/signup/")
def get_signup():
    return render_template("signup.html")


@app.post("/signup/")
def post_signup():
    username = request.form["username"]
    password = request.form["password"]
    gmail = request.form["gmail"]

    curs, conn = get_postgresql_connection()
    curs.execute("SELECT * FROM users WHERE username = %s", (username,))
    existing_user = curs.fetchone()

    if existing_user:
        error_message = "User with this username already exists"
        return render_template("signup.html", error_message=error_message)

    try:
        insert_user_query = """INSERT INTO users (username, gmail, password, email_verified) 
        VALUES (%s, %s, %s, FALSE);"""
        curs.execute(insert_user_query, (username, gmail, password))
        conn.commit()

        verification_code = generate_verification_code()
        send_email(to_addrs=gmail, code=verification_code)

        session['verification_code'] = verification_code

        curs.execute("SELECT * FROM users WHERE username = %s", (username,))
        new_user = curs.fetchone()

        if new_user:
            user_obj = User(id=new_user[0], username=new_user[1], gmail=new_user[2], password=new_user[3],
                            email_verified=new_user[4])
            login_user(user_obj)

        print("New user successfully added")
    except psycopg2.IntegrityError:
        print("Error: Integrity constraint violated.")
    except psycopg2.Error as error:
        print("Error", error)
    finally:
        if conn:
            conn.close()
        if curs:
            curs.close()

    return redirect(url_for("get_verification"))


@app.get("/verification/")
def get_verification():
    return render_template("verification.html")


@app.post("/verify_code/")
def post_verify_code():
    if current_user.is_authenticated:
        print("User is authenticated")

        entered_code = request.form["verification_code"]
        correct_code = session.get('verification_code')

        if not correct_code:
            print("Verification code not found in session!")
            return render_template("verification.html", error_message="Verification code expired or not found.")

        if entered_code == correct_code:
            user_id = current_user.id
            curs, conn = get_postgresql_connection()
            curs.execute("UPDATE users SET email_verified = TRUE WHERE user_id = %s", (user_id,))
            conn.commit()
            conn.close()
            session.pop('verification_code', None)
            print("Email verification successful")

            login_user(current_user)

            return redirect(url_for('get_login'))
        else:
            print("Incorrect verification code")
            return render_template("verification.html", error_message="Incorrect verification code. Please try again.")
    else:
        print("User is not authenticated")
        session.pop('verification_code', None)
        return redirect(url_for("get_login"))


def send_email(to_addrs, code):
    from_addrs = "hktnadm@gmail.com"
    subject = "Welcome to Our Service. That's your security code:"
    body = f"Thank you for signing up! Your verification code is: {code}"

    message = f"From: {from_addrs}\nTo: {to_addrs}\nSubject: {subject}\n\n{body}"

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_addrs, "tvko chtq awmb dttp")
        server.sendmail(from_addrs, to_addrs, message)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)


def generate_verification_code(length=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


@app.get("/logout/")
@login_required
def logout():
    print("Log out user")
    logout_user()
    return redirect(url_for("get_login"))
