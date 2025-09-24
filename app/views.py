"""
Views/Routes cho ứng dụng EBook Reader
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from .services import UserService, BookService, ReadingService, LibraryService, NoteService
from .utils import DirectoryHelper

# Tạo Blueprint cho main routes
main_bp = Blueprint('main', __name__)

# Khởi tạo services
user_service = UserService()
book_service = BookService()
reading_service = ReadingService()
library_service = LibraryService()
note_service = NoteService()

@main_bp.route('/')
def index():
    """Trang chủ hiển thị sách mới và sách đang đọc"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    try:
        data = book_service.get_home_data(session['user_id'])
        
        if 'error' in data:
            flash(data['error'], 'error')
            return render_template('index.html', recent_books=[], reading_books=[])
        
        return render_template('index.html', 
                             recent_books=data['recent_books'], 
                             reading_books=data['reading_books'])
    except Exception as e:
        flash(f'Lỗi tải trang chủ: {str(e)}', 'error')
        return render_template('index.html', recent_books=[], reading_books=[])

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Đăng ký tài khoản mới"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        
        success, message = user_service.register_user(username, email, password, full_name)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('main.login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Đăng nhập"""
    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        success, result = user_service.authenticate_user(username_or_email, password)
        
        if success:
            user = result
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('main.index'))
        else:
            flash(result, 'error')
    
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    """Đăng xuất"""
    session.clear()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('main.login'))

@main_bp.route('/library')
def library():
    """Thư viện cá nhân"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    books, error = library_service.get_user_library(session['user_id'])
    
    if error:
        flash(error, 'error')
    
    return render_template('library.html', books=books)

@main_bp.route('/search')
def search():
    """Tìm kiếm sách"""
    query = request.args.get('q', '').strip()
    genre = request.args.get('genre', '').strip()
    
    data = book_service.search_books(query, genre)
    
    if 'error' in data:
        flash(data['error'], 'error')
    
    return render_template('search.html', 
                         books=data['books'], 
                         genres=data['genres'],
                         query=data['query'], 
                         selected_genre=data['selected_genre'])

@main_bp.route('/book/<int:book_id>')
def book_detail(book_id):
    """Chi tiết sách"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    data, error = book_service.get_book_detail(book_id, session['user_id'])
    
    if error:
        flash(error, 'error')
        return redirect(url_for('main.index'))
    
    return render_template('book_detail.html', 
                         book=data['book'],
                         genres=data['genres'],
                         user_book=data['user_book'],
                         notes=data['notes'])

@main_bp.route('/read/<int:book_id>')
def read_book(book_id):
    """Đọc sách"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    data, error = reading_service.prepare_reading_session(book_id, session['user_id'])
    
    if error:
        flash(error, 'error')
        return redirect(url_for('main.index'))
    
    return render_template('read.html', 
                         book=data['book'],
                         last_position=data['last_position'],
                         book_content=data['book_content'])

@main_bp.route('/add_to_library/<int:book_id>')
def add_to_library(book_id):
    """Thêm sách vào thư viện"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    success, message = library_service.add_to_library(session['user_id'], book_id)
    
    flash(message, 'success' if success else 'info')
    return redirect(url_for('main.book_detail', book_id=book_id))

@main_bp.route('/toggle_favorite/<int:book_id>')
def toggle_favorite(book_id):
    """Chuyển đổi trạng thái yêu thích"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    success, message = library_service.toggle_favorite(session['user_id'], book_id)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('main.book_detail', book_id=book_id))

@main_bp.route('/save_progress', methods=['POST'])
def save_progress():
    """Lưu tiến độ đọc sách (API endpoint)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    book_id = data.get('book_id')
    position = data.get('position', 0)
    
    if not book_id:
        return jsonify({'error': 'Missing book_id'}), 400
    
    success, message = reading_service.save_reading_progress(session['user_id'], book_id, position)
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 500

@main_bp.route('/add_note', methods=['POST'])
def add_note():
    """Thêm ghi chú"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    book_id = request.form.get('book_id')
    content = request.form.get('content', '').strip()
    location = request.form.get('location', '').strip()
    highlighted_text = request.form.get('highlighted_text', '').strip()
    
    if not book_id:
        flash('Thiếu thông tin sách!', 'error')
        return redirect(url_for('main.index'))
    
    success, message = note_service.add_note(
        session['user_id'], book_id, content, location, highlighted_text
    )
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('main.book_detail', book_id=book_id))

@main_bp.route('/upload_book', methods=['GET', 'POST'])
def upload_book():
    """Upload sách mới"""
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        # Lấy thông tin từ form
        title = request.form.get('title', '').strip()
        author_name = request.form.get('author_name', '').strip()
        publisher_name = request.form.get('publisher_name', '').strip()
        description = request.form.get('description', '').strip()
        publication_year = request.form.get('publication_year', type=int)
        genre_names = request.form.getlist('genres')
        
        # Lấy file
        file = request.files.get('book_file')
        
        if not file or file.filename == '':
            flash('Vui lòng chọn file sách!', 'error')
            return render_template('upload_book.html')
        
        success, result = book_service.upload_book(
            file, title, author_name, publisher_name, description,
            publication_year, genre_names, session['user_id']
        )
        
        if success:
            book_id = result
            flash('Đã upload sách thành công!', 'success')
            return redirect(url_for('main.book_detail', book_id=book_id))
        else:
            flash(result, 'error')
    
    return render_template('upload_book.html')

@main_bp.route('/search_in_book/<int:book_id>')
def search_in_book(book_id):
    """Tìm kiếm trong nội dung sách (API endpoint)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': [], 'total': 0})
    
    results, error = reading_service.search_in_book(book_id, query)
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'results': results, 
        'total': len(results),
        'query': query
    })

# Error handlers
@main_bp.errorhandler(404)
def not_found_error(error):
    """Xử lý lỗi 404"""
    return render_template('errors/404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Xử lý lỗi 500"""
    return render_template('errors/500.html'), 500

# Context processor để inject data vào tất cả templates
@main_bp.context_processor
def inject_user():
    """Inject thông tin user vào template context"""
    return {
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'is_authenticated': 'user_id' in session
        }
    }