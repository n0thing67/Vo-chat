from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for,session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid
import hashlib
import secrets
import hmac
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
with app.app_context():
    db.create_all()
    print("Database created")
app.secret_key = os.environ.get('SECRET_KEY')

"""users = []
posts = []
likes = []"""

uploader = os.path.join(app.static_folder, 'image')
format = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = uploader
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
def allowed_file(filename:str)->bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in format
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    mail = db.Column(db.String(120), nullable=False)
    nickname = db.Column(db.String(100), unique=True, nullable=False)
    photo_path = db.Column(db.String(255))
    password = db.Column(db.String(100), nullable=False)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    pname = db.Column(db.String(100), nullable=False)
    mark = db.Column(db.Text, nullable=False)
    photo = db.Column(db.String(255))
    avatar = db.Column(db.String(255))

    likes=db.Column(db.Integer, nullable=False, default=0)

class Likes(db.Model):
    __tablename__ = "Likes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id',name='flike'),)

@app.route("/")
def index():
    return render_template("register.html")


@app.route("/register", methods=["POST", "GET"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    age_str = (request.form.get("age") or "").strip()
    mail = (request.form.get("mail") or "").strip()
    nickname = (request.form.get("nickname") or "").strip()
    password = (request.form.get("password") or "").strip()
    if not name or not phone or not age_str or not mail or not nickname or not password:
        return render_template(
            "register.html",
            error="Пожалуйста, заполните все поля",
            name=name,
            phone=phone,
            age=age_str,
            mail=mail,
            nickname=nickname,
        )

    try:
        age = int(age_str)
    except ValueError:
        return render_template(
            "register.html",
            error="Возраст должен быть числом",
            name=name,
            phone=phone,
            age=age_str,
            mail=mail,
            nickname=nickname,
        )
    if User.query.filter_by(phone=phone).first():

        return render_template(
            "register.html",
            error="Этот номер телефона уже занят",
            name=name,
            phone=phone,
            age=age_str,
            mail=mail,
            nickname=nickname,
        )

    if User.query.filter_by(phone=phone).first():
        return render_template(
            "register.html",
            error="Этот Никнэйм уже занят",
            name=name,
            phone=phone,
            age=age_str,
            mail=mail,
            nickname=nickname,
        )
    photo=request.files.get("photo")
    photo_path = None
    if photo and photo.filename:
        if allowed_file(photo.filename):
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            original=secure_filename(photo.filename)
            ext=original.rsplit(".", 1)[-1].lower()
            special_name=f'{uuid.uuid4().hex}{ext}'
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], special_name)
            photo.save(save_path)
            photo_path = f'image/{special_name}'
        else:
            return render_template('register.html', error="Можно загружать только изображения формата Jpg и PNG")




    user=User(
        name=name,
        phone=phone,
        age=age,
        mail=mail,
        nickname=nickname,
        photo_path=photo_path,
        password=password)

    db.session.add(user)
    db.session.commit()
    session["user_id"]=user.id


    return redirect(url_for("profile"))



@app.route("/profile")
def profile():
    user_id=session.get("user_id")
    if user_id is None:
        return redirect(url_for("Signin"))
    user = User.query.get(user_id)
    if user is None:
        session.clear()
        return redirect(url_for("Signin"))
    return render_template("profile.html", user=user)




@app.route("/users")
def show_users():
    users=User.query.all()
    return render_template("users.html", users=users)


@app.route("/posts", methods=["GET", "POST"])
def posts_page():
    user_id=session.get("user_id")
    if user_id is None:
        return redirect(url_for("Signin"))
    
    user = User.query.get(user_id)
    if user is None:
        session.clear()
        return redirect(url_for("Signin"))
    if request.method == "GET":
        return render_template("posts.html",user=user)



    mark_text = (request.form.get("mark") or "").strip()

    if not mark_text:
        return render_template("posts.html", error="Заполни текст поста", user=user, mark=mark_text)

    ban_words=['негры','67','six seven', 'sixseven', 'сиксевеен', 'сикс севен']

    text_lower = mark_text.lower()

    for word in ban_words:
        if word in text_lower:
            return render_template("posts.html",error='Используйте более политкоректные выражения', user=user)

    user_photo = user.photo_path



    photo=request.files.get("photo")
    photo_path = None
    if photo and photo.filename:
        if allowed_file(photo.filename):
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            original=secure_filename(photo.filename)
            ext=original.rsplit(".", 1)[-1].lower()
            special_name=f'{uuid.uuid4().hex}.{ext}'
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], special_name)
            photo.save(save_path)
            photo_path = f'image/{special_name}'



    post=Post(
        pname=user.name,
        mark=mark_text,
        photo=photo_path,
        avatar=user.photo_path
    )
    db.session.add(post)
    db.session.commit()
    return redirect(url_for("read_posts"))

@app.route("/read")
def read_posts():
    user_id=session.get("user_id")
    if user_id is None:
        return redirect(url_for("Signin"))
    user=User.query.get(user_id)
    if user is None:
        session.clear()
        return redirect(url_for("Signin"))
    posts=Post.query.order_by(Post.id.desc()).all()
    Allikes=Likes.query.filter_by(user_id=user_id).all()
    userLike=[]
    for like in Allikes:
        userLike.append(like.post_id)
    return render_template("read.html", posts=posts, user=user,userLike=userLike)

@app.route("/like/<int:post_id>", methods=[ "POST"])
def like_post(post_id):
    user_id=session.get("user_id")
    if user_id is None:
        return redirect(url_for("Signin"))
    user=User.query.get(user_id)
    if user is None:
        session.clear()
        return redirect(url_for("Signin"))
    post=Post.query.get(post_id)
    if post is None:
        return redirect(url_for("read_posts"))
    flikes=Likes.query.filter_by(user_id=user_id,post_id=post_id).first()
    if flikes:
        db.session.delete(flikes)
        if post.likes>0:
            post.likes-=1
        liked=False
    else:
        newlike=Likes(user_id=user_id,post_id=post_id)
        db.session.add(newlike)
        post.likes+=1
        liked=True
    db.session.commit()
    return {'success':True ,"likes": post.likes, "liked": liked}

@app.route("/signin", methods=["POST", "GET"])
def Signin():

    if request.method == "GET":
        return render_template("Signin.html")

    phone = (request.form.get("phone") or "").strip()
    password = (request.form.get("password") or "").strip()



    if not phone or not password:
        return render_template(
            "Signin.html",
            error="Пожалуйста, заполните все поля",
            phone=phone,
        )
    user=User.query.filter_by(phone=phone, password=password).first()
    if user:
        session["user_id"]=user.id
        return redirect(url_for("profile"))




    return render_template(
        "Signin.html",
        error=" Неверный номер телефона или пароль",
        phone=phone,
    )

@app.route("/Logout")
def logout():
    session.clear()
    return redirect(url_for("Signin"))

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)