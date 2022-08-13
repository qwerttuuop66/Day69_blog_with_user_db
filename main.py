from flask import Flask, render_template, redirect, url_for, flash, g, jsonify,abort,request
from functools import wraps
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_gravatar import Gravatar
import flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

##FLASK GRAVATOR
#generate random user image
gravatar = Gravatar(app,
                    size=100,
                    rating='x',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)
##CONFIGURE TABLES

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
 
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    
    #Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id = db.Column(db.Integer, db.ForeignKey("users.id",ondelete="CASCADE"))
    #Create reference to the User object, the "posts" refers to the posts protperty in the User class.
    author = relationship("User", back_populates="posts",cascade="all, delete",
        passive_deletes=True,)
    comments=relationship('Comment',back_populates='parent_post',cascade="all, delete",
        passive_deletes=True,)
    
class User(db.Model,UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(250),nullable=False)
    password=db.Column(db.String(250),nullable=False)
    email=db.Column(db.String(250),nullable=False)

    #This will act like a List of BlogPost objects attached to each User. 
    #The "author" refers to the author property in the BlogPost class.
    #use cascade to combine the parent and child when delete
    posts = relationship("BlogPost", back_populates='author',cascade="all, delete",
        passive_deletes=True,)
    comments=relationship('Comment',back_populates='author',cascade="all, delete",
        passive_deletes=True,)
#if set new column, delete original db, and create the new
class Comment(db.Model):
    __tablename__='comments'
    id=db.Column(db.Integer,primary_key=True)
    #child must add ondelete after foreignkey
    author_id=db.Column(db.Integer, db.ForeignKey("users.id",ondelete="CASCADE"))
    post_id=db.Column(db.Integer,db.ForeignKey('blog_posts.id',ondelete="CASCADE"))
    author=relationship('User',back_populates='comments')
    parent_post=relationship('BlogPost',back_populates='comments')
    text=db.Column(db.String(250),nullable=False)
db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    users=User.query.all()

    return render_template("index.html", all_posts=posts,all_users=users)


@app.route('/register',methods=['GET','POST'])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        new_user=User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8)
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html",form=form)


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    register_form=RegisterForm()
    if form.validate_on_submit():
        try:
            requested_user=User.query.filter_by(name=form.user_id.data).first()
            if login_user(requested_user) and check_password_hash(requested_user.password,form.password.data) is False:
                flash('Your password is wrong, try again')
            else:
                login_user(requested_user)
                return redirect( url_for('get_all_posts'))
        except AttributeError:
            requested_user=User.query.filter_by(email=form.user_id.data).first()
            # print(login_user(requested_user))
            if requested_user==None:
                flash('you are not permitted, please register first')
            else:
                if not check_password_hash(requested_user.password,form.password.data):
                    flash('Your password is wrong, try again')
                else:
                    login_user(requested_user)
                    return redirect( url_for('get_all_posts'))
                    # return redirect(url_for('get_all_posts',all_posts=posts))
    return render_template("login.html",form=form)
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=['POST','GET'])
def show_post(post_id):
    form=CommentForm()
    requested_post = BlogPost.query.get(post_id)
    
    #add new comment to db,如果没有登陆，返回登陆页面
    if current_user.is_authenticated and form.validate_on_submit():
        new_comment=Comment(
            author_id=current_user.id,
            post_id=requested_post.id,
            text=request.form.get('blog_text').split('<p>')[-1].split('</p>')[0]
        )
        db.session.add(new_comment)
        db.session.commit()
    elif not current_user.is_authenticated and form.validate_on_submit():
        flash('please login first')
        return redirect(url_for('login'))
    
    return render_template("post.html", post=requested_post,form=form,gravatar=gravatar)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")




#custom error page
@app.errorhandler(403)
def resource_not_found(e):
    return jsonify(error=str(e)), 403

#using decorated_function to limit devil vistor
def admin_only(f):
    @wraps(f)
    @app.errorhandler(403)
    def decorated_function(*args, **kwargs):
        if current_user is None or current_user.id !=1:
            error=abort(403, description="you are not permitted")
            return jsonify(error)
        return f(*args, **kwargs)
    return decorated_function


@app.route("/new-post",methods=['GET','POST'])
@admin_only
def add_new_post():
    form = CreatePostForm()
    print(current_user.id)
    print(form.validate_on_submit())
    if form.validate_on_submit():
        
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
            author_id=current_user.id
        )
        print(new_post)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

@app.route("/edit-post/<int:post_id>")
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = edit_form.author.data
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
    app.run(host='0.0.0.0', port=5000)
    # app.run(debug=True)

