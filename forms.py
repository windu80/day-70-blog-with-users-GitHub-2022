from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, EmailField
from wtforms.validators import InputRequired, URL, Email, Length
from flask_ckeditor import CKEditorField


# ------ WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[InputRequired()])
    subtitle = StringField("Subtitle", validators=[InputRequired()])
    img_url = StringField("Blog Image URL", validators=[InputRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[InputRequired()])
    submit = SubmitField("Submit Post")


class RegisterUserForm(FlaskForm):
    email = EmailField(label="Email", validators=[InputRequired(), Email()])
    password = PasswordField(label="Password", validators=[InputRequired(), Length(min=8)])
    name = StringField(label="Name", validators=[InputRequired()])
    submit = SubmitField(label="SIGN ME UP!")


class LoginForm(FlaskForm):
    email = EmailField(label="Email", validators=[InputRequired(), Email()])
    password = PasswordField(label="Password", validators=[InputRequired()])
    submit = SubmitField(label="LET ME IN!")


class CommentForm(FlaskForm):
    comment = CKEditorField(label="Comment", validators=[InputRequired()])
    submit = SubmitField(label="SUBMIT COMMENT")
