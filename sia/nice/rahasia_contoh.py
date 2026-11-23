"""Salin file ini menjadi rahasia.py lalu isi (rahasia.py jangan diunggah ke GitHub).
Di Streamlit Community Cloud, isi Settings > Secrets dengan nama yang sama seperti environment variable di core/config.py
(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_DATABASE, ADMIN_USERNAME, ADMIN_PASSWORD, APP_PASSWORD)."""

MYSQL = dict(host="localhost", port=3306, user="root", password="", database="alpukat estate")

# Login (pilih salah satu, atau hapus keduanya bila dipakai sendiri di komputer sendiri tanpa login):
ADMIN = dict(username="admin", password="ganti-dengan-password")

# atau cukup satu kata sandi:
# APP_PASSWORD = "ganti-dengan-kata-sandi"
