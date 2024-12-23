from flask import Flask, session, render_template, request, jsonify, flash, redirect, url_for
from flaskext.mysql import MySQL
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask app and MySQL
app = Flask(__name__)
app.secret_key = 'farca2024'
app.config['MYSQL_DATABASE_USER'] = 'root'  # Replace with your MySQL username
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'  # Replace with your MySQL password
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_DB'] = 'FARCA'  # Database name
mysql = MySQL(app)

# Utility functions
def check_logged_in():
    return session.get('logged_in', False)

def get_current_user():
    return session.get('username', None)

# Routes
@app.route('/')
@app.route('/home')
def home():
    """Homepage displaying FARCA services and highlights."""
    conn = mysql.connect()
    cursor = conn.cursor()

    # Fetch menu items and events
    cursor.execute("SELECT * FROM Menu_Items")
    menu_items = cursor.fetchall()

    cursor.execute("SELECT * FROM Events ORDER BY event_date DESC")
    events = cursor.fetchall()

    conn.close()
    return render_template('home.html', menu=menu_items, events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password FROM Users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
        conn.close()
    return render_template('login.html')

@app.route('/menu')
def menu():
    """Page displaying the full menu."""
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Menu_Items")
    menu_items = cursor.fetchall()
    conn.close()
    return render_template('menu.html', menu=menu_items)

@app.route('/order', methods=['GET', 'POST'])
def order():
    """Page for placing food orders."""
    if request.method == 'POST':
        food_item = request.form['food_item']
        quantity = request.form['quantity']
        contact = request.form['contact']

        conn = mysql.connect()
        cursor = conn.cursor()

        try:
            # Insert the order into the database
            cursor.execute(
                "INSERT INTO Orders (food_item, quantity, contact, order_date) VALUES (%s, %s, %s, %s)",
                (food_item, quantity, contact, datetime.datetime.now())
            )
            conn.commit()
            flash('Order placed successfully! The kitchen will contact you shortly.', 'success')
        except Exception as e:
            flash(f"Failed to place order: {str(e)}", 'danger')
        finally:
            conn.close()
        return redirect(url_for('menu'))
    return render_template('order.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """Page for customer feedback and suggestions."""
    if request.method == 'POST':
        name = request.form['name']
        comment = request.form['comment']

        conn = mysql.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Feedback (name, comment, feedback_date) VALUES (%s, %s, %s)",
                (name, comment, datetime.datetime.now())
            )
            conn.commit()
            flash('Feedback submitted successfully. Thank you!', 'success')
        except Exception as e:
            flash(f"Failed to submit feedback: {str(e)}", 'danger')
        finally:
            conn.close()
        return redirect(url_for('home'))
    return render_template('feedback.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Admin page to manage menu items and view feedback."""
    if not check_logged_in():
        flash('Please log in to access the admin panel.', 'danger')
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Menu_Items")
    menu_items = cursor.fetchall()
    
    cursor.execute("SELECT * FROM Feedback ORDER BY feedback_date DESC")
    feedbacks = cursor.fetchall()

    conn.close()
    return render_template('admin.html', menu=menu_items, feedbacks=feedbacks)

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)

# Booking Expense Processing
@app.route('/process_expense', methods=['GET', 'POST'])
def process_expense():
    """Process and record expenses for a booking."""
    data_params = request.get_json()
    booking_id = int(data_params['booking_id'])
    date = datetime.datetime.strptime(data_params['date'], '%Y-%m-%d')

    conn = mysql.connect()
    cursor = conn.cursor()

    if date > datetime.datetime.today():
        flash("Expense date cannot be in the future.", 'danger')
    else:
        try:
            # Insert expense record into the database
            cursor.execute(
                "INSERT INTO expenses (booking_id, expense_date, amount, description) VALUES (%s, %s, %s, %s)",
                (booking_id, date, data_params['amount'], data_params['description'])
            )
            conn.commit()
            flash(f"Expense recorded successfully for booking {booking_id}.", 'success')
        except Exception as e:
            flash(f"Failed to record expense: {str(e)}", 'danger')
        finally:
            conn.close()

    return jsonify(dict(redirect='/booking_details', booking_id=booking_id))

# Booking Details View
@app.route('/booking_details')
def booking_details():
    """View details for a specific booking."""
    booking_id = request.args.get('booking_id')
    if not check_logged_in(session):
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()

    # Fetch booking information
    cursor.execute("SELECT * FROM bookings WHERE booking_id = %s", (booking_id,))
    booking_info = cursor.fetchone()

    # Fetch expenses for the booking
    cursor.execute("SELECT * FROM expenses WHERE booking_id = %s", (booking_id,))
    expenses = cursor.fetchall()

    conn.close()

    if booking_info:
        return render_template(
            'booking_details.html',
            booking_info=booking_info,
            expenses=expenses
        )
    else:
        flash("Booking not found.", 'danger')
        return redirect(url_for('home'))

# Event Reviews
@app.route('/event_reviews/<int:page>')
def event_reviews(page=0):
    """Display reviews for events hosted at FARCA."""
    if not check_logged_in(session):
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()

    # Fetch event reviews
    cursor.execute("SELECT * FROM event_reviews ORDER BY review_date DESC")
    reviews = cursor.fetchall()
    conn.close()

    records_per_page = 20
    total_records = len(reviews)
    min_page = 0
    max_page = (total_records // records_per_page) + (total_records % records_per_page > 0)

    reviews_page = reviews[page * records_per_page: (page + 1) * records_per_page]

    return render_template(
        'event_reviews.html',
        reviews=reviews_page,
        page=page,
        min_page=min_page,
        max_page=max_page
    )

# Update Order Status
@app.route('/update_order_status/<string:order_id>/<string:status>')
def update_order_status(order_id, status):
    """Update the status of an order."""
    if not check_logged_in(session):
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE orders SET status = %s WHERE order_id = %s",
            (status, order_id)
        )
        conn.commit()
        flash(f"Order {order_id} status updated to {status}.", 'success')
    except Exception as e:
        flash(f"Failed to update order status: {str(e)}", 'danger')
    finally:
        conn.close()

    return redirect(url_for('home'))

# Update Room Booking
@app.route('/update_room_booking', methods=['POST'])
def update_room_booking():
    """Update room booking details."""
    data_params = request.get_json()
    room_id = data_params['room_id']

    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE room_bookings SET booking_date = %s, customer_name = %s, contact = %s WHERE room_id = %s",
            (data_params['booking_date'], data_params['customer_name'], data_params['contact'], room_id)
        )
        conn.commit()
        flash(f"Room booking {room_id} updated successfully.", 'success')
    except Exception as e:
        flash(f"Failed to update room booking: {str(e)}", 'danger')
    finally:
        conn.close()

    return jsonify(dict(redirect='/room_details', room_id=room_id))

