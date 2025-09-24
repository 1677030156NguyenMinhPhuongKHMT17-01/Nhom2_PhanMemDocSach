"""
Models và operations cho database SQLite
"""
import sqlite3
import os
from .config import Config

class DatabaseManager:
    """Quản lý kết nối và operations cho database"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
        
    def get_connection(self):
        """Lấy kết nối database với cấu hình tối ưu"""
        conn = sqlite3.connect(self.db_path, timeout=Config.DATABASE_TIMEOUT)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Khởi tạo database với tất cả bảng cần thiết"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Tạo bảng Users (Người dùng)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tạo bảng Authors (Tác giả)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authors (
                    author_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_name TEXT NOT NULL,
                    birth_year INTEGER,
                    nationality TEXT
                )
            ''')
            
            # Tạo bảng Publishers (Nhà xuất bản)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS publishers (
                    publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    publisher_name TEXT NOT NULL,
                    address TEXT
                )
            ''')
            
            # Tạo bảng Genres (Thể loại)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS genres (
                    genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    genre_name TEXT UNIQUE NOT NULL
                )
            ''')
            
            # Tạo bảng Books (Sách)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS books (
                    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author_id INTEGER,
                    publisher_id INTEGER,
                    description TEXT,
                    cover_image_url TEXT,
                    file_path TEXT,
                    publication_year INTEGER,
                    page_count INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES authors (author_id),
                    FOREIGN KEY (publisher_id) REFERENCES publishers (publisher_id)
                )
            ''')
            
            # Tạo bảng BookGenres (Liên kết sách và thể loại)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS book_genres (
                    book_id INTEGER,
                    genre_id INTEGER,
                    PRIMARY KEY (book_id, genre_id),
                    FOREIGN KEY (book_id) REFERENCES books (book_id),
                    FOREIGN KEY (genre_id) REFERENCES genres (genre_id)
                )
            ''')
            
            # Tạo bảng UserLibrary (Thư viện cá nhân)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_library (
                    user_library_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    book_id INTEGER,
                    is_favorite BOOLEAN DEFAULT FALSE,
                    last_read_position INTEGER DEFAULT 0,
                    reading_status TEXT DEFAULT 'not_started',
                    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (book_id) REFERENCES books (book_id)
                )
            ''')
            
            # Tạo bảng Notes (Ghi chú)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    book_id INTEGER,
                    content TEXT NOT NULL,
                    location_in_book TEXT,
                    highlighted_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (book_id) REFERENCES books (book_id)
                )
            ''')
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class UserModel:
    """Model cho thao tác với bảng users"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_user(self, username, email, password_hash, full_name=None):
        """Tạo người dùng mới"""
        conn = self.db.get_connection()
        try:
            cursor = conn.execute(
                'INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, full_name)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_user_by_username_or_email(self, username_or_email):
        """Lấy thông tin user theo username hoặc email"""
        conn = self.db.get_connection()
        try:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? OR email = ?',
                (username_or_email, username_or_email)
            ).fetchone()
            return user
        finally:
            conn.close()
    
    def check_user_exists(self, username, email):
        """Kiểm tra username hoặc email đã tồn tại chưa"""
        conn = self.db.get_connection()
        try:
            existing = conn.execute(
                'SELECT user_id FROM users WHERE username = ? OR email = ?',
                (username, email)
            ).fetchone()
            return existing is not None
        finally:
            conn.close()

