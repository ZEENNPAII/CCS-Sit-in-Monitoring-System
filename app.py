from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages and session management

# SQLite Database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # This allows you to access columns by name
    return conn

# Create the database and table if it doesn't exist
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idno TEXT NOT NULL UNIQUE,
            lastname TEXT NOT NULL,
            firstname TEXT NOT NULL,
            midname TEXT,
            course TEXT NOT NULL,
            yearlevel INTEGER NOT NULL,
            email TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Create the admin account
def create_admin_account():
    conn = get_db_connection()
    existing_admin = conn.execute('SELECT * FROM users WHERE idno = ?', ('12345678',)).fetchone()
    if existing_admin is None:
        conn.execute('''
            INSERT INTO users (idno, lastname, firstname, midname, course, yearlevel, email, username, password, is_admin)
            VALUES ('12345678', 'Admin', 'Admin', '', 'Admin', 1, 'admin@example.com', 'admin', 'admin', 1)
        ''')
        conn.commit()
    conn.close()

@app.route('/')
def home():
    if 'user' in session:
        user = session['user']
        return render_template('home_user.html', firstname=user['firstname'], user=user)
    return render_template('home.html')  # Redirect to home page if not logged in

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        idno = request.form['idno']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE (idno = ? OR username = ?) AND password = ?', (idno, idno, password)).fetchone()
        conn.close()

        if user:
            session['user'] = {
                'idno': user['idno'],
                'firstname': user['firstname'],
                'lastname': user['lastname'],
                'midname': user['midname'],
                'course': user['course'],
                'yearlevel': user['yearlevel'],
                'email': user['email'],
                'username': user['username'],
                'is_admin': user['is_admin']
            }

            if user['is_admin']:  # Redirect admin to admin dashboard
                return redirect(url_for('admin_dashboard'))
            else:  # Redirect normal users to user home
                return redirect(url_for('home'))

        flash("Invalid credentials", "error")
        return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/admin')
def admin_dashboard():
    if 'user' in session and session['user'].get('is_admin'):
        conn = get_db_connection()
        users = conn.execute('SELECT * FROM users').fetchall()
        conn.close()
        return render_template('admin_dashboard.html', users=users)
    flash("You do not have access to this page.", "error")
    return redirect(url_for('admin_login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        idno = request.form['idno']
        lastname = request.form['lastname']
        firstname = request.form['firstname']
        midname = request.form['midname']
        course = request.form['course']
        yearlevel = request.form['yearlevel']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE idno = ?', (idno,)).fetchone()

        if existing_user:
            conn.close()
            flash('ID number already exists. Please choose a different ID.', 'error')
            return redirect(url_for('register'))

        conn.execute('''
            INSERT INTO users (idno, lastname, firstname, midname, course, yearlevel, email, username, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (idno, lastname, firstname, midname, course, yearlevel, email, username, password))
        conn.commit()
        conn.close()
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)  # Remove the user from the session
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))  # Redirect to the home page

@app.route('/profile')
def profile():
    if 'user' in session:
        user = session['user']
        return render_template('profile.html', user=user)
    return redirect(url_for('login'))

@app.route('/edit_profile', methods=['GET'])
def edit_profile():
    if 'user' in session:
        user = session['user']
        return render_template('edit_profile.html', user=user)
    return redirect(url_for('login'))

@app.route('/save_profile', methods=['POST'])
def save_profile():
    if 'user' in session:
        user = session['user']
        idno = user['idno']  # ID number should remain unchanged
        
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']

        conn = get_db_connection()
        conn.execute('''
            UPDATE users
            SET firstname = ?, lastname = ?, email = ?
            WHERE idno = ?
        ''', (firstname, lastname, email, idno))
        conn.commit()
        conn.close()

        # Update session data to reflect changes
        session['user']['firstname'] = firstname
        session['user']['lastname'] = lastname
        session['user']['email'] = email

        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))  # Redirect to profile page

    return redirect(url_for('login'))

@app.route('/notifications')
def notifications():
    if 'user' in session:
        user = session['user']
        return render_template('notifications.html', user=user)
    return redirect(url_for('login'))

@app.route('/reservation')
def reservation():
    if 'user' in session:
        user = session['user']
        return render_template('reservation.html', user=user)
    return redirect(url_for('login'))
  #------------------------------------------------------------------------------------------------#

@app.route('/search_student', methods=['POST'])
def search_student():
    if 'user' in session and session['user'].get('is_admin'):
        idno = request.form.get('idno')
        conn = get_db_connection()
        student = conn.execute('SELECT * FROM users WHERE idno = ?', (idno,)).fetchone()
        conn.close()

        if student:
            return {
                "success": True,
                "student": {
                    "idno": student["idno"],
                    "lastname": student["lastname"],
                    "firstname": student["firstname"],
                    "midname": student["midname"],
                    "course": student["course"],
                    "yearlevel": student["yearlevel"],
                    "email": student["email"],
                    "username": student["username"]
                }
            }
        else:
            return {"success": False, "message": "Student not found."}

    return {"success": False, "message": "Unauthorized access."}


if __name__ == '__main__':
    init_db()  # Initialize the database
    create_admin_account()  # Create the admin account
    app.run(debug=True)



  