# Update Event Details
@app.route('/update_event', methods=['POST'])
def update_event():
    """Update event information."""
    data_params = request.get_json()
    event_id = data_params['event_id']

    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE events SET event_name = %s, event_date = %s, description = %s WHERE event_id = %s",
            (data_params['event_name'], data_params['event_date'], data_params['description'], event_id)
        )
        conn.commit()
        flash(f"Event {event_id} updated successfully.", 'success')
    except Exception as e:
        flash(f"Failed to update event: {str(e)}", 'danger')
    finally:
        conn.close()

    return jsonify(dict(redirect='/event_reviews', page=0))

@app.route('/update_customer_feedback')
def update_customer_feedback():
    """Update the status or details of customer feedback for FARCA's services"""
    print('In update_customer_feedback')
    feedback_id = request.args.get('feedback_id')
    print(f"Updating feedback info for feedback {feedback_id}")
    return render_template('update_feedback.html', feedback_id=feedback_id)


@app.route('/go2UpdateCustomerFeedback', methods=['GET', 'POST'])
def go2UpdateCustomerFeedback():
    """Handle updating feedback details for FARCA's feedback database"""
    print('In go2UpdateCustomerFeedback')
    data_params = request.get_json()
    print(data_params)
    conn = mysql.connect()
    cursor = conn.cursor()
    feedback_id = int(data_params['feedback_id'].replace('update_feedback?feedback_id=', ''))

    try:
        # Update feedback details in the database
        cursor.execute("""
            UPDATE feedback
            SET feedback_text = %s, status = %s, updated_at = NOW()
            WHERE feedback_id = %s
        """, (data_params['feedback_text'], data_params['status'], feedback_id))
        conn.commit()
        print(cursor.rowcount, "Feedback updated successfully in the database")
        conn.close()
        flash(f"Success! Feedback ID {feedback_id} updated.")
    except Exception as e:
        flash(f"Failed to update feedback info due to: {str(e)}")

    return jsonify(dict(redirect='/customer_feedback', feedback_id=feedback_id))


