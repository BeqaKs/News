import os
from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# Import your local modules
from models import db, User, News
from forms import RegistrationForm, LoginForm, NewsForm

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///news.sqlite"

# --- FIX: ABSOLUTE PATH SETUP ---
# This ensures the computer finds the folder no matter where you run the script from
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "static/uploads")

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route("/")
def index():
    news_list = News.query.order_by(News.id.desc()).all()
    return render_template("index.html", news_list=news_list)

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists", "danger")
            return redirect(url_for("register"))
        
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))
        
    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("index"))
        else:
            flash("Login Unsuccessful. Please check username and password", "danger")
            
    return render_template("login.html", form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/add_news", methods=["GET", "POST"])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        filename = None
        # Handle Image Upload
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            
            # FIX: Create folder if it doesn't exist
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Save to DB
        news = News(
            title=form.title.data,
            content=form.content.data,
            image_url=filename
        )
        db.session.add(news)
        db.session.commit()
        flash("News post created!", "success")
        return redirect(url_for("index"))
    
    # Check for validation errors and flash them
    if form.errors:
        for err_msg in form.errors.values():
            flash(f"Error: {err_msg}", "danger")

    return render_template("add_news.html", form=form)

@app.route("/news/<int:news_id>")
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    return render_template("news_detail.html", news=news)

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)