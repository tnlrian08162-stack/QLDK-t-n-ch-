import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QRadioButton, QButtonGroup, 
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from models.sinh_vien import SinhVien
from models.admin import AdminModel

class LoginWindow(QWidget):
    # Phát tín hiệu khi đăng nhập thành công. Truyền vào: role ('student' hoặc 'admin'), và username (nếu là student thì là ma_sv)
    login_successful = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hệ thống Đăng ký Học phần - Đăng nhập")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Tiêu đề
        lbl_title = QLabel("ĐĂNG NHẬP HỆ THỐNG")
        lbl_title.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 16, QFont.Bold)
        lbl_title.setFont(title_font)
        main_layout.addWidget(lbl_title)

        # Khung chọn Vai trò
        role_layout = QHBoxLayout()
        lbl_role = QLabel("Vai trò:")
        self.rb_student = QRadioButton("Sinh viên")
        self.rb_admin = QRadioButton("Nhà trường")
        
        self.rb_student.setChecked(True) # Mặc định là sinh viên

        self.role_group = QButtonGroup(self)
        self.role_group.addButton(self.rb_student)
        self.role_group.addButton(self.rb_admin)

        role_layout.addWidget(lbl_role)
        role_layout.addWidget(self.rb_student)
        role_layout.addWidget(self.rb_admin)
        role_layout.addStretch()
        main_layout.addLayout(role_layout)

        # Khung nhập Tài khoản
        user_layout = QHBoxLayout()
        lbl_user = QLabel("Tài khoản:")
        lbl_user.setFixedWidth(80)
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("Nhập mã SV hoặc admin...")
        user_layout.addWidget(lbl_user)
        user_layout.addWidget(self.txt_username)
        main_layout.addLayout(user_layout)

        # Nút Đăng nhập
        self.btn_login = QPushButton("ĐĂNG NHẬP")
        btn_font = QFont("Arial", 12, QFont.Bold)
        self.btn_login.setFont(btn_font)
        self.btn_login.setMinimumHeight(40)
        self.btn_login.setStyleSheet("background-color: #0078D7; color: white; border-radius: 5px;")
        self.btn_login.clicked.connect(self.handle_login)
        main_layout.addWidget(self.btn_login)

        # Label hiển thị lỗi
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: red;")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.lbl_error)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def handle_login(self):
        self.lbl_error.setText("")
        username = self.txt_username.text().strip()

        if not username:
            self.lbl_error.setText("Vui lòng nhập tài khoản!")
            return

        is_student = self.rb_student.isChecked()

        try:
            if is_student:
                # Đăng nhập Sinh viên
                success = SinhVien.login(username)
                if success:
                    QMessageBox.information(self, "Thành công", f"Đăng nhập thành công với vai trò Sinh viên!\n(Tài khoản: {username})")
                    self.login_successful.emit('student', username)
                else:
                    self.lbl_error.setText("Mã sinh viên không đúng!")
            else:
                # Đăng nhập Nhà trường
                success = AdminModel.login_admin(username)
                if success:
                    QMessageBox.information(self, "Thành công", f"Đăng nhập thành công với vai trò Nhà trường!\n(Tài khoản: {username})")
                    self.login_successful.emit('admin', username)
                else:
                    self.lbl_error.setText("Tài khoản admin không đúng!")
        except Exception as e:
            self.lbl_error.setText(f"Lỗi kết nối CSDL: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
