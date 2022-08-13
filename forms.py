from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL

from flask_ckeditor import CKEditorField
import wtforms
##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")
class RegisterForm(FlaskForm):
    email=StringField("User Email", validators=[DataRequired(),wtforms.validators.Email()])
    password=StringField("User Password", validators=[DataRequired()])
    name=StringField("User Name", validators=[DataRequired()])
    submit = SubmitField("Submit Post")
class LoginForm(FlaskForm):
    user_id=StringField("User Email or User Name", validators=[DataRequired()])#user_id可以是邮箱也可是用户名
    password=StringField("User Password", validators=[DataRequired()])
    submit = SubmitField("Submit Post")
class CommentForm(FlaskForm):
    blog_text = CKEditorField('COMMENT')
    submit = SubmitField("Submit Comment")