class BookModel:
    """Model cho thao tác với bảng books và liên quan"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_recent_books(self, limit=8):
        """Lấy danh sách sách mới nhất"""
        conn = self.db.get_connection()
        try:
            books = conn.execute('''
                SELECT b.*, a.author_name, p.publisher_name 
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
                ORDER BY b.added_at DESC LIMIT ?
            ''', (limit,)).fetchall()
            return books
        finally:
            conn.close()
    
    def get_book_by_id(self, book_id):
        """Lấy thông tin sách theo ID"""
        conn = self.db.get_connection()
        try:
            book = conn.execute('''
                SELECT b.*, a.author_name, p.publisher_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
                WHERE b.book_id = ?
            ''', (book_id,)).fetchone()
            return book
        finally:
            conn.close()
    
    def search_books(self, query=None, genre=None):
        """Tìm kiếm sách theo tiêu đề, tác giả hoặc thể loại"""
        conn = self.db.get_connection()
        try:
            sql = '''
                SELECT DISTINCT b.*, a.author_name, p.publisher_name
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
                LEFT JOIN book_genres bg ON b.book_id = bg.book_id
                LEFT JOIN genres g ON bg.genre_id = g.genre_id
                WHERE 1=1
            '''
            params = []
            
            if query:
                sql += ' AND (b.title LIKE ? OR a.author_name LIKE ?)'
                params.extend([f'%{query}%', f'%{query}%'])
            
            if genre:
                sql += ' AND g.genre_name = ?'
                params.append(genre)
            
            sql += ' ORDER BY b.added_at DESC'
            
            books = conn.execute(sql, params).fetchall()
            return books
        finally:
            conn.close()
    
    def create_book(self, title, author_id, publisher_id, description, file_path, publication_year=None):
        """Tạo sách mới"""
        conn = self.db.get_connection()
        try:
            cursor = conn.execute('''
                INSERT INTO books (title, author_id, publisher_id, description, file_path, publication_year)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, author_id, publisher_id, description, file_path, publication_year))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_or_create_author(self, author_name):
        """Lấy hoặc tạo tác giả mới"""
        conn = self.db.get_connection()
        try:
            # Kiểm tra tác giả đã tồn tại
            author = conn.execute('SELECT author_id FROM authors WHERE author_name = ?', (author_name,)).fetchone()
            if author:
                return author['author_id']
            
            # Tạo tác giả mới
            cursor = conn.execute('INSERT INTO authors (author_name) VALUES (?)', (author_name,))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_or_create_publisher(self, publisher_name):
        """Lấy hoặc tạo nhà xuất bản mới"""
        if not publisher_name:
            return None
            
        conn = self.db.get_connection()
        try:
            # Kiểm tra nhà xuất bản đã tồn tại
            publisher = conn.execute('SELECT publisher_id FROM publishers WHERE publisher_name = ?', (publisher_name,)).fetchone()
            if publisher:
                return publisher['publisher_id']
            
            # Tạo nhà xuất bản mới
            cursor = conn.execute('INSERT INTO publishers (publisher_name) VALUES (?)', (publisher_name,))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_or_create_genre(self, genre_name):
        """Lấy hoặc tạo thể loại mới"""
        if not genre_name:
            return None
            
        conn = self.db.get_connection()
        try:
            # Kiểm tra thể loại đã tồn tại
            genre = conn.execute('SELECT genre_id FROM genres WHERE genre_name = ?', (genre_name,)).fetchone()
            if genre:
                return genre['genre_id']
            
            # Tạo thể loại mới
            cursor = conn.execute('INSERT INTO genres (genre_name) VALUES (?)', (genre_name,))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def link_book_genre(self, book_id, genre_id):
        """Liên kết sách với thể loại"""
        conn = self.db.get_connection()
        try:
            conn.execute('INSERT INTO book_genres (book_id, genre_id) VALUES (?, ?)', (book_id, genre_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_book_genres(self, book_id):
        """Lấy danh sách thể loại của sách"""
        conn = self.db.get_connection()
        try:
            genres = conn.execute('''
                SELECT g.genre_name
                FROM genres g
                JOIN book_genres bg ON g.genre_id = bg.genre_id
                WHERE bg.book_id = ?
            ''', (book_id,)).fetchall()
            return genres
        finally:
            conn.close()
    
    def get_all_genres(self):
        """Lấy tất cả thể loại"""
        conn = self.db.get_connection()
        try:
            genres = conn.execute('SELECT * FROM genres ORDER BY genre_name').fetchall()
            return genres
        finally:
            conn.close()

class UserLibraryModel:
    """Model cho thao tác với thư viện cá nhân"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_user_books(self, user_id):
        """Lấy danh sách sách trong thư viện user"""
        conn = self.db.get_connection()
        try:
            books = conn.execute('''
                SELECT b.*, a.author_name, ul.is_favorite, ul.reading_status, ul.last_read_position
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                JOIN user_library ul ON b.book_id = ul.book_id
                WHERE ul.user_id = ?
                ORDER BY ul.added_date DESC
            ''', (user_id,)).fetchall()
            return books
        finally:
            conn.close()
    
    def get_reading_books(self, user_id):
        """Lấy danh sách sách đang đọc"""
        conn = self.db.get_connection()
        try:
            books = conn.execute('''
                SELECT b.*, a.author_name, ul.last_read_position, ul.reading_status
                FROM books b
                LEFT JOIN authors a ON b.author_id = a.author_id
                JOIN user_library ul ON b.book_id = ul.book_id
                WHERE ul.user_id = ? AND ul.reading_status = 'reading'
                ORDER BY ul.added_date DESC
            ''', (user_id,)).fetchall()
            return books
        finally:
            conn.close()
    
    def get_user_book(self, user_id, book_id):
        """Lấy thông tin sách trong thư viện user"""
        conn = self.db.get_connection()
        try:
            user_book = conn.execute('''
                SELECT * FROM user_library 
                WHERE user_id = ? AND book_id = ?
            ''', (user_id, book_id)).fetchone()
            return user_book
        finally:
            conn.close()
    
    def add_to_library(self, user_id, book_id, reading_status='not_started'):
        """Thêm sách vào thư viện user"""
        conn = self.db.get_connection()
        try:
            # Kiểm tra đã tồn tại chưa
            existing = self.get_user_book(user_id, book_id)
            if existing:
                return False  # Đã tồn tại
            
            conn.execute('''
                INSERT INTO user_library (user_id, book_id, reading_status)
                VALUES (?, ?, ?)
            ''', (user_id, book_id, reading_status))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_reading_status(self, user_id, book_id, status):
        """Cập nhật trạng thái đọc sách"""
        conn = self.db.get_connection()
        try:
            conn.execute('''
                UPDATE user_library 
                SET reading_status = ?
                WHERE user_id = ? AND book_id = ?
            ''', (status, user_id, book_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def save_reading_progress(self, user_id, book_id, position):
        """Lưu tiến độ đọc sách"""
        conn = self.db.get_connection()
        try:
            conn.execute('''
                UPDATE user_library 
                SET last_read_position = ?
                WHERE user_id = ? AND book_id = ?
            ''', (position, user_id, book_id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def toggle_favorite(self, user_id, book_id):
        """Chuyển đổi trạng thái yêu thích"""
        conn = self.db.get_connection()
        try:
            user_book = self.get_user_book(user_id, book_id)
            if not user_book:
                return False
            
            new_favorite = not user_book['is_favorite']
            conn.execute('''
                UPDATE user_library 
                SET is_favorite = ?
                WHERE user_id = ? AND book_id = ?
            ''', (new_favorite, user_id, book_id))
            conn.commit()
            return new_favorite
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

class NoteModel:
    """Model cho thao tác với ghi chú"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_note(self, user_id, book_id, content, location=None, highlighted_text=None):
        """Tạo ghi chú mới"""
        conn = self.db.get_connection()
        try:
            cursor = conn.execute('''
                INSERT INTO notes (user_id, book_id, content, location_in_book, highlighted_text)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, book_id, content, location, highlighted_text))
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_book_notes(self, user_id, book_id):
        """Lấy danh sách ghi chú của sách"""
        conn = self.db.get_connection()
        try:
            notes = conn.execute('''
                SELECT * FROM notes 
                WHERE user_id = ? AND book_id = ?
                ORDER BY created_at DESC
            ''', (user_id, book_id)).fetchall()
            return notes
        finally:
            conn.close()