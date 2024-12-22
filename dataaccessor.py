# Modified to match FARCA's food ordering system and customer feedback

def getFoodMenu(cursor):
    """Fetch food menu items and prices from the database"""
    query = "SELECT name, price, description FROM FoodMenu ORDER BY name;"
    cursor.execute(query)
    menu_items = cursor.fetchall()
    return menu_items

def getOrderDetails(cursor, order_id):
    """Fetch details for a specific food order"""
    query = f"SELECT order_id, food_item, quantity, customer_name, customer_phone, status FROM Orders WHERE order_id = {order_id};"
    cursor.execute(query)
    order_details = cursor.fetchall()
    return order_details

def placeFoodOrder(cursor, conn, order_data):
    """Place a food order into the database"""
    food_item = order_data['food_item']
    quantity = order_data['quantity']
    customer_name = order_data['customer_name']
    customer_phone = order_data['customer_phone']
    
    query = """INSERT INTO Orders (food_item, quantity, customer_name, customer_phone, status)
               VALUES (%s, %s, %s, %s, 'Pending');"""
    cursor.execute(query, (food_item, quantity, customer_name, customer_phone))
    conn.commit()
    
    return cursor.lastrowid  # Return the order ID

def updateOrderStatus(cursor, conn, order_id, status):
    """Update the status of a food order (e.g., Pending, In Progress, Completed)"""
    query = """UPDATE Orders SET status = %s WHERE order_id = %s;"""
    cursor.execute(query, (status, order_id))
    conn.commit()

def getFeedback(cursor):
    """Fetch all customer feedback from the discussion board"""
    query = "SELECT name, feedback, date_submitted FROM Feedback ORDER BY date_submitted DESC;"
    cursor.execute(query)
    feedback = cursor.fetchall()
    return feedback

def submitFeedback(cursor, conn, feedback_data):
    """Submit customer feedback to the database"""
    customer_name = feedback_data['customer_name']
    feedback = feedback_data['feedback']
    
    query = """INSERT INTO Feedback (name, feedback, date_submitted) 
               VALUES (%s, %s, NOW());"""
    cursor.execute(query, (customer_name, feedback))
    conn.commit()

def bookRoom(cursor, conn, booking_data):
    """Insert a room booking into the database"""
    room_type = booking_data['room_type']
    customer_name = booking_data['customer_name']
    customer_phone = booking_data['customer_phone']
    check_in_date = booking_data['check_in_date']
    check_out_date = booking_data['check_out_date']
    
    query = """INSERT INTO RoomBookings (room_type, customer_name, customer_phone, check_in_date, check_out_date)
               VALUES (%s, %s, %s, %s, %s);"""
    cursor.execute(query, (room_type, customer_name, customer_phone, check_in_date, check_out_date))
    conn.commit()

def getAvailableRooms(cursor):
    """Fetch available rooms for booking"""
    query = "SELECT room_type, price FROM Rooms WHERE available = 1 ORDER BY room_type;"
    cursor.execute(query)
    available_rooms = cursor.fetchall()
    return available_rooms
def updateMenuItem(cursor, data_params, item_id):
    """Update a menu item in FARCA's menu"""
    updated_name = data_params['updated_name']
    updated_description = data_params['updated_description']
    updated_price = data_params['updated_price']
    query = f"UPDATE Menu SET name = '{updated_name}', description = '{updated_description}', price = {updated_price} WHERE itemID = {item_id};"
    cursor.execute(query)


def updateRoomAvailability(cursor, data_params, room_id):
    """Update the availability of a room in FARCA's booking system"""
    updated_availability = data_params['updated_availability']
    query = f"UPDATE Rooms SET availability = {updated_availability} WHERE roomID = {room_id};"
    cursor.execute(query)


def reservationSearch(cursor, search):
    """Search for reservations based on customer information"""
    lower_search = search.lower()
    query = f"SELECT reservation_num, customer_name, reservation_date, num_people, contact_phone FROM Reservations " \
            f"WHERE LOWER(customer_name) LIKE '%{lower_search}%' OR LOWER(contact_phone) LIKE '%{lower_search}%';"
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def reservationDetails(cursor, reservation_id):
    """Get the details of a specific reservation by reservation number"""
    query = f"SELECT reservation_num, customer_name, reservation_date, num_people, contact_phone, special_requests " \
            f"FROM Reservations WHERE reservation_num = {reservation_id};"
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def calculateTotalOrderAmount(cursor, order_id):
    """Calculate the total amount for a specific order"""
    query = f"SELECT SUM(Menu.price) FROM Orders " \
            f"JOIN OrderItems ON Orders.order_id = OrderItems.order_id " \
            f"JOIN Menu ON OrderItems.item_id = Menu.itemID " \
            f"WHERE Orders.order_id = {order_id};"
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def submitOrderToDb(cursor, order_data, customer_id):
    """Record a new order for FARCA's kitchen"""
    order_date = order_data['order_date']
    order_items = order_data['order_items']  # A list of item IDs and quantities
    total_amount = order_data['total_amount']
    query = f"INSERT INTO Orders (customer_id, order_date, total_amount) VALUES ({customer_id}, '{order_date}', {total_amount});"
    cursor.execute(query)
    order_id = cursor.lastrowid  # Get the last inserted order ID
    
    # Insert the items ordered into the OrderItems table
    for item in order_items:
        item_id = item['item_id']
        quantity = item['quantity']
        query = f"INSERT INTO OrderItems (order_id, item_id, quantity) VALUES ({order_id}, {item_id}, {quantity});"
        cursor.execute(query)
    return order_id


def checkRoomBookingDate(cursor, room_id):
    """Check the booking date for a specific room"""
    query = f"SELECT booking_date FROM Rooms WHERE roomID = {room_id};"
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result[0][0]


