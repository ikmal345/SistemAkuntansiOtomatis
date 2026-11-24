




import datetime as dt

import pandas as pd
import streamlit as st
from sqlalchemy import delete, insert, select, update

from core.db import ambil, sesi, t_akun, t_detail, t_jurnal
from core.util import I, Z, B, angka, dec, kol, rp, tanggal, tgl as tgl_teks
from ui.komponen import NAN, jalankan, num, pesan, pilih_hapus, tampil, total_box

KOL_JURNAL = kol(("Tanggal", 105, "w"), ("Bukti", 90, "w"), ("Keterangan / Akun", 430, "w"), ("Ref", 70, "w"), ("Debit", 140, "e"), ("Kredit", 140, "e"))


# ------------------------------------------------------------------ simpan
def simpan_jurnal(jenis, prefix, tgl_s, bukti, ket, baris):
    """Jurnal manual. baris: [(kode, debit, kredit)]. Jurnal harus seimbang."""
    t, bersih = tanggal(tgl_s), []
    for kode, d, k in baris:
        d, k = angka(d), angka(k)
        if d < 0 or k < 0 or (d and k):
            raise ValueError("Tiap baris hanya boleh diisi di debit atau kredit, dan tidak boleh negatif.")
        if d or k:
            if not kode:
                raise ValueError("Ada nominal yang akunnya belum dipilih.")
            bersih.append((kode, d, k))
    if len(bersih) < 2:
        raise ValueError("Jurnal minimal terdiri dari dua baris akun.")
    td, tk = sum(x[1] for x in bersih), sum(x[2] for x in bersih)
    if td != tk:
        raise ValueError(f"Jurnal belum seimbang: debit {rp(td)}, kredit {rp(tk)}.")
    with sesi(True) as c:
        jid = c.execute(insert(t_jurnal).values(tanggal=t, bukti=bukti.strip(), keterangan=ket.strip(), jenis=jenis,
                                                sumber="MANUAL")).inserted_primary_key[0]
        if not bukti.strip():
            c.execute(update(t_jurnal).where(t_jurnal.c.id == jid).values(bukti=f"{prefix}-{jid:04d}"))
        _isi_detail(c, jid, bersih)


def _isi_detail(c, jid, baris):
    """baris: [(kode, debit, kredit)]"""
    for kode, d, k in baris:
        c.execute(insert(t_detail).values(jurnal_id=jid, kode=kode, debit=d, kredit=k))


def catat_otomatis(c, tgl, ket, baris, prefix, bukti=""):
    """Jurnal umum otomatis dari sebuah transaksi (dipanggil transaksi.py di dalam satu transaksi database).
    baris: [(kode, debit, kredit)]. Mengembalikan (id jurnal, nomor bukti)."""
    bukti = bukti.strip()
    jid = c.execute(insert(t_jurnal).values(tanggal=tgl, bukti=bukti, keterangan=ket, jenis="JU", sumber="TRANSAKSI")).inserted_primary_key[0]
    if not bukti:
        bukti = f"{prefix}-{jid:04d}"
        c.execute(update(t_jurnal).where(t_jurnal.c.id == jid).values(bukti=bukti))
    _isi_detail(c, jid, baris)
    return jid, bukti


def hapus_jurnal(jid):
    r = ambil(select(t_jurnal.c.sumber).where(t_jurnal.c.id == jid))
    if not r:
        raise ValueError("Jurnal tidak ditemukan.")
    if r[0]["sumber"] != "MANUAL":
        raise ValueError("Jurnal ini dibuat otomatis dari transaksi. Hapus lewat halaman transaksinya.")
    with sesi(True) as c:
        c.execute(delete(t_jurnal).where(t_jurnal.c.id == jid))


# ------------------------------------------------------------------ tabel
def tabel_jenis(jenis):
    """Daftar jurnal satu jenis (JU / AJP) lengkap dengan total debit dan kredit."""
    rows, td, tk, sudah = [], Z, Z, set()
    for r in ambil(
            select(t_jurnal.c.id, t_jurnal.c.tanggal, t_jurnal.c.bukti, t_jurnal.c.keterangan, t_jurnal.c.sumber,
                   t_detail.c.kode, t_akun.c.nama, t_detail.c.debit, t_detail.c.kredit)
            .select_from(t_jurnal.join(t_detail, t_detail.c.jurnal_id == t_jurnal.c.id).join(t_akun, t_akun.c.kode == t_detail.c.kode))
            .where(t_jurnal.c.jenis == jenis)
            .order_by(t_jurnal.c.tanggal, t_jurnal.c.id, t_detail.c.id)):
        d, k = dec(r["debit"]), dec(r["kredit"])
        td, tk = td + d, tk + k
        if r["id"] not in sudah:
            sudah.add(r["id"])
            rows.append(([r["tanggal"], r["bukti"], (r["keterangan"] or "") + ("" if r["sumber"] == "MANUAL" else "   [otomatis]")], "b", f"j{r['id']}_{len(rows)}"))
        rows.append((["", "", (I if k else "") + r["nama"], r["kode"], d, k], None, f"j{r['id']}_{len(rows)}"))
    if not rows:
        rows = [B("", "", "Belum ada jurnal. Catat lewat menu Input Transaksi di sebelah kiri.", tag="kosong")]
    return KOL_JURNAL, rows + [B("", "", "TOTAL", "", td, tk, tag="b")]


