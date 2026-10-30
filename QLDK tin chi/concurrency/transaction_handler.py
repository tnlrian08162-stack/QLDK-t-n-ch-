"""
concurrency/transaction_handler.py – Xử lý giao dịch và retry logic (chủ yếu cho Deadlock 1205).
"""

import time
from typing import Callable, Any, Optional

def execute_with_retry(
    func: Callable[[], tuple[bool, str, Any]],
    max_retries: int = 3,
    delay_sec: float = 1.0,
    on_retry: Optional[Callable[[int, int], None]] = None,
) -> tuple[bool, str, Any]:
    """
    Thực thi một hàm có trả về (success, message, data).
    Nếu message chứa 'Deadlock' hoặc '1205', tự động retry tối đa max_retries lần.

    Args:
        func       : Hàm cần thực thi (không tham số, dùng closure).
        max_retries: Số lần thử lại tối đa.
        delay_sec  : Thời gian chờ giữa các lần retry (giây).
        on_retry   : Callback(attempt, max_retries) được gọi mỗi khi retry.
                     Ví dụ: on_retry=lambda i,m: status_bar.setText(f"⏳ Retry {i}/{m}...")

    Returns:
        (success, message, data)
    """
    for attempt in range(1, max_retries + 1):
        success, message, data = func()

        # Nếu thành công hoặc không phải deadlock → trả về ngay
        is_deadlock = (
            "deadlock" in message.lower()
            or "1205" in message
        )
        if success or not is_deadlock:
            return success, message, data

        # Deadlock → gọi callback và chờ trước khi retry
        if attempt < max_retries:
            print(f"[CONCURRENCY] Deadlock phát hiện. Thử lại lần {attempt}/{max_retries} sau {delay_sec}s...")
            if on_retry:
                on_retry(attempt, max_retries)
            time.sleep(delay_sec)
        else:
            print(f"[CONCURRENCY] Deadlock retry thất bại sau {max_retries} lần.")
            return False, "❌ Hệ thống đang quá tải do nhiều người đăng ký cùng lúc. Vui lòng thử lại sau ít giây.", None

    return False, "Lỗi không xác định", None
