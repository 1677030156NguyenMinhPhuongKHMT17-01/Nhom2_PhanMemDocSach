from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime
import json
import PyPDF2
import ebooklib
from ebooklib import epub
import html2text
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Tạo thư mục upload nếu chưa có
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/covers', exist_ok=True)

# Khởi tạo database
def init_db():
    conn = sqlite3.connect('ebook_library.db')
    cursor = conn.cursor()
    
    # Tạo bảng Users
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
    
    # Tạo bảng Authors
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authors (
            author_id INTEGER PRIMARY KEY AUTOINCREMENT,
            author_name TEXT NOT NULL,
            birth_year INTEGER,
            nationality TEXT
        )
    ''')
    
    # Tạo bảng Publishers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS publishers (
            publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
            publisher_name TEXT NOT NULL,
            address TEXT
        )
    ''')
    
    # Tạo bảng Books
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
    
    # Tạo bảng Genres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS genres (
            genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
            genre_name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Tạo bảng BookGenres
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book_genres (
            book_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (book_id, genre_id),
            FOREIGN KEY (book_id) REFERENCES books (book_id),
            FOREIGN KEY (genre_id) REFERENCES genres (genre_id)
        )
    ''')
    
    # Tạo bảng UserLibrary
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
    
    # Tạo bảng Notes
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
    conn.close()

# Hàm tiện ích để lấy kết nối database
def get_db_connection():
    conn = sqlite3.connect('ebook_library.db', timeout=30.0)  # Timeout 30 giây
    conn.row_factory = sqlite3.Row
    return conn

# Hàm đọc nội dung file sách
def read_book_content(file_path):
    """Đọc nội dung sách từ file PDF, EPUB hoặc TXT"""
    if not os.path.exists(file_path):
        return "File không tồn tại."
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.pdf':
            return read_pdf_content(file_path)
        elif file_extension == '.epub':
            return read_epub_content(file_path)
        elif file_extension == '.txt':
            return read_txt_content(file_path)
        else:
            return "Định dạng file không được hỗ trợ."
    except Exception as e:
        return f"Lỗi khi đọc file: {str(e)}"

def read_pdf_content(file_path):
    """Đọc nội dung từ file PDF"""
    content = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            content += page.extract_text() + "\n\n"
    return content

def read_epub_content(file_path):
    """Đọc nội dung từ file EPUB"""
    book = epub.read_epub(file_path)
    content = ""
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup_content = item.get_body_content().decode('utf-8')
            # Chuyển HTML thành text
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            text_content = h.handle(soup_content)
            content += text_content + "\n\n"
    
    return content

def read_txt_content(file_path):
    """Đọc nội dung từ file TXT"""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()



# Routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        
        # Lấy sách mới nhất
        recent_books = conn.execute('''
            SELECT b.*, a.author_name, p.publisher_name 
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
            ORDER BY b.added_at DESC LIMIT 8
        ''').fetchall()
        
        # Lấy sách đang đọc
        reading_books = conn.execute('''
            SELECT b.*, a.author_name, ul.last_read_position, ul.reading_status
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            JOIN user_library ul ON b.book_id = ul.book_id
            WHERE ul.user_id = ? AND ul.reading_status = 'reading'
            ORDER BY ul.added_date DESC
        ''', (session['user_id'],)).fetchall()
        
        return render_template('index.html', recent_books=recent_books, reading_books=reading_books)
        
    except Exception as e:
        app.logger.error(f"Database error in index route: {e}")
        return render_template('index.html', recent_books=[], reading_books=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        if not username or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin!', 'error')
            return render_template('register.html')
        
        try:
            conn = get_db_connection()
            
            # Kiểm tra username và email đã tồn tại
            existing_user = conn.execute(
                'SELECT user_id FROM users WHERE username = ? OR email = ?',
                (username, email)
            ).fetchone()
            
            if existing_user:
                flash('Tên đăng nhập hoặc email đã tồn tại!', 'error')
                return render_template('register.html')
            
            # Tạo tài khoản mới
            password_hash = generate_password_hash(password)
            conn.execute(
                'INSERT INTO users (username, email, password_hash, full_name) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, full_name)
            )
            conn.commit()
            
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            app.logger.error(f"Database error in register: {e}")
            flash('Có lỗi xảy ra. Vui lòng thử lại!', 'error')
            return render_template('register.html')
        finally:
            if 'conn' in locals():
                conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? OR email = ?',
                (username, username)
            ).fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['full_name'] = user['full_name']
                flash('Đăng nhập thành công!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'error')
                
        except Exception as e:
            app.logger.error(f"Database error in login: {e}")
            flash('Có lỗi xảy ra. Vui lòng thử lại!', 'error')
        finally:
            if 'conn' in locals():
                conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('login'))

@app.route('/library')
def library():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        
        # Lấy thư viện của user
        user_books = conn.execute('''
            SELECT b.*, a.author_name, ul.is_favorite, ul.reading_status, ul.last_read_position
            FROM books b
            LEFT JOIN authors a ON b.author_id = a.author_id
            JOIN user_library ul ON b.book_id = ul.book_id
            WHERE ul.user_id = ?
            ORDER BY ul.added_date DESC
        ''', (session['user_id'],)).fetchall()
        
        return render_template('library.html', books=user_books)
        
    except Exception as e:
        app.logger.error(f"Database error in library: {e}")
        return render_template('library.html', books=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/search')
def search():
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    
    conn = get_db_connection()
    
    # Lấy tất cả thể loại
    genres = conn.execute('SELECT * FROM genres ORDER BY genre_name').fetchall()
    
    # Tìm kiếm sách
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
    conn.close()
    
    return render_template('search.html', books=books, genres=genres, query=query, selected_genre=genre)

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Lấy thông tin sách
    book = conn.execute('''
        SELECT b.*, a.author_name, p.publisher_name
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
        WHERE b.book_id = ?
    ''', (book_id,)).fetchone()
    
    if not book:
        flash('Không tìm thấy sách!', 'error')
        return redirect(url_for('index'))
    
    # Lấy thể loại
    genres = conn.execute('''
        SELECT g.genre_name
        FROM genres g
        JOIN book_genres bg ON g.genre_id = bg.genre_id
        WHERE bg.book_id = ?
    ''', (book_id,)).fetchall()
    
    # Kiểm tra sách có trong thư viện user không
    user_book = conn.execute('''
        SELECT * FROM user_library 
        WHERE user_id = ? AND book_id = ?
    ''', (session['user_id'], book_id)).fetchone()
    
    # Lấy ghi chú của user
    notes = conn.execute('''
        SELECT * FROM notes 
        WHERE user_id = ? AND book_id = ?
        ORDER BY created_at DESC
    ''', (session['user_id'], book_id)).fetchall()
    
    conn.close()
    
    return render_template('book_detail.html', book=book, genres=genres, user_book=user_book, notes=notes)

@app.route('/read/<int:book_id>')
def read_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Lấy thông tin sách
    book = conn.execute('''
        SELECT b.*, a.author_name
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        WHERE b.book_id = ?
    ''', (book_id,)).fetchone()
    
    if not book:
        flash('Không tìm thấy sách!', 'error')
        return redirect(url_for('index'))
    
    # Lấy hoặc tạo user_library entry
    user_book = conn.execute('''
        SELECT * FROM user_library 
        WHERE user_id = ? AND book_id = ?
    ''', (session['user_id'], book_id)).fetchone()
    
    if not user_book:
        # Thêm sách vào thư viện user
        conn.execute('''
            INSERT INTO user_library (user_id, book_id, reading_status)
            VALUES (?, ?, 'reading')
        ''', (session['user_id'], book_id))
        conn.commit()
        last_position = 0
    else:
        last_position = user_book['last_read_position']
        # Cập nhật trạng thái thành đang đọc
        conn.execute('''
            UPDATE user_library 
            SET reading_status = 'reading'
            WHERE user_id = ? AND book_id = ?
        ''', (session['user_id'], book_id))
        conn.commit()
    
    conn.close()
    
    # Đọc nội dung sách
    if book['file_path'] and os.path.exists(book['file_path']):
        book_content = read_book_content(book['file_path'])
    else:
        book_content = "Nội dung sách không có sẵn."
    
    return render_template('read.html', book=book, last_position=last_position, book_content=book_content)


@app.route('/add_to_library/<int:book_id>')
def add_to_library(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Kiểm tra sách đã có trong thư viện chưa
    existing = conn.execute('''
        SELECT * FROM user_library 
        WHERE user_id = ? AND book_id = ?
    ''', (session['user_id'], book_id)).fetchone()
    
    if not existing:
        conn.execute('''
            INSERT INTO user_library (user_id, book_id)
            VALUES (?, ?)
        ''', (session['user_id'], book_id))
        conn.commit()
        flash('Đã thêm sách vào thư viện!', 'success')
    else:
        flash('Sách đã có trong thư viện!', 'info')
    
    conn.close()
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/toggle_favorite/<int:book_id>')
def toggle_favorite(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Lấy trạng thái hiện tại
    user_book = conn.execute('''
        SELECT * FROM user_library 
        WHERE user_id = ? AND book_id = ?
    ''', (session['user_id'], book_id)).fetchone()
    
    if user_book:
        new_favorite = not user_book['is_favorite']
        conn.execute('''
            UPDATE user_library 
            SET is_favorite = ?
            WHERE user_id = ? AND book_id = ?
        ''', (new_favorite, session['user_id'], book_id))
        conn.commit()
        
        if new_favorite:
            flash('Đã thêm vào yêu thích!', 'success')
        else:
            flash('Đã bỏ khỏi yêu thích!', 'info')
    
    conn.close()
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/save_progress', methods=['POST'])
def save_progress():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    book_id = data.get('book_id')
    position = data.get('position', 0)
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE user_library 
        SET last_read_position = ?
        WHERE user_id = ? AND book_id = ?
    ''', (position, session['user_id'], book_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/add_note', methods=['POST'])
def add_note():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    book_id = request.form['book_id']
    content = request.form['content']
    location = request.form.get('location', '')
    highlighted_text = request.form.get('highlighted_text', '')
    
    if not content:
        flash('Nội dung ghi chú không được để trống!', 'error')
        return redirect(url_for('book_detail', book_id=book_id))
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO notes (user_id, book_id, content, location_in_book, highlighted_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (session['user_id'], book_id, content, location, highlighted_text))
    conn.commit()
    conn.close()
    
    flash('Đã thêm ghi chú!', 'success')
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/upload_book', methods=['GET', 'POST'])
def upload_book():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Lấy thông tin từ form
        title = request.form['title']
        author_name = request.form['author_name']
        publisher_name = request.form.get('publisher_name', '')
        description = request.form.get('description', '')
        publication_year = request.form.get('publication_year', type=int)
        genre_names = request.form.getlist('genres')
        
        # Kiểm tra file upload
        if 'book_file' not in request.files:
            flash('Vui lòng chọn file sách!', 'error')
            return render_template('upload_book.html')
        
        file = request.files['book_file']
        if file.filename == '':
            flash('Vui lòng chọn file sách!', 'error')
            return render_template('upload_book.html')
        
        # Kiểm tra định dạng file
        allowed_extensions = {'.pdf', '.epub', '.txt'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            flash('Chỉ hỗ trợ file PDF, EPUB và TXT!', 'error')
            return render_template('upload_book.html')
        
        # Lưu file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        conn = get_db_connection()
        
        # Thêm hoặc lấy author
        author = conn.execute('SELECT author_id FROM authors WHERE author_name = ?', (author_name,)).fetchone()
        if author:
            author_id = author['author_id']
        else:
            cursor = conn.execute('INSERT INTO authors (author_name) VALUES (?)', (author_name,))
            author_id = cursor.lastrowid
        
        # Thêm hoặc lấy publisher
        if publisher_name:
            publisher = conn.execute('SELECT publisher_id FROM publishers WHERE publisher_name = ?', (publisher_name,)).fetchone()
            if publisher:
                publisher_id = publisher['publisher_id']
            else:
                cursor = conn.execute('INSERT INTO publishers (publisher_name) VALUES (?)', (publisher_name,))
                publisher_id = cursor.lastrowid
        else:
            publisher_id = None
        
        # Thêm sách
        cursor = conn.execute('''
            INSERT INTO books (title, author_id, publisher_id, description, file_path, publication_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, author_id, publisher_id, description, file_path, publication_year))
        book_id = cursor.lastrowid
        
        # Thêm thể loại
        for genre_name in genre_names:
            if genre_name:
                # Thêm hoặc lấy genre
                genre = conn.execute('SELECT genre_id FROM genres WHERE genre_name = ?', (genre_name,)).fetchone()
                if genre:
                    genre_id = genre['genre_id']
                else:
                    cursor = conn.execute('INSERT INTO genres (genre_name) VALUES (?)', (genre_name,))
                    genre_id = cursor.lastrowid
                
                # Liên kết book với genre
                conn.execute('INSERT INTO book_genres (book_id, genre_id) VALUES (?, ?)', (book_id, genre_id))
        
        # Thêm sách vào thư viện của user upload
        conn.execute('''
            INSERT INTO user_library (user_id, book_id)
            VALUES (?, ?)
        ''', (session['user_id'], book_id))
        
        conn.commit()
        conn.close()
        
        flash('Đã upload sách thành công!', 'success')
        return redirect(url_for('book_detail', book_id=book_id))
    
    return render_template('upload_book.html')

@app.route('/search_in_book/<int:book_id>')
def search_in_book(book_id):
    """Tìm kiếm trong nội dung sách"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []})
    
    conn = get_db_connection()
    book = conn.execute('SELECT file_path FROM books WHERE book_id = ?', (book_id,)).fetchone()
    conn.close()
    
    if not book or not book['file_path']:
        return jsonify({'error': 'Book not found'}), 404
    
    # Đọc nội dung và tìm kiếm
    content = read_book_content(book['file_path'])
    lines = content.split('\n')
    results = []
    
    for i, line in enumerate(lines):
        if query.lower() in line.lower():
            results.append({
                'line_number': i + 1,
                'content': line.strip(),
                'context': ' '.join(lines[max(0, i-1):i+2])  # Hiển thị context
            })
            
            if len(results) >= 20:  # Giới hạn kết quả
                break
    
    return jsonify({'results': results, 'total': len(results)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)