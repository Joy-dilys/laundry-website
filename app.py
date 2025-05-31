from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

# Admin decorator to protect admin routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Access denied: Admins only.")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Added admin role field

    bookings = db.relationship('Booking', backref='user', lazy=True)  # Relationship to bookings


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to user
    phone = db.Column(db.String(15))
    address = db.Column(db.String(250))
    service = db.Column(db.String(100))
    date = db.Column(db.Date)  # Use Date for booking date
    time = db.Column(db.Time)  # Use Time for booking time
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!")
            return redirect(url_for('register'))

        # Make first registered user an admin (optional)
        is_admin = False
        if User.query.count() == 0:
            is_admin = True

        new_user = User(username=username, password=password, is_admin=is_admin)
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
            flash(f"Welcome, {user.username}!")
            return redirect(url_for('home'))

        flash("Invalid credentials")
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        users = User.query.all()
        return render_template('admin_dashboard.html', bookings=bookings, users=users)
    else:
        return render_template('user_dashboard.html')



@app.route('/booking', methods=['GET', 'POST'])
@login_required  # Only logged-in users can book
def booking():
    if request.method == 'POST':
        phone = request.form['phone']
        service = request.form['service']
        date_str = request.form['date']
        time_str = request.form['time']
        address = request.form['address']

        # Convert strings to datetime objects
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            time = datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            flash("Invalid date or time format. Please use YYYY-MM-DD and HH:MM.")
            return redirect(url_for('booking'))

        new_booking = Booking(
            user_id=current_user.id,
            phone=phone,
            address=address,
            service=service,
            date=date,
            time=time
        )
        db.session.add(new_booking)
        db.session.commit()
        flash("Booking submitted successfully!")
        return redirect(url_for('view_bookings'))

    return render_template('booking.html')


@app.route('/my_bookings')
@login_required
def view_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    users = User.query.all()
    return render_template('admin.html', bookings=bookings, users=users)


@app.route('/admin/booking/<int:booking_id>/update', methods=['POST'])
@login_required
@admin_required
def update_booking_status(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_status = request.form.get('status')
    if new_status:
        booking.status = new_status
        db.session.commit()
        flash('Booking status updated successfully.')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/booking/<int:booking_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash("Booking deleted.")
    return redirect(url_for('admin_dashboard'))


@app.route('/services')
def services():
    return render_template('services.html')


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/bookings')
@login_required
def view_other_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/admin/manage')
@login_required
@admin_required
def admin_manage():
    users = User.query.all()
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin_manage.html', users=users, bookings=bookings)



@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.username != 'admin':
        flash("Access denied.")
        return redirect(url_for('home'))

    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash("You cannot delete the admin user.")
        return redirect(url_for('admin_manage'))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted.")
    return redirect(url_for('admin_manage'))


@app.route('/admin/delete_booking/<int:booking_id>', methods=['POST'])
@login_required
def admin_delete_booking(booking_id):
    if current_user.username != 'admin':
        flash("Access denied.")
        return redirect(url_for('home'))

    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash(f"Booking for {booking.name} deleted.")
    return redirect(url_for('admin_manage'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)
