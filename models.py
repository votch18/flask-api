from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

class AudioBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    cover_image = db.Column(db.String(200), nullable=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    audiobook_id = db.Column(db.Integer, db.ForeignKey('audio_book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('votes', lazy=True))
    audiobook = db.relationship('AudioBook', backref=db.backref('votes', lazy=True))