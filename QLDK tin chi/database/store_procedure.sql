USE QuanLyDangKyHocPhan;
GO

/*===============================


--STORED PROCEDURE


================================*/

--A. đăng ký học phần
DROP PROCEDURE sp_DangKyHocPhan;
GO

CREATE PROCEDURE sp_DangKyHocPhan
(
    @MaDK VARCHAR(50),
    @MaSV VARCHAR(20),
    @MaLHP VARCHAR(20),
    @LoaiDangKy NVARCHAR(50)
)
AS
BEGIN
BEGIN TRY

        BEGIN TRANSACTION;

    DECLARE @TongTinChi INT;
    DECLARE @SoTinChiMonMoi INT;

    -- Kiểm tra mã đăng ký đã tồn tại
    IF EXISTS
    (
        SELECT 1
        FROM DangKyHocPhan
        WHERE MaDK = @MaDK
    )
    BEGIN
        PRINT N'Mã đăng ký đã tồn tại';
        RETURN;
    END

    -- Kiểm tra sinh viên tồn tại
    IF NOT EXISTS
    (
        SELECT 1
        FROM SinhVien
        WHERE MaSV = @MaSV
    )
    BEGIN
        PRINT N'Sinh viên không tồn tại';
        RETURN;
    END

    -- Kiểm tra lớp học phần tồn tại
    IF NOT EXISTS
    (
        SELECT 1
        FROM LopHocPhan
        WHERE MaLHP = @MaLHP
    )
    BEGIN
        PRINT N'Lớp học phần không tồn tại';
        RETURN;
    END
    -- Kiểm tra thời gian đăng ký
DECLARE @NgayMo DATETIME;
DECLARE @NgayDong DATETIME;

SELECT
    @NgayMo = HK.NgayMoDangKy,
    @NgayDong = HK.NgayDongDangKy
FROM LopHocPhan LHP
JOIN HocKy HK
    ON LHP.MaHK = HK.MaHK
WHERE LHP.MaLHP = @MaLHP;

IF GETDATE() < @NgayMo
BEGIN
    PRINT N'Chưa đến thời gian đăng ký';
    RETURN;
END

IF GETDATE() > @NgayDong
BEGIN
    PRINT N'Đã hết thời gian đăng ký';
    RETURN;
END
    -- Kiểm tra đăng ký trùng
    IF EXISTS
    (
        SELECT 1
        FROM DangKyHocPhan
        WHERE MaSV = @MaSV
          AND MaLHP = @MaLHP
    )
    BEGIN
        PRINT N'Sinh viên đã đăng ký lớp này';
        RETURN;
    END

    -- Kiểm tra lớp còn chỗ
    IF EXISTS
    (
        SELECT 1
        FROM LopHocPhan
        WHERE MaLHP = @MaLHP
          AND SoLuongDangKy >= SiSoToiDa
    )
    BEGIN
        PRINT N'Lớp học phần đã đầy';
        RETURN;
    END



    -- Lấy mã học phần của lớp sắp đăng ký
    DECLARE @MaHP VARCHAR(20);

SELECT @MaHP = MaHP
FROM LopHocPhan
WHERE MaLHP = @MaLHP;
    
    -- Kiểm tra trùng học phần 
    IF EXISTS
    (
        SELECT 1
        FROM DangKyHocPhan DK
        JOIN LopHocPhan LHP
            ON DK.MaLHP=LHP.MaLHP
        WHERE DK.MaSV =@MaSV
            AND LHP.MaHP = @MaHP
            AND DK.TrangThai = N'Thành công'
    )
    BEGIN 
        PRINT N'Sinh viên đã đăng ký học phần này ở lớp khác';
        ROLLBACK TRANSACTION;
        RETURN;
    END
        -- Kiểm tra học phần tiên quyết
