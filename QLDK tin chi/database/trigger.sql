USE QuanLyDangKyHocPhan;
GO

--TRIGGER


--Tự động tăng số lượng đăng ký khi sinh viên đăng ký học phần
DROP TRIGGER IF EXISTS trg_TangSoLuongDangKy
GO

CREATE TRIGGER trg_TangSoLuongDangKy
ON DangKyHocPhan
AFTER INSERT
AS
BEGIN

    UPDATE LHP
    SET SoLuongDangKy = SoLuongDangKy + I.SoLuong
    FROM LopHocPhan LHP
    INNER JOIN
    (
        SELECT MaLHP, COUNT(*) AS SoLuong
        FROM inserted
        GROUP BY MaLHP
    ) I
    ON LHP.MaLHP = I.MaLHP;

END
GO

--Tự động giảm số lượng đăng ký khi hủy đăng ký
DROP TRIGGER trg_GiamSoLuongDangKy;
GO

CREATE TRIGGER trg_GiamSoLuongDangKy
ON DangKyHocPhan
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE LHP
    SET SoLuongDangKy =
    CASE
        WHEN SoLuongDangKy - D.SoLuong < 0
            THEN 0
        ELSE SoLuongDangKy - D.SoLuong
    END
    FROM LopHocPhan LHP
    INNER JOIN
    (
        SELECT MaLHP, COUNT(*) AS SoLuong
        FROM deleted
        GROUP BY MaLHP
    ) D
    ON LHP.MaLHP = D.MaLHP;
END
GO


--Ghi lịch sử thay đổi (Audit Log) thêm phần này


--Tạo bảng nhật ký
DROP TABLE NhatKyDangKyHocPhan;
GO

CREATE TABLE NhatKyDangKyHocPhan
(
    MaNhatKy INT IDENTITY(1,1) PRIMARY KEY,
    MaDK VARCHAR(50),
    MaSV VARCHAR(20),
    MaLHP VARCHAR(20),
    HanhDong NVARCHAR(20),
    ThoiGian DATETIME DEFAULT GETDATE()
);
GO


--Trigger ghi log khi đăng ký
DROP TRIGGER trg_LogDangKyHocPhan;
GO

CREATE TRIGGER trg_LogDangKyHocPhan
ON DangKyHocPhan
AFTER INSERT
AS
BEGIN

    INSERT INTO NhatKyDangKyHocPhan
    (
        MaDK,
        MaSV,
        MaLHP,
        HanhDong,
        ThoiGian
    )
    SELECT
        MaDK,
        MaSV,
        MaLHP,
        N'Đăng ký',
        GETDATE()
    FROM inserted;

END
GO


--Trigger ghi log khi hủy đăng ký
DROP TRIGGER trg_LogHuyDangKyHocPhan;
GO

CREATE TRIGGER trg_LogHuyDangKyHocPhan
ON DangKyHocPhan
AFTER DELETE
AS
BEGIN

    INSERT INTO NhatKyDangKyHocPhan
    (
        MaDK,
        MaSV,
        MaLHP,
        HanhDong,
        ThoiGian
    )
    SELECT
        MaDK,
        MaSV,
        MaLHP,
        N'Hủy đăng ký',
        GETDATE()
    FROM deleted;

END
GO

--Trigger chặn hủy đăng ký sau khi đóng cổng đăng ký
DROP TRIGGER trg_KhongChoHuyDangKy;
GO

CREATE TRIGGER trg_KhongChoHuyDangKy
ON DangKyHocPhan
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS
    (
        SELECT 1
        FROM deleted D
        JOIN LopHocPhan LHP
            ON D.MaLHP = LHP.MaLHP
        JOIN HocKy HK
            ON LHP.MaHK = HK.MaHK
        WHERE hk.NgayDongDangKy < GETDATE()
    )
    BEGIN
        RAISERROR(N'Đã hết thời gian hủy đăng ký học phần.',16,1);
        RETURN;
    END

    DELETE FROM DangKyHocPhan
    WHERE MaDK IN
    (
        SELECT MaDK
        FROM deleted
    );

END
GO

