import os
import sys
from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    """Tìm đường dẫn gốc cho file .exe"""
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(_BASE_DIR, ".env"))

# set database
server = os.getenv("server") or os.getenv("SERVER")
if not server:
    server = r"localhost\SQLEXPRESS"

DB_CONFIG = {
    "driver": os.getenv("driver", os.getenv("DRIVER", "{ODBC Driver 18 for SQL Server}")),
    "server": server,
    "database": os.getenv("database", os.getenv("DATABASE", "QuanLyDangKyHocPhan")),
}
