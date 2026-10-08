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

# ----------------- LINK GOOGLE SHEETS DATA UTAMA -----------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQU_jpdzrymx_0mJKGVDopip0DPhnmDLIbsTHgVnqgaJZZayJUp-UPF1MF6H6soCA/pub?output=csv"

@st.cache_data(ttl=10)
def load_data(url):
    try:
        df_data = pd.read_csv(url)
        df_data.columns = df_data.columns.astype(str).str.strip()
        return df_data
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

# ----------------- CONSTANTS & LIST KRITERIA -----------------
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

ALL_MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
TARGET_AREAS = ["PVC", "SMS", "STEX", "BTEX", "DFAS", "PPEX", "WH", "SHP", "QA/QC", "MTC"]

RCA_RECOMMENDATION = {
    "Sekitar area kerja": {
        "cause": "(1) Garis kuning pembatas rusak, pudar, atau hilang. (2) Lantai kotor/rusak. (3) Trolley lewat sembarangan.",
        "action_operator": "(1) Dilarang lewat/menginjak jalur yang bukan peruntukannya. (2) Rapikan trolley.",
        "action_gl": "Lakukan patroli harian jalur hijau dan laporkan demarkasi yang rusak ke Foreman.",
        "action_foreman": "Buat Work Order (WO) perbaikan/pengecatan ulang lantai ke tim Maintenance.",
        "action_sh": "Evaluasi alur Material Handling (trolley) dan validasi standar proteksi lantai.",
        "action_dh": "Disetujui anggaran pemeliharaan fasilitas pabrik dan terapkan regulasi kedisiplinan."
    },
    "Penyimpanan Cairan B3": {
        "cause": "(1) Tidak ada wadah/nampan penampung tumpahan. (2) Kertas MSDS dan stiker B3 rusak/hilang.",
        "action_operator": "(1) Gunakan nampan penampung di bawah wadah B3. (2) Sediakan spill kit di lokasi.",
        "action_gl": "Pastikan semua wadah B3 di area memiliki stiker bahaya dan MSDS yang jelas.",
        "action_foreman": "Audit ketersediaan sarana Spill Kit & kelayakan spill tray mingguan.",
        "action_sh": "Koordinasi dengan tim EHS untuk pembaruan dokumen MSDS dan pelatihan tumpahan B3.",
        "action_dh": "Pastikan kepatuhan audit regulasi Lingkungan & K3 terpenuhi 100%."
    },
    "Penyimpanan RM/WIP/FG": {
        "cause": "(1) Barang/bahan menumpuk melebihi batas. (2) Barang baru & lama tercampur (tidak FIFO).",
        "action_operator": "(1) Terapkan sistem FIFO saat mengambil/menaruh material. (2) Tumpuk sesuai Yellow Box.",
        "action_gl": "Cek kebenaran label tanggal masuk (batch FIFO) dan kerapian penataan stock.",
        "action_foreman": "Review batas Max-Min stock dan koordinasikan pengiriman barang yang menumpuk.",
        "action_sh": "Evaluasi Layout Floor Space bersama tim PPC/Logistik agar tidak overstock.",
        "action_dh": "Otorisasi kebijakan efisiensi persediaan dan restrukturisasi aliran material."
    },
    "Penyimpanan Consumable": {
        "cause": "(1) Part kecil berantakan di rak dan tidak ada label nama. (2) Jumlah barang tidak jelas.",
        "action_operator": "(1) Simpan part di dalam kotak berlabel nama. (2) Kembalikan sisa bahan setiap selesai shift.",
        "action_gl": "Lakukan pengecekan visual (3T: Tempat, Tataletak, Jumlah) pada rak consumable.",
        "action_foreman": "Tetapkan standar Reorder Level (Kanban) untuk mencegah kehabisan part.",
        "action_sh": "Standardisasi jenis tempat penyimpanan di seluruh area bagian.",
        "action_dh": "Tinjau efisiensi pemakaian biaya consumable bulanan dan atur sistem pembelian."
    },
    "Area Kerja di Lapangan": {
        "cause": "(1) Banyak barang tak terpakai/sampah di meja. (2) Posisi alat tulis/dokumen acak-acakan.",
        "action_operator": "(1) Buang sampah dan singkirkan barang tak terpakai. (2) Bersihkan meja sebelum pulang.",
        "action_gl": "Inspeksi penerapan Clean Desk Policy dan kerapian penataan meja sebelum shift berakhir.",
        "action_foreman": "Lakukan Red Tag Campaign (Tag Merah) untuk memindahkan barang non-standar.",
        "action_sh": "Tetapkan Visual Layout Matrix (posisi standar barang) di seluruh meja kerja.",
        "action_dh": "Tegakkan budaya kerja SORTIR dan rapi melalui evaluasi rutin manajemen."
    },
    "Peralatan Kerja": {
        "cause": "(1) Alat kerja/tools sering hilang/tercecer. (2) Tidak ada pengecekan kelengkapan saat pergantian shift.",
        "action_operator": "(1) Simpan alat pada Shadow Board. (2) Cek kelengkapan alat 5 menit sebelum & sesudah shift.",
        "action_gl": "Pimpin briefing 5 menit untuk verifikasi checklist serah-terima kelengkapan alat.",
        "action_foreman": "Buat sistem Shadow Board / Busa Cetak dan penandaan warna (Color Coding).",
        "action_sh": "Audit ketersediaan dan kondisi kelayakan tools kerja secara berkala.",
        "action_dh": "Setujui penggantian/penambahan investasi tools kerja yang standar."
    },
    "Penyimpanan Master Work": {
        "cause": "(1) Sampel master kotor atau berdebu. (2) Sampel master tercampur dengan produk biasa.",
        "action_operator": "(1) Simpan sampel master di box terkunci. (2) Bersihkan wadah sampel secara rutin.",
        "action_gl": "Pastikan sampel master selalu memiliki stiker 'MASTER WORK - DILARANG UNTUK PRODUKSI'.",
        "action_foreman": "Lakukan verifikasi kondisi fisik dan validitas kalibrasi master sampel bulanan.",
        "action_sh": "Tinjau SOP pendaftaran, penyimpanan, dan masa kadaluwarsa master sampel.",
        "action_dh": "Sahkan standar kualitas acuan (Master Work) bersama tim Quality Assurance (QA)."
    },
    "Informasi Terdokumentasi": {
        "cause": "(1) Papan informasi kotor dan kusam. (2) Kertas pengumuman/SOP yang ditempel sudah kedaluwarsa.",
        "action_operator": "(1) Bersihkan papan informasi dari debu. (2) Laporkan kertas yang sobek ke Group Leader.",
        "action_gl": "Tarik pengumuman/SOP lama yang kedaluwarsa dan ganti dengan dokumen berlaku.",
        "action_foreman": "Update matriks informasi, grafik pencapaian KPI, dan kontrol dokumen.",
        "action_sh": "Audit kepatuhan pengisian dokumen kontrol dan instruksi kerja ter-update.",
        "action_dh": "Dukung sistem digitalisasi papan informasi (Visual Management Display)."
    },
    "Tempat Istirahat": {
        "cause": "(1) Sisa makanan berserakan di meja/lantai. (2) Tempat sampah penuh atau jalurnya tercampur.",
        "action_operator": "(1) Buang sisa makanan langsung ke tempat sampah terpisah. (2) Jalankan piket kebersihan.",
        "action_gl": "Awasi kepatuhan anggota shift terhadap jadwal piket dan kebersihan area istirahat.",
        "action_foreman": "Sediakan fasilitas tempat sampah terpilah dan fasilitas pembersihan memadai.",
        "action_sh": "Evaluasi ketersediaan dan kelayakan fasilitas tempat istirahat karyawan.",
        "action_dh": "Dukung penciptaan lingkungan kerja yang sehat, nyaman, dan berbudaya 5S."
    },
    "Meja Kerja Leader": {
        "cause": "(1) Laporan dan berkas kertas menumpuk acak-acakan. (2) Dokumen penting dan biasa tercampur.",
        "action_operator": "(1) Taruh berkas laporan masuk pada tray 'IN' yang disediakan di meja Leader.",
        "action_gl": "Gunakan filing tray 3 tingkat (IN, ON PROCESS, OUT) dan rapikan berkas akhir kerja.",
        "action_foreman": "Terapkan Color Coded Filing (Map Warna) berdasarkan prioritas.",
        "action_sh": "Audit kerapian meja kerja Leader saat melakukan Gemba Walk mingguan.",
        "action_dh": "Instruksikan percepatan efisiensi proses kerja paperless (persetujuan digital)."
    },
    "Penempatan Dokumen": {
        "cause": "(1) Map dokumen di lemari/rak tidak ada nomor/kategori. (2) Dokumen lama menumpuk di laci.",
        "action_operator": "(1) Kembalikan map dokumen ke posisi semula setelah selesai dibaca.",
        "action_gl": "Pastikan bagian luar ordner/map tertempel label identifikasi dan nomor urut jelas.",
        "action_foreman": "Pisahkan hardcopy sesuai Jadwal Retensi Dokumen (Dokumen Aktif vs Inaktif).",
        "action_sh": "Buat Master Index Filing Cabinet dan tata kelola pengarsipan terpusat.",
        "action_dh": "Setujui prosedur pemusnahan/penyimpanan jangka panjang untuk arsip dokumen lama."
    }
}

