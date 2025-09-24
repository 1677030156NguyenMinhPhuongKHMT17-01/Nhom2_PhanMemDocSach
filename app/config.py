"""
Cấu hình cho ứng dụng EBook Reader
"""
import os
from datetime import timedelta

class Config:
    """Cấu hình cơ bản cho ứng dụng"""
    
    # Cấu hình Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    
    # Cấu hình database
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'ebook_library.db'
    DATABASE_TIMEOUT = 30.0  # 30 giây timeout cho SQLite
    
    # Cấu hình upload file
    UPLOAD_FOLDER = 'static/uploads'
    COVERS_FOLDER = 'static/covers'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB tối đa cho file upload
    
    # Các định dạng file được hỗ trợ
    ALLOWED_EXTENSIONS = {'.pdf', '.epub', '.txt'}
    
    # Cấu hình session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)  # Session có hiệu lực 24 giờ
    
    # Cấu hình đọc sách
    MAX_SEARCH_RESULTS = 20  # Giới hạn kết quả tìm kiếm trong sách
    DEFAULT_BOOKS_PER_PAGE = 8  # Số sách mặc định hiển thị trên trang chủ

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường phát triển"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Cấu hình cho môi trường production"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production-env'

class TestingConfig(Config):
    """Cấu hình cho môi trường testing"""
    TESTING = True
    DATABASE_PATH = ':memory:'  # Sử dụng SQLite in-memory cho testing

# Dictionary để dễ dàng chọn config theo môi trường
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
