"""Jalankan aplikasi:  python jalankan.py
Menggantikan `streamlit run app.py`, sekaligus mengatur warna tema Streamlit lewat Python (tanpa file .toml)."""
import os
import subprocess
import sys

TEMA = {"BASE": "light", "PRIMARY_COLOR": "#3E6B3A", "BACKGROUND_COLOR": "#FFFFFF",
        "SECONDARY_BACKGROUND_COLOR": "#F4F8E2", "TEXT_COLOR": "#2B2119"}


def main():
    env = dict(os.environ)
    for kunci, nilai in TEMA.items():
        env.setdefault("STREAMLIT_THEME_" + kunci, nilai)
    folder = os.path.dirname(os.path.abspath(__file__))
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py", *sys.argv[1:]], cwd=folder, env=env))


if __name__ == "__main__":
    main()
