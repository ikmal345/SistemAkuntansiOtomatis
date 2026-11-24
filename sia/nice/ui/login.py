
import streamlit as st

from core import config



def perlu_login():
    return bool((config.ADMIN_USER and config.ADMIN_PASSWORD) or config.APP_PASSWORD)


def gerbang():
    """Hentikan halaman dengan form login bila belum masuk."""
    if not perlu_login() or st.session_state.get("masuk"):
        return
    user, pw, sandi = config.ADMIN_USER, config.ADMIN_PASSWORD, config.APP_PASSWORD
    _, tengah, _ = st.columns([1, 1.6, 1])
    with tengah:
        st.title("🥑 Ambarawa Avocado")
        st.caption("Sistem akuntansi kebun alpukat. Silakan masuk untuk melanjutkan.")
        with st.form("form_login"):
            u = st.text_input("Username") if user and pw else None
            p = st.text_input("Password" if user and pw else "Kata sandi", type="password")
            kirim = st.form_submit_button("Masuk", use_container_width=True, type="primary")
        if kirim:
            benar = (u == str(user) and p == str(pw)) if user and pw else p == str(sandi)
            if benar:
                st.session_state["masuk"] = True
                st.rerun()
            st.error("Username atau password salah." if user and pw else "Kata sandi salah.")
    st.stop()


def tombol_keluar():
    """Tombol keluar di sidebar, hanya muncul jika login dipakai."""
    if perlu_login() and st.sidebar.button("Keluar", key="m_keluar_login"):
        st.session_state["masuk"] = False
        st.rerun()
