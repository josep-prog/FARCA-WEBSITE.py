import os

class Config:
    """Base configuration for the FARCA website application."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'your_password'
    MYSQL_DB = 'farca_db'

class ProductionConfig(Config):
    """Production-specific configuration."""
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')

# Determine the configuration to use
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