IF EXISTS
(
    SELECT 1
    FROM DieuKienHocPhan DK
    WHERE DK.MaHP = @MaHP
      AND DK.LoaiDieuKien = N'Tiên quyết'
      AND NOT EXISTS
      (
          SELECT 1
          FROM DangKyHocPhan D
          JOIN LopHocPhan LHP
              ON D.MaLHP = LHP.MaLHP
          WHERE D.MaSV = @MaSV
            AND LHP.MaHP = DK.MaHP_TienQuyet
            AND D.TrangThai = N'Thành công'
      )
)
BEGIN
    PRINT N'Chưa đạt điều kiện tiên quyết';
    RETURN;
END

-- Kiểm tra học phần song hành
IF EXISTS
(
    SELECT 1
    FROM DieuKienHocPhan DK
    WHERE DK.MaHP = @MaHP
      AND DK.LoaiDieuKien = N'Song hành'
      AND NOT EXISTS
      (
          SELECT 1
          FROM DangKyHocPhan D
          JOIN LopHocPhan LHP
              ON D.MaLHP = LHP.MaLHP
          WHERE D.MaSV = @MaSV
            AND LHP.MaHP = DK.MaHP_TienQuyet
            AND D.TrangThai = N'Thành công'
      )
)
BEGIN
    PRINT N'Chưa đăng ký học phần song hành';
    RETURN;
END


    -- Lấy số tín chỉ môn sắp đăng ký
    SELECT
        @SoTinChiMonMoi = hp.SoTinChi
    FROM LopHocPhan lhp
    JOIN HocPhan hp
        ON lhp.MaHP = hp.MaHP
    WHERE lhp.MaLHP = @MaLHP;

    -- Tính tổng tín chỉ hiện tại
    SELECT
        @TongTinChi = ISNULL(SUM(hp.SoTinChi),0)
    FROM DangKyHocPhan dk
    JOIN LopHocPhan lhp
        ON dk.MaLHP = lhp.MaLHP
    JOIN HocPhan hp
        ON lhp.MaHP = hp.MaHP
    WHERE dk.MaSV = @MaSV
      AND dk.TrangThai = N'Thành công';

    -- Giới hạn tối đa 18 tín chỉ
  IF (@TongTinChi + @SoTinChiMonMoi < 15)
BEGIN
    PRINT N'Tổng số tín chỉ hiện tại chưa đạt mức tối thiểu 15 tín chỉ';
END
    IF (@TongTinChi + @SoTinChiMonMoi >24)
    BEGIN
        PRINT N'Vượt quá số tín chỉ tối đa (24 tín chỉ)';
        RETURN;
    END

    -- Kiểm tra trùng lịch học
    IF EXISTS
    (
        SELECT 1
        FROM DangKyHocPhan dk
        JOIN ChiTietLopHocPhan ct1
            ON dk.MaLHP = ct1.MaLHP
        JOIN ChiTietLopHocPhan ct2
            ON ct2.MaLHP = @MaLHP
        WHERE dk.MaSV = @MaSV
          AND dk.TrangThai = N'Thành công'
          AND ct1.ThuHoc = ct2.ThuHoc
          AND ct1.CaHoc = ct2.CaHoc
    )
    BEGIN
        PRINT N'Trùng lịch học với lớp đã đăng ký';
        RETURN;
    END

    -- Đăng ký học phần
    INSERT INTO DangKyHocPhan
    (
        MaDK,
        TrangThai,
        LoaiDangKy,
        NgayDK,
        MaSV,
        MaLHP
    )
    VALUES
    (
        @MaDK,
        N'Thành công',
        @LoaiDangKy,
        GETDATE(),
        @MaSV,
        @MaLHP
    );
    COMMIT TRANSACTION;
    -- Cập nhật sĩ số lớp
   /* UPDATE LopHocPhan
    SET SoLuongDangKy = SoLuongDangKy + 1
    WHERE MaLHP = @MaLHP;*/

    PRINT N'Đăng ký học phần thành công';
    END TRY

    BEGIN CATCH

        ROLLBACK TRANSACTION;

        PRINT ERROR_MESSAGE();

    END CATCH


END
GO

--B. Hủy đăng ký học phần
DROP PROCEDURE IF EXISTS sp_HuyDangKyHocPhan;
GO

