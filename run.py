import os
from app import create_app
import logging
from logging.handlers import RotatingFileHandler

# Create the Flask app
app = create_app()

# Logging setup
if not app.debug:
    # Only set up file logging in production
    handler = RotatingFileHandler('farca_app.log', maxBytes=10000, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

# Make sure the app is using the correct environment variables
if __name__ == '__main__':
    environment = os.getenv('FLASK_ENV', 'production')
    if environment == 'development':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # This is a placeholder for when deploying to production with a WSGI server like Gunicorn
        app.run(debug=False, host='0.0.0.0', port=5000)