def tabel(b):
    return tabel_jenis("JU")


# ------------------------------------------------------------------ halaman
def halaman_jenis(jenis):
    tampil(*tabel_jenis(jenis))
    pilih_hapus(jenis, "Hapus jurnal", ambil(select(t_jurnal.c.id, t_jurnal.c.tanggal, t_jurnal.c.bukti, t_jurnal.c.keterangan)
                                                 .where(t_jurnal.c.jenis == jenis, t_jurnal.c.sumber == "MANUAL").order_by(t_jurnal.c.tanggal, t_jurnal.c.id)),
                lambda r: f"{r['bukti']}   {tgl_teks(r['tanggal'])}   {r['keterangan'] or ''}", lambda r: hapus_jurnal(r["id"]))


def halaman():
    st.caption("Jurnal bertanda [otomatis] berasal dari input Penerimaan, Pengeluaran, dan Transaksi Lainnya. Hapus lewat halaman transaksinya.")
    halaman_jenis("JU")


def form_input(jenis, prefix, nama, cepat=()):
    """Form jurnal manual (umum atau penyesuaian). Baris akun bisa ditambah, debit harus sama dengan kredit."""
    v = st.session_state.setdefault(f"v_{jenis}", 0)
    opsi = [f"{a['kode']}  {a['nama']}" for a in ambil(select(t_akun.c.kode, t_akun.c.nama).where(t_akun.c.kode != "3-103").order_by(t_akun.c.kode))]
    kosong = lambda: pd.DataFrame({"Akun": pd.Series([None] * 4, dtype="object"), "Debit": pd.Series([NAN] * 4), "Kredit": pd.Series([NAN] * 4)})
    awal = st.session_state.get(f"df_{jenis}")
    c = st.columns([1, 1, 3])
    tgl = c[0].date_input("Tanggal", dt.date.today(), format="DD/MM/YYYY", key=f"t_{jenis}_{v}")
    bukti = c[1].text_input("No. bukti (kosong = otomatis)", key=f"b_{jenis}_{v}")
    ket = c[2].text_input("Keterangan", value=st.session_state.get(f"kt_{jenis}", ""), key=f"k_{jenis}_{v}")
    if cepat:
        st.caption("Isi cepat")
        for kolom, (teks, kt, d, k) in zip(st.columns(len(cepat) + 2), cepat):
            if kolom.button(teks, key=f"c_{jenis}_{d}"):
                cari = lambda kode: next((o for o in opsi if o.startswith(kode + " ")), None)
                st.session_state[f"df_{jenis}"] = pd.DataFrame({"Akun": pd.Series([cari(d), cari(k), None, None], dtype="object"),
                                                                "Debit": pd.Series([NAN] * 4), "Kredit": pd.Series([NAN] * 4)})
                st.session_state[f"kt_{jenis}"], st.session_state[f"v_{jenis}"] = kt, v + 1
                st.rerun()
    df = st.data_editor(kosong() if awal is None else awal, num_rows="dynamic", hide_index=True, key=f"e_{jenis}_{v}",
                        column_config={"Akun": st.column_config.SelectboxColumn("Akun", options=opsi, width="large"),
                                       "Debit": st.column_config.NumberColumn("Debit", min_value=0, step=1000),
                                       "Kredit": st.column_config.NumberColumn("Kredit", min_value=0, step=1000)})
    d, k = sum((num(x) for x in df["Debit"]), Z), sum((num(x) for x in df["Kredit"]), Z)
    total_box(f"Total debit **Rp {rp(d, '0')}**  ·  Total kredit **Rp {rp(k, '0')}**")
    if d or k:
        (st.success if d == k else st.warning)("Seimbang" if d == k else f"Belum seimbang, selisih Rp {rp(abs(d - k))}")
    if st.button(f"Simpan {nama.lower()}", type="primary", key=f"s_{jenis}"):
        baris = [(a.split()[0] if isinstance(a, str) and a else "", num(x), num(y)) for a, x, y in zip(df["Akun"], df["Debit"], df["Kredit"])]
        if jalankan(simpan_jurnal, jenis, prefix, tgl.strftime("%d-%m-%Y"), bukti, ket, baris):
            st.session_state.pop(f"df_{jenis}", None)
            st.session_state.pop(f"kt_{jenis}", None)
            st.session_state[f"v_{jenis}"] = v + 1
            pesan("ok", f"{nama} tersimpan dan sudah masuk ke buku besar.")
            st.rerun()


def halaman_input():
    form_input("JU", "JU", "Jurnal Umum")
