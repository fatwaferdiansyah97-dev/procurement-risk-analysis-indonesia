# 01_reduksi.py
# Mengecilkan berkas GTI 10,79 GB menjadi tiga berkas kerja yang ringan.
 
import csv, gzip, time
 
csv.field_size_limit(10**9)
 
SUMBER            = r"C:\Users\cipen\Downloads\ID_data_202402_gti.csv\ID_data_202402_gti.csv"
KELUARAN_KONTRAK  = r"C:\risk_project\kontrak_menang.csv.gz"
KELUARAN_PAKET    = r"C:\risk_project\statistik_paket.csv"
KELUARAN_PENYEDIA = r"C:\risk_project\statistik_penyedia.csv"
 
# 54 kolom dari 187.
KOLOM_SIMPAN = [
    "tender_id", "lot_id", "bid_id", "tender_year",
    "buyer_masterid", "buyer_name", "buyer_city_here", "buyer_county_here",
    "bidder_masterid", "bidder_id", "bidder_name",
    "bidder_city_clean", "bidder_state_clean",
    "tender_title", "tender_proceduretype", "tender_nationalproceduretype",
    "tender_supplytype",
    "lot_bidscount", "tender_recordedbidscount", "tender_lotscount",
    "tender_corrections_count",
    "bid_iswinning", "lot_status", "tender_isawarded", "tender_selectionmethod",
    "bid_price_local_currency", "tender_estimatedprice_local_currency", "savings",
    "cpv_code", "tender_maincpv",
    "advertisement_period", "decision_period", "award_period_length",
    "tender_biddeadline", "tender_publications_firstcallfortenderdate",
    "tender_awarddecisiondate", "tender_contractsignaturedate",
    "corr_singleb", "corr_proc", "corr_subm", "corr_decp",
    "corr_buyer_concentration", "corr_benfords",
    "INTEGRITY_SINGLE_BID", "INTEGRITY_PROCEDURE_TYPE",
    "INTEGRITY_ADVERTISEMENT_PERIOD", "INTEGRITY_DECISION_PERIOD",
    "INTEGRITY_BUYER_CONCENTRATION",
    "local", "local_province", "url_short", "notice_url",
    "tender_description_length", "tender_technicalrequirements_length",
]
 
berkas = open(SUMBER, "rb")
judul  = next(csv.reader([berkas.readline().decode("utf-8", "replace")]))
posisi = {nama: i for i, nama in enumerate(judul)}
indeks_simpan = [posisi[k] for k in KOLOM_SIMPAN]
 
i_lot           = posisi["lot_id"]
i_menang        = posisi["bid_iswinning"]
i_harga         = posisi["bid_price_local_currency"]
i_hps           = posisi["tender_estimatedprice_local_currency"]
i_penyedia      = posisi["bidder_masterid"]
i_nama_penyedia = posisi["bidder_name"]
i_ok            = posisi["filter_ok"]
 
keluaran = gzip.open(KELUARAN_KONTRAK, "wt", newline="",
                     encoding="utf-8", compresslevel=5)
penulis = csv.writer(keluaran)
penulis.writerow(KOLOM_SIMPAN)
 
paket, penyedia = {}, {}
jumlah_baris = jumlah_simpan = 0
mulai = time.time()
sisa = None
 
while True:
    baris = berkas.readline()
    if not baris:
        break
    teks = baris.decode("utf-8", "replace")
    if sisa is not None:
        teks = sisa + teks
        sisa = None
    # satu nilai bertanda kutip bisa terpotong menjadi dua baris
    if teks.count('"') % 2 == 1:
        sisa = teks
        continue
    try:
        data = next(csv.reader([teks]))
    except Exception:
        continue
    if len(data) != len(judul):
        continue
    jumlah_baris += 1
 
    # statistik per paket, dihitung dari SELURUH baris termasuk penawar kalah
    kunci_lot = data[i_lot]
    if kunci_lot:
        rekam = paket.get(kunci_lot)
        if rekam is None:
            # n_baris, n_bernama, n_harga, total, total_kuadrat, min, max, menang, hps
            rekam = [0, 0, 0, 0.0, 0.0, None, None, None, None]
            paket[kunci_lot] = rekam
        rekam[0] += 1
        if data[i_nama_penyedia]:
            rekam[1] += 1
        nilai = None
        if data[i_harga]:
            try:
                nilai = float(data[i_harga])
            except ValueError:
                nilai = None
        if nilai is not None and nilai > 0:
            rekam[2] += 1
            rekam[3] += nilai
            rekam[4] += nilai * nilai
            if rekam[5] is None or nilai < rekam[5]:
                rekam[5] = nilai
            if rekam[6] is None or nilai > rekam[6]:
                rekam[6] = nilai
        if data[i_menang] == "t":
            if nilai is not None:
                rekam[7] = nilai
            if data[i_hps]:
                try:
                    rekam[8] = float(data[i_hps])
                except ValueError:
                    pass
 
    # statistik per penyedia
    kunci_penyedia = data[i_penyedia]
    if kunci_penyedia:
        rp = penyedia.get(kunci_penyedia)
        if rp is None:
            rp = [0, 0, 0.0]
            penyedia[kunci_penyedia] = rp
        rp[0] += 1
        if data[i_menang] == "t":
            rp[1] += 1
            if data[i_harga]:
                try:
                    rp[2] += float(data[i_harga])
                except ValueError:
                    pass
 
    # baris yang disimpan. filter_ok memakai huruf kecil t, bukan TRUE
    if data[i_ok] == "t":
        jumlah_simpan += 1
        penulis.writerow([data[i] for i in indeks_simpan])
 
    if jumlah_baris % 500000 == 0:
        print(jumlah_baris, "baris,", jumlah_simpan, "disimpan,",
              round(time.time() - mulai), "detik")
 
keluaran.close()
 
with open(KELUARAN_PAKET, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["lot_id", "n_baris", "n_penyedia_bernama", "n_harga",
                "total_harga", "total_kuadrat", "harga_min", "harga_max",
                "harga_menang", "hps"])
    for k, r in paket.items():
        w.writerow([k, r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]])
 
with open(KELUARAN_PENYEDIA, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["bidder_masterid", "n_penawaran", "n_menang", "total_nilai_menang"])
    for k, r in penyedia.items():
        w.writerow([k, r[0], r[1], r[2]])
 
print("SELESAI")
print("total baris    :", jumlah_baris)
print("baris pemenang :", jumlah_simpan)
print("jumlah paket   :", len(paket))
print("jumlah penyedia:", len(penyedia))
print("waktu (detik)  :", round(time.time() - mulai))