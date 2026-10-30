import sys
import os
import traceback


# Thêm thư mục gốc vào sys.path để import các module con
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PyQt5.QtWidgets import QApplication
from ui.login_window import LoginWindow
from ui.school_window import SchoolWindow
from ui.student_window import StudentWindow


class AppController:
    """Bộ điều phối trung tâm: quản lý vòng đời các cửa sổ."""

    def __init__(self, app: QApplication):
        self.app = app
        self.main_window = None   # Giữ tham chiếu để app không tắt
        self.login_win = LoginWindow()
        self.login_win.login_successful.connect(self.on_login_success)
        self.login_win.show()

    def on_login_success(self, role: str, username: str): 
        """login windown -> pick role(admin or student)"""
        self.login_win.hide() 

        try:
            if role == "admin":
                self.main_window = SchoolWindow()
            else:
                self.main_window = StudentWindow(ma_sv=username)
            
            self.main_window.destroyed.connect(self._on_main_window_closed)
            self.main_window.show()

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.login_win,
                "Lỗi",
                f"Không thể mở cửa sổ {role}:\n{e}"
            )
            self.login_win.show()

    def _on_main_window_closed(self):
        """Khi cửa sổ chính bị đóng, hiện lại Login để đăng nhập lại."""
        self.main_window = None
        # Reset form login trước khi hiện lại
        self.login_win.txt_username.clear()
        self.login_win.lbl_error.setText("")
        self.login_win.show()


def main():
    if sys.stdout and hasattr(sys.stdout, "encoding") and sys.stdout.encoding:
        if sys.stdout.encoding.lower() != "utf-8":
            try:
                sys.stdout.reconfigure(encoding="utf-8")
            except (AttributeError, Exception):
                pass
    app = QApplication(sys.argv)
    app.setApplicationName("Hệ thống Đăng ký Học phần")
    app.setStyle("Fusion")   # Giao diện nhất quán trên mọi Windows version
    controller = AppController(app)   # Giữ controller sống trong suốt app
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
