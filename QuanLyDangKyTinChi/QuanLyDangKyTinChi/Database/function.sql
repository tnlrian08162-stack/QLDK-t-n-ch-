USE QuanLyDangKyHocPhan;
GO

/*===============================


--Function


================================*/

-- Tính tổng số tín chỉ sinh viên đã đăng ký
DROP FUNCTION dbo.fn_TongTinChiSinhVien;
GO

CREATE FUNCTION dbo.fn_TongTinChiSinhVien
(
    @MaSV VARCHAR(20),
    @MaHK VARCHAR(20)
)
RETURNS INT
AS
BEGIN
    DECLARE @TongTinChi INT = 0;

    -- Kiểm tra sinh viên tồn tại
    IF EXISTS
    (
        SELECT 1
        FROM SinhVien
        WHERE MaSV = @MaSV
    )
    BEGIN
        SELECT
            -- Tránh NULL nếu sinh viên chưa đăng ký học phần nào
            @TongTinChi = ISNULL(SUM(hp.SoTinChi), 0)
        FROM DangKyHocPhan dk
            INNER JOIN LopHocPhan lhp
                ON dk.MaLHP = lhp.MaLHP
            INNER JOIN HocPhan hp
                ON lhp.MaHP = hp.MaHP
        WHERE dk.MaSV = @MaSV
            AND lhp.MaHK = @MaHK
          -- Chỉ tính các đăng ký thành công
            AND dk.TrangThai = N'Thành công'; 
    END

    RETURN @TongTinChi;
END;
GO

--Kiểm tra trùng lịch học
CREATE FUNCTION dbo.fn_KiemTraTrungLich
(
    @MaSV VARCHAR(20),
    @MaLHP VARCHAR(20)
)
RETURNS BIT
AS
BEGIN
    DECLARE @MaHK VARCHAR(20);

    SELECT @MaHK = MaHK
    FROM LopHocPhan
    WHERE MaLHP = @MaLHP;

    IF EXISTS
    (
        SELECT 1
        FROM DangKyHocPhan dk
            INNER JOIN LopHocPhan L1
                ON dk.MaLHP = L1.MaLHP
            INNER JOIN ChiTietLopHocPhan C1
                ON L1.MaLHP = C1.MaLHP
            INNER JOIN ChiTietLopHocPhan C2
                ON C2.MaLHP = @MaLHP
        WHERE dk.MaSV = @MaSV
            AND L1.MaHK = @MaHK
            AND dk.TrangThai = N'Thành công'
            AND dk.MaLHP <> @MaLHP
            AND C1.ThuHoc = C2.ThuHoc
            AND C1.CaHoc = C2.CaHoc
    )
        RETURN 1;

    RETURN 0;
END;
GO

-- Đếm số học phần đã đăng ký
CREATE FUNCTION dbo.fn_DemSoHocPhan
(
    @MaSV VARCHAR(20)
)
RETURNS INT
AS
BEGIN
    DECLARE @SoLuong INT = 0;

    -- Kiểm tra sinh viên tồn tại
    IF EXISTS
    (
        SELECT 1
        FROM SinhVien
        WHERE MaSV = @MaSV
    )
    BEGIN
        SELECT
            @SoLuong = COUNT(*)
        FROM DangKyHocPhan
        WHERE MaSV = @MaSV
            -- Chỉ đếm các đăng ký thành công
            AND TrangThai = N'Thành công';
    END

    RETURN @SoLuong;
END;
GO

-- Kiểm tra lớp học phần còn chỗ hay không
CREATE FUNCTION dbo.fn_ConChoTrong
(
    @MaLHP VARCHAR(20)
)
RETURNS NVARCHAR(50)
AS
BEGIN
    DECLARE @KetQua NVARCHAR(50);

    SELECT
        @KetQua =
        CASE
            WHEN SoLuongDangKy < SiSoToiDa
                THEN N'Còn chỗ'
            ELSE N'Đã đầy'
        END
    FROM LopHocPhan
    WHERE MaLHP = @MaLHP;

    RETURN @KetQua;
