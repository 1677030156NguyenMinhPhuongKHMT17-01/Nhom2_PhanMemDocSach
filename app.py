"""
Entry point cho ứng dụng EBook Reader
Sử dụng cấu trúc modular với app factory pattern
"""
import os
from app import create_app

# Lấy môi trường từ environment variable, mặc định là 'development'
config_name = os.environ.get('FLASK_ENV', 'development')

# Debug: In ra config được sử dụng
print(f"Using config: {config_name}")

# Đảm bảo chạy development mode
if config_name not in ['development', 'production', 'testing']:
    config_name = 'development'
    print(f"Fallback to: {config_name}")

# Tạo Flask app bằng factory pattern
app = create_app(config_name)

if __name__ == '__main__':
    # Chạy ứng dụng
    debug_mode = config_name == 'development'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)