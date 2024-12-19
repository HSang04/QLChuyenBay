#__init.py
from flask import Flask, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from urllib.parse import quote
from flask_migrate import Migrate
import cloudinary



app = Flask(__name__)
app.secret_key = "k8HDLZbie2T8UWvC70S7f-SukGY"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/qlcbdb?charset=utf8mb4" % quote('Admin@123') #123456
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True


db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app=app)

cloudinary.config(
    cloud_name="dtvxkypzm",
    api_key="663141523184771",
    api_secret="TNSjditR1gd1ZzJ9mPll5N1f5PQ",
    secure=True
)

def create_db():
    with app.app_context():
        db.create_all()



