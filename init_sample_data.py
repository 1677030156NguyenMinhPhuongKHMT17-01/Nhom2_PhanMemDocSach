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
    # Nội dung được nhân bản để tạo độ dài cho việc kiểm thử (khoảng 100 lần)
    kieu_content = '''Trăm năm trong cõi người ta,
Chữ tài chữ mệnh khéo là ghét nhau.
Trải qua một cuộc bể dâu,
Những điều trông thấy mà đau đớn lòng.
Lạ gì bỉ sắc tư phong,
Trời xanh quen thói má hồng đánh ghen.
Cảo thơm lần giở trước đèn,
Phong tình cổ lục còn truyền sử xanh.
Rằng năm Gia Tĩnh triều Minh,
Bốn phương phẳng lặng, hai kinh vững vàng.
Có nhà viên ngoại họ Vương,
Gia tư nghỉ cũng thường thường bậc trung.
Một trai con thứ rốt lòng,
Vương Quan là chữ, nối dòng nho gia.
Đầu lòng hai ả tố nga,
Thúy Kiều là chị, em là Thúy Vân.
Mai cốt cách, tuyết tinh thần,
Mỗi người một vẻ, mười phân vẹn mười.
Vân xem trang trọng khác vời,
Khuôn trăng đầy đặn, nét ngài nở nang.
Hoa cười ngọc thốt đoan trang,
Mây thua nước tóc, tuyết nhường màu da.
Kiều càng sắc sảo, mặn mà,
So bề tài sắc, lại là phần hơn.
Làn thu thủy, nét xuân sơn,
Hoa ghen thua thắm, liễu hờn kém xanh.
Một, hai nghiêng nước nghiêng thành,
Sắc đành đòi một, tài đành họa hai.
Thông minh vốn sẵn tính trời,
Pha nghề thi họa, đủ mùi ca ngâm.
Cung thương làu bậc ngũ âm,
Nghề riêng ăn đứt hồ cầm một trương.
Khúc nhà tay lựa nên chương,
Một thiên bạc mệnh, lại càng não nhân.
Phong lưu rất mực hồng quần,
Xuân xanh xấp xỉ tới tuần cập kê.
Êm đềm trướng rủ màn che,
Tường đông ong bướm đi về mặc ai.
''' * 100

    chi_pheo_content = '''CHƯƠNG I

Hắn vừa đi vừa chửi. Bao giờ cũng thế. Bao giờ hắn cũng chửi. Bắt đầu hắn chửi trời. Có hề gì? Trời có của riêng nhà nào? Rồi hắn chửi đời. Thế cũng chẳng sao: đời là tất cả nhưng chẳng là ai. Tức mình, hắn chửi ngay tất cả làng Vũ Đại. Nhưng cả làng Vũ Đại ai cũng nhủ: "Chắc nó trừ mình ra!". Không ai lên tiếng cả. Tức thật! Ồ! Thế này thì tức thật! Tức chết đi được mất! Đã thế, hắn phải chửi cha đứa nào không chửi nhau với hắn. Nhưng cũng không ai ra điều. Mẹ kiếp! Thế có phí rượu không? Thế thì có khổ hắn không? Không biết đứa chết mẹ nào lại đẻ ra thân hắn cho hắn khổ đến nông nỗi này? A ha! Phải đấy hắn cứ thế mà chửi, hắn cứ chửi đứa chết mẹ nào đẻ ra thân hắn, đẻ ra cái thằng Chí Phèo! Hắn nghiến răng vào mà chửi cái đứa đã đẻ ra Chí Phèo. Nhưng mà biết đứa nào đã đẻ ra Chí Phèo? Có mà trời biết! Hắn không biết, cả làng Vũ Đại cũng không ai biết...

Hắn về lớp này trông khác hẳn, mới đầu chẳng ai biết hắn là ai. Trông đặc như thằng sắng cá! Cái đầu thì trọc lốc, cái răng cạo trắng hớn, cái mặt thì đen mà rất cơng cơng, hai mắt gườm gườm trông gớm chết! Hắn mặc cái quần nái đen với cái áo tây vàng. Cái ngực phanh, đầy những nét chạm trổ rồng phượng với một ông tướng cầm chùy, cả hai cánh tay cũng thế. Trông gớm chết!

Hắn về hôm trước, hôm sau đã thấy ngồi ở chợ uống rượu với thịt chó suốt từ trưa đến xế chiều. Rồi say khướt, hắn xách một cái vỏ chai đến cổng nhà bá Kiến, gọi tận tên tục ra mà chửi. Cụ bá không có nhà. Thấy điệu bộ hung hăng của hắn, bà cả đùn bà hai, bà hai thúc bà ba, bà ba gọi bà tư, nhưng kết cục chẳng bà nào dám ra nói với hắn một vài lời phải chăng. Mắc cái phải cái thằng liều lĩnh lại say rượu, tay nó lại lăm lăm cầm một cái vỏ chai, mà nhà lúc ấy toàn đàn bà con trẻ... Thôi thì cứ đóng cái cổng cho thật chặt, rồi mặc thây cha nó, nó chửi thì tai liền miệng đấy, chửi rồi lại nghe! Thành thử chỉ có ba con chó dữ với một thằng say rượu! Thật là ầm ĩ! Hàng xóm phải một phen điếc tai, nhưng có lẽ trong bụng thì họ hả: xưa nay họ mới chỉ được nghe bà cả, bà hai, bà ba, bà tư nhà cụ bá chửi người ta, bây giờ họ mới được xem người ta chửi lại cả nhà cụ bá. Mà chửi mới sướng miệng làm sao! Mới ngoa ngoắt làm sao! Họ bảo nhau: "Phen này cha con thằng bá Kiến đố còn dám vác mặt đi đâu nữa!". Mồ mả tổ tiên đến lộn lên mất.
''' * 100

    de_men_content = '''CHƯƠNG MỘT
DẾ MÈN VÀ CUỘC SỐNG Ở QUÊ NHÀ

Tôi sống độc lập từ thuở bé. Ấy là tục lệ lâu đời trong họ nhà dế chúng tôi. Vả lại, mẹ thường bảo chúng tôi rằng: "Phải như thế để các con biết kiếm ăn một mình cho quen đi. Con cái mà cứ nhong nhóng ăn bám vào bố mẹ thì chỉ sinh ra tính ỷ lại, xấu lắm, rồi ra đời không làm nên trò trống gì đâu".

Bởi thế, lứa sinh ấy, chúng tôi có ba anh em, mẹ cho ra ở riêng cả. Mẹ đưa ba anh em ra đi, mỗi đứa vào một cái hang đất ở bờ ruộng, phía bên kia bờ nước.

Khi mẹ bảo tôi: "Giờ con đã lớn rồi, con phải ra ở riêng thôi", tôi vâng lời mẹ và cảm thấy rất vui sướng. Tôi nghĩ rằng từ nay mình được tự do, muốn làm gì thì làm, muốn đi đâu thì đi, không ai quản lý nữa.

Tôi đào hang sâu, làm nhiều ngách để phòng khi có kẻ thù tấn công. Hàng ngày tôi đi kiếm ăn, ăn uống điều độ và làm việc có chừng mực nên tôi chóng lớn lắm. Chẳng bao lâu, tôi đã trở thành một chàng dế thanh niên cường tráng. Đôi càng tôi mẫm bóng. Những cái vuốt ở chân, ở khoeo cứ cứng dần và nhọn hoắt. Thỉnh thoảng, muốn thử sự lợi hại của những chiếc vuốt, tôi co cẳng lên, đạp phanh phách vào các ngọn cỏ. Những ngọn cỏ gãy rạp y như có nhát dao vừa lia qua. Đôi cánh tôi, trước kia ngắn hủn hoẳn, bây giờ thành cái áo dài kín xuống tận chấm đuôi. Mỗi khi tôi vũ lên, đã nghe tiếng phành phạch giòn giã. Lúc tôi đi bách bộ thì cả người tôi rung rinh một màu nâu bóng mỡ soi gương được và rất ưa nhìn. Đầu tôi to ra và nổi từng tảng, rất bướng. Hai cái răng đen nhánh lúc nào cũng nhai ngoàm ngoạp như hai lưỡi liềm máy làm việc. Sợi râu tôi dài và uốn cong một vẻ rất đỗi hùng dũng. Tôi lấy làm hãnh diện với bà con về cặp râu ấy lắm. Cứ chốc chốc tôi lại trịnh trọng và khoan thai đưa cả hai chân lên vuốt râu.
''' * 100

    sample_books = [
        {
            'title': 'Truyện Kiều',
            'content': kieu_content,
            'author': 'Nguyễn Du',
            'publisher': 'NXB Văn học',
            'cover_image': '/static/covers/TruyenKieu.jpg'
        },
        {
            'title': 'Chí Phèo',
            'content': chi_pheo_content,
            'author': 'Nam Cao',
            'publisher': 'NXB Văn học',
            'cover_image': '/static/covers/ChiPheo.jpg'
        },
        {
            'title': 'Dế Mèn Phiêu Lưu Ký',
            'content': de_men_content,
            'author': 'Tô Hoài',
            'publisher': 'NXB Kim Đồng',
            'cover_image': '/static/covers/DMPLK.jpg'
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
            INSERT OR IGNORE INTO books (title, author_id, publisher_id, description, file_path, publication_year, cover_image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (book_data['title'], author_id, publisher_id, 
              f"Tác phẩm kinh điển của {book_data['author']}", 
              filepath, 2024, book_data['cover_image']))
        
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