# ----------------- HELPER FUNCTIONS -----------------
def get_level_5s(avg_score):
    if avg_score >= 5.0:
        return "Gold", "lvl-gold"
    elif avg_score >= 4.0:
        return "Silver", "lvl-silver"
    elif avg_score >= 3.0:
        return "Bronze", "lvl-bronze"
    else:
        return "Black", "lvl-black"

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
        x=x_labels, y=actual_vals, name='Aktual',
        marker_color=bar_colors, text=actual_vals, textposition='auto',
        width=0.45 if is_kriteria else 0.55
    ))
    fig.add_trace(go.Scatter(
        x=x_labels, y=target_vals, name='Target', mode='lines+markers',
        line=dict(color='#0099ff', width=3, shape='spline'),
        marker=dict(size=9, color='#0099ff')
    ))
    clean_targets = [float(v) for v in target_vals if str(v).replace('.','',1).isdigit()]
    clean_actuals = [float(v) for v in actual_vals if str(v).replace('.','',1).isdigit()]
    max_val = max(max(clean_targets, default=10), max(clean_actuals, default=10))
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=14, color='#004d73')),
        height=300, margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, type='category'),
        yaxis=dict(title="Nilai Patrol", showgrid=True, gridcolor='#e2e8f0', range=[0, max_val * 1.25])
    )
    return fig

