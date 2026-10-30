use QuanLyDangKyHocPhan;
Go

/*====================================================
PHANTOM READ

Mô tả:
- Transaction T1 đọc số lượng đăng ký của một lớp học phần.
- Trong lúc T1 đang chờ, Transaction T2 thêm một đăng ký mới.
- Khi T1 đọc lại cùng điều kiện truy vấn, số bản ghi tăng lên.
- Đây là hiện tượng Phantom Read.

Cách kiểm thử:
1. Mở Query Window 1:
   EXEC sp_DemoPhantomRead;

2. Trong thời gian WAITFOR DELAY,
   mở Query Window 2 và thực hiện INSERT.

3. Kết quả:
   Lần đọc thứ nhất và lần đọc thứ hai cho kết quả khác nhau.
====================================================*/
GO

DROP PROCEDURE IF EXISTS sp_DemoPhantomRead;
GO

CREATE PROCEDURE sp_DemoPhantomRead
AS
BEGIN

    -- Mức cô lập mặc định cho phép xảy ra Phantom Read
    SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
     /*
    =========================================
    KHẮC PHỤC PHANTOM READ

    Chỉ cần đổi thành:

    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    */

    BEGIN TRANSACTION;

    -- Lần đọc thứ nhất
    PRINT N'Lan doc thu nhat';

    SELECT COUNT(*) AS SoLuongDangKy
    FROM DangKyHocPhan
    WHERE MaLHP = 'LHP001';

    -- Tạm dừng để Transaction khác chèn dữ liệu
    WAITFOR DELAY '00:00:10';

    -- Lần đọc thứ hai
    PRINT N'Lan doc thu hai';

    SELECT COUNT(*) AS SoLuongDangKy
    FROM DangKyHocPhan
    WHERE MaLHP = 'LHP001';

    COMMIT TRANSACTION;

END
GO



EXEC sp_DemoPhantomRead;

/*====================================================
KIỂM THỬ PHANTOM READ

Cửa sổ 1:
EXEC sp_DemoPhantomRead;

*/