CREATE PROCEDURE sp_HuyDangKyHocPhan
(
    @MaDK VARCHAR(50)
)
AS
BEGIN
BEGIN TRY

        BEGIN TRANSACTION;
    DECLARE @MaLHP VARCHAR(20);

    -- Kiểm tra phiếu đăng ký tồn tại
    IF NOT EXISTS
    (
        SELECT 1
        FROM DangKyHocPhan
        WHERE MaDK = @MaDK
    )
    BEGIN
        PRINT N'Không tìm thấy phiếu đăng ký';
        RETURN;
    END

    -- Lấy mã lớp học phần để cập nhật sĩ số
    SELECT
        @MaLHP = MaLHP
    FROM DangKyHocPhan
    WHERE MaDK = @MaDK;

    -- Xóa đăng ký
    DELETE FROM DangKyHocPhan
    WHERE MaDK = @MaDK;
    COMMIT TRANSACTION;

    -- Cập nhật lại sĩ số lớp
  /*  UPDATE LopHocPhan
    SET SoLuongDangKy =
        CASE
            WHEN SoLuongDangKy > 0
            THEN SoLuongDangKy - 1
            ELSE 0
        END
    WHERE MaLHP = @MaLHP;*/

    PRINT N'Hủy đăng ký thành công';
    END TRY

    BEGIN CATCH

        ROLLBACK TRANSACTION;

        PRINT ERROR_MESSAGE();

    END CATCH
END
GO


--C. Tính tổng tín chỉ đã đăng ký của sinh viên

DROP PROCEDURE sp_TongTinChiSinhVien;
GO
CREATE PROCEDURE sp_TongTinChiSinhVien
(
    @MaSV VARCHAR(20)
)
AS
BEGIN
    SET NOCOUNT ON;

    
    -- 1. KIỂM TRA SINH VIÊN TỒN TẠI
    
    IF NOT EXISTS (
        SELECT 1
        FROM SinhVien
        WHERE MaSV = @MaSV
    )
    BEGIN
        PRINT N' Không tồn tại sinh viên có mã: ' + @MaSV;
        RETURN;
    END

    
    -- 2. TÍNH TỔNG TÍN CHỈ
        
    SELECT 
        sv.MaSV,
        sv.HoTen,

        -- tránh NULL nếu không có học phần
        COALESCE(SUM(hp.SoTinChi), 0) AS TongTinChi

    FROM SinhVien sv

    LEFT JOIN DangKyHocPhan dk
        ON sv.MaSV = dk.MaSV
        AND dk.TrangThai = N'Thành công'

    LEFT JOIN LopHocPhan lhp
        ON dk.MaLHP = lhp.MaLHP

    LEFT JOIN HocPhan hp
        ON lhp.MaHP = hp.MaHP

    WHERE sv.MaSV = @MaSV

    GROUP BY 
        sv.MaSV,
        sv.HoTen;

    
    -- 3. THÔNG BÁO TRƯỜNG HỢP CHƯA ĐĂNG KÝ
   
    IF NOT EXISTS (
        SELECT 1
        FROM DangKyHocPhan
        WHERE MaSV = @MaSV AND TrangThai = N'Thành công'
    )
    BEGIN
        PRINT N' Sinh viên chưa đăng ký học phần nào (hoặc chưa có đăng ký thành công).';
    END
END
GO


-- ============================================
-- D. 
--PROCEDURE: THÊM LỚP HỌC PHẦN MỚI
-- Chức năng:
-- Admin tạo một lớp học phần mới cho học kỳ
-- ============================================
DROP PROCEDURE sp_ThemLopHocPhan;
GO

