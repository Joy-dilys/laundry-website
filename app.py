from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.route('/')
@login_required
def home():
    return render_template('index.html')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Bookings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(250))
    email = db.Column(db.String(150))
    service = db.Column(db.String(100))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    status = db.Column(db.String(50), default='Pending')    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for('register'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))

        flash("Invalid credentials")
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return f"Welcome {current_user.username}!"


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for('login'))

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        service = request.form['service']
        date = request.form['date']
        time = request.form['time']
        email = request.form['email']
        address = request.form['address']

        new_booking = Bookings(name=name,phone=phone,address=address, email=email, service=service, date=date, time=time)
        db.session.add(new_booking)
        db.session.commit()
        flash("Booking submitted successfully!")
        return redirect(url_for('booking'))
        
        
    return render_template('booking.html')
   

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.username != 'admin':
        flash("Access denied: Admins only.")
        return redirect(url_for('home'))

    bookings = Bookings.query.all()
    return render_template('admin.html', bookings=bookings)

@app.route('/mark_done/<int:booking_id>', methods=['POST'])
@login_required
def mark_done(booking_id):
    if current_user.username != 'admin':
        flash("Access denied.")
        return redirect(url_for('home'))

    booking = Bookings.query.get_or_404(booking_id)
    booking.status = 'Done'
    db.session.commit()


    flash(f"Booking for {booking.name} marked as Done.")
    return redirect(url_for('admin_dashboard'))
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This creates all tables defined by your models
    app.run(debug=True, use_reloader=False)