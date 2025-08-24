import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_URL=postgresql://sydney:password123@localhost:5432/helios_db
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # AI Configuration
    HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    SUMMARY_MODEL = os.environ.get('SUMMARY_MODEL', 'facebook/bart-large-cnn')
    CHAT_MODEL = os.environ.get('CHAT_MODEL', 'microsoft/DialoGPT-medium')

    # Security
    BCRYPT_LOG_ROUNDS = 13
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

    # Command Execution
    COMMAND_TIMEOUT = int(os.environ.get('COMMAND_TIMEOUT', '10'))
    MAX_COMMAND_OUTPUT = int(os.environ.get('MAX_COMMAND_OUTPUT', '10000'))

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'helios.log')

class DevelopmentConfig(Config):
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SSL_REDIRECT = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    BCRYPT_LOG_ROUNDS = 4

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}