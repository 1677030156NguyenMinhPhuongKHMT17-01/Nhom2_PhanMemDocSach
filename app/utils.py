"""
Các utility functions cho ứng dụng EBook Reader
"""
import os
import PyPDF2
import ebooklib
from ebooklib import epub
import html2text
from werkzeug.utils import secure_filename
from .config import Config

class FileProcessor:
    """Class xử lý các file sách"""
    
    @staticmethod
    def is_allowed_file(filename):
        """Kiểm tra định dạng file có được hỗ trợ không"""
        if not filename:
            return False
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_safe_filename(filename):
        """Tạo tên file an toàn"""
        return secure_filename(filename)
    
    @staticmethod
    def save_uploaded_file(file, upload_folder):
        """Lưu file upload và trả về đường dẫn"""
        if not file or file.filename == '':
            return None
        
        if not FileProcessor.is_allowed_file(file.filename):
            raise ValueError("Định dạng file không được hỗ trợ")
        
        # Tạo thư mục nếu chưa có
        os.makedirs(upload_folder, exist_ok=True)
        
        # Tạo tên file an toàn
        filename = FileProcessor.get_safe_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        
        # Lưu file
        file.save(file_path)
        return file_path

class BookContentReader:
    """Class đọc nội dung sách từ các định dạng khác nhau"""
    
    @staticmethod
    def read_book_content(file_path):
        """Đọc nội dung sách từ file PDF, EPUB hoặc TXT"""
        if not os.path.exists(file_path):
            return "File không tồn tại."
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.pdf':
                return BookContentReader._read_pdf_content(file_path)
            elif file_extension == '.epub':
                return BookContentReader._read_epub_content(file_path)
            elif file_extension == '.txt':
                return BookContentReader._read_txt_content(file_path)
            else:
                return "Định dạng file không được hỗ trợ."
        except Exception as e:
            return f"Lỗi khi đọc file: {str(e)}"
    
    @staticmethod
    def _read_pdf_content(file_path):
        """Đọc nội dung từ file PDF"""
        content = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                # Thêm cảnh báo về chất lượng đọc PDF
                content += "=" * 80 + "\n"
                content += "LƯU Ý: Nội dung PDF được trích xuất tự động có thể không chính xác 100%.\n"
                content += "Nếu văn bản hiển thị lỗi, vui lòng sử dụng file EPUB hoặc TXT.\n"
                content += f"Tổng số trang: {total_pages}\n"
                content += "=" * 80 + "\n\n"
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text.strip():  # Chỉ thêm nếu có nội dung
                        content += f"--- Trang {page_num + 1} ---\n"
                        content += page_text + "\n\n"
                    else:
                        content += f"--- Trang {page_num + 1} (Không thể trích xuất text - có thể là ảnh) ---\n\n"
                        
        except Exception as e:
            raise Exception(f"Lỗi đọc file PDF: {str(e)}")
        
        if not content.strip():
            return "Không thể trích xuất nội dung từ file PDF này. File có thể chứa toàn bộ hình ảnh hoặc được bảo vệ."
            
        return content
    
    @staticmethod
    def _read_epub_content(file_path):
        """Đọc nội dung từ file EPUB"""
        try:
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
        except Exception as e:
            raise Exception(f"Lỗi đọc file EPUB: {str(e)}")
        return content
    
    @staticmethod
    def _read_txt_content(file_path):
        """Đọc nội dung từ file TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Thử với encoding khác nếu UTF-8 fail
            try:
                with open(file_path, 'r', encoding='cp1252') as file:
                    return file.read()
            except Exception as e:
                raise Exception(f"Lỗi đọc file TXT: {str(e)}")
        except Exception as e:
            raise Exception(f"Lỗi đọc file TXT: {str(e)}")

class BookSearcher:
    """Class tìm kiếm trong nội dung sách"""
    
    @staticmethod
    def search_in_content(content, query, max_results=None):
        """Tìm kiếm trong nội dung sách"""
        if not query or not content:
            return []
        
        max_results = max_results or Config.MAX_SEARCH_RESULTS
        lines = content.split('\n')
        results = []
        
        query_lower = query.lower()
        
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                results.append({
                    'line_number': i + 1,
                    'content': line.strip(),
                    'context': BookSearcher._get_line_context(lines, i)
                })
                
                if len(results) >= max_results:
                    break
        
        return results
    
    @staticmethod
    def _get_line_context(lines, line_index, context_size=1):
        """Lấy context xung quanh dòng tìm thấy"""
        start = max(0, line_index - context_size)
        end = min(len(lines), line_index + context_size + 1)
        context_lines = lines[start:end]
        return ' '.join(line.strip() for line in context_lines if line.strip())

class ValidationHelper:
    """Class helper cho validation"""
    
    @staticmethod
    def validate_required_fields(data, required_fields):
        """Kiểm tra các field bắt buộc"""
        missing_fields = []
        for field in required_fields:
            if not data.get(field) or str(data.get(field)).strip() == '':
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_email(email):
        """Kiểm tra định dạng email cơ bản"""
        if not email:
            return False
        return '@' in email and '.' in email.split('@')[-1]
    
    @staticmethod
    def validate_username(username):
        """Kiểm tra username hợp lệ"""
        if not username:
            return False
        # Username phải có ít nhất 3 ký tự, chỉ chứa chữ cái, số và underscore
        if len(username) < 3:
            return False
        return username.replace('_', '').isalnum()
    
    @staticmethod
    def validate_password(password):
        """Kiểm tra password mạnh"""
        if not password:
            return False, "Mật khẩu không được để trống"
        
        if len(password) < 6:
            return False, "Mật khẩu phải có ít nhất 6 ký tự"
        
        return True, "Mật khẩu hợp lệ"

class FlashMessageHelper:
    """Class helper cho flash messages"""
    
    @staticmethod
    def get_flash_category_class(category):
        """Lấy CSS class cho flash message category"""
        category_map = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }
        return category_map.get(category, 'alert-info')

class DirectoryHelper:
    """Class helper cho thao tác thư mục"""
    
    @staticmethod
    def ensure_directories_exist():
        """Đảm bảo các thư mục cần thiết tồn tại"""
        directories = [
            Config.UPLOAD_FOLDER,
            Config.COVERS_FOLDER
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def get_file_size_mb(file_path):
        """Lấy kích thước file tính bằng MB"""
        if not os.path.exists(file_path):
            return 0
        return os.path.getsize(file_path) / (1024 * 1024)
    
    @staticmethod
    def delete_file_safe(file_path):
        """Xóa file an toàn"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False