END;
GO

-- Kiểm tra điều kiện tiên quyết

CREATE FUNCTION dbo.fn_KiemTraTienQuyet
(
    @MaSV VARCHAR(20),
    @MaHP VARCHAR(20)
)
RETURNS BIT
AS
BEGIN

    -- Có tiên quyết nào mà SV chưa hoàn thành
    IF EXISTS
    (
        SELECT 1
        FROM DieuKienHocPhan dk
        WHERE dk.MaHP = @MaHP
            AND dk.LoaiDieuKien = N'Tiên quyết'
            AND dk.MaHP_TienQuyet NOT IN
            (
                -- HP SV đã hoàn thành
                SELECT LHP.MaHP
                FROM DangKyHocPhan DK
                    INNER JOIN LopHocPhan LHP
                        ON DK.MaLHP = LHP.MaLHP
                WHERE DK.MaSV = @MaSV
                    AND DK.TrangThai = N'Đã hoàn thành'
            )
    )
        -- Còn thiếu tiên quyết
        RETURN 0;
    -- Đạt đủ hoặc không có tiên quyết
    RETURN 1;
END;
GO

-- Kiểm tra điều kiện song hành
DROP FUNCTION dbo.fn_KiemTraSongHanh;
GO

CREATE FUNCTION dbo.fn_KiemTraSongHanh
(
    @MaSV VARCHAR(20),
    @MaHP VARCHAR(20)
)
RETURNS BIT
AS
BEGIN

    -- Không có điều kiện song hành → tự do ĐK
    IF NOT EXISTS
    (
        SELECT 1
        FROM DieuKienHocPhan
        WHERE MaHP = @MaHP
            AND LoaiDieuKien = N'Song hành'
    )
        RETURN 1;
    
    -- Có điều kiện→ kiểm tra từng HP song hành
    IF EXISTS
    (
        SELECT 1
        FROM DieuKienHocPhan dk
        WHERE dk.MaHP = @MaHP
            AND dk.LoaiDieuKien = N'Song hành'
            AND dk.MaHP_TienQuyet NOT IN
            (
                -- 1) Đang ĐK trong cùng HK (DaDangKy)
                SELECT LHP.MaHP
                FROM DangKyHocPhan DK
                    INNER JOIN LopHocPhan LHP
                        ON DK.MaLHP = LHP.MaLHP
                WHERE DK.MaSV = @MaSV
                    AND DK.TrangThai IN
                    (
                        N'Thành công',
                        N'Đã hoàn thành'
                    )
                UNION
                   -- 2) Đã hoàn thành kỳ trước
                SELECT LHP.MaHP
                FROM DangKyHocPhan DK
                    INNER JOIN LopHocPhan LHP
                        ON LHP.MaLHP = DK.MaLHP
                WHERE DK.MaSV = @MaSV
                    AND DK.TrangThai = N'Đã hoàn thành'

            )
    )
        RETURN 0;

    RETURN 1;
END;
GO

-- Tính phần trăm đăng ký của lớp học phần
DROP FUNCTION dbo.fn_PhanTramDaDangKy;
GO

CREATE FUNCTION dbo.fn_PhanTramDaDangKy
(
    @MaLHP VARCHAR(20)
)
RETURNS DECIMAL(5,1)
AS
BEGIN
    DECLARE @Pct DECIMAL(5,1);

    SELECT
        @Pct =
        CASE
            WHEN SiSoToiDa = 0 THEN 0
            ELSE CAST(
                    SoLuongDangKy * 100.0 / SiSoToiDa
                    AS DECIMAL(5,1)
                 )
        END
    FROM LopHocPhan
    WHERE MaLHP = @MaLHP;

    RETURN ISNULL(@Pct, 0);
END;
GO