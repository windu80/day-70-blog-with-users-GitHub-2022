from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterUserForm, LoginForm, CommentForm
from sqlite_db import db, BlogPost, User, Comment
from flask_gravatar import Gravatar  # --> allows user to have an icon
from functools import wraps
import os

# ----- INIT THE FLASK APP
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
ckeditor = CKEditor(app)
Bootstrap(app)
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# ----- CONNECT TO DB
# We use the env variable DATABASE_URL if avail, if not, the default value
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(key='DATABASE_URL', default='sqlite:///blog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.app = app
db.init_app(app)
db.create_all()

# ----- INIT LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader  # Requirement from FlaskLogin
def load_user(id):
    return User.query.get(id)


def admin_only(function):
    """To use as a decorator function, only allows to call a route/function if admin"""
    @wraps(function)  # --> must be imported, from functools
    def wrapper_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return function(*args, **kwargs)
        else:
            return abort(403)
    return wrapper_function


# ----- DEFINING ALL THE ROUTES
@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts)


@app.route('/register', methods=["GET", "POST"])
def register():
    register_form = RegisterUserForm()
    if register_form.validate_on_submit():
        email = register_form.email.data
        if User.query.filter_by(email=email).first():
            flash("There is already a user registered with that email. "
                  "If it's you, you might want to log in on this page instead.")
            return redirect(url_for("login"))
        else:
            new_user = User()
            new_user.name = register_form.name.data.title()
            new_user.email = email
            new_user.password = generate_password_hash(
                password=register_form.password.data,
                method="pbkdf2:sha256", salt_length=8
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("get_all_posts"))
    else:
        return render_template("register.html", form=register_form)


@app.route('/login', methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user_email = login_form.email.data
        user_pwd = login_form.password.data
        user = User.query.filter_by(email=user_email).first()
        if user:
            is_password_correct = check_password_hash(user.password, user_pwd)
            if is_password_correct:
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                flash("Password incorrect. Please try again.")
                return redirect(url_for("login"))
        else:
            flash("That email does not exist, please try again.")
            return redirect(url_for("login"))
    else:
        if request.args.get("login_to_comment"):
            flash("You need to login or register to comment.")
            print("You need to log in!")
        return render_template("login.html", form=login_form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        new_comment = Comment(
            body=comment_form.comment.data,
            comment_author=current_user,  # pass in the User Object, who is author of this comment
            parent_post=requested_post,  # pass in the BlogPost object, on which this comment is written
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post_id))
    else:
        # NO NEED FOR THAT, WE ALREADY HAVE THE LIST OF COMMENTS AS A PROPERTY FROM BLOGPOST
        # existing_comments = Comment.query.filter_by(blog_post_id=post_id).all()
        # return render_template("post.html", post=requested_post, form=comment_form, comments=existing_comments)

        # print(requested_post.comments)  # PRINTED AS A LIST
        return render_template("post.html", post=requested_post, form=comment_form)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,    # -> not the current_user.id or .name, but the User object
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        # author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        # post.author = edit_form.author.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form)


@app.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    # app.run(host='0.0.0.0', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000)  # without debut mode
