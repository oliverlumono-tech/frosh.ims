import os
import sqlite3
from flask import Flask, render_template, redirect, request, g

app = Flask(__name__)
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

@app.route('/')
def index():
    return render_template('index.html', sports=SPORTS)

@app.route('/deregister', methods=['POST'])
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
def registrants(): 
    conn = get_db()
    cur = conn.execute("SELECT id, name, sport FROM registrants")
    registrants = [dict(row) for row in cur.fetchall()]
    return render_template("registrants.html", registrants=registrants)

init_db()

if __name__ == '__main__':
    app.run(debug=True, port=5004)
