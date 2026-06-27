from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
import sqlite3

online_users = set()

app = Flask(__name__)
app.secret_key = "123456"
socketio = SocketIO(app)


# د ډیټابیس جوړول
def init_db():
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():

    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users(email,password) VALUES(?,?)",
            (email, password)
        )

        conn.commit()

    except:
        return "User already exists"

    finally:
        conn.close()

    return redirect("/login")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect('users.db')
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email, password)
    )

    user = cur.fetchone()

    conn.close()

    if user:
        session["email"] = user[1]
        return redirect("/lobby")
    else:
        return "Invalid login"

@app.route("/admin")
def admin():
    if request.args.get("key") != "123456789":
        return "Access Denied", 403

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT id, email, password FROM users")
    users = cur.fetchall()

    conn.close()

    return render_template("admin.html", users=users)

from flask_socketio import emit

@socketio.on("connect")
def handle_connect():
    print("A user connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("A user disconnected")
@app.route("/lobby")
def lobby():
    if "email" not in session:
        return redirect("/")
    return render_template("lobby.html", email=session["email"])

online_users = set()

@socketio.on("connect")
def connect():
    if "email" in session:
        online_users.add(session["email"])
    emit("online_users", list(online_users), broadcast=True)

@socketio.on("disconnect")
def disconnect():
    if "email" in session:
        online_users.discard(session["email"])
    emit("online_users", list(online_users), broadcast=True)

from flask_socketio import emit

@socketio.on("challenge")
def handle_challenge(data):
    emit("challenge_received", {
        "from": session["email"]
    }, broadcast=True)

if __name__ == "__main__":
   socketio.run(app, debug=True)
   
