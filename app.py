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
app.config['MYSQL_DATABASE_PORT'] = 3306  # Ensure the default port is specified
app.config['MYSQL_DATABASE_DB'] = 'FARCA'
mysql = MySQL(app)

# Utility Functions
def check_logged_in():
    return session.get('logged_in', False)

def get_current_user():
    return session.get('username', None)

def is_admin():
    return session.get('role') == 'admin'

# Test Connection Function
def test_db_connection():
    """Function to test the database connection."""
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Error connecting to the database: {e}")

# Routes
@app.route('/')
@app.route('/home')
def home():
    """Homepage displaying FARCA services and highlights."""
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM Menu_Items")
        menu_items = cursor.fetchall()

        cursor.execute("SELECT * FROM Events ORDER BY event_date DESC")
        events = cursor.fetchall()

        conn.close()
        return render_template('home.html', menu_items=menu_items, events=events)
    except Exception as e:
        return f"Database error: {str(e)}"

# Run the Flask app with a DB test
if __name__ == '__main__':
    test_db_connection()
    app.run(debug=True)
