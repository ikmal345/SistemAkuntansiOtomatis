


import os

try:
    import rahasia as _r
except ImportError:
    _r = None

_MYSQL = getattr(_r, "MYSQL", None) or {}
_ADMIN = getattr(_r, "ADMIN", None) or {}


def _db(kunci, default):
    return _MYSQL.get(kunci) or os.getenv("DB_" + kunci.upper(), default)


DB = {
    "host": _db("host", "localhost"),
    "port": int(_db("port", 3306)),
    "user": _db("user", "root"),
    "password": _db("password", ""),          # kosong = tanpa password
    "database": _db("database", "alpukat estate"),
}

# login: pilih username + password, atau satu kata sandi saja; semuanya kosong = aplikasi terbuka tanpa login
ADMIN_USER = _ADMIN.get("username") or os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = _ADMIN.get("password") or os.getenv("ADMIN_PASSWORD")
APP_PASSWORD = getattr(_r, "APP_PASSWORD", None) or os.getenv("APP_PASSWORD")
