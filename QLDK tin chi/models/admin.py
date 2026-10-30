import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.connection import execute_query, execute_procedure, get_connection

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

class AdminModel:
    @staticmethod
    def login_admin(username: str, password: str | None = None) -> bool:
        """
        Xác thực đăng nhập admin.
        Chỉ cần nhập tên tài khoản, không yêu cầu mật khẩu.
        """
        if not username:
            return False
        return username.strip().lower() == ADMIN_USERNAME
    
    @staticmethod
    def get_lop_hoc_phan(ma_hk: str) -> list[dict]:
        """
        Lấy danh sách các lớp HP trong 1 học kỳ.
        """
        rows = execute_query(
            "SELECT L.MaLHP, HP.MaHP, HP.TenHP, L.SiSoToiDa, L.SoLuongDangKy, "
            "(L.SiSoToiDa - L.SoLuongDangKy) AS SoChoConLai, "
            "CAST((L.SoLuongDangKy * 100.0 / NULLIF(L.SiSoToiDa, 0)) AS DECIMAL(5,2)) AS PhanTramDaDangKy "
            "FROM LopHocPhan L "
            "JOIN HocPhan HP ON L.MaHP = HP.MaHP "
            "WHERE L.MaHK = ? "
            "ORDER BY HP.MaHP, L.MaLHP",
            (ma_hk,),
        )
        return [
            {
                "MaLHP": r.MaLHP,
                "MaHP": r.MaHP,
                "TenHP": r.TenHP,
                "SiSoToiDa": r.SiSoToiDa,
                "SoLuongDangKy": r.SoLuongDangKy,
                "SoChoConLai": r.SoChoConLai,
                "PhanTramDaDangKy": float(r.PhanTramDaDangKy or 0),
            }
            for r in rows
        ]

    @staticmethod
    def set_thoi_gian_dang_ky(ma_hk: str, ngay_mo: str, ngay_dong: str) -> tuple[bool, str]:
        """
        Admin thiết lập thời gian mở và đóng đăng ký cho một học kỳ.
        ngay_mo, ngay_dong: Chuỗi ngày tháng định dạng YYYY-MM-DD HH:MM:SS
        """
        # Kiểm tra học kỳ có tồn tại không
        check = execute_query("SELECT MaHK FROM HocKy WHERE MaHK = ?", (ma_hk,))
        if not check:
            return False, f"Học kỳ {ma_hk} không tồn tại."
        
        try:
            execute_query(
                "UPDATE HocKy SET NgayMoDangKy = ?, NgayDongDangKy = ? WHERE MaHK = ?",
                (ngay_mo, ngay_dong, ma_hk),
                fetch=False
            )
            return True, "Cập nhật thời gian đăng ký thành công."
        except Exception as e:
            return False, f"Lỗi khi cập nhật thời gian: {e}"

    @staticmethod
    def lay_thoi_gian_dang_ky(ma_hk: str) -> dict | None:
        """
        Lấy thông tin thời gian mở/đóng đăng ký của một học kỳ.
        """
        rows = execute_query(
            "SELECT NgayMoDangKy, NgayDongDangKy FROM HocKy WHERE MaHK = ?", 
            (ma_hk,)
        )
        if rows:
            return {
                "NgayMoDangKy": str(rows[0].NgayMoDangKy) if rows[0].NgayMoDangKy else None,
                "NgayDongDangKy": str(rows[0].NgayDongDangKy) if rows[0].NgayDongDangKy else None
            }
        return None

 
    @staticmethod
    def get_all_hoc_phan(ma_hk: str = "ALL") -> list[dict]:
        if ma_hk == "ALL" or not ma_hk:
            rows = execute_query("SELECT MaHP, TenHP, SoTinChi, BatBuoc FROM HocPhan WITH (NOLOCK) ORDER BY MaHP")
        else:
            rows = execute_query("""
                SELECT HP.MaHP, HP.TenHP, HP.SoTinChi, HP.BatBuoc 
                FROM HocPhan HP WITH (NOLOCK)
                JOIN LopHocPhan L WITH (NOLOCK) ON HP.MaHP = L.MaHP
                WHERE L.MaHK = ?
                ORDER BY HP.MaHP
            """, (ma_hk,))
            
        return [
            {
                "MaHP": r.MaHP,
                "TenHP": r.TenHP,
                "SoTinChi": r.SoTinChi,
                "BatBuoc": bool(r.BatBuoc)
            }
            for r in rows
        ]

    @staticmethod
    def them_hoc_phan(ma_hp: str, ten_hp: str, tc: int, bb: bool, ma_hk_demo: str = None) -> tuple[bool, str]:
        try:
            execute_query(
                "INSERT INTO HocPhan (MaHP, TenHP, SoTinChi, BatBuoc) VALUES (?, ?, ?, ?)",
                (ma_hp, ten_hp, tc, 1 if bb else 0),
                fetch=False
            )
            # Dành cho Demo Phantom Read: Tạo sẵn 1 lớp ảo để sinh viên có thể thấy ngay
            if ma_hk_demo and ma_hk_demo != "ALL":
                try:
                    execute_query(
                        "INSERT INTO LopHocPhan (MaLHP, MaHP, MaHK, SoLuongDangKy, SiSoToiDa) VALUES (?, ?, ?, 0, 50)",
                        (f"{ma_hp}_DEMO", ma_hp, ma_hk_demo),
                        fetch=False
                    )
                except Exception as e:
                    print(f"Lỗi tạo lớp demo: {e}")
            return True, "Thêm học phần thành công."
        except Exception as e:
            return False, f"Lỗi khi thêm: {e}"

    @staticmethod
    def xoa_hoc_phan(ma_hp: str) -> tuple[bool, str]:
        try:
            execute_query("DELETE FROM HocPhan WHERE MaHP = ?", (ma_hp,), fetch=False)
            return True, "Xóa học phần thành công."
        except Exception as e:
            return False, f"Lỗi khi xóa (Có thể môn này đã có lớp HP, dính khóa ngoại): {e}"

    @staticmethod
    def start_update_hoc_phan_dirty_read(ma_hp: str, ten_hp: str, tc: int, bb: bool):
        """
        Khởi tạo kết nối, chạy UPDATE, nhưng KHÔNG COMMIT. Trả về đối tượng connection
        để UI có thể hiện Popup hỏi Yes/No rồi mới quyết định Commit/Rollback.
        Trả về (connection_object, message)
        """

        conn = get_connection()
        if not conn:
            return None, "Không thể kết nối CSDL."
        
        try:
            conn.autocommit = False # Bắt đầu Transaction
            cur = conn.cursor()
            # Thực thi UPDATE
            cur.execute(
                "UPDATE HocPhan SET TenHP = ?, SoTinChi = ?, BatBuoc = ? WHERE MaHP = ?",
                (ten_hp, tc, 1 if bb else 0, ma_hp)
            )
            # Lúc này DB đã ghi nhận thay đổi (trong transaction đang chờ)
            # Nếu view của sinh viên dùng WITH (NOLOCK), họ sẽ đọc được dữ liệu này (Dirty Read)
            return conn, "Đã tạm lưu thay đổi vào DB. Đang chờ xác nhận Commit."
        except Exception as e:
            conn.close()
            return None, f"Lỗi SQL: {e}"

    @staticmethod
    def get_all_lop_hoc_phan_demo() -> list[dict]:
        """Lấy danh sách lớp học phần để dùng trong UI demo Dirty Read."""
        rows = execute_query(
            "SELECT MaLHP, MaHP, MaHK FROM LopHocPhan ORDER BY MaHK, MaLHP"
        )
        return [{"MaLHP": r.MaLHP, "MaHP": r.MaHP, "MaHK": r.MaHK} for r in rows]

    @staticmethod
    def get_all_sinh_vien_demo() -> list[dict]:
        """Lấy danh sách sinh viên để dùng trong UI demo Dirty Read."""
        rows = execute_query(
            "SELECT MaSV, HoTen FROM SinhVien ORDER BY MaSV"
        )
        return [{"MaSV": r.MaSV, "HoTen": r.HoTen or ""} for r in rows]

    @staticmethod
    def get_chi_tiet_lop_hoc_phan(ma_lhp: str) -> list[dict]:
        """Lấy các dòng chi tiết lịch học của một lớp học phần để admin chỉnh sửa."""
        rows = execute_query(
            "SELECT MaCTLHP, MaLHP, NgayBatDau, NgayKetThuc, ThuHoc, CaHoc, PhongHoc "
            "FROM ChiTietLopHocPhan WHERE MaLHP = ? ORDER BY MaCTLHP",
            (ma_lhp,),
        )
        return [
            {
                "MaCTLHP": r.MaCTLHP,
                "MaLHP": r.MaLHP,
                "NgayBatDau": str(r.NgayBatDau) if r.NgayBatDau else "",
                "NgayKetThuc": str(r.NgayKetThuc) if r.NgayKetThuc else "",
                "ThuHoc": r.ThuHoc or "",
                "CaHoc": r.CaHoc or "",
                "PhongHoc": r.PhongHoc or "",
            }
            for r in rows
        ]

    @staticmethod
    def update_chi_tiet_lop_hoc_phan(ma_ctlhp: str, thu_hoc: str, ca_hoc: str, phong_hoc: str) -> tuple[bool, str]:
        """Cập nhật một dòng chi tiết lịch học của lớp học phần."""
        try:
            execute_query(
                "UPDATE ChiTietLopHocPhan SET ThuHoc = ?, CaHoc = ?, PhongHoc = ? WHERE MaCTLHP = ?",
                (thu_hoc, ca_hoc, phong_hoc, ma_ctlhp),
                fetch=False,
            )
            return True, "Cập nhật lịch học thành công."
        except Exception as e:
            return False, f"Lỗi khi cập nhật lịch học: {e}"

    @staticmethod
    def start_update_chi_tiet_lop_hoc_phan_dirty_read(changes: list[dict]):
        """Cập nhật chi tiết lịch học trong một transaction chưa commit để demo Dirty Read."""
        conn = get_connection()
        if not conn:
            return None, "Không thể kết nối đến CSDL."

        try:
            conn.autocommit = False
            cur = conn.cursor()
            for change in changes:
                cur.execute(
                    "UPDATE ChiTietLopHocPhan SET ThuHoc = ?, CaHoc = ?, PhongHoc = ? WHERE MaCTLHP = ?",
                    (change["ThuHoc"], change["CaHoc"], change["PhongHoc"], change["MaCTLHP"]),
                )
            return conn, f"Đã ghi {len(changes)} dòng vào transaction chưa commit."
        except Exception as e:
            try:
                conn.close()
            except Exception:
                pass
            return None, f"Lỗi khi cập nhật lịch học: {e}"

    @staticmethod
    def demo_dirty_read_admin(ma_lhp: str, thu_hoc: str) -> tuple[bool, str]:
        """Kích hoạt demo Dirty Read phía admin bằng stored procedure đã có."""
        ok, msg, rows, err_code = execute_procedure(
            "sp_Demo_DirtyRead_Admin",
            (ma_lhp, thu_hoc),
        )
        if ok:
            return True, f"Đã kích hoạt demo Dirty Read cho lớp {ma_lhp}."
        return False, msg or "Lỗi khi kích hoạt demo Dirty Read."

    @staticmethod
    def demo_dirty_read_sinh_vien(ma_sv: str) -> list[dict]:
        """Gọi stored procedure của sinh viên để xem lịch học trong demo Dirty Read."""
        ok, msg, rows, err_code = execute_procedure(
            "sp_Demo_DirtyRead_SinhVien",
            (ma_sv,),
        )
        if not ok:
            return []
        return [
            {
                "MaSV": r.MaSV,
                "HoTen": r.HoTen or "",
                "TenHP": r.TenHP or "",
                "MaLHP": r.MaLHP or "",
                "ThuHoc": r.ThuHoc or "",
                "CaHoc": r.CaHoc or "",
                "PhongHoc": r.PhongHoc or "",
            }
            for r in rows
        ]

    @staticmethod
    def demo_deadlock_admin(ma_hk: str, ten_hk: str, nam_hoc: int, ngay_mo: str, ngay_dong: str) -> tuple[bool, str]:
        """
        Demo lỗi Deadlock: Admin cập nhật thời gian Học Kỳ.
        """
        ok, msg, rows, err_code = execute_procedure(
            "sp_Demo_Deadlock_Admin",
            (ma_hk, ten_hk, nam_hoc, ngay_mo, ngay_dong),
        )
        
        if err_code == "DEADLOCK" or "deadlock" in msg.lower():
            return False, "Error 1205: Transaction was deadlocked... Bị hệ thống hủy để giải phóng bế tắc."
            
        if rows:
            r = rows[0]
            return bool(getattr(r, 'Success', ok)), getattr(r, 'Message', msg)
        return ok, msg
