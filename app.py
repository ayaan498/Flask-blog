# This is a blog website created by Ayaan Gani
# Various functions of Flask micro-framework have been used
import math
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from werkzeug.utils import secure_filename
import json
from datetime import datetime

with open('config_blog.json', 'r') as c:
    params = json.load(c)["params"]  # storing json file in 'params' variable

app = Flask(__name__)
app.secret_key = 'super-secret-key'         # setting secret-key for login
app.config.update(
    MAIL_SERVER='smtp.gmail.com',           # setting all parameters for mail service
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_pswd']
)

if params['local_server']:          # determining the type of server
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
mail = Mail(app)


class my_contacts(db.Model):        # creating the class for my_contacts database
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class my_posts(db.Model):       # creating the class for my_posts database
    sno = db.Column(db.Integer, primary_key=True)
    img_url = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(80), nullable=False)
    tag_line = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(40), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")         # the default url
def home():
    page = request.args.get('page', 1, type=int)        # breaking down a variable url parameter 'page'
    posts = my_posts.query.paginate(page=page, per_page=params["no_of_posts"])
    count_posts = my_posts.query.all()          # created for counting the number of posts
    last = math.ceil(len(count_posts) / int(params['no_of_posts']))
    if page == 1:
        prev = "#"
        next = "/?page=" + str(page + 1)
    elif page == last:
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/post/<string:post_slug>", methods=['GET'])     # using a variable url parameter post_slug
def post_route(post_slug):
    post = my_posts.query.filter_by(slug=post_slug).first()        # searching for the post with given 'sno'
    return render_template('post.html', params=params, post=post)


@app.route("/about")
def about():
    return render_template('about.html', params=params)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')     # accessing the form values from contact.html
                                            # and inserting them into the database my_contacts
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = my_contacts(name=name, email=email, phone=phone, message=message, date=datetime.now())
        db.session.add(entry)      # making the database entry
        db.session.commit()
        mail.send_message('New message from ' + name,
                          sender=email,
                          recipients=[params['gmail_user']],
                          body=message + "\n" + phone
                          )
    return render_template('contact.html', params=params)


@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:       # checking if user is already in session
        posts = my_posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get("uname")
        userpass = request.form.get("upass")
        if username == params['admin_user'] and userpass == params['admin_password']:       # validating the login info
            session['user'] = username      # adding user into the session
            posts = my_posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
        else:
            return redirect('/dashboard')   # redirecting back to login page if login fails
    else:
        return render_template("login.html", params=params)


@app.route("/logout")
def logout():
    session.pop('user')     # remove the user from the session
    return redirect('/dashboard')


@app.route("/edit/<string:sno>", methods=['GET', 'POST'])       # using a variable url parameter 'sno'
def edit(sno):
    if "user" in session and session['user'] == params['admin_user']:
        if request.method == "POST":
            title = request.form.get('title')
            tag_line = request.form.get('tag_line')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_url = request.form.get('img_url')
            name = request.form.get('name')
            date = datetime.now()

            if sno == 'new-post':                   # for adding a new post
                new_post = my_posts(img_url=img_url, title=title, tag_line=tag_line, slug=slug, content=content,
                                    name=name, date=date)
                db.session.add(new_post)
                db.session.commit()
            else:                                                # for editing existing post
                post = my_posts.query.filter_by(sno=sno).first()
                post.title = title
                post.tag_line = tag_line
                post.slug = slug
                post.img_url = img_url
                post.content = content
                post.name = name
                db.session.commit()         # finalizing the changes in the post
                return redirect('/edit/' + sno)

        post = my_posts.query.filter_by(sno=sno).first()        # searching the post with given 'sno'
        return render_template('edit.html', params=params, post=post, sno=sno)


@app.route('/delete/<string:sno>', methods=['GET', 'POST'])         # using a variable url parameter 'sno'
def delete(sno):
    if "user" in session and session['user'] == params['admin_user']:
        post = my_posts.query.filter_by(sno=sno).first()
        db.session.delete(post)         # deleting the selected post
        db.session.commit()
        return redirect('/dashboard')


# @app.route('/uploader', methods=['GET', 'POST'])        # for uploading files in given directory
# def uploader():
#     if "user" in session and session['user'] == params['admin_user']:
#         if request.method == "POST":
#             f = request.files['file1']      # request to access the file uploaded on variable 'file1'
#             f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))          # saving file at given file location
#             return 'Uploaded Successfully'

if __name__ == '__main__':
    app.run()       # running the flask web app
