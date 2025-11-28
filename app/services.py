"""
Business logic services cho ứng dụng EBook Reader
"""
from werkzeug.security import generate_password_hash, check_password_hash
from .models import DatabaseManager, UserModel, BookModel, UserLibraryModel, NoteModel
from .utils import BookContentReader, BookSearcher, FileProcessor, ValidationHelper
from .config import Config

class UserService:
    """Service xử lý logic liên quan đến người dùng"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        self.user_model = UserModel(self.db)
    
    def register_user(self, username, email, password, full_name=None):
        """Đăng ký người dùng mới"""
        # Validate input
        if not ValidationHelper.validate_username(username):
            return False, "Tên đăng nhập không hợp lệ (ít nhất 3 ký tự, chỉ chữ cái, số và _)"
        
        if not ValidationHelper.validate_email(email):
            return False, "Email không hợp lệ"
        
        is_valid_password, password_message = ValidationHelper.validate_password(password)
        if not is_valid_password:
            return False, password_message
        
        # Kiểm tra user đã tồn tại
        if self.user_model.check_user_exists(username, email):
            return False, "Tên đăng nhập hoặc email đã tồn tại"
        
        # Tạo user mới
        try:
            password_hash = generate_password_hash(password)
            user_id = self.user_model.create_user(username, email, password_hash, full_name)
            return True, f"Đăng ký thành công với user_id: {user_id}"
        except Exception as e:
            return False, f"Lỗi khi tạo tài khoản: {str(e)}"
    
    def authenticate_user(self, username_or_email, password):
        """Xác thực đăng nhập người dùng"""
        try:
            user = self.user_model.get_user_by_username_or_email(username_or_email)
            
            if user and check_password_hash(user['password_hash'], password):
                return True, user
            else:
                return False, "Tên đăng nhập hoặc mật khẩu không đúng"
        except Exception as e:
            return False, f"Lỗi xác thực: {str(e)}"

    def get_user_info(self, user_id):
        """Lấy thông tin người dùng"""
        try:
            user = self.user_model.get_user_by_id(user_id)
            if user:
                return user
            return None
        except Exception:
            return None

    def update_profile(self, user_id, full_name, email):
        """Cập nhật thông tin cá nhân"""
        # Validate email
        if not ValidationHelper.validate_email(email):
            return False, "Email không hợp lệ"
            
        try:
            # Check if email is taken by another user (skip for now for simplicity or implement check)
            self.user_model.update_user(user_id, full_name, email)
            return True, "Cập nhật thông tin thành công"
        except Exception as e:
            return False, f"Lỗi cập nhật: {str(e)}"

    def change_password(self, user_id, current_password, new_password):
        """Đổi mật khẩu"""
        try:
            user = self.user_model.get_user_by_id(user_id)
            if not user:
                return False, "Người dùng không tồn tại"
            
            if not check_password_hash(user['password_hash'], current_password):
                return False, "Mật khẩu hiện tại không đúng"
            
            is_valid, msg = ValidationHelper.validate_password(new_password)
            if not is_valid:
                return False, msg
                
            new_hash = generate_password_hash(new_password)
            self.user_model.update_password(user_id, new_hash)
            return True, "Đổi mật khẩu thành công"
        except Exception as e:
            return False, f"Lỗi đổi mật khẩu: {str(e)}"

class BookService:
    """Service xử lý logic liên quan đến sách"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        self.book_model = BookModel(self.db)
    
    def get_home_data(self, user_id, limit=None):
        """Lấy dữ liệu cho trang chủ"""
        limit = limit or Config.DEFAULT_BOOKS_PER_PAGE
        try:
            recent_books = self.book_model.get_recent_books(limit)
            
            # Lấy sách đang đọc của user
            user_library = UserLibraryModel(self.db)
            reading_books = user_library.get_reading_books(user_id)
            
            return {
                'recent_books': recent_books,
                'reading_books': reading_books
            }
        except Exception as e:
            return {
                'recent_books': [],
                'reading_books': [],
                'error': f"Lỗi khi lấy dữ liệu: {str(e)}"
            }
    
    def get_book_detail(self, book_id, user_id):
        """Lấy chi tiết sách và thông tin liên quan"""
        try:
            # Lấy thông tin sách
            book = self.book_model.get_book_by_id(book_id)
            if not book:
                return None, "Không tìm thấy sách"
            
            # Lấy thể loại
            genres = self.book_model.get_book_genres(book_id)
            
            # Lấy thông tin trong thư viện user
            user_library = UserLibraryModel(self.db)
            user_book = user_library.get_user_book(user_id, book_id)
            
            # Lấy ghi chú
            note_model = NoteModel(self.db)
            notes = note_model.get_book_notes(user_id, book_id)
            
            return {
                'book': book,
                'genres': genres,
                'user_book': user_book,
                'notes': notes
            }, None
            
        except Exception as e:
            return None, f"Lỗi khi lấy thông tin sách: {str(e)}"
    
    def search_books(self, query=None, genre=None):
        """Tìm kiếm sách"""
        try:
            books = self.book_model.search_books(query, genre)
            genres = self.book_model.get_all_genres()
            
            return {
                'books': books,
                'genres': genres,
                'query': query,
                'selected_genre': genre
            }
        except Exception as e:
            return {
                'books': [],
                'genres': [],
                'query': query,
                'selected_genre': genre,
                'error': f"Lỗi tìm kiếm: {str(e)}"
            }
    
    def upload_book(self, file, title, author_name, publisher_name="", description="", 
                   publication_year=None, genre_names=None, user_id=None):
        """Upload và xử lý sách mới"""
        genre_names = genre_names or []
        
        # Validate input
        required_fields = {'title': title, 'author_name': author_name}
        missing_fields = ValidationHelper.validate_required_fields(required_fields, required_fields.keys())
        if missing_fields:
            return False, f"Thiếu thông tin: {', '.join(missing_fields)}"
        
        try:
            # Lưu file
            file_path = FileProcessor.save_uploaded_file(file, Config.UPLOAD_FOLDER)
            if not file_path:
                return False, "Lỗi khi lưu file"
            
            # Lấy hoặc tạo author
            author_id = self.book_model.get_or_create_author(author_name)
            
            # Lấy hoặc tạo publisher
            publisher_id = self.book_model.get_or_create_publisher(publisher_name) if publisher_name else None
            
            # Tạo sách
            book_id = self.book_model.create_book(
                title, author_id, publisher_id, description, file_path, publication_year
            )
            
            # Thêm thể loại
            for genre_name in genre_names:
                if genre_name.strip():
                    genre_id = self.book_model.get_or_create_genre(genre_name.strip())
                    self.book_model.link_book_genre(book_id, genre_id)
            
            # Thêm vào thư viện của user upload (nếu có user_id)
            if user_id:
                user_library = UserLibraryModel(self.db)
                user_library.add_to_library(user_id, book_id)
            
            return True, book_id
            
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Lỗi khi upload sách: {str(e)}"

