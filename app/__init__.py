from flask import Flask
from flask_login import LoginManager

from connection import create_user_table


app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config["SECRET_KEY"] = "q"
app.config['SESSION_PROTECTION'] = "strong"
create_user_table()
