from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit, rooms
import sqlite3

app = Flask(__name__)
app.secret_key = "snooker_secret_key"

socketio = SocketIO(app, cors_allowed_origins="*")

online_users = set()


def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

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

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users(email,password) VALUES(?,?)",
            (email, password)
        )
        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return "User already exists"

    conn.close()

    return redirect("/login")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
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

    return "Invalid Email or Password"
@app.route("/lobby")
def lobby():
    if "email" not in session:
        return redirect("/login")

    return render_template(
        "lobby.html",
        email=session["email"]
    )


@app.route("/logout")
def logout():

    if "email" in session:
        online_users.discard(session["email"])
        session.clear()

    return redirect("/login")


@app.route("/admin")
def admin():

    if request.args.get("key") != "123456789":
        return "Access Denied", 403

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT id,email,password FROM users")

    users = cur.fetchall()

    conn.close()

    return render_template("admin.html", users=users)


@socketio.on("connect")
def handle_connect():

    if "email" in session:

        online_users.add(session["email"])

        emit(
            "online_users",
            list(online_users),
            broadcast=True
        )


@socketio.on("disconnect")
def handle_disconnect():

    if "email" in session:

        online_users.discard(session["email"])

        emit(
            "online_users",
            list(online_users),
            broadcast=True
        )


@socketio.on("challenge")
def handle_challenge(data):

    emit(
        "challenge_received",
        {
            "from": session["email"],
            "to": data["player"]
        },
        broadcast=True
    )
    rooms = {}


@socketio.on("accept_challenge")
def accept_challenge(data):

    room = data["room"]

    emit(
        "game_started",
        {
            "room": room
        },
        broadcast=True
    )


@socketio.on("join_room")
def join_room_event(data):

    room = data["room"]

    if room not in rooms:
        rooms[room] = []

    if session["email"] not in rooms[room]:
        rooms[room].append(session["email"])

    emit(
        "room_players",
        {
            "room": room,
            "players": rooms[room]
        },
        broadcast=True
    )


@socketio.on("leave_room")
def leave_room_event(data):

    room = data["room"]

    if room in rooms:

        if session["email"] in rooms[room]:
            rooms[room].remove(session["email"])

        if len(rooms[room]) == 0:
            del rooms[room]

        emit(
            "room_players",
            {
                "room": room,
                "players": rooms.get(room, [])
            },
            broadcast=True
        )


if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )