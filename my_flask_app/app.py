from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL

app = Flask(__name__)

# Set a secret key for the session
app.secret_key = 'your_secret_key_here'

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Change if needed
app.config['MYSQL_DB'] = 'db_lspu_event_reservation'

# Initialize MySQL
mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('signin.html')

@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    if request.method == 'POST':
        # Get data from the form
        event_name = request.form['event_name']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        user_email = session.get('user')  # Get user email from session

        # Insert reservation into the database
        cur = mysql.connection.cursor()
        cur.execute('INSERT INTO reservations (event_name, start_date, end_date, user_email) VALUES (%s, %s, %s, %s)', 
                    (event_name, start_date, end_date, user_email))
        mysql.connection.commit()  # Commit the changes
        cur.close()  # Close the cursor

        flash('Reservation successful!')
        return redirect(url_for('dashboard'))  # Redirect to the dashboard

    return render_template('reservation.html')  # Render the reservation form


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Use MySQLdb to connect and execute the query
        cur = mysql.connection.cursor()  # Create a cursor object
        cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))  # Use %s for placeholders
        user = cur.fetchone()  # Fetch one result
        cur.close()  # Close the cursor

        # Check if user exists
        if user:
            session['user'] = user[1]  # Assuming email is the second field in your user table
            return redirect(url_for('dashboard'))  # Redirect to dashboard
        else:
            flash('Invalid credentials, please try again.')  # Flash message for invalid login
            return redirect(url_for('signin'))  # Redirect back to sign-in page

    return render_template('signin.html')

@app.route('/reservations')
def reservations():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT event_name, start_date, end_date, user_email FROM reservations')
    reservations = cursor.fetchall()
    cursor.close()

    # Prepare the data for JSON response
    events = []
    for reservation in reservations:
        events.append({
            'title': reservation[0],
            'start': reservation[1],
            'end': reservation[2],
            'user_email': reservation[3]
        })

    return jsonify(events)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if the user already exists
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        existing_user = cur.fetchone()
        
        if existing_user:
            flash('Email address already exists.')
            return redirect(url_for('signup'))
        
        # Insert the new user into the database
        cur.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (email, password))
        mysql.connection.commit()  # Commit the changes
        cur.close()  # Close the cursor
        
        flash('Signup successful! Please log in.')
        return redirect(url_for('signin'))  # Redirect to the sign-in page

    return render_template('signup.html')  # Render the signup template


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('signin'))  # Redirect to sign-in if not logged in
    
    return render_template('dashboard.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('signin'))  # Redirect to sign-in if not logged in

    user_email = session['user']
    
    # Fetch user details from the database based on their email
    cur = mysql.connection.cursor()
    cur.execute('SELECT name, email, password FROM users WHERE email = %s', (user_email,))
    user = cur.fetchone()
    cur.close()
    
    if request.method == 'POST':
        # Get the updated details from the form
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

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

    return render_template('profile.html', user=user)

@app.route('/events')
def events():
    return render_template('events.html')  # Render the events page

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')  # Render the calendar page


if __name__ == '__main__':
    app.run(debug=True)
