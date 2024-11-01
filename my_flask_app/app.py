from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

# Set a secret key for the session
app.secret_key = 'your_secret_key_here'

# Define the upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Change if needed
app.config['MYSQL_DB'] = 'db_lspu_event_reservation'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'  # Path to your database file
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Initialize MySQL
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('signin.html')

import MySQLdb

@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    if request.method == 'POST':
        event_name = request.form['event_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        start_time = request.form['start_time']  # Start time field
        end_time = request.form['end_time']      # End time field
        venue = request.form['venue']
        department = request.form['department']   # Get department from form
        user_email = session.get('user')  # Get user email from session

        # Insert the new reservation into the database
        cur = mysql.connection.cursor()
        cur.execute('''
            INSERT INTO reservations (
                event_name, start_date, end_date, start_time, end_time, venue, department, user_email
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (event_name, start_date, end_date, start_time, end_time, venue, department, user_email))
        mysql.connection.commit()
        cur.close()

        flash('Reservation successful!')
        return redirect(url_for('events'))  # Redirect to the events page

    return render_template('reservation.html')


@app.route('/submit_reservation', methods=['POST'])
def submit_reservation():
    # Logic to handle form submission
    event_name = request.form['event_name']
    department = request.form['department']
    # Handle the rest of the form fields and logic here

    # Example: Redirect to a success page or back to the dashboard
    return redirect(url_for('dashboard'))  # Change 'dashboard' to whatever page you want

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cur = mysql.connection.cursor()
        cur.execute('SELECT username, email, role FROM users WHERE email = %s AND password = %s', (email, password))
        user = cur.fetchone()  # Fetch one result
        cur.close()

        if user is None:
            flash('Invalid credentials, please try again.')
            return redirect(url_for('signin'))

        # Store the username, email, and role in session
        session['username'] = user[0]  # Assuming 'username' is in index 0
        session['user'] = user[1]  # Assuming 'email' is in index 1
        session['role'] = user[2]  # Assuming 'role' is in index 2

        if session['role'].lower() == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif session['role'].lower() == 'student':
            return redirect(url_for('dashboard'))
        else:
            flash('Unknown role! Please contact support.')
            return redirect(url_for('signin'))

    return render_template('signin.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    # Check if the user is logged in and has admin role
    if 'user' not in session or session['role'].lower() != 'admin':
        flash('Access denied!')
        return redirect(url_for('signin'))

    # Create a cursor to interact with the database
    cur = mysql.connection.cursor()

    # Fetch only pending reservations for admin review
    cur.execute('''
        SELECT id, event_name, start_date, end_date, start_time, end_time, venue, user_email 
        FROM reservations 
        WHERE status = 'pending'
    ''')
    reservations = cur.fetchall()

    # Get total users
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    # Get active users using the correct column
    cur.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    active_users = cur.fetchone()[0]

    # Get total events
    cur.execute("SELECT COUNT(*) FROM events")
    total_events = cur.fetchone()[0]

    # Get pending approvals
    cur.execute("SELECT COUNT(*) FROM reservations WHERE status = 'pending'")
    pending_approvals = cur.fetchone()[0]

    # Get approved and denied events count
    cur.execute("SELECT COUNT(*) FROM reservations WHERE status = 'Approved'")
    total_approved = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM reservations WHERE status = 'Denied'")
    total_denied = cur.fetchone()[0]

    # Close the cursor
    cur.close()

    # Render the admin dashboard template with the retrieved data
    return render_template('admin_dashboard.html',
                           total_users=total_users,
                           active_users=active_users,
                           total_events=total_events,
                           pending_approvals=pending_approvals,
                           total_approved=total_approved,
                           total_denied=total_denied,
                           reservations=reservations)

@app.route('/admin_events')
def admin_events():
    if 'user' not in session or session['role'].lower() != 'admin':
        flash('Access denied!')
        return redirect(url_for('signin'))

    # Fetch only pending events for the admin
    cur = mysql.connection.cursor()
    cur.execute('SELECT id, event_name, start_date, end_date, start_time, end_time, venue, user_email FROM reservations WHERE status = "pending"')
    events = cur.fetchall()  # Fetch only pending reservations
    cur.close()

    return render_template('admin_events.html', events=events)

# Route to approve an event
@app.route('/approve_event/<int:event_id>', methods=['POST'])
def approve_event(event_id):
    if 'user' not in session or session['role'].lower() != 'admin':
        flash('Access denied!')
        return redirect(url_for('signin'))

    try:
        # Update event status to Approved
        cur = mysql.connection.cursor()
        cur.execute('UPDATE reservations SET status = "Approved" WHERE id = %s', (event_id,))
        mysql.connection.commit()
        cur.close()

        flash('Event approved!')
    except Exception as e:
        flash(f'Error approving event: {e}')
    finally:
        return redirect(url_for('admin_dashboard'))

# Route to deny an event
@app.route('/deny_event/<int:event_id>', methods=['POST'])
def deny_event(event_id):
    if 'user' not in session or session['role'].lower() != 'admin':
        flash('Access denied!')
        return redirect(url_for('signin'))

    try:
        # Update event status to Denied
        cur = mysql.connection.cursor()
        cur.execute('UPDATE reservations SET status = "Denied" WHERE id = %s', (event_id,))
        mysql.connection.commit()
        cur.close()

        flash('Event denied!')
    except Exception as e:
        flash(f'Error denying event: {e}')
    finally:
        return redirect(url_for('admin_dashboard'))

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    if request.method == 'POST':
        print(request.form)  # Debugging
        event_name = request.form.get('event_name')
        start_date = request.form.get('start_date')  # Ensure this matches the form
        end_date = request.form.get('end_date')      # Ensure this matches the form
        user_email = session.get('user')

        # Check for required fields
        if not event_name or not start_date or not end_date or not user_email:
            flash('All fields are required!', 'error')  # Make sure to import flash
            return redirect(url_for('reservations'))  # Redirect back to the form

        # Here you can add logic to save the reservation to the database
        # e.g., save_reservation(event_name, start_date, end_date, user_email)

        flash('Reservation created successfully!', 'success')  # Feedback message
        return redirect(url_for('some_other_page'))  # Redirect to another page after success

    return render_template('reservations.html')  # GET request returns the reservation form


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']  # New username field
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # Role field
        
        # Check if the user already exists
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = cur.fetchone()
        
        if existing_user:
            flash('Email address already exists.')
            return redirect(url_for('signup'))
        
        # Insert the new user into the database, including the username
        cur.execute('INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)', 
                    (username, email, password, role))
        mysql.connection.commit()  # Commit the changes
        cur.close()  # Close the cursor
        
        flash('Signup successful! Please log in.')
        return redirect(url_for('signin'))  # Redirect to the sign-in page

    return render_template('signup.html')  # Render the signup template


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('signin'))
    return render_template('dashboard.html')

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('signin'))  # Redirect to sign-in if not logged in

    user_email = session['user']
    
    # Fetch user details from the database based on their email
    cur = mysql.connection.cursor()
    cur.execute('SELECT name, email, profile_picture, password FROM users WHERE email = %s', (user_email,))
    user = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        # (Handle form submission, including profile picture upload here...)
        pass
    
    if request.method == 'POST':
        # Get the updated details from the form
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        profile_picture = request.files['profile_picture']

        filename = None
        # If a profile picture is uploaded, handle the upload
        if profile_picture and allowed_file(profile_picture.filename):
            filename = secure_filename(profile_picture.filename)
            profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Update the user details in the database
        cur = mysql.connection.cursor()
        cur.execute('UPDATE users SET name = %s, email = %s, password = %s WHERE email = %s', 
                    (name, email, password, user_email))
        mysql.connection.commit()
        cur.close()

        # Update the session if the email is changed
        session['user'] = email
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user, user_profile_picture=user[2])

from datetime import datetime

# Events Route: Fetches all reservations from the database for display
@app.route('/events')
def events():
    cur = mysql.connection.cursor()
    cur.execute('SELECT id, event_name, start_date, end_date, start_time, end_time, venue , user_email, department, status FROM reservations ')
    events = cur.fetchall()
    cur.close()

    return render_template('events.html', events=events)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')  # Render the calendar page

@app.route('/report')
def report():
    # Your report logic here
    return render_template('report.html')

@app.route('/generate_report')
def generate_report():
    return render_template('generate_report.html')

@app.route('/view_report')
def view_report():
    return render_template('view_report.html')


if __name__ == '__main__':
    app.run(debug=True)
