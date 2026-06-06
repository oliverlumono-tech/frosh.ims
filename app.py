import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, redirect, request, g, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")
DATABASE = os.path.join(os.path.dirname(__file__), "froshims.db")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS registrants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sport TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

SPORTS = ['Soccer', 'Basketball', 'Ultimate Frisbee']

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_user():
    return {'current_user': session.get('user')}

@app.route('/')
def index():
    return render_template('index.html', sports=SPORTS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            return render_template('login.html', error='Please enter a username.')
        session['user'] = username
        return redirect(url_for('index'))
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/deregister', methods=['POST'])
@login_required
def deregister():
    id = request.form.get('id')
    if id:
        conn = get_db()
        conn.execute("DELETE FROM registrants WHERE id = ?", (id,))
        conn.commit()
    return redirect("/registrants")

@app.route('/register', methods=['POST'])
def register():
    # validate name and sport
    name = request.form.get('name')
    if not name:
        return render_template("error.html", message="Please enter your name.")
    
    sports = request.form.getlist('sport')
    if not sports or not all(s in SPORTS for s in sports):
        return render_template("error.html", message="Please choose a valid sport.")
    
    conn = get_db()
    for s in sports:
        conn.execute("INSERT INTO registrants (name, sport) VALUES (?, ?)", (name, s))
    conn.commit()
    return redirect("/registrants")

@app.route('/registrants')
@login_required
def registrants():
    conn = get_db()
    cur = conn.execute("SELECT id, name, sport FROM registrants")
    registrants = [dict(row) for row in cur.fetchall()]
    return render_template("registrants.html", registrants=registrants)

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5004)
