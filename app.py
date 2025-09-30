from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap5
from flask_paginate import Pagination, get_page_args
from models import db, User, Book, Loan
from forms import LoginForm, RegisterForm, BookForm, ProfileForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Ganti dengan kunci rahasia yang aman
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['UPLOAD_FOLDER'] = 'static/assets/images'

db.init_app(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap5(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

logging.basicConfig(level=logging.DEBUG)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def is_authorized(role_required):
    def decorator(f):
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Anda harus login terlebih dahulu.', 'error')
                return redirect(url_for('login'))
            if current_user.role != 'admin' and role_required == 'admin':
                flash('Akses ditolak. Hanya admin yang diizinkan.', 'error')
                return redirect(url_for('home'))
            if current_user.role not in ['admin', 'pustakawan'] and role_required == 'pustakawan':
                flash('Akses ditolak. Hanya pustakawan atau admin yang diizinkan.', 'error')
                return redirect(url_for('home'))
            if current_user.role != 'user' and role_required == 'user':
                flash('Akses ditolak. Hanya pengguna yang diizinkan.', 'error')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login berhasil!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Username atau password salah.', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username sudah digunakan.', 'error')
            return render_template('register.html', form=form)
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_pw, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/home')
@login_required
def home():
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    pagination_books = Book.query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('home.html', books=pagination_books.items, pagination=pagination_books, role=current_user.role)

@app.route('/books')
@login_required
def books():
    search = request.args.get('search')
    query = Book.query
    if search:
        query = query.filter(db.or_(Book.title.ilike(f'%{search}%'), Book.author.ilike(f'%{search}%')))
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    pagination = query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('books.html', books=pagination.items, pagination=pagination, search=search)

@app.route('/book/<int:id>')
@login_required
def book_detail(id):
    book = Book.query.get_or_404(id)
    active_loans = Loan.query.filter_by(book_id=id, returned=False).count()
    return render_template('book_detail.html', book=book, active_loans=active_loans)

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
@is_authorized('pustakawan')
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(title=form.title.data, author=form.author.data, year=form.year.data, description=form.description.data)
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                form.image.data.save(filepath)
                book.image_path = f'static/assets/images/{filename}'
        db.session.add(book)
        db.session.commit()
        flash('Buku berhasil ditambahkan.', 'success')
        return redirect(url_for('books'))
    return render_template('add_books.html', form=form)

@app.route('/edit_book/<int:id>', methods=['GET', 'POST'])
@login_required
@is_authorized('pustakawan')
def edit_book(id):
    book = Book.query.get_or_404(id)
    form = BookForm(obj=book)
    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.year = form.year.data
        book.description = form.description.data
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            if filename:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                form.image.data.save(filepath)
                book.image_path = f'static/assets/images/{filename}'
        db.session.commit()
        flash('Buku berhasil diedit.', 'success')
        return redirect(url_for('books'))
    return render_template('edit_books.html', form=form, book=book)

@app.route('/delete_book/<int:id>')
@login_required
@is_authorized('admin')
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    flash('Buku berhasil dihapus.', 'success')
    return redirect(url_for('books'))

@app.route('/borrow/<int:book_id>')
@login_required
@is_authorized('user')
def borrow(book_id):
    book = Book.query.get_or_404(book_id)
    existing_loan = Loan.query.filter_by(user_id=current_user.id, book_id=book_id, returned=False).first()
    if existing_loan:
        flash('Buku ini sudah dipinjam oleh Anda.', 'error')
    else:
        active_loan = Loan.query.filter_by(book_id=book_id, returned=False).first()
        if active_loan:
            flash('Buku sedang dipinjam oleh pengguna lain.', 'error')
        else:
            loan = Loan(user_id=current_user.id, book_id=book_id, borrow_date=datetime.utcnow(), due_date=datetime.utcnow() + timedelta(days=14))
            db.session.add(loan)
            db.session.commit()
            flash('Buku berhasil dipinjam.', 'success')
    return redirect(url_for('books'))

@app.route('/return/<int:loan_id>')
@login_required
@is_authorized('user')
def return_book(loan_id):
    loan = Loan.query.filter_by(id=loan_id, user_id=current_user.id).first_or_404()
    if loan.returned:
        flash('Buku sudah dikembalikan.', 'error')
    else:
        loan.return_date = datetime.utcnow()
        loan.returned = True
        db.session.commit()
        flash('Buku berhasil dikembalikan.', 'success')
    return redirect(url_for('profile'))

@app.route('/profile')
@login_required
def profile():
    loans = Loan.query.filter_by(user_id=current_user.id).order_by(Loan.borrow_date.desc()).all()
    active_loans = [loan for loan in loans if not loan.returned]
    return render_template('profile.html', user=current_user, loans=loans, active_loans=active_loans)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.password, form.current_password.data):
            flash('Password saat ini salah.', 'error')
            return render_template('edit_profile.html', form=form)
        current_user.password = generate_password_hash(form.new_password.data)
        db.session.commit()
        flash('Password berhasil diubah.', 'success')
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', form=form)

