from flask import Flask, session, render_template, request, jsonify, flash, redirect, url_for
from flaskext.mysql import MySQL
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from utils import send_email_notification, send_sms_notification, calculate_delivery_cost

# Initialize Flask app and MySQL
app = Flask(__name__)
app.secret_key = 'farca2024'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'k@#+ymej@AQ@3'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_DB'] = 'FARCA'
mysql = MySQL(app)

@app.route('/')
def home():
    try:
        # Connect to the database
        conn = mysql.connect()
        cursor = conn.cursor()
        
        # Replace 'your_table_name' with your actual table name
        cursor.execute('SELECT * FROM your_table_name')
        data = cursor.fetchall()
        
        # Return the result as a string (for testing purposes)
        return str(data)
    except Exception as e:
        # If there's an error, return the error message
        return f"Error: {str(e)}"

# Utility Functions
def check_logged_in():
    return session.get('logged_in', False)

def get_current_user():
    return session.get('username', None)

def is_admin():
    return session.get('role') == 'admin'

# Routes
@app.route('/')
@app.route('/home')
def home():
    """Homepage displaying FARCA services and highlights."""
    conn = mysql.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Menu_Items")
    menu_items = cursor.fetchall()

    cursor.execute("SELECT * FROM Events ORDER BY event_date DESC")
    events = cursor.fetchall()

    conn.close()
    return render_template('home.html', menu=menu_items, events=events)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # "customer" or "admin"

        hashed_password = generate_password_hash(password)
        conn = mysql.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO Users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password, role)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, role FROM Users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session['logged_in'] = True
            session['username'] = user[0]
            session['role'] = user[2]
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
        location = request.form['location']

        delivery_cost = calculate_delivery_cost(location)

        conn = mysql.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO Orders (food_item, quantity, contact, location, delivery_cost, order_date)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (food_item, quantity, contact, location, delivery_cost, datetime.datetime.now())
            )
            conn.commit()
            order_id = cursor.lastrowid

            send_sms_notification(contact, f"Your order #{order_id} has been placed successfully!")
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
        rating = request.form['rating']  # New field for rating

        conn = mysql.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO Feedback (name, comment, rating, feedback_date) VALUES (%s, %s, %s, %s)",
                (name, comment, rating, datetime.datetime.now())
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
    if not check_logged_in() or not is_admin():
        flash('Unauthorized access. Admins only.', 'danger')
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

# Fetch expenses for the booking
@app.route('/booking_details')
def booking_details():
    """View details for a specific booking."""
    booking_id = request.args.get('booking_id')
    if not check_logged_in():
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
    if not check_logged_in():
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
    if not check_logged_in():
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

# Update Customer Feedback
@app.route('/update_customer_feedback')
def update_customer_feedback():
    """Update the status or details of customer feedback for FARCA's services."""
    feedback_id = request.args.get('feedback_id')
    return render_template('update_feedback.html', feedback_id=feedback_id)

@app.route('/go2UpdateCustomerFeedback', methods=['GET', 'POST'])
def go2UpdateCustomerFeedback():
    """Handle updating feedback details for FARCA's feedback database."""
    data_params = request.get_json()
    conn = mysql.connect()
    cursor = conn.cursor()
    feedback_id = int(data_params['feedback_id'])

    try:
        cursor.execute("""
            UPDATE feedback
            SET feedback_text = %s, status = %s, updated_at = NOW()
            WHERE feedback_id = %s
        """, (data_params['feedback_text'], data_params['status'], feedback_id))
        conn.commit()
        flash(f"Success! Feedback ID {feedback_id} updated.")
    except Exception as e:
        flash(f"Failed to update feedback info due to: {str(e)}")
    finally:
        conn.close()

    return jsonify(dict(redirect='/customer_feedback', feedback_id=feedback_id))

# Book Room
@app.route('/book_room/<int:room_id>', methods=['GET', 'POST'])
def book_room(room_id):
    """Manage room bookings for FARCA."""
    if not check_logged_in():
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
        return redirect(url_for('home'))

    return render_template('book_room.html', room_id=room_id)

# Order Food
@app.route('/order_food', methods=['GET', 'POST'])
def order_food():
    """Manage food orders for FARCA."""
    if not check_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        order_details = request.form
        food_item_id = order_details['food_item_id']
        quantity = order_details['quantity']
        customer_name = session.get('username')

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (food_item_id, quantity, customer_name, order_date)
            VALUES (%s, %s, %s, NOW())
        """, (food_item_id, quantity, customer_name))
        conn.commit()
        conn.close()

        flash("Food order placed successfully.", 'success')
        return redirect(url_for('menu'))

    return render_template('order_food.html')

@app.route('/order_food', methods=['GET', 'POST'])
def order_food():
    """Manage food orders for FARCA."""
    if not check_logged_in():
        flash("Please log in to place an order.", "danger")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            order_details = request.form
            food_item_id = order_details['food_item_id']
            quantity = int(order_details['quantity'])
            customer_name = session.get('username')

            if not customer_name:
                flash("You must be logged in to place an order.", "danger")
                return redirect(url_for('login'))

            conn = mysql.connect()
            cursor = conn.cursor()

            # Insert the order into the database
            cursor.execute("""
                INSERT INTO orders (food_item_id, quantity, customer_name, order_date)
                VALUES (%s, %s, %s, NOW())
            """, (food_item_id, quantity, customer_name))
            conn.commit()

            flash("Order placed successfully!", "success")
        except Exception as e:
            flash(f"Failed to place order: {str(e)}", "danger")
        finally:
            conn.close()

        return redirect(url_for('menu'))
    
    # Fetch active menu items for ordering
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu WHERE active=1")
    menu_items = cursor.fetchall()
    conn.close()

    return render_template('order_food.html', menu_items=menu_items)


@app.route('/event_details/<int:event_id>')
def event_details(event_id):
    """Display details of a specific FARCA event."""
    if not check_logged_in():
        flash("Please log in to view event details.", "danger")
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM events WHERE event_id=%s", (event_id,))
        event = cursor.fetchone()
        if not event:
            flash("Event not found.", "danger")
            return redirect(url_for('home'))
    except Exception as e:
        flash(f"Failed to fetch event details: {str(e)}", "danger")
    finally:
        conn.close()

    return render_template('event_details.html', event=event)


@app.route('/feedback', methods=['POST'])
def feedback():
    """Submit customer feedback for FARCA services."""
    if not check_logged_in():
        flash("Please log in to submit feedback.", "danger")
        return redirect(url_for('login'))

    feedback_text = request.form['feedback']
    user_id = session.get('user_id')

    if not user_id:
        flash("Invalid user session. Please log in again.", "danger")
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO feedback (user_id, feedback_text, created_at)
            VALUES (%s, %s, NOW())
        """, (user_id, feedback_text))
        conn.commit()
        flash("Thank you for your feedback!", "success")
    except Exception as e:
        flash(f"Failed to submit feedback: {str(e)}", "danger")
    finally:
        conn.close()

    return redirect(url_for('home'))


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Handle customer contact messages for FARCA."""
    if request.method == 'POST':
        contact_details = request.form
        customer_name = contact_details['name']
        customer_email = contact_details['email']
        message = contact_details['message']

        conn = mysql.connect()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO contact_messages (name, email, message, submitted_at)
                VALUES (%s, %s, %s, NOW())
            """, (customer_name, customer_email, message))
            conn.commit()
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            flash(f"Failed to send message: {str(e)}", "danger")
        finally:
            conn.close()

        return redirect(url_for('contact'))

    return render_template('contact.html')
