"""
Factory function để tạo Flask app với cấu trúc modular
"""
from flask import Flask
from .config import config
from .models import DatabaseManager
from .utils import DirectoryHelper
from .views import main_bp

def create_app(config_name='default'):
    """
    Factory function để tạo và cấu hình Flask app
    
    Args:
        config_name (str): Tên môi trường config ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application
    """
    # Tạo Flask app với đường dẫn template và static chính xác
    import os
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Load configuration
    config_class = config.get(config_name, config['default'])
    app.config.from_object(config_class)
    
    # Đảm bảo các thư mục cần thiết tồn tại
    DirectoryHelper.ensure_directories_exist()
    
    # Khởi tạo database
    db_manager = DatabaseManager(app.config.get('DATABASE_PATH'))
    db_manager.init_database()
    
    # Đăng ký Blueprint
    app.register_blueprint(main_bp)
    
    # Cấu hình logging
    import logging
    from logging.handlers import RotatingFileHandler
    import os
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # File handler cho tất cả môi trường
    file_handler = RotatingFileHandler('logs/ebook_reader.log', maxBytes=10240000, backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s'
    ))
    file_handler.setLevel(logging.INFO if app.debug else logging.WARNING)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO if app.debug else logging.WARNING)
    
    return app
