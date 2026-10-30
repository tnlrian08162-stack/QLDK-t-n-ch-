

/*====================================================
NON-REPEATABLE READ

Mô tả:
- Transaction T1 đọc thông tin của một lớp học phần.
- Trong lúc T1 đang chờ, Transaction T2 cập nhật dữ liệu.
- Khi T1 đọc lại cùng bản ghi, giá trị đã thay đổi.
- Đây là hiện tượng Non-Repeatable Read.

Ngữ cảnh:
- Lớp học phần LHP001 hiện có 45 sinh viên đăng ký.
- Phòng Đào tạo kiểm tra sĩ số lớp để lập báo cáo.
- Trong lúc đó, Quản trị viên cập nhật lại sĩ số lớp.
- Khi Phòng Đào tạo đọc lại dữ liệu, sĩ số đã thay đổi.

Cách kiểm thử:
1. Mở Query Window 1:
   EXEC sp_DemoNonRepeatableRead;

2. Trong thời gian WAITFOR DELAY,
   mở Query Window 2 và thực hiện UPDATE.

3. Kết quả:
   Lần đọc thứ nhất và lần đọc thứ hai trả về
   giá trị SoLuongDangKy khác nhau.
====================================================*/
USE QuanLyDangKyHocPhan;
GO

DROP PROCEDURE IF EXISTS sp_DemoNonRepeatableRead;
GO

CREATE PROCEDURE sp_DemoNonRepeatableRead
AS
BEGIN

    -- READ COMMITTED là mức cô lập mặc định
    -- Cho phép xảy ra Non-Repeatable Read
    SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
    --Khắc phục Non-Repeatable Read
    -- SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    BEGIN TRANSACTION;

    PRINT N'===== LẦN ĐỌC 1 =====';

    SELECT
        MaLHP,
        SoLuongDangKy
    FROM LopHocPhan
    WHERE MaLHP = 'LHP001';

    -- Chờ 10 giây để Transaction khác cập nhật dữ liệu
    WAITFOR DELAY '00:00:10';

    PRINT N'===== LẦN ĐỌC 2 =====';

    SELECT
        MaLHP,
        SoLuongDangKy
    FROM LopHocPhan
    WHERE MaLHP = 'LHP001';

    COMMIT TRANSACTION;

END
GO
EXEC sp_DemoNonRepeatableRead;


