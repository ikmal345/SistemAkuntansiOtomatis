"""BERANDA - ringkasan keuangan, tiga pintu input transaksi, dan alur siklus akuntansi."""
import streamlit as st  # type: ignore[reportMissingImports]
from sqlalchemy import func, select, update  # type: ignore[reportMissingImports]

from core.buku import Buku
from core.db import ambil, sesi, t_jurnal, t_pengaturan, t_transaksi
from core.util import Z, rp
from siklus import laporan, neraca_saldo, persediaan
from ui.komponen import bagian, buka, jalankan, pesan


def _ringkasan(b):
    n = b.net(("JU", "AJP"))
    g = lambda k: n.get(k, Z)
    try:
        segar = persediaan.stok("1-104")[0]
    except Exception:
        segar = Z
    return [("Kas dan Bank", f"Rp {rp(g('1-101') + g('1-102'), '0')}", "uang di tangan"),
            ("Piutang Usaha", f"Rp {rp(g('1-103'), '0')}", "belum diterima dari customer"),
            ("Utang Usaha", f"Rp {rp(-g('2-101'), '0')}", "belum dibayar ke supplier"),
            ("Stok Alpukat Segar", f"{persediaan.kgs(segar)} kg", "di kartu stok"),
            ("Laba Berjalan", f"Rp {rp(laporan.hitung(b)['laba'], '0')}", "sementara, periode ini")]


def simpan_periode(usaha, periode, awal, akhir):
    if akhir < awal:
        raise ValueError("Tanggal akhir tidak boleh sebelum tanggal awal.")
    with sesi(True) as c:
        c.execute(update(t_pengaturan).where(t_pengaturan.c.id == 1).values(
            nama_usaha=usaha.strip() or "Ambarawa Avocado", nama_periode=periode.strip(), tgl_awal=awal, tgl_akhir=akhir))


def halaman():
    b = Buku()
    with st.container(border=True):
        st.caption(b.pg["nama_periode"].upper())
        st.header("🥑 " + b.pg["nama_usaha"])
        st.write("Catat dari tiga pintu: penerimaan, pengeluaran, dan transaksi lainnya. Sisanya mengalir otomatis sampai laporan keuangan.")
    ringkas = _ringkasan(b)
    for kolom, (j_, v, k) in zip(st.columns(len(ringkas)), ringkas):
        with kolom.container(border=True):
            st.caption(j_)
            st.write(f"**{v}**")
            st.caption(k)

    bagian("Catat transaksi")
    pintu = [("", "Penerimaan", "Penjualan alpukat, pelunasan piutang, setoran modal, dan uang masuk lainnya.", "terima"),
             ("k2", "Pengeluaran", "Pembelian alpukat, bayar gaji, air, listrik, perawatan, dan uang keluar lainnya.", "keluar"),
             ("k3", "Transaksi Lainnya", "Pembelian atau penjualan kredit, gaji terutang, dan produksi frozen.", "lain")]
    for kolom, (_, judul, ket, tujuan) in zip(st.columns(3), pintu):
        with kolom.container(border=True):
            st.subheader(judul)
            st.write(ket)
            st.button(f"Buka {judul}", key=f"bi_{tujuan}", on_click=buka, args=(tujuan,), type="primary", use_container_width=True)
    st.caption("Input lain: saldo awal dan jurnal manual")
    for kolom, (teks, k) in zip(st.columns(3), [("Input Saldo Awal", "in_saldo"), ("Input Jurnal Umum Manual", "in_ju"), ("Input Jurnal Penyesuaian", "in_ajp")]):
        kolom.button(teks, key=f"bi_{k}", on_click=buka, args=(k,), use_container_width=True)

    n = {r["jenis"]: r["n"] for r in ambil(select(t_jurnal.c.jenis, func.count().label("n")).group_by(t_jurnal.c.jenis))}
    jt = {r["kelompok"]: r["n"] for r in ambil(select(t_transaksi.c.kelompok, func.count().label("n")).group_by(t_transaksi.c.kelompok))}
    awal = any(d or k for d, k, _ in b.sa.values())
    _, rows = neraca_saldo.tabel(b)
    td, tkr = rows[-1][0][2], rows[-1][0][3]
    langkah = [("saldo_awal", "Saldo awal", "sudah terisi" if awal else "belum diisi", awal),
               ("ju", "Jurnal umum", f"{n.get('JU', 0)} jurnal, {sum(jt.values())} dari transaksi", bool(n.get("JU"))),
               ("bb", "Buku besar", "otomatis", True),
               ("ns", "Neraca saldo", "seimbang" if td == tkr and td else "menunggu data", bool(td) and td == tkr),
               ("ajp", "Jurnal penyesuaian", f"{n.get('AJP', 0)} jurnal", bool(n.get("AJP"))), ("nl", "Neraca lajur", "otomatis", True),
               ("lap", "Laporan keuangan", "otomatis", True), ("pnt", "Jurnal penutup", "tersimpan" if n.get("PNT") else "belum disimpan", bool(n.get("PNT")))]
    kiri, kanan = st.columns([3, 2])
    with kiri:
        bagian("Alur siklus")
        for kunci, teks, ket, selesai in langkah:
            c = st.columns([0.35, 3, 2.6], vertical_alignment="center")
            c[0].write("🟢" if selesai else "⚪")
            c[1].button(teks, key=f"al_{kunci}", on_click=buka, args=(kunci,))
            c[2].caption(ket)
    with kanan:
        bagian("Periode")
        with st.form("form_periode"):
            usaha, periode = st.text_input("Nama usaha", b.pg["nama_usaha"]), st.text_input("Nama periode", b.pg["nama_periode"])
            c = st.columns(2)
            a, z = c[0].date_input("Tanggal awal", b.pg["tgl_awal"], format="DD/MM/YYYY"), c[1].date_input("Tanggal akhir", b.pg["tgl_akhir"], format="DD/MM/YYYY")
            ok = st.form_submit_button("Simpan periode")
        if ok and jalankan(simpan_periode, usaha, periode, a, z):
            pesan("ok", "Periode disimpan.")
            st.rerun()
