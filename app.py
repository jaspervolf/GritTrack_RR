import os
import json
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-me-in-production')

_db_url = os.environ.get('DATABASE_URL', 'sqlite:///grittrack.db')
if _db_url.startswith('postgres://'):
    _db_url = _db_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif _db_url.startswith('postgresql://'):
    _db_url = _db_url.replace('postgresql://', 'postgresql+psycopg://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db           = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth_page'

# ── Models ─────────────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sessions      = db.relationship('WorkoutSession', backref='user', lazy=True,
                                    cascade='all, delete-orphan')

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)


class WorkoutSession(db.Model):
    __tablename__ = 'workout_sessions'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date        = db.Column(db.String(50), nullable=False)
    notes       = db.Column(db.Text, default='')
    lifts_json  = db.Column(db.Text, default='[]')
    cardio_json = db.Column(db.Text, default='[]')
    created_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id':     self.id,
            'date':   self.date,
            'notes':  self.notes or '',
            'lifts':  json.loads(self.lifts_json  or '[]'),
            'cardio': json.loads(self.cardio_json or '[]'),
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ── Auth pages ─────────────────────────────────────────────────────────────────
@app.route('/login')
@app.route('/register')
def auth_page():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('auth.html')


# ── Auth API ───────────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
def register():
    d        = request.get_json()
    username = (d.get('username') or '').strip().lower()
    email    = (d.get('email')    or '').strip().lower()
    password =  d.get('password') or ''

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required.'}), 400
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters.'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'That username is already taken.'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'That email is already registered.'}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({'ok': True, 'username': user.username}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    d        = request.get_json()
    username = (d.get('username') or '').strip().lower()
    password =  d.get('password') or ''

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    login_user(user, remember=True)
    return jsonify({'ok': True, 'username': user.username})


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'ok': True})


# ── Session API ────────────────────────────────────────────────────────────────
@app.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    rows = (WorkoutSession.query
            .filter_by(user_id=current_user.id)
            .order_by(WorkoutSession.date.asc())
            .all())
    return jsonify([r.to_dict() for r in rows])


@app.route('/api/sessions', methods=['POST'])
@login_required
def create_session():
    d  = request.get_json()
    ws = WorkoutSession(
        user_id     = current_user.id,
        date        = d.get('date', datetime.now(timezone.utc).isoformat()),
        notes       = d.get('notes', ''),
        lifts_json  = json.dumps(d.get('lifts',  [])),
        cardio_json = json.dumps(d.get('cardio', [])),
    )
    db.session.add(ws)
    db.session.commit()
    return jsonify(ws.to_dict()), 201


@app.route('/api/sessions/<int:sid>', methods=['PUT'])
@login_required
def update_session(sid):
    ws = WorkoutSession.query.filter_by(id=sid, user_id=current_user.id).first_or_404()
    d  = request.get_json()
    ws.notes       = d.get('notes', ws.notes)
    ws.lifts_json  = json.dumps(d.get('lifts',  []))
    ws.cardio_json = json.dumps(d.get('cardio', []))
    ws.updated_at  = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(ws.to_dict())


@app.route('/api/sessions/<int:sid>', methods=['DELETE'])
@login_required
def delete_session(sid):
    ws = WorkoutSession.query.filter_by(id=sid, user_id=current_user.id).first_or_404()
    db.session.delete(ws)
    db.session.commit()
    return jsonify({'ok': True})


# ── Serve service worker from root for full PWA scope ─────────────────────────
@app.route('/sw.js')
def service_worker():
    return (app.send_static_file('sw.js'), 200,
            {'Content-Type': 'application/javascript'})


# ── Main app ───────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    return render_template('app.html', username=current_user.username)


# ── DB init ────────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