def getMonthlyReservationsReport(cursor):
    """Generate a monthly report on FARCA's reservations"""
    query = """
    SELECT YEAR(reservation_date) as year, MONTH(reservation_date) as month, COUNT(*) as num_reservations
    FROM Reservations
    WHERE reservation_date BETWEEN DATE_SUB(CURDATE(), INTERVAL 6 MONTH) AND CURDATE()
    GROUP BY YEAR(reservation_date), MONTH(reservation_date)
    ORDER BY year DESC, month DESC;
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def getCustomerOrderHistory(cursor, customer_id):
    """Get the order history of a specific customer"""
    query = """
    SELECT Orders.order_id, Orders.order_date, SUM(Menu.price * OrderItems.quantity) AS total_amount
    FROM Orders
    JOIN OrderItems ON Orders.order_id = OrderItems.order_id
    JOIN Menu ON OrderItems.item_id = Menu.itemID
    WHERE Orders.customer_id = {customer_id}
    GROUP BY Orders.order_id;
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def submitRoomBookingToDb(cursor, room_id, customer_id, booking_date):
    """Record a new room booking for FARCA"""
    query = f"INSERT INTO RoomBookings (room_id, customer_id, booking_date) VALUES ({room_id}, {customer_id}, '{booking_date}');"
    cursor.execute(query)

def getBookingReport(cursor, year, month):
    """Get the monthly booking report for FARCA"""
    query = """
    SELECT 
        YEAR(booking_date) AS year,
        MONTH(booking_date) AS month,
        COUNT(DISTINCT booking_id) AS num_bookings,
        SUM(total_amount) AS total_revenue
    FROM Bookings
    WHERE booking_date BETWEEN
        DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) - 1 DAY), INTERVAL 12 MONTH)
        AND DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
    GROUP BY YEAR(booking_date), MONTH(booking_date)
    ORDER BY YEAR(booking_date), MONTH(booking_date);
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def getEventAttendanceReport(cursor, year, month):
    """Get the attendance report for events at FARCA"""
    query = """
    SELECT 
        YEAR(event_date) AS year,
        MONTH(event_date) AS month,
        event_name,
        COUNT(DISTINCT attendee_id) AS num_attendees
    FROM Events
    LEFT JOIN EventAttendees ON Events.event_id = EventAttendees.event_id
    WHERE event_date BETWEEN
        DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) - 1 DAY), INTERVAL 12 MONTH)
        AND DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
    GROUP BY YEAR(event_date), MONTH(event_date), event_name
    ORDER BY YEAR(event_date), MONTH(event_date), event_name;
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def getCustomerFeedbackReport(cursor, year, month):
    """Get the customer feedback for FARCA"""
    query = """
    SELECT 
        YEAR(feedback_date) AS year,
        MONTH(feedback_date) AS month,
        AVG(rating) AS average_rating,
        COUNT(feedback_id) AS num_feedbacks
    FROM CustomerFeedback
    WHERE feedback_date BETWEEN
        DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) - 1 DAY), INTERVAL 12 MONTH)
        AND DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
    GROUP BY YEAR(feedback_date), MONTH(feedback_date)
    ORDER BY YEAR(feedback_date), MONTH(feedback_date);
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def getMonthlySalesReport(cursor, year, month):
    """Get monthly sales report for FARCA"""
    query = """
    WITH 
        food_sales AS (
            SELECT 
                YEAR(order_date) AS year,
                MONTH(order_date) AS month,
                SUM(order_total) AS total_food_sales
            FROM Orders
            WHERE order_date BETWEEN
                DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) - 1 DAY), INTERVAL 12 MONTH)
                AND DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
            GROUP BY YEAR(order_date), MONTH(order_date)
        ),
        drink_sales AS (
            SELECT 
                YEAR(order_date) AS year,
                MONTH(order_date) AS month,
                SUM(order_total) AS total_drink_sales
            FROM Orders
            WHERE order_date BETWEEN
                DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) - 1 DAY), INTERVAL 12 MONTH)
                AND DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
            GROUP BY YEAR(order_date), MONTH(order_date)
        )
    SELECT 
        COALESCE(food_sales.year, drink_sales.year) AS year,
        COALESCE(food_sales.month, drink_sales.month) AS month,
        COALESCE(total_food_sales, 0) AS total_food_sales,
        COALESCE(total_drink_sales, 0) AS total_drink_sales,
        COALESCE(total_food_sales, 0) + COALESCE(total_drink_sales, 0) AS total_sales
    FROM food_sales
    LEFT JOIN drink_sales 
        ON food_sales.year = drink_sales.year 
        AND food_sales.month = drink_sales.month
    ORDER BY year DESC, month DESC;
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def getRoomBookingReport(cursor, year, month):
    """Get room booking report for FARCA"""
    query = """
    SELECT 
        YEAR(booking_date) AS year,
        MONTH(booking_date) AS month,
        COUNT(DISTINCT booking_id) AS num_room_bookings,
        SUM(total_amount) AS total_room_revenue
    FROM RoomBookings
    WHERE booking_date BETWEEN
        DATE_SUB(DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) - 1 DAY), INTERVAL 12 MONTH)
        AND DATE_SUB(CURDATE(), INTERVAL DAY(CURDATE()) DAY)
    GROUP BY YEAR(booking_date), MONTH(booking_date)
    ORDER BY YEAR(booking_date), MONTH(booking_date);
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result


def getExpenseAnalysis(cursor):
    """Get the expense analysis for FARCA"""
    query = """
    SELECT vendor, SUM(amount) AS total_amount
    FROM Expenses
    GROUP BY vendor
    ORDER BY total_amount DESC;
    """
    cursor.execute(query)
    query_result = cursor.fetchall()
    return query_result
