"""Komponen tampilan yang dipakai semua halaman: tabel, pesan, tombol hapus, dan pembantu kecil lainnya."""
import datetime as dt

import pandas as pd
import streamlit as st

from core.util import D, Z, angka, rp, tgl

NAN = float("nan")


def num(x):
    """Isi sel / kolom angka -> Decimal (kosong dianggap 0)."""
    return angka(x) if x is not None and not pd.isna(x) else Z


def pesan(jenis, teks):
    """Simpan pesan untuk ditampilkan di halaman berikutnya (setelah st.rerun)."""
    st.session_state["pesan"] = (jenis, teks)


def buka(halaman):
    st.session_state["hal"] = halaman


def jalankan(fn, *arg):
    """Salah input tampil sebagai pesan merah. Mengembalikan True bila berhasil."""
    try:
        fn(*arg)
        return True
    except ValueError as e:
        st.error(str(e))
    except Exception as e:
        st.error(f"{e}\n\nPeriksa koneksi MySQL (rahasia.py atau core/config.py) dan pastikan database menyala.")
    return False


def bagian(teks, nomor=None):
    """Judul kecil untuk satu bagian halaman, dengan nomor bila ada."""
    st.subheader(f"{nomor}. {teks}" if nomor else teks)


def catatan(teks):
    """Kotak catatan (teks biasa; gunakan **tebal** gaya markdown bila perlu)."""
    st.info(teks, icon="📝")


def total_box(teks):
    """Kotak ringkasan angka, mis. total debit dan kredit."""
    st.success(teks, icon="🧮")


def fmt(sel, tag):
    """Sel tabel -> teks. Angka nol ditulis kosong, kecuali pada baris tebal (jumlah dan total)."""
    if isinstance(sel, dt.date):
        return tgl(sel)
    if isinstance(sel, D):
        return rp(sel, "0" if tag == "b" else "")
    return "" if sel is None else str(sel)


def tampil(kolom, baris):
    """Tabel bawaan Streamlit. baris = (isi sel, tag, iid)."""
    data = []
    for isi, tag, *_ in baris:
        sel = [fmt(x, tag) for x in isi]
        data.append((sel + [""] * len(kolom))[:len(kolom)])
    df = pd.DataFrame(data, columns=[j for j, _, _ in kolom])
    st.dataframe(df, hide_index=True, use_container_width=True, height=min(740, 38 + 35 * max(len(df), 1)))


def pilih_hapus(kunci, judul, daftar, label, aksi):
    """Kotak hapus: pilih satu baris dari daftar lalu hapus."""
    if not daftar:
        return
    with st.expander(judul):
        i = st.selectbox("Pilih", range(len(daftar)), format_func=lambda i: label(daftar[i]), key=f"sel_{kunci}")
        if st.button(judul, key=f"hps_{kunci}") and jalankan(aksi, daftar[i]):
            pesan("ok", "Data dihapus.")
            st.rerun()