class ReadingService:
    """Service xử lý logic liên quan đến việc đọc sách"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        self.book_model = BookModel(self.db)
        self.user_library = UserLibraryModel(self.db)
    
    def prepare_reading_session(self, book_id, user_id):
        """Chuẩn bị session đọc sách"""
        try:
            # Lấy thông tin sách
            book = self.book_model.get_book_by_id(book_id)
            if not book:
                return None, "Không tìm thấy sách"
            
            # Lấy hoặc tạo user_library entry
            user_book = self.user_library.get_user_book(user_id, book_id)
            if not user_book:
                # Thêm sách vào thư viện user
                self.user_library.add_to_library(user_id, book_id, 'reading')
                last_position = 0
            else:
                last_position = user_book['last_read_position']
                # Cập nhật trạng thái thành đang đọc
                self.user_library.update_reading_status(user_id, book_id, 'reading')
            
            # Đọc nội dung sách
            if book['file_path']:
                book_content = BookContentReader.read_book_content(book['file_path'])
            else:
                book_content = "Nội dung sách không có sẵn."
            
            return {
                'book': book,
                'last_position': last_position,
                'book_content': book_content
            }, None
            
        except Exception as e:
            return None, f"Lỗi khi chuẩn bị đọc sách: {str(e)}"
    
    def save_reading_progress(self, user_id, book_id, position):
        """Lưu tiến độ đọc"""
        try:
            self.user_library.save_reading_progress(user_id, book_id, position)
            return True, "Đã lưu tiến độ"
        except Exception as e:
            return False, f"Lỗi lưu tiến độ: {str(e)}"
    
    def search_in_book(self, book_id, query):
        """Tìm kiếm trong nội dung sách"""
        try:
            book = self.book_model.get_book_by_id(book_id)
            if not book or not book['file_path']:
                return [], "Không tìm thấy sách hoặc file không tồn tại"
            
            # Đọc nội dung và tìm kiếm
            content = BookContentReader.read_book_content(book['file_path'])
            results = BookSearcher.search_in_content(content, query)
            
            return results, None
            
        except Exception as e:
            return [], f"Lỗi tìm kiếm: {str(e)}"

class LibraryService:
    """Service xử lý logic liên quan đến thư viện cá nhân"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        self.user_library = UserLibraryModel(self.db)
    
    def get_user_library(self, user_id):
        """Lấy thư viện của user"""
        try:
            books = self.user_library.get_user_books(user_id)
            return books, None
        except Exception as e:
            return [], f"Lỗi khi lấy thư viện: {str(e)}"
    
    def add_to_library(self, user_id, book_id):
        """Thêm sách vào thư viện"""
        try:
            success = self.user_library.add_to_library(user_id, book_id)
            if success:
                return True, "Đã thêm sách vào thư viện"
            else:
                return False, "Sách đã có trong thư viện"
        except Exception as e:
            return False, f"Lỗi khi thêm vào thư viện: {str(e)}"
    
    def toggle_favorite(self, user_id, book_id):
        """Chuyển đổi trạng thái yêu thích"""
        try:
            new_favorite = self.user_library.toggle_favorite(user_id, book_id)
            if new_favorite is False:
                return False, "Sách không có trong thư viện"
            
            message = "Đã thêm vào yêu thích" if new_favorite else "Đã bỏ khỏi yêu thích"
            return True, message
        except Exception as e:
            return False, f"Lỗi khi cập nhật yêu thích: {str(e)}"

class NoteService:
    """Service xử lý logic liên quan đến ghi chú"""
    
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        self.note_model = NoteModel(self.db)
    
    def add_note(self, user_id, book_id, content, location=None, highlighted_text=None):
        """Thêm ghi chú mới"""
        # Validate
        if not content or not content.strip():
            return False, "Nội dung ghi chú không được để trống"
        
        try:
            note_id = self.note_model.create_note(
                user_id, book_id, content.strip(), location, highlighted_text
            )
            return True, f"Đã thêm ghi chú (ID: {note_id})"
        except Exception as e:
            return False, f"Lỗi khi thêm ghi chú: {str(e)}"
    
    def get_book_notes(self, user_id, book_id):
        """Lấy danh sách ghi chú của sách"""
        try:
            notes = self.note_model.get_book_notes(user_id, book_id)
            return notes, None
        except Exception as e:
            return [], f"Lỗi khi lấy ghi chú: {str(e)}"