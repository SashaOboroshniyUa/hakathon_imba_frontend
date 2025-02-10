import psycopg2

from flask import render_template, redirect, url_for, request
from flask_login import current_user, login_required

from app import app
from connection import get_postgresql_connection


@app.get("/")
def start():
    if current_user.is_authenticated:
        return redirect(url_for("menu_page"))
    else:
        return redirect(url_for("get_signup"))


@app.get("/menu/")
def menu_page():
    if not current_user.email_verified:
        return redirect(url_for("get_verification"))
    elif current_user.username == "admin" and current_user.password == "@dm1n":
        return render_template("admin_page.html")
    return render_template("menu.html")