CREATE PROCEDURE sp_ThemLopHocPhan
(
    @MaLHP VARCHAR(20),
    @MaHP VARCHAR(20),
    @MaHK VARCHAR(20),
    @SiSoToiDa INT,
    @NgayBatDau DATETIME = NULL,
    @NgayKetThuc DATETIME = NULL,
    @ThuHoc NVARCHAR(20) = NULL,
    @CaHoc NVARCHAR(20) = NULL,
    @PhongHoc NVARCHAR(50) = NULL 
)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY 
        BEGIN TRANSACTION;
    --------------------------------------------------
    -- 1. Kiểm tra mã lớp học phần đã tồn tại chưa
    --------------------------------------------------
        IF EXISTS
        (
            SELECT 1
            FROM LopHocPhan
            WHERE MaLHP = @MaLHP
        )
        BEGIN
            PRINT N'Mã lớp học phần đã tồn tại';
            RETURN;
        END

    --------------------------------------------------
    -- 2. Kiểm tra học phần có tồn tại không
    --------------------------------------------------
        IF NOT EXISTS
        (
            SELECT 1
            FROM HOCPHAN
            WHERE MaHP = @MaHP
        )
        BEGIN
            PRINT N'Học phần không tồn tại';
            RETURN;
        END

    --------------------------------------------------
    -- 3. Kiểm tra học kỳ có tồn tại không
    --------------------------------------------------
        IF NOT EXISTS
        (
            SELECT 1
            FROM HOCKY
            WHERE MaHK = @MaHK
        )
        BEGIN
            PRINT N'Học kỳ không tồn tại';
            RETURN;
        END

    --------------------------------------------------
    -- 4. Kiểm tra sĩ số tối đa hợp lệ
    --------------------------------------------------
        IF @SiSoToiDa <= 0
        BEGIN
            PRINT N'Sĩ số tối đa phải lớn hơn 0';
            RETURN;
        END

    --------------------------------------------------
    -- 5. Kiểm tra lịch học 
    --------------------------------------------------
        IF @ThuHoc IS NOT NULL
            AND @CaHoc IS NOT NULL
            AND @PhongHoc IS NOT NULL
        BEGIN
            IF @NgayBatDau IS NULL OR @NgayKetThuc IS NULL
            RAISERROR(N'Phải nhập ngày bắt đầu và ngày kết thúc.',16,1);
            IF @NgayBatDau >= @NgayKetThuc

    --------------------------------------------------
    -- 6. Kiểm tra trùng phòng học
    --------------------------------------------------
         IF EXISTS
         (
            SELECT 1
            FROM ChiTietLopHocPhan
            WHERE ThuHoc = @ThuHoc
                AND CaHoc = @CaHoc
                AND PhongHoc = @PhongHoc
                AND @NgayBatDau <= NgayKetThuc
                AND @NgayKetThuc >= NgayBatDau
         )
            RAISERROR(N'Phòng học đã được sử dụng trong khoảng thời gian này.',16,1);
    END
    --------------------------------------------------
    -- 7. Thêm lớp học phần mới
    --------------------------------------------------
        INSERT INTO LopHocPhan
        (
            MaLHP,
            MaHP,
            MaHK,
            SoLuongDangKy,
            SiSoToiDa
        )
        VALUES
        (
            @MaLHP,
            @MaHP,
            @MaHK,
            0,
            @SiSoToiDa
        );
    
    --------------------------------------------------
    -- 8. Thêm chi tiết lịch học
    --------------------------------------------------
        IF @ThuHoc IS NOT NULL AND @CaHoc IS NOT NULL
        BEGIN
            DECLARE @MaCTLHP NVARCHAR(20) = 'CT_' + @MaLHP;
            INSERT INTO ChiTietLopHocPhan (MaCTLHP, MaLHP, NgayBatDau, NgayKetThuc, ThuHoc, CaHoc, PhongHoc)
            VALUES (@MaCTLHP, @MaLHP, @NgayBatDau, @NgayKetThuc, @ThuHoc, @CaHoc, @PhongHoc);
        END
    
        COMMIT TRANSACTION;
    --------------------------------------------------
    -- 9. Thông báo thành công
    --------------------------------------------------
        SELECT 1 AS Success, N'Thêm lớp học phần thành công';
    END TRY

    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        SELECT 0 AS Success, ERROR_MESSAGE() AS MESSAGE;
    END CATCH
END
GO
-- ============================================
--E 
--PROCEDURE: CẬP NHẬT LỚP HỌC PHẦN
-- Chức năng:
-- Admin cập nhật thông tin lớp học phần
-- ============================================
DROP PROCEDURE IF EXISTS sp_CapNhatLopHocPhan;
GO

