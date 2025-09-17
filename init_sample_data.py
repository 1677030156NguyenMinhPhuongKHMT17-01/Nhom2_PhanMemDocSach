"""
Script để thêm dữ liệu mẫu vào database
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

def init_sample_data():
    # Kết nối database
    conn = sqlite3.connect('ebook_library.db')
    cursor = conn.cursor()
    
    # Tạo thư mục uploads nếu chưa có
    os.makedirs('static/uploads', exist_ok=True)
    
    # Thêm user mẫu
    password_hash = generate_password_hash('123456')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, full_name)
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin@example.com', password_hash, 'Admin User'))
    
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash, full_name)
        VALUES (?, ?, ?, ?)
    ''', ('user1', 'user1@example.com', password_hash, 'Nguyễn Văn A'))
    
    # Thêm tác giả mẫu
    authors = [
        ('Nguyễn Du',),
        ('Nam Cao',),
        ('Vũ Trọng Phụng',),
        ('Tô Hoài',),
        ('Ngô Tất Tố',),
        ('Dale Carnegie',),
        ('Napoleon Hill',),
        ('Robert Kiyosaki',)
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO authors (author_name) VALUES (?)', authors)
    
    # Thêm nhà xuất bản mẫu
    publishers = [
        ('NXB Trẻ',),
        ('NXB Kim Đồng',),
        ('NXB Văn học',),
        ('NXB Giáo dục',),
        ('NXB Thế giới',)
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO publishers (publisher_name) VALUES (?)', publishers)
    
    # Thêm thể loại mẫu
    genres = [
        ('Văn học',),
        ('Tiểu thuyết',),
        ('Truyện ngắn',),
        ('Tự lực',),
        ('Kinh doanh',),
        ('Tâm lý học',),
        ('Lịch sử',),
        ('Khoa học',)
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO genres (genre_name) VALUES (?)', genres)
    
    # Tạo file text mẫu
    sample_books = [
        {
            'title': 'Truyện Kiều',
            'content': '''Chính văn

Trăm năm trong cõi người ta,
Chữ tài chữ mệnh khéo là ghét nhau.
Trải qua một cuộc bể dâu,
Những điều trông thấy mà đau đớn lòng.
Lạ gì bỉ sắc tư phong,
Trời xanh quen thói má hồng đánh ghen.

Cảm khái ngày nay còn mới,
Lời đêm mà gửi tình tôi hay chi?
Dù ai đọc cuộc tình si,
Dẫu là hiền nữ thì gì mà không?

Nguyên tiêu gặp nạn trong nhà,
Chuyện tình cảm không tả bằng lời...

(Tóm tắt nội dung và bối cảnh lịch sử của tác phẩm)
Truyện Kiều là tác phẩm kinh điển của văn học Việt Nam, được sáng tác bởi đại thi hào Nguyễn Du vào đầu thế kỷ 19. Tác phẩm kể về số phận của nàng Thúy Kiều, một cô gái tài sắc vẹn toàn nhưng phải chịu nhiều khổ đau trong cuộc đời.

Với 3.254 câu thơ lục bát, Truyện Kiều không chỉ là một tác phẩm văn học xuất sắc mà còn là bức tranh phản ánh sâu sắc về xã hội phfeudal Việt Nam, về số phận người phụ nữ trong chế độ phong kiến.''',
            'author': 'Nguyễn Du',
            'publisher': 'NXB Văn học'
        },
        {
            'title': 'Chí Phèo',
            'content': '''CHƯƠNG I

Hắn vừa đi vừa chửi. Bao giờ cũng thế. Bao giờ hắn cũng chửi.

Trước hắn chửi ông địa chủ mình làm cho hắn khổ. Bây giờ ông địa chủ chết rồi hắn chửi thằng con ông địa chủ - thằng Lý Kiều.

Rồi hắn chửi đời, chửi trời, chửi cả những thằng cầm quyền, chửi luôn cả thằng khốn nào bắt mình phải sống, chửi cả bọn xóm giềng hay tụ lại mà xầm xì về hắn.

"Thôi được! Được hết! Tao biết tao là ai! Tao là Chí Phèo!"

Rồi hắn lại chửi lũ đàn bà đàn ông ngoài đằng kia.

"Bây giờ tao khổ thế này cũng tại mẹ những con điên như các mi!"

Hắn chửi vậy và hắn nghỉ ở bệ cầu.

Chí Phèo là một nhân vật tiêu biểu cho số phận của nông dân nghèo trong xã hội thực dân phong kiến. Qua hình tượng Chí Phèo, Nam Cao đã phản ánh sâu sắc về thực trạng xã hội và số phận con người thời bấy giờ.''',
            'author': 'Nam Cao',
            'publisher': 'NXB Văn học'
        },
        {
            'title': 'Dế Mèn Phiêu Lưu Ký',
            'content': '''CHƯƠNG MỘT
DẾ MÈN VÀ CUỘC SỐNG Ở QUÊ NHÀG

Trong một cái hang nho nhỏ ở chân cái sển cây khế, có một con dế mèn tên là Dế Mèn. Hang nó ở khá kín đáo, có lối vào nhỏ thò thế mà trong lại rộng rãi và thoáng mát.

Dế Mèn là một chú dế khoẻ mạnh và vui tính. Nó có cặp đùi to khỏe, hai cái càng cứng cáp và đôi râu dài lúc nào cũng đung đưa. Màu áo của nó nâu xám, trông rất đẹp và bắt mắt.

Hàng ngày, Dế Mèn thức dậy từ sớm. Nó rời hang ra ngoài, hít thở không khí trong lành của buổi sáng và tìm kiếm thức ăn cho mình.

Trong truyện này, Tô Hoài đã tạo nên một thế giới đầy màu sắc và hấp dẫn cho các bạn nhỏ, qua đó truyền tải những bài học về tình bạn, lòng can đảm và tinh thần phiêu lưu khám phá.''',
            'author': 'Tô Hoài',
            'publisher': 'NXB Kim Đồng'
        }
    ]
    
    # Tạo file và thêm sách vào database
    for book_data in sample_books:
        # Tạo file nội dung
        filename = f"{book_data['title'].replace(' ', '_')}.txt"
        filepath = os.path.join('static/uploads', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(book_data['content'])
        
        # Lấy ID tác giả và nhà xuất bản
        author_id = cursor.execute('SELECT author_id FROM authors WHERE author_name = ?', 
                                 (book_data['author'],)).fetchone()[0]
        publisher_id = cursor.execute('SELECT publisher_id FROM publishers WHERE publisher_name = ?', 
                                    (book_data['publisher'],)).fetchone()[0]
        
        # Thêm sách
        cursor.execute('''
            INSERT OR IGNORE INTO books (title, author_id, publisher_id, description, file_path, publication_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (book_data['title'], author_id, publisher_id, 
              f"Tác phẩm kinh điển của {book_data['author']}", 
              filepath, 2024))
        
        book_id = cursor.lastrowid
        
        # Thêm thể loại cho sách
        genre_id = cursor.execute('SELECT genre_id FROM genres WHERE genre_name = ?', 
                                ('Văn học',)).fetchone()[0]
        cursor.execute('INSERT OR IGNORE INTO book_genres (book_id, genre_id) VALUES (?, ?)', 
                      (book_id, genre_id))
    
    conn.commit()
    conn.close()
    print("Đã thêm dữ liệu mẫu thành công!")

if __name__ == '__main__':
    init_sample_data()