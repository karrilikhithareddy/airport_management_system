from flask import Flask, request, redirect, render_template, make_response, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

# =========================================
# SECRET KEY
# =========================================

app.secret_key = "airport-management-secret-key"


# =========================================
# DATABASE CONNECTION
# =========================================

def get_database_connection():
    connection = sqlite3.connect("users.db")
    connection.row_factory = sqlite3.Row
    return connection


# =========================================
# CREATE DATABASE AND TABLES
# =========================================

def create_database():

    connection = get_database_connection()
    cursor = connection.cursor()

    # USERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # FLIGHTS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_number TEXT NOT NULL,
            airline TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_time TEXT NOT NULL,
            arrival_time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # PASSENGERS TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            phone TEXT NOT NULL,
            flight_number TEXT NOT NULL,
            seat_number TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

    print("Database and tables created successfully!")


# =========================================
# LOGIN CHECK
# =========================================

def login_required():
    return "user_id" in session


# =========================================
# SET THEME
# =========================================

@app.route("/set-theme/<theme>")
def set_theme(theme):

    if theme not in ["light", "dark"]:
        theme = "light"

    previous_page = request.referrer or "/"

    response = make_response(
        redirect(previous_page)
    )

    response.set_cookie(
        "theme",
        theme,
        max_age=60 * 60 * 24 * 365
    )

    return response


# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():

    if not login_required():
        return redirect("/login")

    theme = request.cookies.get("theme", "light")

    connection = get_database_connection()
    cursor = connection.cursor()

    # Total flights
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM flights
    """)

    total_flights = cursor.fetchone()["total"]

    # Total passengers
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM passengers
    """)

    total_passengers = cursor.fetchone()["total"]

    # Scheduled flights
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM flights
        WHERE status = 'Scheduled'
    """)

    scheduled_flights = cursor.fetchone()["total"]

    connection.close()

    username = session.get("username")
    fullname = session.get("fullname")

    return render_template(
        "home.html",
        theme=theme,
        username=username,
        fullname=fullname,
        total_flights=total_flights,
        total_passengers=total_passengers,
        scheduled_flights=scheduled_flights
    )


# =========================================
# REGISTER PAGE
# =========================================

@app.route("/registerdemo", methods=["GET"])
def register_page():

    theme = request.cookies.get("theme", "light")

    return render_template(
        "registerdemo.html",
        theme=theme
    )


# =========================================
# REGISTER
# =========================================

@app.route("/registerdemo", methods=["POST"])
def register():

    fullname = request.form.get("fullname", "").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    theme = request.cookies.get("theme", "light")

    if not fullname:
        return render_template(
            "registerdemo.html",
            theme=theme,
            error="Full name is required."
        )

    if not username:
        return render_template(
            "registerdemo.html",
            theme=theme,
            error="Username is required."
        )

    if not password:
        return render_template(
            "registerdemo.html",
            theme=theme,
            error="Password is required."
        )

    hashed_password = generate_password_hash(password)

    connection = get_database_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (
                fullname,
                username,
                password
            )
            VALUES (?, ?, ?)
        """, (
            fullname,
            username,
            hashed_password
        ))

        connection.commit()

    except sqlite3.IntegrityError:

        connection.close()

        return render_template(
            "registerdemo.html",
            theme=theme,
            error="Username already exists."
        )

    connection.close()

    return redirect("/login")


# =========================================
# LOGIN PAGE
# =========================================

@app.route("/login", methods=["GET"])
def login_page():

    if "user_id" in session:
        return redirect("/")

    theme = request.cookies.get("theme", "light")

    return render_template(
        "login.html",
        theme=theme
    )


# =========================================
# LOGIN
# =========================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    theme = request.cookies.get("theme", "light")

    if not username or not password:
        return render_template(
            "login.html",
            theme=theme,
            error="Username and password are required."
        )

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            fullname,
            username,
            password
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()

    connection.close()

    if user is None:
        return render_template(
            "login.html",
            theme=theme,
            error="Username or password is incorrect."
        )

    password_correct = check_password_hash(
        user["password"],
        password
    )

    if not password_correct:
        return render_template(
            "login.html",
            theme=theme,
            error="Username or password is incorrect."
        )

    session.clear()

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["fullname"] = user["fullname"]

    return redirect("/")


# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================================
# ADD FLIGHT PAGE
# =========================================

@app.route("/add-flight", methods=["GET"])
def add_flight_page():

    if not login_required():
        return redirect("/login")

    theme = request.cookies.get("theme", "light")

    return render_template(
        "add-flight.html",
        theme=theme
    )


# =========================================
# ADD FLIGHT
# =========================================

@app.route("/add-flight", methods=["POST"])
def add_flight():

    if not login_required():
        return redirect("/login")

    flight_number = request.form.get(
        "flight_number", ""
    ).strip()

    airline = request.form.get(
        "airline", ""
    ).strip()

    source = request.form.get(
        "source", ""
    ).strip()

    destination = request.form.get(
        "destination", ""
    ).strip()

    departure_time = request.form.get(
        "departure_time", ""
    ).strip()

    arrival_time = request.form.get(
        "arrival_time", ""
    ).strip()

    status = request.form.get(
        "status", ""
    ).strip()

    if not flight_number:
        return "Flight number is required!"

    if not airline:
        return "Airline is required!"

    if not source:
        return "Source is required!"

    if not destination:
        return "Destination is required!"

    if not departure_time:
        return "Departure time is required!"

    if not arrival_time:
        return "Arrival time is required!"

    if not status:
        return "Flight status is required!"

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO flights
        (
            flight_number,
            airline,
            source,
            destination,
            departure_time,
            arrival_time,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        flight_number,
        airline,
        source,
        destination,
        departure_time,
        arrival_time,
        status
    ))

    connection.commit()
    connection.close()

    return redirect("/flights")


# =========================================
# FLIGHTS LIST
# =========================================

@app.route("/flights")
def flights():

    if not login_required():
        return redirect("/login")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM flights
        ORDER BY id DESC
    """)

    flights = cursor.fetchall()

    connection.close()

    theme = request.cookies.get("theme", "light")

    return render_template(
        "flights.html",
        flights=flights,
        theme=theme
    )


# =========================================
# DELETE FLIGHT
# =========================================

@app.route("/delete-flight/<int:id>")
def delete_flight(id):

    if not login_required():
        return redirect("/login")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM flights
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    return redirect("/flights")


# =========================================
# ADD PASSENGER PAGE
# =========================================

@app.route("/add-passenger", methods=["GET"])
def add_passenger_page():

    if not login_required():
        return redirect("/login")

    theme = request.cookies.get("theme", "light")

    return render_template(
        "add-passenger.html",
        theme=theme
    )


# =========================================
# ADD PASSENGER
# =========================================

@app.route("/add-passenger", methods=["POST"])
def add_passenger():

    if not login_required():
        return redirect("/login")

    name = request.form.get(
        "name", ""
    ).strip()

    age = request.form.get(
        "age", ""
    ).strip()

    gender = request.form.get(
        "gender", ""
    ).strip()

    phone = request.form.get(
        "phone", ""
    ).strip()

    flight_number = request.form.get(
        "flight_number", ""
    ).strip()

    seat_number = request.form.get(
        "seat_number", ""
    ).strip()

    if not name:
        return "Passenger name is required!"

    if not age:
        return "Age is required!"

    if not gender:
        return "Gender is required!"

    if not phone:
        return "Phone is required!"

    if not flight_number:
        return "Flight number is required!"

    if not seat_number:
        return "Seat number is required!"

    try:
        age = int(age)
    except ValueError:
        return "Age must be a number!"

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO passengers
        (
            name,
            age,
            gender,
            phone,
            flight_number,
            seat_number
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        age,
        gender,
        phone,
        flight_number,
        seat_number
    ))

    connection.commit()
    connection.close()

    return redirect("/passengers")


# =========================================
# PASSENGERS LIST
# =========================================

@app.route("/passengers")
def passengers():

    if not login_required():
        return redirect("/login")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM passengers
        ORDER BY id DESC
    """)

    passengers = cursor.fetchall()

    connection.close()

    theme = request.cookies.get("theme", "light")

    return render_template(
        "passengers.html",
        passengers=passengers,
        theme=theme
    )


