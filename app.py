from flask import Flask, render_template, request, flash, session, logging, redirect, url_for
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from data import data_sets
from models import *
from functools import wraps

app = Flask(__name__)

app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:8889/flask_articles'
app.config['SECRET_KEY'] =  b'_5#y2L"F4Q8z\n\xec]/'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else: 
            flash('Unauthorised, Please logIn to continue', 'danger')   
            return redirect(url_for('login', next= request.endpoint))
    return wrap 




@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    data = data_sets()
    return render_template('articles.html', content = data)


@app.route('/article/<int:id>')
def article(id):
    data = [dat for dat in data_sets() if dat['id'] == id]
    print(data)
    return render_template('article.html', content = data[0])


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired(), validators.equal_to('confirm', message= 'Password doest not match')])
    confirm = PasswordField('Confirm Password')

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=6, max=255)])    
    body = TextAreaField('Body', [validators.Length(min=4)])
       

@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        # check whether the user is already exist in database
        username = form.username.data
        exist_username = UsersModel.query.filter_by(username = username).first()
        if exist_username:
             flash('User details already exist', 'warning')
             return render_template('login.html') #TODO Change to login page once the login is implemented
        password = sha256_crypt.encrypt(str(form.password.data))
        user = UsersModel(name= form.name.data, email = form.email.data, username = username, password = password)
        db.session.add(user)
        db.session.commit()
        flash('You are now successfully registered. Please log in to continue', 'success')
        return redirect(url_for('login'))
        #return render_template('register.html', form=form)
    else:   
        return render_template('register.html', form=form)   


@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        print(request.args.get('next'))
        exist_username = UsersModel.query.filter_by(username = username).first()
        if exist_username:
            if sha256_crypt.verify(password_candidate, exist_username.password):
                flash(f'You are successfully logged in', 'info')
                session['logged_In'] = True
                session['username'] = username
                nxt = request.args.get('next')
                #return redirect_dest(fallback=render_template('dashboard.html'))
                return  redirect( url_for(nxt)) if nxt else render_template('dashboard.html')
            else:
                error = 'Invalid password'
                return render_template('login.html', error= error)   
        else:
            error = 'User not found'
            return render_template('login.html', error= error)    
    return render_template('login.html')             

@app.route('/dashboard')
@login_required
def dashboard():
    articles = Articles.query.all()
    if len(articles) >0:
        msg = "No articles found"
        return render_template('dashboard.html', msg = msg)
    else:
        return render_template('dashboard.html', articles = articles)

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect( url_for('login'))

@app.route('/add_article', methods = ['POST', 'GET'])
def add_article():
    article_form = ArticleForm(request.form)

    if request.method == 'POST' and article_form.validate():
        title = article_form.title.data
        body = article_form.body.data
        article = Articles(title= title, author = session['username'], body = body)
        db.session.add(article)
        db.session.commit()
        flash('Your article is successfully added', 'success')
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', form = article_form)


def create_database():
        with app.app_context():
             db.create_all()
       

if __name__ =='main':
    app.run()