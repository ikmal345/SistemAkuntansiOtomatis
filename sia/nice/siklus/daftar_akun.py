


import streamlit as st
from sqlalchemy import delete, func, insert, select

from core.buku import Buku
from core.db import ambil, sesi, t_akun, t_detail, t_saldo_awal
from core.konstanta import DIKUNCI
from core.util import B, dec, kol
from siklus import transaksi
from ui.komponen import bagian, catatan, jalankan, pesan, tampil

KELOMPOK = ["Aset", "Liabilitas", "Ekuitas", "Pendapatan", "Pembelian", "HPP", "Beban"]
KOL_AKUN = kol(("Kode", 90, "w"), ("Nama Akun", 340, "w"), ("Kelompok", 130, "w"), ("Saldo Normal", 110, "w"), ("Status", 330, "w"))


def tambah_akun(kode, nama, kelompok, normal):
    kode, nama = kode.strip(), nama.strip()
    if not kode or not nama:
        raise ValueError("Kode dan nama akun wajib diisi.")
    if ambil(select(t_akun.c.kode).where(t_akun.c.kode == kode)):
        raise ValueError("Kode akun sudah dipakai.")
    with sesi(True) as c:
        c.execute(insert(t_akun).values(kode=kode, nama=nama, kelompok=kelompok, saldo_normal=normal))


def alasan_terkunci():
    """{kode: alasan akun tidak bisa dihapus}. Akun yang tidak ada di kamus ini aman dihapus."""
    alasan = {k: "Dikunci: dipakai langsung oleh laporan keuangan" for k in DIKUNCI}
    for r in ambil(select(t_detail.c.kode, func.count().label("n")).group_by(t_detail.c.kode)):
        alasan.setdefault(r["kode"], f"Sudah dipakai di {r['n']} baris jurnal, hapus jurnalnya dulu")
    for r in ambil(select(t_saldo_awal.c.kode, t_saldo_awal.c.debit, t_saldo_awal.c.kredit, t_saldo_awal.c.qty)):
        if dec(r["debit"]) or dec(r["kredit"]) or dec(r["qty"]):
            alasan.setdefault(r["kode"], "Punya saldo awal, kosongkan dulu di Saldo Awal")
    return alasan


def hapus_akun(kode):
    a = ambil(select(t_akun.c.kode).where(t_akun.c.kode == kode))
    if not a:
        raise ValueError("Akun tidak ditemukan.")
    alasan = alasan_terkunci().get(kode)
    if alasan:
        raise ValueError(f"Akun {kode} tidak bisa dihapus. {alasan}.")
    with sesi(True) as c:
        c.execute(delete(t_saldo_awal).where(t_saldo_awal.c.kode == kode))
        c.execute(delete(t_akun).where(t_akun.c.kode == kode))


def tabel(b):
    alasan = alasan_terkunci()
    return KOL_AKUN, [B(a["kode"], a["nama"], a["kelompok"], "Debit" if a["saldo_normal"] == "D" else "Kredit",
                        alasan.get(a["kode"], "Bebas dihapus")) for a in b.akun]


def halaman():
    bagian("Tambah akun baru", 1)
    with st.form("form_akun", clear_on_submit=True):
        c = st.columns([1, 3, 1.5, 1.2])
        kode, nama = c[0].text_input("Kode"), c[1].text_input("Nama akun")
        kel = c[2].selectbox("Kelompok", KELOMPOK)
        normal = c[3].selectbox("Saldo normal", ["Debit", "Kredit"])
        ok = st.form_submit_button("Tambah akun")
    if ok and jalankan(tambah_akun, kode, nama, kel, "D" if normal == "Debit" else "K"):
        pesan("ok", f"Akun {kode} ditambahkan.")
        st.rerun()

    bagian("Daftar akun", 2)
    b = Buku()
    tampil(*tabel(b))

    bagian("Hapus akun", 3)
    alasan = alasan_terkunci()
    if st.session_state.get("hapus_akun_pilih") not in b.a:      # akun yang baru dihapus tidak lagi ada di daftar
        st.session_state.pop("hapus_akun_pilih", None)
    kode = st.selectbox("Pilih akun yang akan dihapus", [a["kode"] for a in b.akun], key="hapus_akun_pilih",
                        format_func=lambda k: f"{k}   {b.a[k]['nama']}")
    if alasan.get(kode):
        st.warning(f"Akun ini belum bisa dihapus. {alasan[kode]}.")
    else:
        dampak = transaksi.item_terdampak(kode)
        if dampak:
            catatan("Bila akun ini dihapus, jenis transaksi berikut ikut hilang dari daftar input: **" + "; ".join(dampak) + "**.")
        yakin = st.checkbox(f"Ya, saya yakin ingin menghapus akun {kode} {b.a[kode]['nama']}", key=f"yakin_{kode}")
        if st.button("Hapus akun", key="btn_hapus_akun", disabled=not yakin) and jalankan(hapus_akun, kode):
            pesan("ok", f"Akun {kode} dihapus.")
            st.rerun()
