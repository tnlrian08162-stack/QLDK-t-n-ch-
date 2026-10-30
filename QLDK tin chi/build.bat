@echo off
chcp 65001 >nul
echo ================================================
echo  Build QLSV DangKyHocPhan -- PyInstaller
echo ================================================

:: Kich hoat venv neu co
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated.
) else (
    echo [WARNING] Khong tim thay venv. Dung Python he thong.
)

:: Kiem tra PyInstaller
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Cai dat PyInstaller...
    pip install pyinstaller
)

:: Xoa build cu
if exist "build" rmdir /s /q "build"
if exist "dist\QLSV_DangKyHocPhan" rmdir /s /q "dist\QLSV_DangKyHocPhan"

echo.
echo [INFO] Dang build tu QLSV_DangKyHocPhan.spec ...
echo.

pyinstaller --noconfirm QLSV_DangKyHocPhan.spec

if errorlevel 1 (
    echo.
    echo [ERROR] Build that bai!
    pause
    exit /b 1
)

echo.
echo ================================================
echo  [SUCCESS] Build thanh cong!
echo  File exe: dist\QLSV_DangKyHocPhan\QLSV_DangKyHocPhan.exe
echo ================================================
echo.

:: Copy file .env vao dist de chay duoc
if exist ".env" (
    copy ".env" "dist\QLSV_DangKyHocPhan\.env" >nul
    echo [INFO] Da copy .env vao dist\
)

pause