CREATE PROCEDURE sp_CapNhatLopHocPhan
(
    @MaLHP VARCHAR(20),
    @MaHP VARCHAR(20),
    @MaHK VARCHAR(20),
    @SiSoToiDa INT,
    @NgayBatDau DATETIME = NULL,
    @NgayKetThuc DATETIME = NULL,
    @ThuHoc NVARCHAR(20) = NULL,
    @CaHoc NVARCHAR(20) = NULL,
    @PhongHoc NVARCHAR(50) = NULL
)
AS
BEGIN
    SET NOCOUNT ON;

    SET TRANSACTION ISOLATION LEVEL READ COMMITTED;

    BEGIN TRY
        BEGIN TRANSACTION;
    --------------------------------------------------
    -- 1. Kiểm tra lớp học phần tồn tại
    --------------------------------------------------
            IF NOT EXISTS
            (
                SELECT 1
                FROM LopHocPhan
                WHERE MaLHP = @MaLHP
            )
            BEGIN
                PRINT N'Không tìm thấy lớp học phần';
                RETURN;
            END

    --------------------------------------------------
    -- 2. Kiểm tra học phần tồn tại
    --------------------------------------------------
            IF NOT EXISTS
            (
                SELECT 1
                FROM HOCPHAN
                WHERE MaHP = @MaHP
            )
            BEGIN
                PRINT N'Học phần không tồn tại';
                RETURN;
            END

    --------------------------------------------------
    -- 3. Kiểm tra học kỳ tồn tại
    --------------------------------------------------
            IF NOT EXISTS
            (
                SELECT 1
                FROM HOCKY
                WHERE MaHK = @MaHK
            )
            BEGIN
                PRINT N'Học kỳ không tồn tại';
                RETURN;
            END

    --------------------------------------------------
    -- 4. Kiểm tra sĩ số hợp lệ
    --------------------------------------------------
            IF @SiSoToiDa <= 0
            BEGIN
                PRINT N'Sĩ số tối đa phải lớn hơn 0';
                RETURN;
            END

    --------------------------------------------------
    -- 5. Không cho giảm sĩ số nhỏ hơn số SV đã đăng ký
    --------------------------------------------------
            IF EXISTS
            (
                SELECT 1
                FROM LopHocPhan
                WHERE MaLHP = @MaLHP
                AND SoLuongDangKy > @SiSoToiDa
            )
            BEGIN
                PRINT N'Sĩ số tối đa không được nhỏ hơn số lượng đã đăng ký';
                RETURN;
            END
    ----------------------------------------------
    -- 6. Cập nhật lớp học phần
    --------------------------------------------------
            UPDATE LopHocPhan
        SET
            MaHP = @MaHP,
            MaHK = @MaHK,
            SiSoToiDa = @SiSoToiDa
        WHERE MaLHP = @MaLHP;   
   
    --------------------------------------------------
    -- 7. Cập nhật lịch học
    --------------------------------------------------
            IF @ThuHoc IS NOT NULL
                OR @CaHoc IS NOT NULL
                OR @PhongHoc IS NOT NULL
                OR @NgayBatDau IS NOT NULL
                OR @NgayKetThuc IS NOT NULL
            BEGIN
                UPDATE ChiTietLopHocPhan
                SET
                    ThuHoc = ISNULL(@ThuHoc, ThuHoc),
                    CaHoc = ISNULL(@CaHoc, CaHoc),
                    PhongHoc = ISNULL(@PhongHoc, PhongHoc),
                    NgayBatDau = ISNULL(@NgayBatDau, NgayBatDau),
                    NgayKetThuc = ISNULL(@NgayKetThuc, NgayKetThuc)
                WHERE MaLHP = @MaLHP;
            END

            COMMIT TRANSACTION;


    --------------------------------------------------
    -- 8. Thông báo thành công
    --------------------------------------------------
            SELECT 1 AS Success, N'Cập nhật lớp học thành công' AS Message;

        END TRY
        
        BEGIN CATCH
            IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
            SELECT 0 AS Success, ERROR_MESSAGE() AS Message;
        END CATCH