@app.route('/book_room/<int:room_id>', methods=['GET', 'POST'])
def book_room(room_id):
    """Manage room bookings for FARCA"""
    if not check_loggin(session):
        return redirect(url_for('login'))

    if request.method == 'POST':
        booking_details = request.form
        customer_name = booking_details['name']
        customer_contact = booking_details['contact']
        booking_date = booking_details['date']
        booking_time = booking_details['time']
        
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bookings (room_id, customer_name, customer_contact, booking_date, booking_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (room_id, customer_name, customer_contact, booking_date, booking_time))
        conn.commit()
        conn.close()

        flash(f"Room {room_id} booked successfully!")
        return redirect(url_for('index'))

    return render_template('book_room.html', room_id=room_id)


@app.route('/order_food', methods=['GET', 'POST'])
def order_food():
    """Manage food orders for FARCA"""
    if not check_loggin(session):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        order_details = request.form
        food_item_id = order_details['food_item_id']
        quantity = order_details['quantity']
        customer_name = session.get('user')
        
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (food_item_id, quantity, customer_name, order_date)
            VALUES (%s, %s, %s, NOW())
        """, (food_item_id, quantity, customer_name))
        conn.commit()
        conn.close()

        flash("Order placed successfully!")
        return redirect(url_for('index'))
    
    # Fetch available menu items for ordering
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu WHERE active=1")
    menu_items = cursor.fetchall()
    conn.close()

    return render_template('order_food.html', menu_items=menu_items)


@app.route('/event_details/<int:event_id>')
def event_details(event_id):
    """Display details of a specific FARCA event"""
    if not check_loggin(session):
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE event_id=%s", (event_id,))
    event = cursor.fetchone()
    conn.close()

    return render_template('event_details.html', event=event)


@app.route('/feedback', methods=['POST'])
def feedback():
    """Submit customer feedback for FARCA services"""
    if not check_loggin(session):
        return redirect(url_for('login'))

    feedback_data = request.form['feedback']
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (user_id, feedback_text, created_at)
        VALUES (%s, %s, NOW())
    """, (session.get('user_id'), feedback_data))
    conn.commit()
    conn.close()

    flash("Thank you for your feedback!")
    return redirect(url_for('index'))


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Handle customer contact messages for FARCA"""
    if request.method == 'POST':
        contact_details = request.form
        customer_name = contact_details['name']
        customer_email = contact_details['email']
        message = contact_details['message']
        
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contact_messages (name, email, message, submitted_at)
            VALUES (%s, %s, %s, NOW())
        """, (customer_name, customer_email, message))
        conn.commit()
        conn.close()

        flash("Your message has been sent successfully!")
        return redirect(url_for('contact'))
    
    return render_template('contact.html')
