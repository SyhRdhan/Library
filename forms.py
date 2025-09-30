from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SelectField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Masuk')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Konfirmasi Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('user', 'Pengguna'), ('pustakawan', 'Pustakawan')], validators=[DataRequired()])
    submit = SubmitField('Daftar')

class BookForm(FlaskForm):
    title = StringField('Judul', validators=[DataRequired(), Length(min=1, max=200)])
    author = StringField('Penulis', validators=[DataRequired(), Length(min=1, max=100)])
    year = IntegerField('Tahun', validators=[DataRequired(), NumberRange(min=1000, max=2100)])
    description = TextAreaField('Deskripsi', validators=[Length(max=500)])
    image = FileField('Gambar Sampul', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Hanya gambar JPG/PNG!')])
    submit = SubmitField('Simpan')

class ProfileForm(FlaskForm):
    current_password = PasswordField('Password Saat Ini', validators=[DataRequired()])
    new_password = PasswordField('Password Baru', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Konfirmasi Password Baru', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Profil')