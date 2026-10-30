import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from database.connection import execute_query, execute_procedure

class SinhVien:
    """Đại diện cho một sinh viên trong hệ thống."""

    def __init__(
        self,
        ma_sv: str,
        ho_ten: str = "",
        ngay_sinh: str = "",
        nganh: str = "",
        chuyen_nganh: str = "",
        bac_dao_tao: str = "",
        khoa_hoc: str = "",
    ):
        self.ma_sv = ma_sv
        self.ho_ten = ho_ten
        self.ngay_sinh = ngay_sinh
        self.nganh = nganh
        self.chuyen_nganh = chuyen_nganh
        self.bac_dao_tao = bac_dao_tao
        self.khoa_hoc = khoa_hoc

    @staticmethod
    def login(username: str, password: str | None = None) -> bool:
        """Xác thực đăng nhập sinh viên. Chỉ cần mã sinh viên."""
        username = username.strip()
        rows = execute_query(
            "SELECT MaSV FROM SinhVien WHERE MaSV = ?", (username,)
        )
        return bool(rows)

    @classmethod
    def get_by_id(cls, ma_sv: str) -> "SinhVien | None":
        """Truy vấn DB và trả về đối tượng SinhVien. None nếu không tìm thấy."""
        rows = execute_query(
            "SELECT MaSV, HoTen, NgaySinh, Nganh, ChuyenNganh, BacDaoTao, KhoaHoc "
            "FROM SinhVien WHERE MaSV = ?",
            (ma_sv,),
        )
        if rows:
            r = rows[0]
            return cls(
                ma_sv=r.MaSV,
                ho_ten=r.HoTen or "",
                ngay_sinh=str(r.NgaySinh) if r.NgaySinh else "",
                nganh=r.Nganh or "",
                chuyen_nganh=r.ChuyenNganh or "",
                bac_dao_tao=r.BacDaoTao or "",
                khoa_hoc=r.KhoaHoc or "",
            )
        return None

    @staticmethod
    def get_danh_sach_hoc_ky() -> list[dict]:
        """Lấy danh sách toàn bộ học kỳ để hiện vào ComboBox."""
        rows = execute_query(
            "SELECT MaHK, TenHK, NamHoc FROM HocKy ORDER BY NamHoc DESC, MaHK DESC"
        )
        return [
            {"MaHK": r.MaHK, "TenHK": r.TenHK, "NamHoc": r.NamHoc}
            for r in rows
        ]

    def get_hoc_phan_co_the_dang_ky(self, ma_hk: str) -> list[dict]:
        """Lấy danh sách Học Phần SV có thể đăng ký trong HK, kèm kiểm tra điều kiện."""
        rows = execute_query(
            "SELECT HP.MaHP, HP.TenHP, HP.SoTinChi, HP.BatBuoc, "
            "'' AS DieuKienDangKy, '' AS TienQuyet, '' AS SongHanh "
            "FROM HocPhan HP "
            "JOIN LopHocPhan L WITH (NOLOCK) ON HP.MaHP = L.MaHP "
            "WHERE L.MaHK = ?",
            (ma_hk,)
        )
        result = []
        for r in rows:
            dat_tien_quyet = True
            dat_song_hanh = True

            try:
                tq = execute_query(
                    "SELECT dbo.fn_KiemTraTienQuyet(?, ?) AS KQ",
                    (self.ma_sv, r.MaHP),
                )
                if tq and tq[0].KQ == 0:
                    dat_tien_quyet = False
            except Exception:
                pass

            try:
                sh = execute_query(
                    "SELECT dbo.fn_KiemTraSongHanh(?, ?) AS KQ",
                    (self.ma_sv, r.MaHP),
                )
                if sh and sh[0].KQ == 0:
                    dat_song_hanh = False
            except Exception:
                pass

            result.append(
                {
                    "MaHP": r.MaHP,
                    "TenHP": r.TenHP,
                    "SoTinChi": r.SoTinChi,
                    "BatBuoc": bool(r.BatBuoc),
                    "DieuKienDangKy": r.DieuKienDangKy or "",
                    "TienQuyet": r.TienQuyet or "",
                    "SongHanh": r.SongHanh or "",
                    "DatTienQuyet": dat_tien_quyet,
                    "DatSongHanh": dat_song_hanh,
                }
            )
        return result

    @staticmethod
    def get_lop_hoc_phan(ma_hp: str, ma_hk: str) -> list[dict]:
        """Lấy danh sách Lớp HP của 1 môn trong 1 HK."""
        rows = execute_query(
            "SELECT L.MaLHP, L.MaHP, HP.TenHP, HP.SoTinChi, L.MaHK, "
            "L.SoLuongDangKy, L.SiSoToiDa, "
            "(L.SiSoToiDa - L.SoLuongDangKy) AS SoChoConLai, "
            "CAST((L.SoLuongDangKy * 100.0 / NULLIF(L.SiSoToiDa, 0)) AS DECIMAL(5,2)) AS PhanTramDaDangKy "
            "FROM LopHocPhan L "
            "JOIN HocPhan HP ON L.MaHP = HP.MaHP "
            "WHERE L.MaHP = ? AND L.MaHK = ?",
            (ma_hp, ma_hk),
        )
        return [
            {
                "MaLHP": r.MaLHP,
                "MaHP": r.MaHP,
                "TenHP": r.TenHP,
                "SoTinChi": r.SoTinChi,
                "MaHK": r.MaHK,
                "SoLuongDangKy": r.SoLuongDangKy,
                "SiSoToiDa": r.SiSoToiDa,
                "SoChoConLai": r.SoChoConLai,
                "PhanTramDaDangKy": float(r.PhanTramDaDangKy or 0),
            }
            for r in rows
        ]

    @staticmethod
    def get_lich_lop(ma_lhp: str) -> list[dict]:
        """Lấy chi tiết lịch học (phòng, ca, thứ) của 1 lớp HP."""
        rows = execute_query(
            "SELECT MaCTLHP, MaLHP, NgayBatDau, NgayKetThuc, ThuHoc, CaHoc, PhongHoc "
            "FROM ChiTietLopHocPhan WITH (NOLOCK) WHERE MaLHP = ?",
            (ma_lhp,),
        )
        return [
            {
                "MaCTLHP": r.MaCTLHP,
                "MaLHP": r.MaLHP,
                "Thu": r.ThuHoc or "",
                "Cahoc": r.CaHoc or "",
                "PhongHoc": r.PhongHoc or "",
                "NgayBatDau": str(r.NgayBatDau) if r.NgayBatDau else "",
                "NgayKetThuc": str(r.NgayKetThuc) if r.NgayKetThuc else "",
            }
            for r in rows
        ]

    def kiem_tra_trung_lich(self, ma_lhp: str) -> bool:
        """Kiểm tra lớp HP có bị trùng lịch với lớp SV đã ĐK không. True = bị trùng."""
        try:
            rows = execute_query(
                "SELECT dbo.fn_KiemTraTrungLich(?, ?) AS KQ",
                (self.ma_sv, ma_lhp),
            )
            return bool(rows and rows[0].KQ == 1)
        except Exception:
            return False

    def dang_ky_lop(
        self, ma_lhp: str, loai_dk: str = "Mới", max_retries: int = 3
    ) -> tuple[bool, str]:
        """Đăng ký vào 1 lớp HP. Tự thử lại khi gặp Deadlock."""
        for attempt in range(1, max_retries + 1):
            ma_dk = f"DK_{self.ma_sv}_{ma_lhp}_{int(time.time() * 1000)}"
            ok, msg, rows, err_code = execute_procedure(
                "sp_DangKyHocPhan", (ma_dk, self.ma_sv, ma_lhp, loai_dk)
            )
            if rows:
                r = rows[0]
                return bool(r.Success), r.Message
            if ok:
                return True, "Đăng ký thành công!"
            if err_code == "DEADLOCK" or "deadlock" in msg.lower():
                if attempt < max_retries:
                    time.sleep(0.5 * attempt)
                    continue
            return False, msg
        return False, "Không thể hoàn tất đăng ký, vui lòng thử lại."

    def get_danh_sach_da_dang_ky(self, ma_hk: str) -> list[dict]:
        """Lấy danh sách các lớp HP SV đã đăng ký trong HK."""
        rows = execute_query(
            "SELECT DK.MaDK, DK.MaLHP, HP.MaHP, HP.TenHP, HP.SoTinChi, "
            "DK.TrangThai, DK.LoaiDangKy, DK.NgayDK AS NgayDk, 0 AS HocPhi "
            "FROM DangKyHocPhan DK "
            "JOIN LopHocPhan L ON DK.MaLHP = L.MaLHP "
            "JOIN HocPhan HP ON L.MaHP = HP.MaHP "
            "WHERE DK.MaSV = ? AND L.MaHK = ? "
            "ORDER BY DK.NgayDK DESC",
            (self.ma_sv, ma_hk),
        )
        return [
            {
                "MaDK": r.MaDK,
                "MaLHP": r.MaLHP,
                "MaHP": r.MaHP,
                "TenHP": r.TenHP,
                "SoTinChi": r.SoTinChi,
                "TrangThai": r.TrangThai or "",
                "LoaiDangKy": r.LoaiDangKy or "",
                "NgayDk": str(r.NgayDk) if r.NgayDk else "",
                "HocPhi": int(r.HocPhi) if r.HocPhi else 0,
            }
            for r in rows
        ]

    def get_lich_hoc(self, ma_hk: str) -> list[dict]:
        """Lấy lịch học tổng hợp của SV trong 1 HK (chưa bị hủy)."""
        rows = execute_query(
            "SELECT L.MaLHP, HP.MaHP, HP.TenHP, HP.SoTinChi, "
            "CT.ThuHoc AS Thu, CT.CaHoc AS Cahoc, CT.PhongHoc, CT.NgayBatDau, CT.NgayKetThuc "
            "FROM DangKyHocPhan DK "
            "JOIN LopHocPhan L ON DK.MaLHP = L.MaLHP "
            "JOIN HocPhan HP ON L.MaHP = HP.MaHP "
            "JOIN ChiTietLopHocPhan CT ON L.MaLHP = CT.MaLHP "
            "WHERE DK.MaSV = ? AND L.MaHK = ?",
            (self.ma_sv, ma_hk),
        )
        return [
            {
                "MaLHP": r.MaLHP,
                "MaHP": r.MaHP,
                "TenHP": r.TenHP,
                "SoTinChi": r.SoTinChi,
                "Thu": r.Thu or "",
                "Cahoc": r.Cahoc or "",
                "PhongHoc": r.PhongHoc or "",
                "NgayBatDau": str(r.NgayBatDau) if r.NgayBatDau else "",
                "NgayKetThuc": str(r.NgayKetThuc) if r.NgayKetThuc else "",
            }
            for r in rows
        ]

    def huy_dang_ky(self, ma_dk: str) -> tuple[bool, str]:
        """Hủy đăng ký theo MaDK. Nếu stored procedure lỗi, dùng fallback trực tiếp."""
        ok, msg, rows, err_code = execute_procedure("sp_HuyDangKyHocPhan", (ma_dk,))
        if ok and rows:
            r = rows[0]
            return bool(r.Success), r.Message

        try:
            rows = execute_query(
                "SELECT MaDK, MaSV FROM DangKyHocPhan WHERE MaDK = ?",
                (ma_dk,),
            )
            if not rows:
                return False, "Không tìm thấy phiếu đăng ký."
            if rows[0].MaSV != self.ma_sv:
                return False, "Phiếu đăng ký không thuộc sinh viên này."

            execute_query("DELETE FROM DangKyHocPhan WHERE MaDK = ?", (ma_dk,), fetch=False)
            return True, "Hủy đăng ký thành công."
        except Exception as e:
            return False, f"Lỗi khi hủy đăng ký: {e}"

    def demo_deadlock_sinhvien(self, ma_lhp: str, ma_hk: str) -> tuple[bool, str]:
        """Demo lỗi Deadlock: SV đăng ký lớp học phần."""
        ok, msg, rows, err_code = execute_procedure("sp_Demo_Deadlock_SinhVien", (ma_lhp, ma_hk))
        if err_code == "DEADLOCK" or "deadlock" in msg.lower():
            return False, "Error 1205: Transaction was deadlocked... Bị hệ thống hủy để giải phóng bế tắc."
        if rows:
            r = rows[0]
            return bool(r.Success), r.Message
        return ok, msg

    def __repr__(self):
        return f"<SinhVien {self.ma_sv} – {self.ho_ten}>"