@app.route('/dashboard')
@login_required
@is_authorized('pustakawan')
def dashboard():
    total_users = User.query.count()
    total_books = Book.query.count()
    active_loans = Loan.query.filter_by(returned=False).count()
    return render_template('dashboard.html', stats={'users': total_users, 'books': total_books, 'loans': active_loans})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout berhasil.', 'success')
    return redirect(url_for('login'))

def init_sample_data():
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            if admin.role != 'admin':
                admin.role = 'admin'
                db.session.commit()
        else:
            hashed_pw = generate_password_hash('adminpass')
            admin = User(username='admin', password=hashed_pw, role='admin')
            db.session.add(admin)
            db.session.commit()
        
        if not User.query.filter_by(username='pustakawan').first():
            hashed_pw = generate_password_hash('pustawanpass')
            pustakawan = User(username='pustakawan', password=hashed_pw, role='pustakawan')
            db.session.add(pustakawan)
            db.session.commit()
        
        if not Book.query.first():
            books = [
                Book(
                    title='Buku Contoh 1', 
                    author='Penulis A', 
                    year=2020, 
                    description='Buku ini mengeksplorasi dasar-dasar manajemen perpustakaan digital di era pasca-pandemi, dengan fokus pada integrasi teknologi AI untuk katalogisasi otomatis. Melalui studi kasus dari berbagai institusi global, penulis membahas tantangan aksesibilitas dan solusi berbasis cloud, menjadikannya panduan esensial bagi pustakawan modern yang ingin mentransformasi koleksi tradisional menjadi platform interaktif.',
                    image_path='static/assets/images/Hitam_2045.jpg'
                ),
                Book(
                    title='Buku Contoh 2', 
                    author='Penulis B', 
                    year=2021, 
                    description='Sebuah analisis mendalam tentang etika peminjaman digital, Buku Contoh 2 mengungkap isu hak cipta, privasi data pembaca, dan dampak sosial dari perpustakaan virtual. Dengan pendekatan interdisipliner yang menggabungkan hukum, teknologi, dan sosiologi, penulis menyajikan kerangka kerja praktis untuk kebijakan berkelanjutan, ideal untuk administrator yang menghadapi regulasi baru di bidang informasi digital.',
                    image_path=None  # Placeholder; upload nanti
                ),
                Book(
                    title='Buku Contoh 3', 
                    author='Penulis C', 
                    year=2022, 
                    description='Buku ini membahas inovasi dalam pengalaman pengguna perpustakaan digital, termasuk rekomendasi berbasis machine learning dan integrasi realitas augmented untuk navigasi virtual. Didukung oleh data empiris dari survei global, penulis menawarkan strategi implementasi langkah demi langkah, menjadikannya sumber daya berharga bagi pengembang dan pengguna yang mencari cara meningkatkan keterlibatan dengan konten literatur.',
                    image_path=None  # Placeholder; upload nanti
                )
            ]
            db.session.add_all(books)
            db.session.commit()
        
        if not Loan.query.first():
            sample_user = User.query.filter_by(username='user1').first()
            if not sample_user:
                hashed_pw = generate_password_hash('userpass')
                sample_user = User(username='user1', password=hashed_pw, role='user')
                db.session.add(sample_user)
                db.session.commit()
            sample_loan = Loan(user_id=sample_user.id, book_id=1, borrow_date=datetime.utcnow() - timedelta(days=5), due_date=datetime.utcnow() + timedelta(days=9))
            db.session.add(sample_loan)
            db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_sample_data()
    app.run(debug=True)