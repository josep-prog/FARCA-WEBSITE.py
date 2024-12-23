import mysql.connector

# Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'farca_db'
}

# SQL statements for initializing the database
TABLES = {
    'users': """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            role ENUM('admin', 'staff', 'customer') DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'menu': """
        CREATE TABLE IF NOT EXISTS menu (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'orders': """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            food_item_id INT NOT NULL,
            quantity INT NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('pending', 'preparing', 'completed', 'cancelled') DEFAULT 'pending',
            FOREIGN KEY (food_item_id) REFERENCES menu(item_id)
        )
    """,
    'room_bookings': """
        CREATE TABLE IF NOT EXISTS room_bookings (
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            room_id INT NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            contact VARCHAR(100),
            booking_date DATE NOT NULL,
            booking_time TIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'feedback': """
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            feedback_text TEXT NOT NULL,
            status ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """,
    'events': """
        CREATE TABLE IF NOT EXISTS events (
            event_id INT AUTO_INCREMENT PRIMARY KEY,
            event_name VARCHAR(255) NOT NULL,
            description TEXT,
            event_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    'event_reviews': """
        CREATE TABLE IF NOT EXISTS event_reviews (
            review_id INT AUTO_INCREMENT PRIMARY KEY,
            event_id INT NOT NULL,
            customer_name VARCHAR(255) NOT NULL,
            review_text TEXT,
            review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES events(event_id)
        )
    """,
    'contact_messages': """
        CREATE TABLE IF NOT EXISTS contact_messages (
            message_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
}

def initialize_database():
    """Initialize the database with the required tables."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for table_name, ddl in TABLES.items():
            print(f"Creating table {table_name}...")
            cursor.execute(ddl)
        
        print("Database initialization complete!")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    initialize_database()
