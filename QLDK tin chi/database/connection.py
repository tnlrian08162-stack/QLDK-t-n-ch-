
import sys
import os
import pyodbc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DB_CONFIG

def _conn_str() -> str:
    c = DB_CONFIG
    return (
        f"DRIVER={c['driver']};"
        f"SERVER={c['server']};"
        f"DATABASE={c['database']};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Trusted_Connection=yes;"
    )
    
_CONN_STR = _conn_str()

def get_connection() -> pyodbc.Connection | None:
    try:
        conn = pyodbc.connect(_CONN_STR, timeout=10)
        return conn
    except pyodbc.Error as e:
        print(f"[DB] Lỗi kết nối: {e}")
        return None


def execute_query(sql: str, params: tuple = (), fetch: bool = True):
    conn = get_connection()
    if conn is None:
        return []
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
            return []
    except pyodbc.Error as e:
        print(f"[DB] Lỗi execute_query: {e}")
        return []
    finally:
        conn.close()


_ERROR_KEYWORDS = [
    ("hết chỗ",         "LOP_DAY_CHO"),        # Lost Update: lớp đầy
    ("sĩ số",           "LOP_DAY_CHO"),        # cùng loại
    ("trùng lịch",      "TRUNG_LICH"),         # Lịch bị trùng
    ("tiên quyết",      "TIEN_QUYET"),         # Chưa học tiên quyết
    ("song hành",       "SONG_HANH"),          # Thiếu song hành
    ("đã đăng ký",      "DA_DANG_KY"),         # Trùng HP trong HK
    ("tín chỉ",         "QUA_TC"),             # Vượt 24 TC
    ("1205",            "DEADLOCK"),            # Deadlock SQL Server
    ("deadlock",        "DEADLOCK"),
    ("timeout",         "TIMEOUT"),
    ("kết nối",         "CONNECTION_ERROR"),
]

def _classify_error(error_str: str) -> str:
    """
    Phân loại lỗi dựa trên nội dung message.
    Trả về error_code chuẩn để UI xử lý thông báo phù hợp.
    """
    low = error_str.lower()
    for keyword, code in _ERROR_KEYWORDS:
        if keyword in low:
            return code
    return "UNKNOWN_ERROR"


def execute_procedure(proc_name: str, params: tuple = ()):
    conn = get_connection()
    if conn is None:
        return False, "Không thể kết nối đến CSDL. Vui lòng kiểm tra kết nối mạng.", [], "CONNECTION_ERROR"
    try:
        with conn:
            cur = conn.cursor()
            placeholders = ", ".join(["?" for _ in params])
            cur.execute(f"EXEC {proc_name} {placeholders}", params)

            rows = []
            try:
                rows = cur.fetchall()
            except pyodbc.ProgrammingError:
                pass  # SP không trả về resultset

            conn.commit()
            return True, "Thành công", rows, None
    except pyodbc.Error as e:
        error_str = str(e)
        error_code = _classify_error(error_str)
        # Trích xuất message thân thiện từ RAISERROR (prefix 50001:)
        friendly_msg = _extract_raiserror_msg(error_str)
        # Nếu không trích được message thân thiện, tạo message theo error_code
        if friendly_msg == error_str or "50001" not in error_str:
            friendly_msg = _make_friendly_message(error_code, error_str)
        return False, friendly_msg, [], error_code
    finally:
        conn.close()


def _make_friendly_message(error_code: str, raw: str) -> str:
    """Tạo thông báo thân thiện từ error_code khi không có RAISERROR message."""
    messages = {
        "DEADLOCK":         "⚠️ Hệ thống đang bận do nhiều người đăng ký cùng lúc. Đang thử lại...",
        "LOP_DAY_CHO":      "⚠️ Lớp học phần đã hết chỗ do có người đăng ký trước bạn.",
        "TRUNG_LICH":       "⚠️ Lớp này bị trùng lịch với môn bạn đã đăng ký.",
        "TIEN_QUYET":       "⚠️ Bạn chưa hoàn thành học phần tiên quyết.",
        "SONG_HANH":        "⚠️ Bạn cần đăng ký kèm học phần song hành.",
        "DA_DANG_KY":       "⚠️ Bạn đã đăng ký học phần này trong học kỳ này rồi.",
        "QUA_TC":           "⚠️ Tổng tín chỉ đã vượt quá 24 TC. Không thể đăng ký thêm.",
        "TIMEOUT":          "⚠️ Kết nối quá chậm. Vui lòng thử lại sau.",
        "CONNECTION_ERROR": "⚠️ Mất kết nối đến CSDL. Kiểm tra lại kết nối mạng.",
    }
    return messages.get(error_code, f"Lỗi CSDL: {raw[:200]}")


def _extract_raiserror_msg(error_str: str) -> str:
    """Trích xuất message từ RAISERROR của SQL Server."""
    try:
        # Format: "('...', 'HY000')" → lấy phần text
        start = error_str.find("('") + 2
        end   = error_str.find("',", start)
        return error_str[start:end] if start > 1 else error_str
    except Exception:
        return error_str