# =========================================
# DELETE PASSENGER
# =========================================

@app.route("/delete-passenger/<int:id>")
def delete_passenger(id):

    if not login_required():
        return redirect("/login")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM passengers
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    return redirect("/passengers")


# =========================================
# EDIT PASSENGER PAGE
# =========================================

@app.route("/edit-passenger/<int:id>", methods=["GET"])
def edit_passenger_page(id):

    if not login_required():
        return redirect("/login")

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM passengers
        WHERE id = ?
    """, (id,))

    passenger = cursor.fetchone()

    connection.close()

    if passenger is None:
        return """
        <h2>Passenger not found!</h2>
        <a href="/passengers">Back to Passengers</a>
        """

    theme = request.cookies.get("theme", "light")

    return render_template(
        "edit-passenger.html",
        passenger=passenger,
        theme=theme
    )


# =========================================
# EDIT PASSENGER
# =========================================

@app.route("/edit-passenger/<int:id>", methods=["POST"])
def edit_passenger(id):

    if not login_required():
        return redirect("/login")

    name = request.form.get(
        "name", ""
    ).strip()

    age = request.form.get(
        "age", ""
    ).strip()

    gender = request.form.get(
        "gender", ""
    ).strip()

    phone = request.form.get(
        "phone", ""
    ).strip()

    flight_number = request.form.get(
        "flight_number", ""
    ).strip()

    seat_number = request.form.get(
        "seat_number", ""
    ).strip()

    if not name:
        return "Passenger name is required!"

    if not age:
        return "Age is required!"

    if not gender:
        return "Gender is required!"

    if not phone:
        return "Phone is required!"

    if not flight_number:
        return "Flight number is required!"

    if not seat_number:
        return "Seat number is required!"

    try:
        age = int(age)
    except ValueError:
        return "Age must be a number!"

    connection = get_database_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE passengers
        SET
            name = ?,
            age = ?,
            gender = ?,
            phone = ?,
            flight_number = ?,
            seat_number = ?
        WHERE id = ?
    """, (
        name,
        age,
        gender,
        phone,
        flight_number,
        seat_number,
        id
    ))

    connection.commit()
    connection.close()

    return redirect("/passengers")


# =========================================
# SEARCH
# =========================================

@app.route("/search")
def search():

    if not login_required():
        return redirect("/login")

    search_text = request.args.get(
        "q", ""
    ).strip()

    connection = get_database_connection()
    cursor = connection.cursor()

    search_value = f"%{search_text}%"

    # SEARCH FLIGHTS
    cursor.execute("""
        SELECT *
        FROM flights
        WHERE
            flight_number LIKE ?
            OR airline LIKE ?
            OR source LIKE ?
            OR destination LIKE ?
        ORDER BY id DESC
    """, (
        search_value,
        search_value,
        search_value,
        search_value
    ))

    flights = cursor.fetchall()

    # SEARCH PASSENGERS
    cursor.execute("""
        SELECT *
        FROM passengers
        WHERE
            name LIKE ?
            OR phone LIKE ?
            OR flight_number LIKE ?
            OR seat_number LIKE ?
        ORDER BY id DESC
    """, (
        search_value,
        search_value,
        search_value,
        search_value
    ))

    passengers = cursor.fetchall()

    connection.close()

    theme = request.cookies.get("theme", "light")

    return render_template(
        "search.html",
        flights=flights,
        passengers=passengers,
        search_text=search_text,
        theme=theme
    )


# =========================================
# START APPLICATION
# =========================================

if __name__ == "__main__":
    create_database()
    app.run(debug=True)