END
GO


-- ============================================
--F.
-- PROCEDURE: CẬP NHẬT HỌC KỲ
-- Chức năng:
-- Admin cập nhật thông tin học kỳ
-- ============================================
DROP PROCEDURE IF EXISTS sp_CapNhatHocKy
GO

CREATE PROCEDURE sp_CapNhatHocKy
(
    @MaHK VARCHAR(20),
    @TenHK NVARCHAR(50),
    @NamHoc INT,
    @NgayMoDangKy DATETIME,
    @NgayDongDangKy DATETIME
)
AS
BEGIN

    --------------------------------------------------
    -- 1. Kiểm tra học kỳ tồn tại
    --------------------------------------------------
    IF NOT EXISTS
    (
        SELECT 1
        FROM HOCKY
        WHERE MaHK = @MaHK
    )
    BEGIN
        PRINT N'Học kỳ không tồn tại';
        RETURN;
    END

    --------------------------------------------------
    -- 2. Kiểm tra thời gian đăng ký hợp lệ
    --------------------------------------------------
    IF @NgayDongDangKy <= @NgayMoDangKy
    BEGIN
        PRINT N'Ngày đóng đăng ký phải lớn hơn ngày mở đăng ký';
        RETURN;
    END

    --------------------------------------------------
    -- 3. Kiểm tra năm học hợp lệ
    --------------------------------------------------
    IF @NamHoc <= 0
    BEGIN
        PRINT N'Năm học không hợp lệ';
        RETURN;
    END

    --------------------------------------------------
    -- 4. Cập nhật học kỳ
    --------------------------------------------------
    UPDATE HOCKY
    SET
        TenHK = @TenHK,
        NamHoc = @NamHoc,
        NgayMoDangKy = @NgayMoDangKy,
        NgayDongDangKy = @NgayDongDangKy
    WHERE MaHK = @MaHK;

    --------------------------------------------------
    -- 5. Thông báo thành công
    --------------------------------------------------
    PRINT N'Cập nhật học kỳ thành công';

END
GO


-- kiem thu stored procedure
-- Lệnh gọi để kiểm tra đăng ký học phần:
EXEC sp_DangKyHocPhan
    @MaDK = 'DK045',
    @MaSV = 'SV002',
    @MaLHP = 'LHP007',
    @LoaiDangKy = N'Học mới';
    SELECT *
FROM DangKyHocPhan
WHERE MaSV = 'SV002';
-- Lệnh gọi để kiểm tra hủy đăng ký học phần:
EXEC sp_HuyDangKyHocPhan
'DK021';

-- Lệnh gọi để kiểm tra tổng tín chỉ của sinh viên:
EXEC sp_TongTinChiSinhVien
    @MaSV = 'SV002';
-- Lệnh gọi để kiểm tra thêm lớp học phần mới:
EXEC sp_ThemLopHocPhan
    @MaLHP = 'LHP010',
    @MaHP = 'HP025',
    @MaHK = 'HK001',
    @SiSoToiDa = 60;
-- Lệnh gọi để kiểm tra cập nhật lớp học phần:
EXEC sp_CapNhatLopHocPhan
    @MaLHP = 'LHP001',
    @MaHP = 'HP002',
    @MaHK = 'HK001',
    @SiSoToiDa = 80;
-- Lệnh gọi để kiểm tra cập nhật học kỳ:
EXEC sp_CapNhatHocKy
    @MaHK = 'HK001',
    @TenHK = N'Học kỳ 1',
    @NamHoc = 2025,
    @NgayMoDangKy = '2025-08-01',
    @NgayDongDangKy = '2025-08-15';


 EXEC sp_CapNhatHocKy
    @MaHK = 'HK1_2026',
    @TenHK = N'Học kỳ 1',
    @NamHoc = 2026,
    @NgayMoDangKy = '2026-06-01',
    @NgayDongDangKy = '2026-07-01';