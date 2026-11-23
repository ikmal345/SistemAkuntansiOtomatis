"""Pengaturan koneksi MySQL dan login.
Urutan pembacaan: rahasia.py -> Streamlit Secrets -> environment variable -> nilai default.
"""
import os
import streamlit as st

try:
    import rahasia as _r
except ImportError:
    _r = None

_MYSQL = getattr(_r, "MYSQL", None) or {}
_ADMIN = getattr(_r, "ADMIN", None) or {}

# Cek apakah [db] tersedia di st.secrets (Streamlit Cloud)
_st_db = st.secrets.get("db", {})

def _db(kunci, default):
    # Prioritas 1: Streamlit Secrets ([db] di Settings > Secrets)
    if kunci in _st_db:
        return _st_db[kunci]
    # Prioritas 2: rahasia.py
    if kunci in _MYSQL:
        return _MYSQL[kunci]
    # Prioritas 3: Environment variable atau default
    return os.getenv("DB_" + kunci.upper(), default)

DB = {
    "host": _db("host", "localhost"),
    "port": int(_db("port", 3306)),
    "user": _db("user", "root"),
    "password": _db("password", ""),
    "database": _db("database", "alpukat_estate"),
}

# login: pilih username + password, atau satu kata sandi saja
ADMIN_USER = _ADMIN.get("username") or os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = _ADMIN.get("password") or os.getenv("ADMIN_PASSWORD")
APP_PASSWORD = getattr(_r, "APP_PASSWORD", None) or os.getenv("APP_PASSWORD")