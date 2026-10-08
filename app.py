import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import datetime
import os

# ----------------- KONFIGURASI HALAMAN -----------------
st.set_page_config(
    page_title="Dashboard Patrol 5S",
    page_icon="🧹",
    layout="wide"
)

# Custom Styling Adaptif (Dark & Light Mode Support)
st.markdown("""
    <style>
    .dashboard-title {
        color: var(--primary-color, #1370a6);
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .dashboard-subtitle {
        color: var(--text-color);
        opacity: 0.7;
        font-size: 14px;
        margin-bottom: 20px;
    }

    .section-header {
        color: var(--primary-color, #1370a6);
        font-size: 18px;
        font-weight: 700;
        letter-spacing: 0.5px;
        border-bottom: 2px solid var(--primary-color, #1370a6);
        padding-bottom: 5px;
        margin-top: 20px;
        margin-bottom: 15px;
    }

    /* Tabel 5S Adaptif */
    .table-container {
        overflow-x: auto;
    }
    .table-5s {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        margin-bottom: 15px;
        font-size: 12px;
        text-align: center;
        background-color: var(--secondary-background-color, rgba(255, 255, 255, 0.05));
        border-radius: 8px;
        overflow: hidden;
    }
    .table-5s th {
        background-color: var(--primary-color, #1370a6);
        color: #ffffff !important;
        padding: 10px 6px;
        font-weight: 600;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .table-5s td {
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 8px 6px;
        color: var(--text-color);
    }
    .bg-label { 
        background-color: rgba(128, 128, 128, 0.1); 
        font-weight: bold; 
        color: var(--text-color); 
        text-align: left; 
        padding-left: 10px !important; 
    }
    
    .judge-ok { background-color: rgba(46, 125, 50, 0.2); color: #2e7d32; font-weight: bold; }
    .judge-ng { background-color: rgba(198, 40, 40, 0.2); color: #c62828; font-weight: bold; }

    /* Box Kesimpulan Adaptif */
    .summary-box {
        background-color: var(--secondary-background-color, rgba(255, 255, 255, 0.05));
        border-left: 4px solid var(--primary-color, #1370a6);
        border-radius: 6px;
        padding: 14px 18px;
        margin-top: 12px;
        font-size: 13px;
        color: var(--text-color);
        line-height: 1.6;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .summary-box-global {
        background-color: rgba(46, 125, 50, 0.1);
        border-left: 5px solid #2e7d32;
        padding: 15px 20px;
        border-radius: 8px;
        margin-top: 25px;
        font-size: 14px;
        color: var(--text-color);
        line-height: 1.6;
    }

    /* Badge Level 5S */
    .badge-level {
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 11px;
        display: inline-block;
        color: white !important;
    }
    .lvl-black { background-color: #374151; }
    .lvl-bronze { background-color: #d97706; }
    .lvl-silver { background-color: #6b7280; }
    .lvl-gold { background-color: #eab308; }

    /* Card Box Analisa */
    .analysis-card {
        background-color: var(--secondary-background-color, #ffffff);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-top: 4px solid #d32f2f;
        border-radius: 6px;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- LINK GOOGLE SHEETS DATA UTAMA (PUBLISH / READ-ONLY) -----------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQU_jpdzrymx_0mJKGVDopip0DPhnmDLIbsTHgVnqgaJZZayJUp-UPF1MF6H6soCA/pub?output=csv"

@st.cache_data(ttl=10)
def load_data(url):
    try:
        df_load = pd.read_csv(url)
        df_load.columns = df_load.columns.astype(str).str.strip()
        return df_load
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
        return pd.DataFrame()

df = load_data(SHEET_URL)

# ----------------- STORAGE LOKAL CSV UNTUK CAPA LOG -----------------
CAPA_CSV_FILE = "capa_log_database.csv"

def load_capa_from_gsheets():
    if os.path.exists(CAPA_CSV_FILE):
        try:
            df_capa = pd.read_csv(CAPA_CSV_FILE)
            return df_capa.to_dict("records")
        except Exception:
            return []
    return []

def save_capa_to_gsheets(data_list):
    df_capa = pd.DataFrame(data_list)
    df_capa.to_csv(CAPA_CSV_FILE, index=False)

if "capa_log_data" not in st.session_state:
    st.session_state["capa_log_data"] = load_capa_from_gsheets()

# ----------------- LIST 11 KRITERIA PENILAIAN EXPLICIT -----------------
DEFAULT_KRITERIA_LIST = [
    "Sekitar area kerja",
    "Penyimpanan Cairan B3",
    "Penyimpanan RM/WIP/FG",
    "Penyimpanan Consumable",
    "Area Kerja di Lapangan",
    "Peralatan Kerja",
    "Penyimpanan Master Work",
    "Informasi Terdokumentasi",
    "Tempat Istirahat",
    "Meja Kerja Leader",
    "Penempatan Dokumen"
]

# ----------------- REKOMENDASI RCA & ACTION PLAN PER JENJANG JABATAN -----------------
RCA_RECOMMENDATION = {
    "Sekitar area kerja": {
        "cause": "(1) Garis kuning pembatas rusak, pudar, atau hilang. (2) Lantai kotor/rusak karena terkena bahan kimia atau tergores. (3) Trolley lewat sembarangan di luar jalur hijau.",
        "action_operator": "(1) Dilarang lewat/menginjak jalur yang bukan peruntukannya. (2) Rapikan trolley dan selalu lewati jalur hijau.",
        "action_gl": "Lakukan patroli harian jalur hijau dan laporkan demarkasi/garis kuning yang rusak ke Foreman.",
        "action_foreman": "Buat Work Order (WO) perbaikan/pengecatan ulang lantai ke tim Facility/Maintenance.",
        "action_sh": "Evaluasi alur Material Handling (trolley) dan validasi standar proteksi lantai di area produksi.",
        "action_dh": "Disetujui anggaran pemeliharaan fasilitas pabrik dan terapkan regulasi kedisiplinan (5S Policy)."
    },
    "Penyimpanan Cairan B3": {
        "cause": "(1) Tidak ada wadah/nampan penampung tumpahan oli/kimia. (2) Kertas petunjuk B3 (MSDS) dan stiker bahaya tidak terpasang/rusak.",
        "action_operator": "(1) Gunakan nampan penampung di bawah wadah B3. (2) Sediakan majun/spill kit di dekat lokasi simpan.",
        "action_gl": "Pastikan semua wadah B3 di area memiliki stiker bahaya dan MSDS yang terlapisi plastik transparan.",
        "action_foreman": "Audit ketersediaan sarana Spill Kit & kelayakan sekunder containment (spill tray) mingguan.",
        "action_sh": "Koordinasi dengan tim EHS untuk pembaruan dokumen MSDS dan pelatihan tanggap darurat tumpahan B3.",
        "action_dh": "Pastikan kepatuhan audit regulasi Lingkungan & K3 (B3 Management) terpenuhi 100%."
    },
    "Penyimpanan RM/WIP/FG": {
        "cause": "(1) Barang/bahan menumpuk melebihi batas lokasi. (2) Barang baru dan barang lama tercampur (tidak pakai aturan FIFO).",
        "action_operator": "(1) Terapkan sistem FIFO saat mengambil/menaruh material. (2) Tumpuk barang sesuai batas Yellow Box.",
        "action_gl": "Cek kebenaran label tanggal masuk (batch FIFO) dan kerapian penataan stock setiap pergantian shift.",
        "action_foreman": "Review batas Max-Min stock di area produksi dan koordinasikan pengiriman barang yang menumpuk.",
        "action_sh": "Evaluasi Layout Floor Space bersama tim PPC/Logistik agar tidak terjadi overstock.",
        "action_dh": "Otorisasi kebijakan efisiensi persediaan dan restrukturisasi sistem aliran material utama."
    },
    "Penyimpanan Consumable": {
        "cause": "(1) Barang/part kecil berantakan di rak dan tidak ada label nama. (2) Jumlah barang tidak jelas (sering kehabisan/kebanyakan).",
        "action_operator": "(1) Simpan part di dalam kotak berlabel nama/kode barang. (2) Kembalikan sisa bahan setiap selesai shift.",
        "action_gl": "Lakukan pengecekan visual (3T: Tempat, Tataletak, Jumlah) pada rak consumable setiap hari.",
        "action_foreman": "Tetapkan standar Reorder Level (Kanban) untuk mencegah kehabisan/kelebihan part consumable.",
        "action_sh": "Standardisasi jenis tempat penyimpanan (part box/rak) di seluruh area bagian.",
        "action_dh": "Tinjau efisiensi pemakaian biaya consumable bulanan dan atur sistem pembelian terpusat."
    },
    "Area Kerja di Lapangan": {
        "cause": "(1) Banyak barang tak terpakai/sampah menumpuk di atas meja. (2) Posisi alat tulis, dokumen, dan alat kerja acak-acakan.",
        "action_operator": "(1) Buang sampah dan singkirkan barang tak terpakai. (2) Bersihkan meja setiap sebelum pulang shift.",
        "action_gl": "Inspeksi penerapan Clean Desk Policy dan kerapian garis stiker penataan meja sebelum shift berakhir.",
        "action_foreman": "Lakukan Red Tag Campaign (Tag Merah) untuk memindahkan barang non-standar dari meja kerja.",
        "action_sh": "Tetapkan Visual Layout Matrix (posisi standar barang) di seluruh meja kerja lapangan.",
        "action_dh": "Tegakkan budaya kerja SORTIR dan rapi melalui evaluasi rutin manajemen."
    },
    "Peralatan Kerja": {
        "cause": "(1) Alat kerja/tools sering hilang/tercecer. (2) Tidak ada pengecekan kelengkapan alat saat pergantian shift.",
        "action_operator": "(1) Simpan alat pada Shadow Board (papan kontur alat). (2) Cek kelengkapan alat 5 menit sebelum & sesudah shift.",
        "action_gl": "Pimpin briefing 5 menit untuk verifikasi checklist serah-terima kelengkapan alat antar shift.",
        "action_foreman": "Buat sistem Shadow Board / Busa Cetak (Foam Inlay) dan penandaan warna (Color Coding) perkakas.",
        "action_sh": "Audit ketersediaan dan kondisi kelayakan tools kerja secara berkala.",
        "action_dh": "Setujui penggantian/penambahan investasi tools kerja yang standar dan ergonomis."
    },
    "Penyimpanan Master Work": {
        "cause": "(1) Sampel master kotor, terbentur, atau berdebu. (2) Sampel master tercampur dengan produk biasa/cacat.",
        "action_operator": "(1) Simpan sampel master di dalam box akrilik terkunci. (2) Bersihkan wadah sampel secara rutin.",
        "action_gl": "Pastikan sampel master selalu memiliki stiker identifikasi 'MASTER WORK - DILARANG UNTUK PRODUKSI'.",
        "action_foreman": "Lakukan verifikasi kondisi fisik dan validitas kalibrasi/kesesuaian master sampel bulanan.",
        "action_sh": "Tinjau SOP pendaftaran, penyimpanan, dan masa kadaluwarsa master sampel produksi.",
        "action_dh": "Sahkan standar kualitas acuan (Master Work) bersama tim Quality Assurance (QA)."
    },
    "Informasi Terdokumentasi": {
        "cause": "(1) Papan informasi kotor dan kusam. (2) Kertas pengumuman/SOP yang ditempel sudah kedaluwarsa atau rusak.",
        "action_operator": "(1) Bersihkan papan informasi dari debu. (2) Laporkan kertas yang sobek/rusak ke Group Leader.",
        "action_gl": "Tarik pengumuman/SOP lama yang sudah kedaluwarsa dan ganti dengan dokumen berstatus berlaku.",
        "action_foreman": "Update matriks informasi, grafik pencapaian KPI, dan kontrol dokumen pada papan informasi.",
        "action_sh": "Audit kepatuhan pengisian dokumen kontrol dan instruksi kerja ter-update di area.",
        "action_dh": "Dukung sistem digitalisasi papan informasi (Visual Management Display) secara bertahap."
    },
    "Tempat Istirahat": {
        "cause": "(1) Sisa makanan dan sampah berserakan di meja/lantai. (2) Tempat sampah penuh atau jenis jalurnya tercampur.",
        "action_operator": "(1) Buang sisa makanan langsung ke tempat sampah terpisah. (2) Jalankan piket kebersihan area istirahat.",
        "action_gl": "Awasi kepatuhan anggota shift terhadap jadwal piket dan kebersihan area istirahat pasca-istirahat.",
        "action_foreman": "Sediakan fasilitas tempat sampah terpilah (Organik/Anorganik) dan fasilitas pembersihan memadai.",
        "action_sh": "Evaluasi ketersediaan dan kelayakan fasilitas tempat istirahat karyawan secara periodik.",
        "action_dh": "Dukung penciptaan lingkungan kerja yang sehat, nyaman, dan berbudaya 5S tinggi."
    },
    "Meja Kerja Leader": {
        "cause": "(1) Laporan dan berkas kertas menumpuk acak-acakan di meja Leader. (2) Dokumen penting dan biasa tercampur.",
        "action_operator": "(1) Taruh berkas laporan masuk pada tray 'IN' yang sudah disediakan di meja Leader.",
        "action_gl": "Gunakan filing tray 3 tingkat (IN, ON PROCESS, OUT) dan rapikan berkas setiap akhir kerja.",
        "action_foreman": "Terapkan Color Coded Filing (Map Warna) berdasarkan prioritas (Merah = Urgent, Kuning = Biasa).",
        "action_sh": "Audit kerapian meja kerja Leader saat melakukan Gemba Walk mingguan.",
        "action_dh": "Instruksikan percepatan efisiensi proses kerja paperless (persetujuan digital)."
    },
    "Penempatan Dokumen": {
        "cause": "(1) Map dokumen di lemari/rak tidak ada nomor atau nama kategorinya. (2) Dokumen lama masih menumpuk di laci.",
        "action_operator": "(1) Kembalikan map dokumen ke posisi semula setelah selesai dibaca.",
        "action_gl": "Pastikan bagian luar ordner/map tertempel label identifikasi dan nomor urut yang jelas.",
        "action_foreman": "Pisahkan hardcopy sesuai Jadwal Retensi Dokumen (Dokumen Aktif vs Arsip Inaktif).",
        "action_sh": "Buat Master Index Filing Cabinet dan tata kelola pengarsipan terpusat di departemen.",
        "action_dh": "Setujui prosedur pemusnahan/penyimpanan jangka panjang untuk arsip dokumen lama."
    }
}

# ----------------- FUNGSI PENENTUAN LEVEL 5S -----------------
def get_level_5s(avg_score):
    if avg_score >= 5.0:
        return "Gold", "lvl-gold"
    elif avg_score >= 4.0:
        return "Silver", "lvl-silver"
    elif avg_score >= 3.0:
        return "Bronze", "lvl-bronze"
    else:
        return "Black", "lvl-black"

# ----------------- GRAFIK & TABEL BUILDER -----------------
def create_exact_chart(x_labels, target_vals, actual_vals, title, is_kriteria=False):
    fig = go.Figure()
    
    bar_colors = []
    for act, tgt in zip(actual_vals, target_vals):
        try:
            act_num = float(act)
            tgt_num = float(tgt)
            if act_num >= tgt_num:
                bar_colors.append('#a8f087')
            else:
                bar_colors.append('#ff5252')
        except (ValueError, TypeError):
            bar_colors.append('#e0e0e0')
    
    fig.add_trace(go.Bar(
        x=x_labels,
        y=actual_vals,
        name='Aktual',
        marker_color=bar_colors,
        text=actual_vals,
        textposition='auto',
        width=0.45 if is_kriteria else 0.55
    ))
    
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=target_vals,
        name='Target',
        mode='lines+markers',
        line=dict(color='#0099ff', width=3, shape='spline'),
        marker=dict(size=9, color='#0099ff')
    ))
    
    clean_targets = [float(v) for v in target_vals if str(v).replace('.','',1).isdigit()]
    clean_actuals = [float(v) for v in actual_vals if str(v).replace('.','',1).isdigit()]
    max_val = max(max(clean_targets, default=10), max(clean_actuals, default=10))
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=14, color='#004d73')),
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, type='category'),
        yaxis=dict(title="Nilai Patrol", showgrid=True, gridcolor='#e2e8f0', range=[0, max_val * 1.25])
    )
    return fig

def render_exact_table(columns_header, targets, actuals, first_col_label="Line"):
    html = '<table class="table-5s">'
    html += f'<tr><th style="width: 10%;">{first_col_label}</th>'
    for col in columns_header:
        html += f'<th>{col}</th>'
    html += '</tr>'
    
    html += '<tr><td class="bg-label">Target</td>'
    for t in targets:
        html += f'<td>{t if t is not None and str(t) != "" else "-"}</td>'
    html += '</tr>'
    
    html += '<tr><td class="bg-label">Aktual</td>'
    for a in actuals:
        html += f'<td>{a if a is not None and str(a) != "" else "-"}</td>'
    html += '</tr>'
    
    html += '<tr><td class="bg-label">Judge</td>'
    for a, t in zip(actuals, targets):
        try:
            act_num = float(a)
            tgt_num = float(t)
            if act_num >= tgt_num:
                html += '<td class="judge-ok">OK</td>'
            else:
                html += '<td class="judge-ng">NG</td>'
        except (ValueError, TypeError):
            html += '<td>-</td>'
    html += '</tr>'
    
    html += '</table>'
    return html

def create_pareto_chart(kriteria_list, scores_list):
    df_pareto = pd.DataFrame({'Kriteria': kriteria_list, 'Nilai': scores_list})
    df_pareto['Nilai'] = pd.to_numeric(df_pareto['Nilai'], errors='coerce').fillna(0)
    df_pareto = df_pareto.sort_values(by='Nilai', ascending=True).reset_index(drop=True)
    
    total_val = df_pareto['Nilai'].sum()
    df_pareto['CumPercentage'] = (df_pareto['Nilai'].cumsum() / total_val * 100) if total_val > 0 else 0

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=df_pareto['Kriteria'],
            y=df_pareto['Nilai'],
            name="Rata-rata Nilai",
            marker_color='#ff5252',
            text=df_pareto['Nilai'].round(2),
            textposition='auto'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=df_pareto['Kriteria'],
            y=df_pareto['CumPercentage'],
            name="Kumulatif (%)",
            mode='lines+markers',
            line=dict(color='#004d73', width=2),
            marker=dict(size=6)
        ),
        secondary_y=True
    )

    fig.update_layout(
        title=dict(text="<b>DIAGRAM PARETO: EVALUASI KRITERIA DENGAN PERFORMA TERRENDAH</b>", font=dict(size=14, color='#004d73')),
        height=380,
        margin=dict(l=20, r=20, t=40, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, tickangle=-30)
    )
    fig.update_yaxes(title_text="Rata-rata Nilai Kriteria", secondary_y=False, showgrid=True, gridcolor='#e2e8f0')
    fig.update_yaxes(title_text="Persentase Kumulatif (%)", secondary_y=True, range=[0, 110], showgrid=False)
    
    return fig

# ----------------- EKSEKUSI PEMBACAAN DATA EXCEL -----------------
if df.empty:
    st.error("Data Google Sheets kosong atau tidak ditemukan. Harap periksa koneksi dan link file.")
else:
    all_columns = df.columns.tolist()
    ALL_MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    col_tgt_m = next((c for c in all_columns if 'target' in c.lower() and 'month' in c.lower()), None) or next((c for c in all_columns if 'target' in c.lower()), None)
    col_act_m = next((c for c in all_columns if 'aktual' in c.lower() and 'month' in c.lower()), None) or next((c for c in all_columns if 'aktual' in c.lower()), None)
    
    months_data = df['Bulan'].tolist() if 'Bulan' in all_columns else ALL_MONTHS
    targets_m_data = df[col_tgt_m].tolist() if col_tgt_m else []
    actuals_m_data = df[col_act_m].tolist() if col_act_m else []

    EXCLUDE_KEYWORDS = ['by area', 'by_area', 'total', 'summary', 'all area']
    lines_info = []
    
    for col in all_columns:
        if 'target' in col.lower() and not ('month' in col.lower()):
            clean_name = col.replace('Target', '').replace('target', '').strip()
            if clean_name and not any(kw in clean_name.lower() for kw in EXCLUDE_KEYWORDS):
                lines_info.append((clean_name, clean_name))

    ALL_AREAS = [info[1] for info in lines_info]

    # Sidebar Filter
    st.sidebar.header("🔍 Filter & Kontrol Dashboard")
    if st.sidebar.button("🔄 Refresh Data Sheets"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    selected_months = st.sidebar.multiselect("🗓️ Filter Bulan (By Month):", options=months_data, default=months_data)
    selected_departments = st.sidebar.multiselect("🏢 Filter Department / Line:", options=ALL_AREAS, default=ALL_AREAS)

    def generate_excel_download(dataframe):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, sheet_name='Data_5S', index=False)
        return output.getvalue()

    # Header
    col_title, col_export = st.columns([3, 1])
    with col_title:
        st.markdown('<div class="dashboard-title">🧹 DASHBOARD PERFORMANCE PATROL 5S</div>', unsafe_allow_html=True)
        st.markdown('<div class="dashboard-subtitle">Monitoring Real-time Pencapaian Patrol 5S Terintegrasi Full Data Google Sheets</div>', unsafe_allow_html=True)

    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Download Excel Report",
            data=generate_excel_download(df),
            file_name="Laporan_Patrol_5S_Realtime.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("---")

    # APLIKASI UNIFIED LAYOUT TAB
    tab_summary, tab_details, tab_monthly_area, tab_pareto, tab_action = st.tabs([
        "📊 Executive Summary (By Month & By Area)", 
        "🏭 Detail 11 Kriteria Penilaian (By Line)", 
        "📅 Tren Bulanan Per Area (Jan - Dec)",
        "📈 Pareto Analisis Kriteria Rendah",
        "🛠️ CAPA Tracking"
    ])

    if 'Kriteria' in all_columns and not df['Kriteria'].dropna().empty:
        kriteria_labels = df['Kriteria'].dropna().tolist()
    else:
        kriteria_labels = DEFAULT_KRITERIA_LIST

    ng_areas = []
    ok_areas = []

    IMAGE_DIR = "uploaded_images"
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    # --- TAB 1: SUMMARY & ANALYSIS ---
    with tab_summary:
        filtered_months = [m for m in months_data if m in selected_months]
        indices_m = [months_data.index(m) for m in filtered_months]
        t_m = [targets_m_data[i] if i < len(targets_m_data) else 0 for i in indices_m]
        a_m = [actuals_m_data[i] if i < len(actuals_m_data) else 0 for i in indices_m]

        total_actual_sum = 0.0
        total_target_sum = 0.0

        filtered_selected_areas = [a for a in selected_departments if not any(kw in a.lower() for kw in EXCLUDE_KEYWORDS)]

        for area in filtered_selected_areas:
            c_t = next((c for c in all_columns if area.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in all_columns if area.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            
            if c_a:
                total_actual_sum += df[c_a].dropna().sum()
            if c_t:
                total_target_sum += df[c_t].dropna().sum()

        JUMLAH_AREA = 10
        JUMLAH_KRITERIA = 11

        avg_actual = total_actual_sum / (JUMLAH_AREA * JUMLAH_KRITERIA)
        avg_target = total_target_sum / (JUMLAH_AREA * JUMLAH_KRITERIA) if total_target_sum > 0 else 4.0

        overall_level, level_css = get_level_5s(avg_actual)

        if overall_level in ["Gold", "Silver"]:
            status_summary = "<span style='color: #2e7d32; font-weight: bold;'>SANGAT BAIK (PERTAHANKAN)</span>"
            action_summary = "Performa 5S secara keseluruhan berada pada standar tinggi. Pertahankan budaya kerja ini dan lakukan audit rutin secara konsisten."
        elif overall_level == "Bronze":
            status_summary = "<span style='color: #e65100; font-weight: bold;'>BUTUH PERBAIKAN FOKUS</span>"
            action_summary = "Beberapa kriteria/area belum mencapai target. Segera tindak lanjuti temuan NG pada area terkait dan percepat penyelesaian CAPA."
        else:
            status_summary = "<span style='color: #c62828; font-weight: bold;'>PERLU TINDAKAN DARURAT (CRITICAL)</span>"
            action_summary = "Pencapaian 5S berada di bawah standar minimum. Direkomendasikan melakukan Gemba Walk gabungan bersama Management dan Red Tag Campaign."

        st.markdown(f"""
            <div class="summary-box" style="background-color: var(--secondary-background-color, #ffffff); border-left: 5px solid #004d73; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #004d73; font-size: 15px;">📋 RANGKUMAN & KESIMPULAN EXECUTIVE SUMMARY</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; line-height: 1.6;">
                    <tr>
                        <td style="width: 25%; font-weight: bold;">Status Performa 5S</td>
                        <td>: {status_summary}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Ketercapaian Skor Akhir</td>
                        <td>: Skor Akhir <b>{avg_actual:.2f}</b> dari Target <b>{avg_target:.2f}</b> (Level <b>{overall_level}</b>)</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Formula Perhitungan</td>
                        <td>: Total Nilai ({total_actual_sum:.1f}) ÷ 10 Area ÷ 11 Kriteria = <b>{avg_actual:.2f}</b></td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Rekomendasi Tindakan</td>
                        <td>: {action_summary}</td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">BY ALL (PENCAPAIAN BY MONTH)</div>', unsafe_allow_html=True)
        
        if filtered_months and t_m and a_m:
            st.plotly_chart(create_exact_chart(filtered_months, t_m, a_m, "PENCAPAIAN AKTIVITAS 5S BY MONTH"), use_container_width=True)
            st.markdown(render_exact_table(filtered_months, t_m, a_m, "Bulan"), unsafe_allow_html=True)
            
            ok_m_cnt = sum(1 for act, tgt in zip(a_m, t_m) if float(act) >= float(tgt))
            total_m_cnt = len(filtered_months)
            ng_m_cnt = total_m_cnt - ok_m_cnt
            
            st.markdown(f"""
                <div class="summary-box">
                    <strong>📌 Kesimpulan Pencapaian Bulanan:</strong><br>
                    Dari total <b>{total_m_cnt} bulan</b> yang dipantau, sebanyak <b>{ok_m_cnt} bulan</b> berhasil mencapai target 5S, 
                    sedangkan <b>{ng_m_cnt} bulan</b> masih belum memenuhi target yang ditetapkan.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Data By Month tidak ditemukan pada Excel.")

        st.markdown("<hr style='margin: 35px 0; border: 0; border-top: 2px dashed #cbd5e1;'>", unsafe_allow_html=True)

        st.markdown('<div class="section-header">BY DEPARTMENT / AREA</div>', unsafe_allow_html=True)
        
        area_targets = []
        area_actuals = []
        
        for area in filtered_selected_areas:
            c_t = next((c for c in all_columns if area.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in all_columns if area.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            
            sum_t = df[c_t].dropna().sum() if c_t else 0
            sum_a = df[c_a].dropna().sum() if c_a else 0
            area_targets.append(sum_t)
            area_actuals.append(sum_a)

        if filtered_selected_areas:
            st.plotly_chart(create_exact_chart(filtered_selected_areas, area_targets, area_actuals, "PENCAPAIAN PER AREA / DEPARTMENT"), use_container_width=True)
            st.markdown(render_exact_table(filtered_selected_areas, area_targets, area_actuals, "Area"), unsafe_allow_html=True)
            
            ok_areas = []
            ng_areas = []
            
            for area, act, tgt in zip(filtered_selected_areas, area_actuals, area_targets):
                if float(act) >= float(tgt):
                    ok_areas.append(area)
                else:
                    ng_areas.append(area)
            
            ok_str = ", ".join(ok_areas) if ok_areas else "-"
            ng_str = ", ".join(ng_areas) if ng_areas else "Tidak ada"
            
            st.markdown(f"""
                <div class="summary-box">
                    <strong>📌 Kesimpulan Pencapaian Area:</strong><br>
                    Area yang <b>mencapai target (OK)</b>: <b>{ok_str}</b>.<br>
                    Area yang <b>perlu perbaikan (NG)</b>: <b style='color:#c0392b;'>{ng_str}</b>.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Pilih minimal satu area.")

    # --- TAB 2: DETAIL KRITERIA & LEVELING ---
    with tab_details:
        st.markdown('<div class="section-header">BY KRITERIA PENILAIAN & ANALISA PERBAIKAN (DETAIL PER LINE / DEPARTMENT)</div>', unsafe_allow_html=True)
        
        available_lines_map = {title: (title, key) for title, key in lines_info if key in selected_departments}
        available_line_names = list(available_lines_map.keys())

        if available_line_names:
            selected_tab2_lines = st.multiselect(
                "🎯 Pilih Area / Line yang Ingin Ditampilkan:",
                options=available_line_names,
                default=available_line_names,
                key="filter_tab2_lines"
            )
            filtered_lines = [available_lines_map[name] for name in selected_tab2_lines]
        else:
            filtered_lines = []
        st.markdown("<br>", unsafe_allow_html=True)

        x_kriteria_num = [str(i) for i in range(1, len(kriteria_labels) + 1)]

        def render_line_analysis(title_area, key_area, targets_list, actuals_list):
            ng_items = []
            for k_name, act, tgt in zip(kriteria_labels, actuals_list, targets_list):
                try:
                    if float(act) < float(tgt):
                        ng_items.append((k_name, float(act), float(tgt)))
                except (ValueError, TypeError):
                    pass
            
            if ng_items:
                ng_items.sort(key=lambda x: x[1])
                
                with st.popover(f"🔍 Tindak Lanjut Analisa & Rekomendasi ({len(ng_items)} Temuan NG)", use_container_width=True):
                    list_items_html = ""
                    for k_name, act_val, tgt_val in ng_items:
                        rec_data = RCA_RECOMMENDATION.get(k_name, {
                            "cause": "Belum ada standar visual dan pengawasan rutin di area kerja.",
                            "action_operator": "Lakukan pembersihan total, rapikan penataan, dan pasang label petunjuk.",
                            "action_gl": "Monitoring kebersihan dan kerapian area harian.",
                            "action_foreman": "Buat standar penataan visual dan evaluasi mingguan.",
                            "action_sh": "Review ketercapaian standar 5S area secara periodik.",
                            "action_dh": "Dukung kebutuhan fasilitas dan sosialisasi budaya 5S."
                        })
                        
                        list_items_html += (
                            f"<li style='margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #ffcdd2;'>"
                            f"<b>{k_name}</b> (Nilai: <span style='color:#d32f2f; font-weight:bold;'>{act_val:.1f}</span> / Target: {tgt_val:.1f})<br>"
                            f"&bull; <i>Penyebab Utama:</i> {rec_data.get('cause', '-')}<br>"
                            f"<div style='margin-top: 4px; padding-left: 8px; border-left: 2px solid #e57373;'>"
                            f"&bull; <b>Tindakan Operator:</b> <span style='color:#1b5e20;'>{rec_data.get('action_operator', '-')}</span><br>"
                            f"&bull; <b>Tindakan Group Leader:</b> <span style='color:#0d47a1;'>{rec_data.get('action_gl', '-')}</span><br>"
                            f"&bull; <b>Tindakan Foreman:</b> <span style='color:#e65100;'>{rec_data.get('action_foreman', '-')}</span><br>"
                            f"&bull; <b>Tindakan Section Head:</b> <span style='color:#4a148c;'>{rec_data.get('action_sh', '-')}</span><br>"
                            f"&bull; <b>Tindakan Dept Head:</b> <span style='color:#880e4f;'>{rec_data.get('action_dh', '-')}</span>"
                            f"</div>"
                            f"</li>"
                        )
                    
                    html_card = f"""
                    <div class="analysis-card">
                        <h5 style="color: #b71c1c; margin-top: 0; font-weight: 700;">🔍 ANALISA & REKOMENDASI PERBAIKAN AREA {title_area.upper()}:</h5>
                        <p style="font-size: 13px; margin-bottom: 8px;">Ditemukan <b>{len(ng_items)} kriteria</b> yang belum mencapai target:</p>
                        <ol style="margin: 5px 0 5px 15px; padding: 0; font-size: 12px;">{list_items_html}</ol>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)
            else:
                st.success(f"🎉 Luar Biasa! Area {title_area} memenuhi seluruh kriteria target 5S (100% OK).")

        if not filtered_lines:
            st.warning("Silakan pilih minimal satu area pada dropdown di atas.")
        else:
            for title_line, key_line in filtered_lines:
                c_tgt = next((c for c in all_columns if key_line.lower() in c.lower() and 'target' in c.lower()), None)
                c_act = next((c for c in all_columns if key_line.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
                
                t_k = df[c_tgt].dropna().tolist() if c_tgt else []
                a_k = df[c_act].dropna().tolist() if c_act else []
                
                clean_act = [float(x) for x in a_k if str(x).replace('.', '', 1).isdigit()]
                avg_val = (sum(clean_act) / len(clean_act)) if clean_act else 0.0
                lvl_val, css_val = get_level_5s(avg_val)

                st.markdown(f"#### 🏭 {title_line} &nbsp; <span class='badge-level {css_val}'>Level: {lvl_val} ({avg_val:.2f})</span>", unsafe_allow_html=True)
                st.plotly_chart(create_exact_chart(x_kriteria_num[:len(t_k)], t_k, a_k, f"Kriteria Penilaian - {key_line}", is_kriteria=True), use_container_width=True)
                st.markdown(render_exact_table(kriteria_labels[:len(t_k)], t_k, a_k, "Kriteria"), unsafe_allow_html=True)
                render_line_analysis(title_line, key_line, t_k, a_k)
                st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px dashed #cbd5e1;'>", unsafe_allow_html=True)

# --- TAB 3: REKAP TREN BULANAN PER AREA (SHEET 3) ---
    with tab_monthly_area:
        st.markdown('<div class="section-header">REKAPITULASI TREN PENCAPAIAN 5S PER AREA (JANUARI - DESEMBER)</div>', unsafe_allow_html=True)
        
        # 1. BACA DATA SPESIFIK SHEET 3 TANPA MEMPENGARUHI TAB LAIN
        @st.cache_data(ttl=10)
        def load_data_sheet3(base_url):
            try:
                # Membuat URL khusus untuk membaca Sheet3 dari spreadsheet
                if "pub?output=csv" in base_url:
                    s3_url = base_url.replace("pub?output=csv", "pub?sheet=Sheet3&output=csv")
                else:
                    s3_url = base_url
                df_s3 = pd.read_csv(s3_url)
                df_s3.columns = df_s3.columns.astype(str).str.strip()
                return df_s3
            except Exception:
                return pd.DataFrame()

        df_sheet3 = load_data_sheet3(SHEET_URL)

        # Fallback jika URL publik tidak otomatis beralih sheet (menggunakan df utama)
        if df_sheet3.empty:
            df_sheet3 = df.copy()

        all_cols_s3 = df_sheet3.columns.tolist()
        
        # 2. IDENTIFIKASI KOLOM TARGET & AKTUAL AREA DI SHEET 3
        area_pairs_s3 = []
        for col in all_cols_s3:
            if 'target' in col.lower() and not ('month' in col.lower()):
                clean_area = col.replace('Target', '').replace('target', '').strip()
                if clean_area and not any(kw in clean_area.lower() for kw in EXCLUDE_KEYWORDS):
                    act_col = next((c for c in all_cols_s3 if clean_area.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
                    if act_col:
                        area_pairs_s3.append((clean_area, col, act_col))

        filtered_pairs_s3 = [p for p in area_pairs_s3 if not selected_departments or any(sd.lower() in p[0].lower() or p[0].lower() in sd.lower() for sd in selected_departments)]
        if not filtered_pairs_s3:
            filtered_pairs_s3 = area_pairs_s3

        # 3. KESIMPULAN KHUSUS TAB 3 (REKAP NILAI BULANAN PER AREA)
        summary_stats = []
        for area_name, c_t, c_a in filtered_pairs_s3:
            t_vals = [float(v) for v in df_sheet3[c_t].dropna() if str(v).replace('.','',1).isdigit()]
            a_vals = [float(v) for v in df_sheet3[c_a].dropna() if str(v).replace('.','',1).isdigit()]
            
            avg_a = sum(a_vals) / len(a_vals) if a_vals else 0.0
            avg_t = sum(t_vals) / len(t_vals) if t_vals else 4.0
            ok_months = sum(1 for a_v, t_v in zip(a_vals, t_vals) if a_v >= t_v)
            
            summary_stats.append({
                "area": area_name,
                "avg_actual": avg_a,
                "avg_target": avg_t,
                "ok_months": ok_months,
                "total_months": len(a_vals)
            })

        if summary_stats:
            best_area = max(summary_stats, key=lambda x: x['avg_actual'])
            lowest_area = min(summary_stats, key=lambda x: x['avg_actual'])
            consistent_areas = [s['area'] for s in summary_stats if s['ok_months'] == s['total_months'] and s['total_months'] > 0]
            consistent_str = ", ".join(consistent_areas) if consistent_areas else "Belum ada area yang 100% konsisten tiap bulan"

            st.markdown(f"""
                <div class="summary-box" style="background-color: var(--secondary-background-color, #ffffff); border-left: 5px solid #004d73; margin-bottom: 25px;">
                    <h4 style="margin: 0 0 8px 0; color: #004d73; font-size: 15px;">📋 RANGKUMAN REKAPITULASI TREN BULANAN PER AREA (SHEET 3)</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; line-height: 1.6;">
                        <tr>
                            <td style="width: 32%; font-weight: bold;">Area Performa Terbaik (Jan - Dec)</td>
                            <td>: <b>{best_area['area'].upper()}</b> (Rata-rata Skor: <b style="color:#2e7d32;">{best_area['avg_actual']:.2f}</b>)</td>
                        </tr>
                        <tr>
                            <td style="font-weight: bold;">Area Perlu Perhatian Khusus</td>
                            <td>: <b>{lowest_area['area'].upper()}</b> (Rata-rata Skor: <b style="color:#c62828;">{lowest_area['avg_actual']:.2f}</b>)</td>
                        </tr>
                        <tr>
                            <td style="font-weight: bold;">Area 100% Target Achieved (Tiap Bulan)</td>
                            <td>: <b>{consistent_str}</b></td>
                        </tr>
                        <tr>
                            <td style="font-weight: bold;">Catatan Rekapitulasi Sheet 3</td>
                            <td>: Tab ini khusus menyajikan rekap tren pencapaian 10 area dari bulan Januari hingga Desember berdasarkan data akumulasi Sheet 3 (tanpa rincian kriteria).</td>
                        </tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)

        # 4. RENDERING GRAFIK & TABEL DARI DATA SHEET 3 (GRID 2 KOLOM)
        for i in range(0, len(filtered_pairs_s3), 2):
            cols_m = st.columns(2)
            
            # Area 1
            area_name1, col_t1, col_a1 = filtered_pairs_s3[i]
            t_m1 = df_sheet3[col_t1].dropna().tolist()
            a_m1 = df_sheet3[col_a1].dropna().tolist()
            months_label1 = ALL_MONTHS[:len(a_m1)] if len(a_m1) <= 12 else ALL_MONTHS
            
            with cols_m[0]:
                st.plotly_chart(create_exact_chart(months_label1, t_m1, a_m1, f"REKAP TREN BULANAN 5S - {area_name1.upper()}"), use_container_width=True)
                st.markdown(render_exact_table(months_label1, t_m1, a_m1, "Bulan"), unsafe_allow_html=True)
            
            # Area 2 (Jika Ada)
            if i + 1 < len(filtered_pairs_s3):
                area_name2, col_t2, col_a2 = filtered_pairs_s3[i+1]
                t_m2 = df_sheet3[col_t2].dropna().tolist()
                a_m2 = df_sheet3[col_a2].dropna().tolist()
                months_label2 = ALL_MONTHS[:len(a_m2)] if len(a_m2) <= 12 else ALL_MONTHS
                
                with cols_m[1]:
                    st.plotly_chart(create_exact_chart(months_label2, t_m2, a_m2, f"REKAP TREN BULANAN 5S - {area_name2.upper()}"), use_container_width=True)
                    st.markdown(render_exact_table(months_label2, t_m2, a_m2, "Bulan"), unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 25px 0; border: 0; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

    # --- TAB 4: PARETO & AI RECOMMENDATION ---
    with tab_pareto:
        st.markdown('<div class="section-header">DIAGRAM PARETO: EVALUASI KRITERIA DENGAN NILAI TERRENDAH</div>', unsafe_allow_html=True)
        
        kriteria_scores = {k: [] for k in kriteria_labels}
        for _, key_line in lines_info:
            if key_line in selected_departments:
                c_act_p = next((c for c in all_columns if key_line.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
                if c_act_p:
                    vals = df[c_act_p].dropna().tolist()
                    for idx_k, val_k in enumerate(vals):
                        if idx_k < len(kriteria_labels) and str(val_k).replace('.', '', 1).isdigit():
                            kriteria_scores[kriteria_labels[idx_k]].append(float(val_k))

        avg_scores = [
            (sum(kriteria_scores[k]) / len(kriteria_scores[k])) if kriteria_scores[k] else 0.0
            for k in kriteria_labels
        ]

        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            st.plotly_chart(create_pareto_chart(kriteria_labels, avg_scores), use_container_width=True)
            
            df_rank_p = pd.DataFrame({'Kriteria': kriteria_labels, 'Nilai': avg_scores})
            df_rank_p = df_rank_p.sort_values(by='Nilai', ascending=True).reset_index(drop=True)
            top_3_lowest = df_rank_p.head(3).values.tolist()
            
            p_items_html = "".join([f"<li><b>{item[0]}</b> (Rata-rata Score: <b>{item[1]:.2f}</b>)</li>" for item in top_3_lowest])
            
            st.markdown(f"""
                <div class="summary-box">
                    <strong>📌 Kesimpulan Evaluasi Kriteria (Pareto):</strong><br>
                    3 Kriteria dengan performa terendah yang membutuhkan tindakan korektif utama adalah:
                    <ol style="margin: 5px 0 0 20px; padding: 0;">
                        {p_items_html}
                    </ol>
                </div>
            """, unsafe_allow_html=True)
            
        with col_p2:
            st.markdown("##### 🔍 Ranking Kriteria Terrendah")
            df_rank = pd.DataFrame({'Kriteria Penilaian': kriteria_labels, 'Rata-Rata Nilai': avg_scores})
            df_rank = df_rank.sort_values(by='Rata-Rata Nilai', ascending=True).reset_index(drop=True)
            df_rank.index = df_rank.index + 1
            st.dataframe(df_rank, use_container_width=True)

    # --- TAB 5: CAPA TRACKING & LOG INPUT TEMUAN NG ---
    with tab_action:
        st.markdown('<div class="section-header">TINDAKAN PERBAIKAN & CAPA TRACKING</div>', unsafe_allow_html=True)
        
        st.subheader("💡 1. Rekomendasi Solusi & Action Plan Berdasarkan RCA 5S")
        selected_rca_kriteria = st.selectbox(
            "🎯 Pilih Kriteria Penilaian untuk Melihat Panduan Action Plan:",
            options=list(RCA_RECOMMENDATION.keys()),
            key="select_rca_kriteria_tab4"
        )
        rec_info = RCA_RECOMMENDATION.get(selected_rca_kriteria, {})
        
        st.markdown(f"""
            <div class="summary-box" style="background-color: var(--secondary-background-color, #f9f9f9); border-left: 5px solid #2980b9; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
                <p style="margin-bottom: 8px;"><b>🔍 Root Cause Analysis / Akar Masalah (Why):</b><br>{rec_info.get('cause', '-')}</p>
                <hr style="margin: 10px 0; border: 0; border-top: 1px solid #e0e0e0;">
                <p style="margin-bottom: 8px;"><b>💡 Rekomendasi Solusi & Matriks Action Plan (How):</b></p>
                <div style="padding-left: 10px; font-size: 13px; line-height: 1.6;">
                    &bull; <b>Operator:</b> <span style="color:#1b5e20;">{rec_info.get('action_operator', '-')}</span><br>
                    &bull; <b>Group Leader (GL):</b> <span style="color:#0d47a1;">{rec_info.get('action_gl', '-')}</span><br>
                    &bull; <b>Foreman:</b> <span style="color:#e65100;">{rec_info.get('action_foreman', '-')}</span><br>
                    &bull; <b>Section Head (SH):</b> <span style="color:#4a148c;">{rec_info.get('action_sh', '-')}</span><br>
                    &bull; <b>Department Head (DH):</b> <span style="color:#880e4f;">{rec_info.get('action_dh', '-')}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.subheader("📝 2. Log Input Temuan Patrol NG & Penugasan Action Plan")
        with st.form(key="form_input_patrol_ng", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                input_area = st.selectbox("Area / Department Temuan:", options=[line[0] for line in lines_info] if lines_info else ["Area Production", "Area Warehouse", "Area Office"])
                input_kriteria = st.selectbox("Kriteria 5S Bermasalah:", options=kriteria_labels)
                input_detail_problem = st.text_area("Detail Temuan Masalah (Kondisi Lapangan):", placeholder="Misal: Garis kuning pembatas terkelupas di dekat mesin A")
                input_pic = st.text_input("PIC / Penanggung Jawab Perbaikan:", placeholder="Nama Operator / Group Leader")
            
            with col_f2:
                input_target_date = st.date_input("Target Selesai Perbaikan:")
                input_priority = st.selectbox("Tingkat Prioritas Penanganan:", options=["High (Urgent)", "Medium (Standard)", "Low (Rutin)"])
                input_tier = st.selectbox("Penugasan Eksekusi Utama:", options=["Operator", "Group Leader", "Foreman", "Section Head", "Department Head"])
                input_status = st.selectbox("Status Penanganan Saat Ini:", options=["Open (Belum Ditindak)", "On Progress (Proses Pengerjaan)", "Closed (Selesai)"])
                uploaded_file = st.file_uploader("📷 Upload Foto Temuan NG (JPG/PNG):", type=["jpg", "jpeg", "png"])

            btn_submit_capa = st.form_submit_button("💾 Simpan Log Temuan & Action Plan")

        if btn_submit_capa:
            if input_detail_problem.strip() == "":
                st.warning("⚠️ Mohon isi Detail Temuan Masalah sebelum menyimpan.")
            else:
                image_path = "-"
                if uploaded_file is not None:
                    file_ext = uploaded_file.name.split(".")[-1]
                    filename = f"img_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                    image_path = os.path.join(IMAGE_DIR, filename)
                    with open(image_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                new_entry = {
                    "Tanggal Input": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                    "Area": input_area,
                    "Kriteria 5S": input_kriteria,
                    "Detail Masalah": input_detail_problem,
                    "PIC": input_pic if input_pic else "-",
                    "Target Selesai": str(input_target_date),
                    "Prioritas": input_priority,
                    "Penanggung Jawab Tier": input_tier,
                    "Status": input_status,
                    "Foto Temuan": image_path
                }
                st.session_state["capa_log_data"].append(new_entry)
                try:
                    save_capa_to_gsheets(st.session_state["capa_log_data"])
                    st.success(f"✅ Data temuan NG & Foto di area '{input_area}' berhasil disimpan!")
                except Exception as e:
                    st.error(f"Gagal menyimpan data lokal: {e}")

                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 3. Daftar Monitoring Action Plan (CAPA Log)")
        
        if st.session_state["capa_log_data"]:
            df_capa_log = pd.DataFrame(st.session_state["capa_log_data"])
            if "Target Selesai" in df_capa_log.columns:
                df_capa_log["Target Selesai"] = pd.to_datetime(df_capa_log["Target Selesai"], errors="coerce").dt.date
            
            status_filter = st.multiselect(
                "Filter Status CAPA:",
                options=["Open (Belum Ditindak)", "On Progress (Proses Pengerjaan)", "Closed (Selesai)"],
                default=["Open (Belum Ditindak)", "On Progress (Proses Pengerjaan)", "Closed (Selesai)"]
            )
            df_filtered_capa = df_capa_log[df_capa_log["Status"].isin(status_filter)]

            edited_df = st.data_editor(
                df_filtered_capa,
                column_config={
                    "Status": st.column_config.SelectboxColumn(
                        "Status Penanganan",
                        options=["Open (Belum Ditindak)", "On Progress (Proses Pengerjaan)", "Closed (Selesai)"],
                        required=True,
                    ),
                    "Target Selesai": st.column_config.DateColumn("Target Selesai", format="YYYY-MM-DD"),
                    "Prioritas": st.column_config.SelectboxColumn("Prioritas", options=["High (Urgent)", "Medium (Standard)", "Low (Rutin)"]),
                    "Foto Temuan": st.column_config.TextColumn("Path Foto", disabled=True)
                },
                disabled=["Tanggal Input", "Area", "Kriteria 5S", "Detail Masalah"],
                use_container_width=True,
                num_rows="dynamic",
                key="capa_editor"
            )

            if st.button("💾 Simpan Perubahan Status / Tabel", type="primary"):
                for idx, row in edited_df.iterrows():
                    for orig_entry in st.session_state["capa_log_data"]:
                        if orig_entry["Tanggal Input"] == row["Tanggal Input"] and orig_entry["Detail Masalah"] == row["Detail Masalah"]:
                            orig_entry["Status"] = row["Status"]
                            orig_entry["PIC"] = row["PIC"]
                            orig_entry["Target Selesai"] = str(row["Target Selesai"])
                            orig_entry["Prioritas"] = row["Prioritas"]
                            orig_entry["Penanggung Jawab Tier"] = row["Penanggung Jawab Tier"]
                            break
                try:
                    save_capa_to_gsheets(st.session_state["capa_log_data"])
                    st.success("✅ Perubahan status CAPA Log berhasil diperbarui!")
                except Exception as e:
                    st.error(f"Gagal memperbarui data: {e}")
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("🖼️ 4. Galeri Foto Temuan NG Lapangan")
            
            has_image = False
            cols_img = st.columns(3)
            col_idx = 0

            for item in st.session_state["capa_log_data"]:
                img_path = item.get("Foto Temuan", "-")
                if isinstance(img_path, str) and img_path.strip() not in ["-", "", "nan", "None"]:
                    if os.path.exists(img_path):
                        has_image = True
                        with cols_img[col_idx % 3]:
                            st.image(
                                img_path, 
                                caption=f"📍 {item.get('Area', '-')}\n🗓️ {item.get('Tanggal Input', '-')} | Status: {item.get('Status', '-')}", 
                                use_container_width=True
                            )
                        col_idx += 1

            if not has_image:
                st.info("Belum ada foto temuan yang diunggah.")

            st.markdown("<br>", unsafe_allow_html=True)
            csv_capa = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data CAPA (CSV)",
                data=csv_capa,
                file_name="CAPA_Tracking_5S_Report.csv",
                mime="text/csv"
            )
        else:
            st.info("Belum ada log temuan yang diinputkan. Gunakan form di atas untuk mencatat temuan patrol 5S.")

    # --- KESIMPULAN UMUM KESELURUHAN (GLOBAL SUMMARY) ---
    st.markdown("---")
    grand_avg_score = (sum(avg_scores) / len(avg_scores)) if 'avg_scores' in locals() and avg_scores else 0.0
    global_level = get_level_5s(grand_avg_score)[0]
    
    top_lowest_kriteria = df_rank_p.head(2)['Kriteria'].tolist() if 'df_rank_p' in locals() else []
    top_lowest_str = " & ".join([f"<b>{k}</b>" for k in top_lowest_kriteria]) if top_lowest_kriteria else "tertentu"

    if ng_areas:
        action_plan_str = f"Fokus utama perbaikan dialokasikan pada area <b>{', '.join(ng_areas)}</b>, khususnya penanganan kriteria {top_lowest_str}."
    else:
        action_plan_str = "Seluruh area telah berhasil memenuhi target minimal 5S, pertahankan performa dengan konsistensi patrol berkala."

    st.markdown(f"""
        <div class="summary-box-global">
            <h3 style="margin: 0 0 8px 0; font-size: 16px;">📝 KESIMPULAN UMUM PERFORMA PATROL 5S</h3>
            Secara keseluruhan, rata-rata performa penerapan Patrol 5S di seluruh department berada pada skor <b>{grand_avg_score:.2f}</b> dengan predikat <b>LEVEL {str(global_level).upper()}</b>.<br>
            {action_plan_str}
        </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 Lihat Raw Data Google Sheets"):
        st.dataframe(df, use_container_width=True)