def render_exact_table(columns_header, targets, actuals, first_col_label="Line"):
    html = '<table class="table-5s">'
    html += f'<tr><th style="width: 10%;">{first_col_label}</th>'
    for col in columns_header:
        html += f'<th>{col}</th>'
    html += '</tr><tr><td class="bg-label">Target</td>'
    for t in targets:
        html += f'<td>{t if t is not None and str(t) != "" else "-"}</td>'
    html += '</tr><tr><td class="bg-label">Aktual</td>'
    for a in actuals:
        html += f'<td>{a if a is not None and str(a) != "" else "-"}</td>'
    html += '</tr><tr><td class="bg-label">Judge</td>'
    for a, t in zip(actuals, targets):
        try:
            if float(a) >= float(t):
                html += '<td class="judge-ok">OK</td>'
            else:
                html += '<td class="judge-ng">NG</td>'
        except (ValueError, TypeError):
            html += '<td>-</td>'
    html += '</tr></table>'
    return html

def create_pareto_chart(kriteria_list, scores_list):
    df_pareto = pd.DataFrame({'Kriteria': kriteria_list, 'Nilai': scores_list})
    df_pareto['Nilai'] = pd.to_numeric(df_pareto['Nilai'], errors='coerce').fillna(0)
    df_pareto = df_pareto.sort_values(by='Nilai', ascending=True).reset_index(drop=True)
    total_val = df_pareto['Nilai'].sum()
    df_pareto['CumPercentage'] = (df_pareto['Nilai'].cumsum() / total_val * 100) if total_val > 0 else 0

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=df_pareto['Kriteria'], y=df_pareto['Nilai'], name="Rata-rata Nilai",
        marker_color='#ff5252', text=df_pareto['Nilai'].round(2), textposition='auto'
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=df_pareto['Kriteria'], y=df_pareto['CumPercentage'], name="Kumulatif (%)",
        mode='lines+markers', line=dict(color='#004d73', width=2), marker=dict(size=6)
    ), secondary_y=True)

    fig.update_layout(
        title=dict(text="<b>DIAGRAM PARETO: EVALUASI KRITERIA DENGAN PERFORMA TERRENDAH</b>", font=dict(size=14, color='#004d73')),
        height=380, margin=dict(l=20, r=20, t=40, b=80),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, tickangle=-30)
    )
    fig.update_yaxes(title_text="Rata-rata Nilai Kriteria", secondary_y=False, showgrid=True, gridcolor='#e2e8f0')
    fig.update_yaxes(title_text="Persentase Kumulatif (%)", secondary_y=True, range=[0, 110], showgrid=False)
    return fig

# ----------------- EXECUTION & DATA PROCESSING -----------------
if df.empty:
    st.error("Data Google Sheets kosong atau tidak ditemukan. Harap periksa koneksi dan link file.")
