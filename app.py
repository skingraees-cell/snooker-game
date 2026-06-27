from flask import Flask, render_template, request, redirect

app = Flask(__name__)

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
        return render_template("dashboard.html")
    else:
        return "Invalid login"

@app.route("/admin")
def admin():
    if request.args.get("key") != "123456789":
        return "Access Denied", 403

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT id, email FROM users")
    users = cur.fetchall()

    conn.close()

    return render_template("admin.html", users=users)


if __name__ == "__main__":
    app.run(debug=True)
