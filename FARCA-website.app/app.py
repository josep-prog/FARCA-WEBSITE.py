from flask import Flask, Response, session, render_template, request, jsonify, flash, redirect, url_for
from flaskext.mysql import MySQL
import datetime

# Initialize Flask app and MySQL
app = Flask(__name__)
app.secret_key = 'farca2024'
app.config['MYSQL_DATABASE_USER'] = 'USER'
app.config['MYSQL_DATABASE_PASSWORD'] = 'PASSWORD'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_DB'] = 'farca_db'
mysql = MySQL(app)

# Utility functions
def check_logged_in(session):
    return session.get('logged_in', False)

def get_current_user(session):
    return session.get('username', None)

# Routes
@app.route('/')
@app.route('/home')
def home():
    """Homepage displaying FARCA services and highlights."""
    conn = mysql.connect()
    cursor = conn.cursor()
    
    # Fetch menu items, events, and highlights
    cursor.execute("SELECT * FROM menu")
    menu_items = cursor.fetchall()
    
    cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
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
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user and user[0] == password:
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
    cursor.execute("SELECT * FROM menu")
    menu_items = cursor.fetchall()
    conn.close()
    return render_template('menu.html', menu=menu_items)

@app.route('/order', methods=['GET', 'POST'])
def order():
    """Page for placing food orders."""
    if request.method == 'POST':
        data = request.form
        food_item = data['food_item']
        quantity = data['quantity']
        contact = data['contact']
        
        conn = mysql.connect()
        cursor = conn.cursor()
        
        try:
            # Insert the order into the database
            cursor.execute(
                "INSERT INTO orders (food_item, quantity, contact, order_date) VALUES (%s, %s, %s, %s)",
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
        data = request.form
        name = data['name']
        comment = data['comment']
        
        conn = mysql.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO feedback (name, comment, feedback_date) VALUES (%s, %s, %s)",
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

# FARCA Website Contextual Adaptation

def process_booking_request(data_params):
    # Collect input details for the booking
    input_booking = {
        'customer_name': data_params['customer_name'],
        'customer_contact': data_params['customer_contact'],
        'booking_date': data_params['booking_date'],
        'booking_time': data_params['booking_time'],
        'table_number': data_params['table_number'],
        'special_request': data_params['special_request'],
    }

    # Ensure unique booking identifier
    booking_exists = check_unique_booking(cursor, data_params['customer_contact'], data_params['booking_date'], data_params['booking_time'])

    # Business rules for table booking validation
    if not is_valid_table(data_params['table_number']):
        flash(f"Fail! Table {data_params['table_number']} does not exist.")
    elif booking_exists:
        flash(f"Fail! A booking for this contact already exists for the selected date and time.")
    else:
        # Insert booking into the database
        try:
            conn = mysql.connect()
            cursor = conn.cursor()
            insert_booking(cursor, conn, input_booking)
            conn.commit()
            print(cursor.rowcount, "Record inserted successfully into booking table")
            conn.close()
            flash(f"Success! Booking confirmed for {input_booking['customer_name']}.")
        except Exception as e:
            flash(f"Fail! Problem adding booking: {str(e)}")

    # Redirect to dashboard
    return jsonify(dict(redirect='dashboard'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    print('in logout')
    print(session)
    session.pop('logged_in', None)
    session.pop('admin', None)
    session.pop('username', None)
    print(session)
    return redirect(url_for('login'))

@app.route('/add_booking')
def add_booking():
    print('in add_booking')
    if not check_logged_in(session):
        print('redirect to login')
        return redirect(url_for('login'))
    return render_template('add_booking.html')

@app.route('/report_generator')
def report_generator():
    print('in report_generator')
    if not check_logged_in(session):
        print('redirect to login')
        return redirect(url_for('login'))
    return render_template('report_generator.html')

@app.route('/add_expense')
def add_expense():
    print('in add_expense')
    booking_id = request.args.get('booking_id')
    print(f"adding expense for booking {booking_id}")
    return render_template('add_expense.html', booking_id=booking_id)

@app.route('/process_expense', methods=['GET', 'POST'])
def process_expense():
    print('in process_expense')
    data_params = request.get_json()
    print(data_params)
    booking_id = int(data_params['booking_id'])
    date = datetime.datetime.strptime(data_params['date'], '%Y-%m-%d')
    print(date)

    conn = mysql.connect()
    cursor = conn.cursor()

    if date > datetime.datetime.today():
        flash("Fail! Expense date cannot be in the future.")
    else:
        try:
            add_expense_record(cursor, data_params, booking_id)
            conn.commit()
            print(cursor.rowcount, "Expense added successfully.")
            conn.close()
            flash(f"Success! Expense recorded for booking {booking_id}.")
        except Exception as e:
            flash(f"Fail! Error recording expense: {str(e)}")

    return jsonify(dict(redirect='/booking_details', booking_id=booking_id))

@app.route('/booking_details')
def booking_details():
    print('in booking_details')
    booking_id = request.args.get('booking_id')
    print(f"Viewing details for booking {booking_id}")
    if not check_logged_in(session):
        print('redirect to login')
        return redirect(url_for('login'))
    return redirect(url_for('view_booking_details', booking_id=booking_id))

@app.route('/view_booking_details', methods=['GET', 'POST'])
def view_booking_details():
    print('in view_booking_details')
    if not check_logged_in(session):
        print('redirect to login')
        return redirect(url_for('login'))

    booking_id = request.args.get('booking_id')
    print(f"Displaying details for booking {booking_id}")

    conn = mysql.connect()
    cursor = conn.cursor()

    booking_info = get_booking_details(cursor, booking_id)
    print(booking_info)

    customer_name = booking_info[0]
    booking_date = booking_info[1].strftime('%Y-%m-%d')
    booking_time = booking_info[2]
    table_number = booking_info[3]
    special_request = booking_info[4]

    total_expenses = calculate_booking_expenses(cursor, booking_id)
    print(f"Total expenses for booking {booking_id}: {total_expenses}")

    booking_details = [
        customer_name, booking_date, booking_time, table_number, special_request, total_expenses
    ]

    expense_records = get_booking_expenses(cursor, booking_id)

    return render_template('booking_details.html', 
                           booking_details=booking_details, 
                           expense_records=expense_records)

# Adjustments to meet FARCA's needs (located in City-West, Rwanda)
# FARCA website needs booking functionalities, customer order management, and event details

@app.route('/dog_expenses/<int:dog_id>')
def dog_expenses(dog_id):
    """Display the dog expense details, and adapt them to FARCA's context"""
    print(f"Fetching dog expenses for dog ID: {dog_id}")
    
    # Get expenses (relevant to FARCA services)
    dog_expense = get_dog_expenses(dog_id)
    dog_expense_num = len(dog_expense)
    print(f"There are {dog_expense_num} transactions associated with dog {dog_id}")

    # Adjust format for dog_expenses (i.e., restaurant services, food, room bookings)
    dog_expense_list = []
    for i in range(dog_expense_num):
        result = []
        for j in range(5):  # Adjust based on FARCA service data (food orders, bookings, etc.)
            if j == 1:
                result.append(dog_expense[i][j].strftime('%Y-%m-%d'))
            else:
                result.append(dog_expense[i][j])
        dog_expense_list.append(result)

    # Check for admin (relevant for FARCA's admin dashboard)
    admin = check_admin(session)

    # For FARCA, check booking or ordering eligibility (example: room bookings or meal orders)
    if is_eligible_for_booking(dog_id):  # You can define this function as per FARCA's needs
        booking_eligible_flag = 1
    else:
        booking_eligible_flag = 0

    return render_template('dog_expenses.html', dog_id=dog_id, dog_expenses=dog_expense_list, 
                           dog_expense_num=dog_expense_num, admin_flag=int(admin), booking_eligible_flag=booking_eligible_flag)


@app.route('/event_reviews/<int:page>')
def event_reviews(page=0):
    """Reviews and details of events hosted at FARCA (restaurant)"""
    print('Fetching event reviews')
    if not check_loggin(session):
        print('Redirecting to login')
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()
    event_reviews_data = get_event_reviews(cursor)  # FARCA events data
    event_titles = get_event_review_column_names()
    conn.close()

    records_per_page, total_records = 20, len(event_reviews_data)
    min_page = 0
    max_page = int(total_records / records_per_page) + (total_records % records_per_page > 0)

    data = event_reviews_data[page * records_per_page: (page + 1) * records_per_page]
    return render_template('event_reviews.html', data=data, titles=event_titles, page=page, 
                           minpage=min_page, maxpage=max_page)


@app.route('/update_order_status/<string:order_id>/<string:status>')
def update_order_status(order_id, status):
    """Update the status of a customer's food or room booking order at FARCA"""
    print(f'Updating order status for order ID: {order_id}')
    if not check_loggin(session):
        print('Redirecting to login')
        return redirect(url_for('login'))

    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        # Update order status based on customer requests
        if status == "approved":
            flash(f"Success! The order for {order_id} has been approved.")
        else:
            flash(f"Success! The order for {order_id} has been rejected.")
    except Exception as e:
        flash(f"Failed to update the order status due to: {str(e)}")
    conn.close()
    return redirect(url_for('event_reviews', page=0))


@app.route('/update_room_booking')
def update_room_booking():
    """From dog_details, update room booking information (e.g., booking for FARCA)"""
    print('In update_room_booking')
    room_id = request.args.get('room_id')
    print(f"Updating room booking info for room {room_id}")
    return render_template('update_room_booking.html', room_id=room_id)


@app.route('/go2UpdateRoomBooking', methods=['GET', 'POST'])
def go2UpdateRoomBooking():
    print('In go2UpdateRoomBooking')
    data_params = request.get_json()
    print(data_params)
    conn = mysql.connect()
    cursor = conn.cursor()
    room_id = int(data_params['room_id'].replace('update_room_booking?room_id=', ''))

    try:
        update_room_booking_info(cursor, data_params, room_id)
        conn.commit()
        print(cursor.rowcount, "Record updated successfully in the database")
        conn.close()
        flash(f"Success! Room booking info updated.")
    except Exception as e:
        flash(f"Failed to update room booking info due to: {str(e)}")

    return jsonify(dict(redirect='/room_details', room_id=room_id))


@app.route('/update_event')
def update_event():
    """From dog_details, update event information (e.g., FARCA's hosted events)"""
    print('In update_event')
    event_id = request.args.get('event_id')
    print(f"Updating event info for event {event_id}")
    return render_template('update_event.html', event_id=event_id)


@app.route('/go2UpdateEvent', methods=['GET', 'POST'])
def go2UpdateEvent():
    print('In go2UpdateEvent')
    data_params = request.get_json()
    print(data_params)
    event_id = data_params['event_id'].replace('update_event?event_id=', '')
    conn = mysql.connect()
    cursor = conn.cursor()

    try:
        update_event_info(cursor, data_params, event_id)
        conn.commit()
        print(cursor.rowcount, "Event info updated successfully in the database")
        conn.close()
        flash(f"Success! Event info updated.")
    except Exception as e:
        flash(f"Failed to update event info due to: {str(e)}")

    return jsonify(dict(redirect='/event_details', event_id=event_id))


@app.route('/update_customer_feedback')
def update_customer_feedback():
    """From customer feedback, update the status of feedback for FARCA"""
    print('In update_customer_feedback')
    feedback_id = request.args.get('feedback_id')
    print(f"Updating feedback info for feedback {feedback_id}")
    return render_template('update_feedback.html', feedback_id=feedback_id)


@app.route('/go2UpdateCustomerFeedback', methods=['GET', 'POST'])
def go2UpdateCustomerFeedback():
    print('In go2UpdateCustomerFeedback')
    data_params = request.get_json()
    print(data_params)
    conn = mysql.connect()
    cursor = conn.cursor()
    feedback_id = int(data_params['feedback_id'].replace('update_feedback?feedback_id=', ''))

    try:
        update_customer_feedback(cursor, data_params, feedback_id)
        conn.commit()
        print(cursor.rowcount, "Feedback updated successfully in the database")
        conn.close()
        flash(f"Success! Feedback info updated.")
    except Exception as e:
        flash(f"Failed to update feedback info due to: {str(e)}")

    return jsonify(dict(redirect='/customer_feedback', feedback_id=feedback_id))

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import datetime
import mysql.connector as mysql

app = Flask(__name__)

# Check login and admin status functions
def check_loggin(session):
    # Implement session check for user login
    return 'user' in session

def check_admin(session):
    # Implement session check for admin status
    return session.get('role') == 'admin'


@app.route('/index')
def index():
    if not check_loggin(session):
        return redirect(url_for('login'))
    
    # Connect to the database
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM services WHERE active=1")
    services = cursor.fetchall()
    cursor.execute("SELECT * FROM events WHERE active=1")
    events = cursor.fetchall()
    conn.close()

    return render_template('index.html', services=services, events=events)


@app.route('/book_room/<int:room_id>', methods=['GET', 'POST'])
def book_room(room_id):
    if not check_loggin(session):
        return redirect(url_for('login'))

    if request.method == 'POST':
        booking_details = request.form
        customer_name = booking_details['name']
        customer_contact = booking_details['contact']
        booking_date = booking_details['date']
        
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO bookings (room_id, customer_name, customer_contact, booking_date)
            VALUES (%s, %s, %s, %s)
        """, (room_id, customer_name, customer_contact, booking_date))
        conn.commit()
        conn.close()

        flash(f"Room {room_id} booked successfully!")
        return redirect(url_for('index'))

    return render_template('book_room.html', room_id=room_id)


@app.route('/order_food', methods=['GET', 'POST'])
def order_food():
    if not check_loggin(session):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        order_details = request.form
        food_item = order_details['food_item']
        quantity = order_details['quantity']
        
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (food_item, quantity, customer_name)
            VALUES (%s, %s, %s)
        """, (food_item, quantity, session.get('user')))
        conn.commit()
        conn.close()

        flash("Order placed successfully!")
        return redirect(url_for('index'))
    
    return render_template('order_food.html')


@app.route('/event_details/<int:event_id>')
def event_details(event_id):
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
    if not check_loggin(session):
        return redirect(url_for('login'))

    feedback_data = request.form['feedback']
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (user_id, feedback_text)
        VALUES (%s, %s)
    """, (session.get('user_id'), feedback_data))
    conn.commit()
    conn.close()

    flash("Thank you for your feedback!")
    return redirect(url_for('index'))


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        contact_details = request.form
        customer_name = contact_details['name']
        customer_email = contact_details['email']
        message = contact_details['message']
        
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contact_messages (name, email, message)
            VALUES (%s, %s, %s)
        """, (customer_name, customer_email, message))
        conn.commit()
        conn.close()

        flash("Your message has been sent successfully!")
        return redirect(url_for('contact'))
    
    return render_template('contact.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if not check_loggin(session):
        return redirect(url_for('login'))

    if not check_admin(session):
        return redirect(url_for('index'))

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings")
    bookings = cursor.fetchall()
    cursor.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    cursor.execute("SELECT * FROM feedback")
    feedback = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', bookings=bookings, orders=orders, feedback=feedback)


if __name__ == '__main__':
    app.run(host='localhost', port=8888, debug=True)