else:
    # ----------------- LOGIKA PEMISAHAN DATA (GAMBAR 1 VS GAMBAR 2) -----------------
    col_b = df.columns[1] # Kolom B (Kriteria Penilaian / Bulan Berjalan)

    # A. DATA GAMBAR 1 (Khusus 11 Kriteria Penilaian - Tab 1, 2, 4, 5)
    df_kriteria = df[df[col_b].astype(str).str.contains(
        "Sekitar area|Penyimpanan|Area Kerja|Peralatan|Informasi|Tempat|Meja|Penempatan|Mesin", 
        case=False, na=False
    )].copy()
    df_kriteria.columns = [c.replace('.1', '').strip() for c in df_kriteria.columns]

    # B. DATA GAMBAR 2 (Khusus Tren Bulanan Jan - Dec - Tab 3)
    df_bulanan = df[df[col_b].astype(str).str.contains(
        "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Mei|Jun|Jul|Aug|Sep|Oct|Nov|Dec", 
        case=False, na=False
    )].copy()
    df_bulanan.columns = [c.replace('.1', '').strip() for c in df_bulanan.columns]

    # Sidebar Filter
    st.sidebar.header("🔍 Filter & Kontrol Dashboard")
    if st.sidebar.button("🔄 Refresh Data Sheets"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    selected_months = st.sidebar.multiselect("🗓️ Filter Bulan (By Month):", options=ALL_MONTHS, default=ALL_MONTHS)
    selected_departments = st.sidebar.multiselect("🏢 Filter Department / Line:", options=TARGET_AREAS, default=TARGET_AREAS)

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

    # UNIFIED TABS
    tab_summary, tab_details, tab_monthly_area, tab_pareto, tab_action = st.tabs([
        "📊 Executive Summary (By Month & By Area)", 
        "🏭 Detail 11 Kriteria Penilaian (By Line)", 
        "📅 Tren Bulanan Per Area (Jan - Dec)",
        "📈 Pareto Analisis Kriteria Rendah",
        "🛠️ CAPA Tracking"
    ])

    kriteria_labels = DEFAULT_KRITERIA_LIST
    IMAGE_DIR = "uploaded_images"
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    # =========================================================================
    # --- TAB 1: SUMMARY & ANALYSIS ---
    # =========================================================================
    with tab_summary:
        st.markdown('<div class="section-header">PENCAPAIAN 5S PER AREA (GAMBAR 1 SUMMARY)</div>', unsafe_allow_html=True)
        
        total_actual_sum = 0.0
        total_target_sum = 0.0
        area_targets = []
        area_actuals = []
        
        all_cols_k = df_kriteria.columns.tolist()
        for area in selected_departments:
            c_t = next((c for c in all_cols_k if area.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in all_cols_k if area.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            
            sum_t = df_kriteria[c_t].dropna().sum() if c_t else 0
            sum_a = df_kriteria[c_a].dropna().sum() if c_a else 0
            area_targets.append(sum_t)
            area_actuals.append(sum_a)
            total_actual_sum += sum_a
            total_target_sum += sum_t

        JUMLAH_AREA = len(selected_departments) if selected_departments else 10
        JUMLAH_KRITERIA = 11
        avg_actual = total_actual_sum / (JUMLAH_AREA * JUMLAH_KRITERIA) if JUMLAH_AREA > 0 else 0
        avg_target = total_target_sum / (JUMLAH_AREA * JUMLAH_KRITERIA) if total_target_sum > 0 else 4.0
        overall_level, level_css = get_level_5s(avg_actual)

        if overall_level in ["Gold", "Silver"]:
            status_summary = "<span style='color: #2e7d32; font-weight: bold;'>SANGAT BAIK (PERTAHANKAN)</span>"
            action_summary = "Performa 5S secara keseluruhan berada pada standar tinggi. Pertahankan budaya kerja ini dan lakukan audit rutin."
        elif overall_level == "Bronze":
            status_summary = "<span style='color: #e65100; font-weight: bold;'>BUTUH PERBAIKAN FOKUS</span>"
            action_summary = "Beberapa kriteria/area belum mencapai target. Segera tindak lanjuti temuan NG pada area terkait."
        else:
            status_summary = "<span style='color: #c62828; font-weight: bold;'>PERLU TINDAKAN DARURAT (CRITICAL)</span>"
            action_summary = "Pencapaian 5S berada di bawah standar minimum. Direkomendasikan melakukan Gemba Walk gabungan."

        st.markdown(f"""
            <div class="summary-box" style="background-color: var(--secondary-background-color, #ffffff); border-left: 5px solid #004d73; margin-bottom: 20px;">
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
                        <td>: Total Nilai ({total_actual_sum:.1f}) ÷ {JUMLAH_AREA} Area ÷ 11 Kriteria = <b>{avg_actual:.2f}</b></td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Rekomendasi Tindakan</td>
                        <td>: {action_summary}</td>
                    </tr>
                </table>
            </div>
        """, unsafe_allow_html=True)

        if selected_departments:
            st.plotly_chart(create_exact_chart(selected_departments, area_targets, area_actuals, "PENCAPAIAN PER AREA / DEPARTMENT"), use_container_width=True)
            st.markdown(render_exact_table(selected_departments, area_targets, area_actuals, "Area"), unsafe_allow_html=True)

        st.markdown("<hr style='margin: 40px 0; border: 0; border-top: 3px solid #004d73;'>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">ANALISA KETIDAKTERCAPAIAN AKTIVITAS PATROL 5S</div>', unsafe_allow_html=True)
        
        st.subheader("📋 1. Analisa Kondisi Yang Ada (4M Analysis)")
        data_4m = [
            {"No": 1, "Man": "", "Machine": "", "Material": "", "Method": "✓", "Control Item": "Pelaksanaan Patrol 5S", "Control Point": "Frekuensi & Jadwal Patrol", "Standard": "Patrol rutin 1x/minggu sesuai kalender", "Actual": "Patrol hanya terlaksana 2x/bulan", "Ilustration": "-", "Judge": "NG"},
            {"No": 2, "Man": "✓", "Machine": "", "Material": "", "Method": "", "Control Item": "Kedisiplinan Area Owner", "Control Point": "Penyelesaian CAPA 5S", "Standard": "Closing CAPA 100% tepat waktu (< 7 hari)", "Actual": "Penyelesaian CAPA terlambat (rata-rata 14 hari)", "Ilustration": "-", "Judge": "NG"},
            {"No": 3, "Man": "", "Machine": "", "Material": "✓", "Method": "", "Control Item": "Fasilitas & Labeling 5S", "Control Point": "Kelengkapan Line Marking & Label", "Standard": "100% Area terlabeli & border utuh", "Actual": "Garis pembatas pudar & label alat hilang di 3 area", "Ilustration": "-", "Judge": "NG"}
        ]
        st.dataframe(pd.DataFrame(data_4m), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🔍 2. Analisa Sebab Akibat (5 Why's Analysis)")
        data_5why = [
            {"NO": 1, "PROBLEM DESCRIPTION": "Frekuensi Patrol 5S tidak mencapai target bulanan", "STD": "Patrol 1x/minggu", "ACT": "Terlaksana 2x/bulan", "4M": "Method", "WHY 1": "Jadwal patrol sering bertabrakan dengan schedule produksi urgent", "WHY 2": "Belum ada alokasi waktu khusus (fixed slot) untuk patrol", "WHY 3": "Patrol dianggap aktivitas opsional di luar operasional utama", "WHY 4": "Belum ada KPI spesifik terkait kepatuhan jadwal Patrol 5S", "WHY 5": "Sistem manajemen belum mengintegrasikan 5S ke dalam Standar Kerja Harian"},
            {"NO": 2, "PROBLEM DESCRIPTION": "Penyelesaian CAPA 5S sering delay", "STD": "Close < 7 hari", "ACT": "Rata-rata 14 hari", "4M": "Man", "WHY 1": "PIC terlambat melakukan tindak lanjut perbaikan", "WHY 2": "PIC tidak menerima notifikasi reminder tugas perbaikan", "WHY 3": "Monitoring CAPA masih dilakukan secara manual berkala", "WHY 4": "Sistem tracking CAPA belum terhubung langsung dengan alert PIC", "WHY 5": "Belum ada sistem eskalasi otomatis jika CAPA melewati due date"}
        ]
        st.dataframe(pd.DataFrame(data_5why), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("🐟 3. Diagram Fishbone / Ishikawa (Ketidaktercapaian 5S)")
        fig_fishbone = go.Figure()
        fig_fishbone.add_trace(go.Scatter(
            x=[0, 10, 11], y=[0, 0, 0], mode='lines+text',
            line=dict(color='#1f77b4', width=4),
            text=["", "", "<b>Pencapaian 5S<br>Tidak Tercapai</b>"], textposition="middle right", showlegend=False
        ))
        categories = [
            ("METHOD", 3, 2, "Jadwal bentrok produksi<br>→ Tanpa fixed time slot"),
            ("MAN", 7, 2, "Delay tindakan perbaikan<br>→ Tanpa reminder sistem"),
            ("MATERIAL", 3, -2, "Border & label pudar/hilang<br>→ Tidak ada jadwal peremajaan"),
            ("MACHINE", 7, -2, "Alat kebersihan rusak<br>→ Penanggung jawab tidak jelas")
        ]
        for cat, x_top, y_top, subtext in categories:
            fig_fishbone.add_trace(go.Scatter(
                x=[x_top - 1, x_top], y=[y_top, 0], mode='lines+text',
                line=dict(color='#2c3e50', width=2), text=[f"<b>{cat}</b>", ""],
                textposition="top center" if y_top > 0 else "bottom center", showlegend=False
            ))
            fig_fishbone.add_annotation(x=x_top - 0.5, y=y_top / 2, text=subtext, showarrow=False, font=dict(size=10, color="#555555"))
        
        fig_fishbone.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 14]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-4, 4]),
            height=320, margin=dict(l=20, r=20, t=20, b=20), plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_fishbone, use_container_width=True)

    # =========================================================================
    # --- TAB 2: DETAIL 11 KRITERIA PENILAIAN (GAMBAR 1) ---
    # =========================================================================
    with tab_details:
        st.markdown('<div class="section-header">BY KRITERIA PENILAIAN & ANALISA PERBAIKAN (GAMBAR 1)</div>', unsafe_allow_html=True)
        
        all_cols_kriteria = df_kriteria.columns.tolist()
        lines_info_t2 = []
        for area_code in TARGET_AREAS:
            c_t = next((c for c in all_cols_kriteria if area_code.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in all_cols_kriteria if area_code.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            if c_t and c_a:
                lines_info_t2.append((area_code, c_t, c_a))

        available_area_names = [info[0] for info in lines_info_t2]
        selected_tab2_lines = st.multiselect(
            "🎯 Pilih Area / Line yang Ingin Ditampilkan:",
            options=available_area_names,
            default=available_area_names,
            key="filter_tab2_lines"
        )
        
        filtered_lines_t2 = [info for info in lines_info_t2 if info[0] in selected_tab2_lines]
        st.markdown("<br>", unsafe_allow_html=True)
        x_kriteria_num = [str(i) for i in range(1, len(kriteria_labels) + 1)]

        def render_line_analysis(title_area, targets_list, actuals_list):
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
                        rec_data = next((v for k, v in RCA_RECOMMENDATION.items() if k.lower() in k_name.lower() or k_name.lower() in k.lower()), {
                            "cause": "Belum ada catatan.", "action_operator": "-", "action_gl": "-", "action_foreman": "-"
                        })
                        list_items_html += (
                            f"<li style='margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #ffcdd2;'>"
                            f"<b>{k_name}</b> (Nilai: <span style='color:#d32f2f; font-weight:bold;'>{act_val:.1f}</span> / Target: {tgt_val:.1f})<br>"
                            f"&bull; <i>Penyebab Utama:</i> {rec_data.get('cause', '-')}<br>"
                            f"<div style='margin-top: 4px; padding-left: 8px; border-left: 2px solid #e57373;'>"
                            f"&bull; <b>Tindakan Operator:</b> <span style='color:#1b5e20;'>{rec_data.get('action_operator', '-')}</span><br>"
                            f"&bull; <b>Tindakan Group Leader:</b> <span style='color:#0d47a1;'>{rec_data.get('action_gl', '-')}</span><br>"
                            f"&bull; <b>Tindakan Foreman:</b> <span style='color:#e65100;'>{rec_data.get('action_foreman', '-')}</span><br>"
                            f"</div></li>"
                        )
                    st.markdown(f"""
                    <div class="analysis-card">
                        <h5 style="color: #b71c1c; margin-top: 0; font-weight: 700;">🔍 ANALISA & REKOMENDASI PERBAIKAN AREA {title_area.upper()}:</h5>
                        <ol style="margin: 5px 0 5px 15px; padding: 0; font-size: 12px;">{list_items_html}</ol>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success(f"🎉 Area {title_area} memenuhi seluruh kriteria target 5S (100% OK).")

        if not filtered_lines_t2:
            st.warning("Silakan pilih minimal satu area pada filter di atas.")
        else:
            for area_code, col_tgt, col_act in filtered_lines_t2:
                t_k = df_kriteria[col_tgt].dropna().tolist()
                a_k = df_kriteria[col_act].dropna().tolist()
                
                clean_act = [float(x) for x in a_k if str(x).replace('.', '', 1).isdigit()]
                avg_val = (sum(clean_act) / len(clean_act)) if clean_act else 0.0
                lvl_val, css_val = get_level_5s(avg_val)

                st.markdown(f"#### 🏭 AREA {area_code} &nbsp; <span class='badge-level {css_val}'>Level: {lvl_val} ({avg_val:.2f})</span>", unsafe_allow_html=True)
                st.plotly_chart(create_exact_chart(x_kriteria_num[:len(t_k)], t_k, a_k, f"Kriteria Penilaian 5S - {area_code}", is_kriteria=True), use_container_width=True)
                st.markdown(render_exact_table(kriteria_labels[:len(t_k)], t_k, a_k, "Kriteria"), unsafe_allow_html=True)
                render_line_analysis(area_code, t_k, a_k)
                st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px dashed #cbd5e1;'>", unsafe_allow_html=True)

    # =========================================================================
    # --- TAB 3: TREN BULANAN PER AREA (GAMBAR 2) ---
    # =========================================================================
    with tab_monthly_area:
        st.markdown('<div class="section-header">REKAPITULASI TREN PENCAPAIAN 5S PER AREA (JANUARI - DESEMBER)</div>', unsafe_allow_html=True)
        
        all_cols_bulanan = df_bulanan.columns.tolist()
        area_pairs_t3 = []
        for area_code in TARGET_AREAS:
            c_t = next((c for c in all_cols_bulanan if area_code.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in all_cols_bulanan if area_code.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            if c_t and c_a:
                area_pairs_t3.append((area_code, c_t, c_a))

        filtered_pairs_t3 = [
            p for p in area_pairs_t3 
            if not selected_departments or any(sd.lower() in p[0].lower() or p[0].lower() in sd.lower() for sd in selected_departments)
        ]
        if not filtered_pairs_t3:
            filtered_pairs_t3 = area_pairs_t3

        if df_bulanan.empty or not filtered_pairs_t3:
            st.warning("⚠️ Data Tren Bulanan (Gambar 2) tidak terdeteksi. Pastikan baris bulan (January - December) tersedia di spreadsheet.")
        else:
            col_bulan_name = df_bulanan.columns[1]
            months_label_g2 = df_bulanan[col_bulan_name].dropna().tolist()

            summary_stats = []
            for area_name, c_t, c_a in filtered_pairs_t3:
                t_vals = [float(v) for v in df_bulanan[c_t].dropna() if str(v).replace('.','',1).isdigit()]
                a_vals = [float(v) for v in df_bulanan[c_a].dropna() if str(v).replace('.','',1).isdigit()]
                
                avg_a = sum(a_vals) / len(a_vals) if a_vals else 0.0
                avg_t = sum(t_vals) / len(t_vals) if t_vals else 4.0
                ok_months = sum(1 for a_v, t_v in zip(a_vals, t_vals) if a_v >= t_v)
                
                summary_stats.append({
                    "area": area_name, "avg_actual": avg_a, "avg_target": avg_t,
                    "ok_months": ok_months, "total_months": len(a_vals)
                })

            if summary_stats:
                best_area = max(summary_stats, key=lambda x: x['avg_actual'])
                lowest_area = min(summary_stats, key=lambda x: x['avg_actual'])
                consistent_areas = [s['area'] for s in summary_stats if s['ok_months'] == s['total_months'] and s['total_months'] > 0]
                consistent_str = ", ".join(consistent_areas) if consistent_areas else "Belum ada area yang 100% konsisten tiap bulan"

                st.markdown(f"""
                    <div class="summary-box" style="background-color: var(--secondary-background-color, #ffffff); border-left: 5px solid #004d73; margin-bottom: 25px;">
                        <h4 style="margin: 0 0 8px 0; color: #004d73; font-size: 15px;">📋 RANGKUMAN REKAPITULASI TREN BULANAN PER AREA (GAMBAR 2)</h4>
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
                        </table>
                    </div>
                """, unsafe_allow_html=True)

            for i in range(0, len(filtered_pairs_t3), 2):
                cols_m = st.columns(2)
                area_name1, col_t1, col_a1 = filtered_pairs_t3[i]
                t_m1 = df_bulanan[col_t1].dropna().tolist()
                a_m1 = df_bulanan[col_a1].dropna().tolist()
                
                with cols_m[0]:
                    st.plotly_chart(create_exact_chart(months_label_g2[:len(a_m1)], t_m1, a_m1, f"REKAP TREN BULANAN 5S - {area_name1.upper()}"), use_container_width=True)
                    st.markdown(render_exact_table(months_label_g2[:len(a_m1)], t_m1, a_m1, "Bulan"), unsafe_allow_html=True)
                
                if i + 1 < len(filtered_pairs_t3):
                    area_name2, col_t2, col_a2 = filtered_pairs_t3[i+1]
                    t_m2 = df_bulanan[col_t2].dropna().tolist()
                    a_m2 = df_bulanan[col_a2].dropna().tolist()
                    
                    with cols_m[1]:
                        st.plotly_chart(create_exact_chart(months_label_g2[:len(a_m2)], t_m2, a_m2, f"REKAP TREN BULANAN 5S - {area_name2.upper()}"), use_container_width=True)
                        st.markdown(render_exact_table(months_label_g2[:len(a_m2)], t_m2, a_m2, "Bulan"), unsafe_allow_html=True)
                
                st.markdown("<hr style='margin: 25px 0; border: 0; border-top: 1px dashed #cbd5e1;'>", unsafe_allow_html=True)

    # =========================================================================
    # --- TAB 4: PARETO ANALYSIS ---
    # =========================================================================
    with tab_pareto:
        st.markdown('<div class="section-header">DIAGRAM PARETO: EVALUASI KRITERIA DENGAN NILAI TERRENDAH</div>', unsafe_allow_html=True)
        
        kriteria_scores = {k: [] for k in kriteria_labels}
        for area_code in TARGET_AREAS:
            c_act_p = next((c for c in df_kriteria.columns if area_code.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            if c_act_p:
                vals = df_kriteria[c_act_p].dropna().tolist()
                for idx_k, val_k in enumerate(vals):
                    if idx_k < len(kriteria_labels) and str(val_k).replace('.', '', 1).isdigit():
                        kriteria_scores[kriteria_labels[idx_k]].append(float(val_k))

        avg_scores = [(sum(kriteria_scores[k]) / len(kriteria_scores[k])) if kriteria_scores[k] else 0.0 for k in kriteria_labels]
        
        col_p1, col_p2 = st.columns([2, 1])
        with col_p1:
            st.plotly_chart(create_pareto_chart(kriteria_labels, avg_scores), use_container_width=True)
            df_rank_p = pd.DataFrame({'Kriteria': kriteria_labels, 'Nilai': avg_scores}).sort_values(by='Nilai', ascending=True).reset_index(drop=True)
            top_3_lowest = df_rank_p.head(3).values.tolist()
            p_items_html = "".join([f"<li><b>{item[0]}</b> (Rata-rata Score: <b>{item[1]:.2f}</b>)</li>" for item in top_3_lowest])
            
            st.markdown(f"""
                <div class="summary-box">
                    <strong>📌 Kesimpulan Evaluasi Kriteria (Pareto):</strong><br>
                    3 Kriteria dengan performa terendah yang membutuhkan tindakan korektif utama adalah:
                    <ol style="margin: 5px 0 0 20px; padding: 0;">{p_items_html}</ol>
                </div>
            """, unsafe_allow_html=True)
            
        with col_p2:
            st.markdown("##### 🔍 Ranking Kriteria Terrendah")
            df_rank = pd.DataFrame({'Kriteria Penilaian': kriteria_labels, 'Rata-Rata Nilai': avg_scores}).sort_values(by='Rata-Rata Nilai', ascending=True).reset_index(drop=True)
            df_rank.index = df_rank.index + 1
            st.dataframe(df_rank, use_container_width=True)

    # =========================================================================
    # --- TAB 5: CAPA TRACKING & LOG INPUT ---
    # =========================================================================
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
                input_area = st.selectbox("Area / Department Temuan:", options=TARGET_AREAS)
                input_kriteria = st.selectbox("Kriteria 5S Bermasalah:", options=kriteria_labels)
                input_detail_problem = st.text_area("Detail Temuan Masalah (Kondisi Lapangan):", placeholder="Misal: Garis kuning pembatas terkelupas di mesin A")
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
                save_capa_to_gsheets(st.session_state["capa_log_data"])
                st.success(f"✅ Data temuan NG di area '{input_area}' berhasil disimpan!")
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 3. Daftar Monitoring Action Plan (CAPA Log)")
        
        if st.session_state["capa_log_data"]:
            df_capa_log = pd.DataFrame(st.session_state["capa_log_data"])
            edited_df = st.data_editor(df_capa_log, use_container_width=True, key="capa_editor")
            if st.button("💾 Simpan Perubahan Status / Tabel", type="primary"):
                st.session_state["capa_log_data"] = edited_df.to_dict("records")
                save_capa_to_gsheets(st.session_state["capa_log_data"])
                st.success("✅ CAPA Log berhasil diperbarui!")
                st.rerun()
        else:
            st.info("Belum ada log temuan yang diinputkan.")

    with st.expander("📋 Lihat Raw Data Google Sheets"):
        st.dataframe(df, use_container_width=True)
