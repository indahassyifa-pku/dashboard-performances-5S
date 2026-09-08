import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import datetime
from groq import Groq
from streamlit_gsheets import GSheetsConnection

# ----------------- KONFIGURASI HALAMAN -----------------
st.set_page_config(
    page_title="Dashboard Patrol 5S",
    page_icon="🧹",
    layout="wide"
)

# Custom Styling Adaptif (Dark & Light Mode Support)
st.markdown("""
    <style>
    /* Menggunakan variabel CSS bawaan Streamlit untuk kompatibilitas Dark & Light Mode */
    
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

    /* Card Container untuk Grafik Plotly */
    div[data-testid="stPlotlyChart"] {
        background-color: var(--secondary-background-color, rgba(255, 255, 255, 0.03));
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 12px;
        padding: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    .lvl-black { background-color: #374151; }
    .lvl-bronze { background-color: #d97706; }
    .lvl-silver { background-color: #6b7280; }
    .lvl-gold { background-color: #eab308; }
    
    </style>
""", unsafe_allow_html=True)



import os

# ----------------- LINK GOOGLE SHEETS DATA UTAMA (PUBLISH / READ-ONLY) -----------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQU_jpdzrymx_0mJKGVDopip0DPhnmDLIbsTHgVnqgaJZZayJUp-UPF1MF6H6soCA/pub?output=csv"

@st.cache_data(ttl=10)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
        return pd.DataFrame()

df = load_data(SHEET_URL)


# ----------------- STORAGE LOKAL CSV UNTUK CAPA LOG -----------------
CAPA_CSV_FILE = "capa_log_database.csv"

def load_capa_from_gsheets():
    """Membaca data CAPA dari file CSV lokal"""
    if os.path.exists(CAPA_CSV_FILE):
        try:
            df_capa = pd.read_csv(CAPA_CSV_FILE)
            return df_capa.to_dict("records")
        except Exception:
            return []
    return []

def save_capa_to_gsheets(data_list):
    """Menyimpan data CAPA ke file CSV lokal"""
    df_capa = pd.DataFrame(data_list)
    df_capa.to_csv(CAPA_CSV_FILE, index=False)

# Inisialisasi Session State CAPA Log menggunakan CSV Lokal
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

# ----------------- GRAFIK PLOTLY MODERN & ADAPTIF -----------------
def create_exact_chart(x_labels, target_vals, actual_vals, title, is_kriteria=False):
    fig = go.Figure()
    
    # Elemen Warna Modern (Soft Emerald & Soft Coral)
    bar_colors = []
    for act, tgt in zip(actual_vals, target_vals):
        try:
            act_num = float(act)
            tgt_num = float(tgt)
            if act_num >= tgt_num:
                bar_colors.append('#10B981')  # Emerald Green
            else:
                bar_colors.append('#F43F5E')  # Rose / Soft Red
        except (ValueError, TypeError):
            bar_colors.append('#9CA3AF')  # Slate Gray
    
    # Bar Chart (Nilai Aktual)
    fig.add_trace(go.Bar(
        x=x_labels,
        y=actual_vals,
        name='Aktual',
        marker=dict(
            color=bar_colors,
            line=dict(width=0),
            opacity=0.9
        ),
        text=actual_vals,
        textposition='outside',
        textfont=dict(size=11, weight='bold'),
        width=0.4 if is_kriteria else 0.45
    ))
    
    # Line Chart (Nilai Target)
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=target_vals,
        name='Target',
        mode='lines+markers',
        line=dict(color='#6366F1', width=3, shape='spline'),  # Indigo
        marker=dict(size=7, color='#4338CA', symbol='circle')
    ))
    
    clean_targets = [float(v) for v in target_vals if str(v).replace('.','',1).isdigit()]
    clean_actuals = [float(v) for v in actual_vals if str(v).replace('.','',1).isdigit()]
    max_val = max(max(clean_targets, default=10), max(clean_actuals, default=10))
    
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>", 
            font=dict(size=15, family="Inter, sans-serif")
        ),
        height=340,
        margin=dict(l=15, r=15, t=50, b=15),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="right", 
            x=1,
            font=dict(size=12)
        ),
        xaxis=dict(
            showgrid=False, 
            type='category',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title="Nilai Patrol", 
            showgrid=True, 
            gridcolor='rgba(156, 163, 175, 0.15)',
            range=[0, max_val * 1.28]
        ),
        hovermode="x unified"
    )
    return fig


def create_pareto_chart(kriteria_list, scores_list):
    df_pareto = pd.DataFrame({'Kriteria': kriteria_list, 'Nilai': scores_list})
    df_pareto['Nilai'] = pd.to_numeric(df_pareto['Nilai'], errors='coerce').fillna(0)
    df_pareto = df_pareto.sort_values(by='Nilai', ascending=True).reset_index(drop=True)
    
    total_val = df_pareto['Nilai'].sum()
    df_pareto['CumPercentage'] = (df_pareto['Nilai'].cumsum() / total_val * 100) if total_val > 0 else 0

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Bar Chart Pareto
    fig.add_trace(
        go.Bar(
            x=df_pareto['Kriteria'],
            y=df_pareto['Nilai'],
            name="Rata-rata Nilai",
            marker=dict(color='#F43F5E', opacity=0.85),
            text=df_pareto['Nilai'].round(2),
            textposition='outside',
            textfont=dict(size=10, weight='bold')
        ),
        secondary_y=False
    )
    
    # Line Chart Kumulatif (%)
    fig.add_trace(
        go.Scatter(
            x=df_pareto['Kriteria'],
            y=df_pareto['CumPercentage'],
            name="Kumulatif (%)",
            mode='lines+markers',
            line=dict(color='#0EA5E9', width=2.5, shape='spline'),
            marker=dict(size=6, color='#0284C7')
        ),
        secondary_y=True
    )

    fig.update_layout(
        title=dict(
            text="<b>DIAGRAM PARETO: EVALUASI KRITERIA TERRENDAH</b>", 
            font=dict(size=14, family="Inter, sans-serif")
        ),
        height=380,
        margin=dict(l=15, r=15, t=50, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, tickangle=-30, tickfont=dict(size=10))
    )
    
    fig.update_yaxes(title_text="Rata-rata Nilai", secondary_y=False, showgrid=True, gridcolor='rgba(156, 163, 175, 0.15)')
    fig.update_yaxes(title_text="Persentase Kumulatif (%)", secondary_y=True, range=[0, 115], showgrid=False)
    
    return fig

# ----------------- EKSEKUSI PEMBACAAN DATA EXCEL -----------------
if df.empty:
    st.error("Data Google Sheets kosong atau tidak ditemukan. Harap periksa koneksi dan link file.")
else:
    all_columns = df.columns.tolist()
    ALL_MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    
    # Deteksi otomatis kolom target & aktual By Month
    col_tgt_m = next((c for c in all_columns if 'target' in c.lower() and 'month' in c.lower()), None) or next((c for c in all_columns if 'target' in c.lower()), None)
    col_act_m = next((c for c in all_columns if 'aktual' in c.lower() and 'month' in c.lower()), None) or next((c for c in all_columns if 'aktual' in c.lower()), None)
    
    months_data = df['Bulan'].tolist() if 'Bulan' in all_columns else ALL_MONTHS
    targets_m_data = df[col_tgt_m].tolist() if col_tgt_m else []
    actuals_m_data = df[col_act_m].tolist() if col_act_m else []

    # Filter khusus area agar kata 'by area', 'total', 'summary' diabaikan
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

    # PERBAIKAN: Penambahan Tab "🛠️ Analisa Perbaikan & CAPA"
    tab_summary, tab_details, tab_pareto, tab_action = st.tabs([
        "📊 Executive Summary (By Month & By Area)", 
        "🏭 Detail 11 Kriteria Penilaian (By Line)", 
        "📈 Pareto Analisis Kriteria Rendah",
        "🛠️ CAPA Tracking"
    ])

    # Ambilitas Nama Kriteria dari Kolom "Kriteria" Excel / Default
    if 'Kriteria' in all_columns and not df['Kriteria'].dropna().empty:
        kriteria_labels = df['Kriteria'].dropna().tolist()
    else:
        kriteria_labels = DEFAULT_KRITERIA_LIST

    # Variables untuk ketersediaan analisis global
    ng_areas = []
    ok_areas = []

# ----------------- KONFIGURASI DIREKTORI GAMBAR LOKAL -----------------
IMAGE_DIR = "uploaded_images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

    # --- TAB 1: SUMMARY & ANALYSIS ---
with tab_summary:
    # ----------------- LOGIKA BARU: HITUNG RATA-RATA DIBAGI 10 AREA & 11 KRITERIA -----------------
    filtered_months = [m for m in months_data if m in selected_months]
    indices_m = [months_data.index(m) for m in filtered_months]
    t_m = [targets_m_data[i] if i < len(targets_m_data) else 0 for i in indices_m]
    a_m = [actuals_m_data[i] if i < len(actuals_m_data) else 0 for i in indices_m]

    # Menghitung Total Nilai Aktual Seluruh Area & Kriteria
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

    # Perhitungan Formula Akhir: Total Nilai / 10 Area / 11 Kriteria
    JUMLAH_AREA = 10
    JUMLAH_KRITERIA = 11

    avg_actual = total_actual_sum / (JUMLAH_AREA * JUMLAH_KRITERIA)
    avg_target = total_target_sum / (JUMLAH_AREA * JUMLAH_KRITERIA) if total_target_sum > 0 else 4.0

    # Menentukan Overall Level berdasarkan Hasil Akhir Skor
    overall_level, level_css = get_level_5s(avg_actual)

    # ----------------- BOX KESIMPULAN UTAMA -----------------
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
        <div class="summary-box" style="background-color: #ffffff; border-left: 5px solid #004d73; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px;">
            <h4 style="margin: 0 0 8px 0; color: #004d73; font-size: 15px;">📋 RANGKUMAN & KESIMPULAN EXECUTIVE SUMMARY</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; line-height: 1.6;">
                <tr>
                    <td style="width: 25%; font-weight: bold; color: #555;">Status Performa 5S</td>
                    <td>: {status_summary}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #555;">Ketercapaian Skor Akhir</td>
                    <td>: Skor Akhir <b>{avg_actual:.2f}</b> dari Target <b>{avg_target:.2f}</b> (Level <b>{overall_level}</b>)</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #555;">Formula Perhitungan</td>
                    <td>: Total Nilai ({total_actual_sum:.1f}) ÷ 10 Area ÷ 11 Kriteria = <b>{avg_actual:.2f}</b></td>
                </tr>
                <tr>
                    <td style="font-weight: bold; color: #555;">Rekomendasi Tindakan</td>
                    <td>: {action_summary}</td>
                </tr>
            </table>
        </div>
    """, unsafe_allow_html=True)

    # ---------------- BARIS 1: BY ALL (PENCAPAIAN BY MONTH) ----------------
    st.markdown('<div class="section-header">BY ALL (PENCAPAIAN BY MONTH)</div>', unsafe_allow_html=True)
    def render_exact_table(columns_header, targets, actuals, first_col_label="Line"):
    try:
        html = '<div class="table-container"><table class="table-5s">'
        html += f'<tr><th style="width: 12%;">{first_col_label}</th>'
        for col in columns_header:
            html += f'<th>{col}</th>'
        html += '</tr>'
        
        # Baris Target
        html += '<tr><td class="bg-label">Target</td>'
        for t in targets:
            val_display = "-" if t is None or pd.isna(t) or str(t).strip() == "" else t
            html += f'<td>{val_display}</td>'
        html += '</tr>'
        
        # Baris Aktual
        html += '<tr><td class="bg-label">Aktual</td>'
        for a in actuals:
            val_display = "-" if a is None or pd.isna(a) or str(a).strip() == "" else a
            html += f'<td>{val_display}</td>'
        html += '</tr>'
        
        # Baris Judge (OK / NG)
        html += '<tr><td class="bg-label">Judge</td>'
        for a, t in zip(actuals, targets):
            try:
                if a is None or t is None or pd.isna(a) or pd.isna(t):
                    html += '<td>-</td>'
                    continue
                act_num = float(a)
                tgt_num = float(t)
                if act_num >= tgt_num:
                    html += '<td class="judge-ok">OK</td>'
                else:
                    html += '<td class="judge-ng">NG</td>'
            except (ValueError, TypeError):
                html += '<td>-</td>'
        html += '</tr>'
        
        html += '</table></div>'
        return html
    except Exception as e:
        return f'<div style="color: red; padding: 10px;">Gagal memuat tabel: {str(e)}</div>'
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

    # ---------------- BARIS 2: BY DEPARTMENT / AREA ----------------
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

    st.markdown("<hr style='margin: 40px 0; border: 0; border-top: 3px solid #004d73;'>", unsafe_allow_html=True)

    # =========================================================================
    # BAGIAN BARU: ANALISA KETIDAKTERCAPAIAN (4M, 5 WHY, FISHBONE & ACTION PLAN)
    # =========================================================================
    st.markdown('<div class="section-header">ANALISA KETIDAKTERCAPAIAN AKTIVITAS PATROL 5S</div>', unsafe_allow_html=True)

    # 1. ANALISA KONDISI YANG ADA (4M ANALYSIS)
    st.subheader("📋 1. Analisa Kondisi Yang Ada (4M Analysis)")
    data_4m = [
        {
            "No": 1, "Man": "", "Machine": "", "Material": "", "Method": "✓",
            "Control Item": "Pelaksanaan Patrol 5S", "Control Point": "Frekuensi & Jadwal Patrol",
            "Standard": "Patrol rutin 1x/minggu sesuai kalender", "Actual": "Patrol hanya terlaksana 2x/bulan",
            "Ilustration": "-", "Judge": "NG"
        },
        {
            "No": 2, "Man": "✓", "Machine": "", "Material": "", "Method": "",
            "Control Item": "Kedisiplinan Area Owner", "Control Point": "Penyelesaian CAPA 5S",
            "Standard": "Closing CAPA 100% tepat waktu (< 7 hari)", "Actual": "Penyelesaian CAPA terlambat (rata-rata 14 hari)",
            "Ilustration": "-", "Judge": "NG"
        },
        {
            "No": 3, "Man": "", "Machine": "", "Material": "✓", "Method": "",
            "Control Item": "Fasilitas & Labeling 5S", "Control Point": "Kelengkapan Line Marking & Label",
            "Standard": "100% Area terlabeli & border utuh", "Actual": "Garis pembatas pudar & label alat hilang di 3 area",
            "Ilustration": "-", "Judge": "NG"
        }
    ]
    st.dataframe(
        pd.DataFrame(data_4m),
        column_config={
            "Man": st.column_config.TextColumn("Man", width="small"),
            "Machine": st.column_config.TextColumn("Mc", width="small"),
            "Material": st.column_config.TextColumn("Mat", width="small"),
            "Method": st.column_config.TextColumn("Met", width="small"),
            "Judge": st.column_config.TextColumn("Judge", width="small"),
        },
        use_container_width=True, hide_index=True
    )

    st.markdown("---")

    # 2. ANALISA SEBAB AKIBAT (5 WHY'S ANALYSIS)
    st.subheader("🔍 2. Analisa Sebab Akibat (5 Why's Analysis)")
    data_5why = [
        {
            "NO": 1, "PROBLEM DESCRIPTION": "Frekuensi Patrol 5S tidak mencapai target bulanan",
            "STD": "Patrol 1x/minggu", "ACT": "Terlaksana 2x/bulan", "4M": "Method",
            "WHY 1": "Jadwal patrol sering bertabrakan dengan schedule produksi urgent",
            "WHY 2": "Belum ada alokasi waktu khusus (fixed slot) untuk patrol",
            "WHY 3": "Patrol dianggap aktivitas opsional di luar operasional utama",
            "WHY 4": "Belum ada KPI spesifik terkait kepatuhan jadwal Patrol 5S",
            "WHY 5": "Sistem manajemen belum mengintegrasikan 5S ke dalam Standar Kerja Harian"
        },
        {
            "NO": 2, "PROBLEM DESCRIPTION": "Penyelesaian CAPA 5S sering delay",
            "STD": "Close < 7 hari", "ACT": "Rata-rata 14 hari", "4M": "Man",
            "WHY 1": "PIC terlambat melakukan tindak lanjut perbaikan",
            "WHY 2": "PIC tidak menerima notifikasi reminder tugas perbaikan",
            "WHY 3": "Monitoring CAPA masih dilakukan secara manual berkala",
            "WHY 4": "Sistem tracking CAPA belum terhubung langsung dengan alert PIC",
            "WHY 5": "Belum ada sistem eskalasi otomatis jika CAPA melewati due date"
        }
    ]
    st.dataframe(pd.DataFrame(data_5why), use_container_width=True, hide_index=True)

    st.markdown("---")

    # 3. DIAGRAM ISHIKAWA / FISHBONE
    st.subheader("🐟 3. Diagram Fishbone / Ishikawa (Ketidaktercapaian 5S)")
    import plotly.graph_objects as go

    fig_fishbone = go.Figure()
    fig_fishbone.add_trace(go.Scatter(
        x=[0, 10, 11], y=[0, 0, 0],
        mode='lines+text',
        line=dict(color='#1f77b4', width=4),
        text=["", "", "<b>Pencapaian 5S<br>Tidak Tercapai</b>"],
        textposition="middle right", showlegend=False
    ))

    categories = [
        ("METHOD", 3, 2, "Jadwal bentrok produksi<br>→ Tanpa fixed time slot"),
        ("MAN", 7, 2, "Delay tindakan perbaikan<br>→ Tanpa reminder sistem"),
        ("MATERIAL", 3, -2, "Border & label pudar/hilang<br>→ Tidak ada jadwal peremajaan"),
        ("MACHINE", 7, -2, "Alat kebersihan rusak<br>→ Penanggung jawab tidak jelas")
    ]

    for cat, x_top, y_top, subtext in categories:
        fig_fishbone.add_trace(go.Scatter(
            x=[x_top - 1, x_top], y=[y_top, 0],
            mode='lines+text',
            line=dict(color='#2c3e50', width=2),
            text=[f"<b>{cat}</b>", ""],
            textposition="top center" if y_top > 0 else "bottom center",
            showlegend=False
        ))
        fig_fishbone.add_annotation(
            x=x_top - 0.5, y=y_top / 2,
            text=subtext, showarrow=False,
            font=dict(size=10, color="#555555")
        )

    fig_fishbone.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 14]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-4, 4]),
        height=320, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_fishbone, use_container_width=True)

    st.markdown("---")

    # 4. RENCANA PERBAIKAN (ACTION PLAN)
    st.subheader("📅 4. Rencana & Tindakan Perbaikan (Action Plan)")
    data_action_plan = [
        {"No": 1, "Item Problem": "Frekuensi Patrol 5S tidak mencapai target bulanan", "Activity": "Penetapan Fixed Time Slot & KPI 5S", "Detail Activity": "Penyusunan jadwal terintegrasi kalender produksi", "Days": 3, "PIC": "OS & Produksi", "Target": "Mei W-III"},
        {"No": 2, "Item Problem": "Frekuensi Patrol 5S tidak mencapai target bulanan", "Activity": "Penetapan Fixed Time Slot & KPI 5S", "Detail Activity": "Sosialisasi & Kick Off Jam Khusus 5S", "Days": 2, "PIC": "ALL Dept", "Target": "Mei W-IV"},
        {"No": 3, "Item Problem": "Penyelesaian CAPA 5S sering delay", "Activity": "Digitalisasi System Tracking CAPA", "Detail Activity": "Pengembangan Dashboard & Auto Notification", "Days": 7, "PIC": "IT / OS", "Target": "Juni W-I"},
        {"No": 4, "Item Problem": "Penyelesaian CAPA 5S sering delay", "Activity": "Digitalisasi System Tracking CAPA", "Detail Activity": "Trial System & Evaluasi Dashboard", "Days": 5, "PIC": "ALL Dept", "Target": "Juni W-II"},
        {"No": 5, "Item Problem": "Penyelesaian CAPA 5S sering delay", "Activity": "Digitalisasi System Tracking CAPA", "Detail Activity": "Standarisasi Sistem Eskalasi Overdue CAPA", "Days": 3, "PIC": "OS & SH", "Target": "Juni W-III"}
    ]
    st.dataframe(pd.DataFrame(data_action_plan), use_container_width=True, hide_index=True)
    
    # --- TAB 2: DETAIL KRITERIA & LEVELING ---
    with tab_details:
        st.markdown('<div class="section-header">BY KRITERIA PENILAIAN & ANALISA PERBAIKAN (DETAIL PER LINE / DEPARTMENT)</div>', unsafe_allow_html=True)
        
        # ----------------- FITUR TAMBAHAN: PILIH AREA KHUSUS -----------------
        # Mengambil daftar semua nama area yang tersedia
        available_lines_map = {title: (title, key) for title, key in lines_info if key in selected_departments}
        available_line_names = list(available_lines_map.keys())

        if available_line_names:
            # Widget Multiselect untuk memilih area secara fleksibel
            selected_tab2_lines = st.multiselect(
                "🎯 Pilih Area / Line yang Ingin Ditampilkan:",
                options=available_line_names,
                default=available_line_names,  # Default menampilkan semua area
                key="filter_tab2_lines"
            )
            filtered_lines = [available_lines_map[name] for name in selected_tab2_lines]
        else:
            filtered_lines = []
        st.markdown("<br>", unsafe_allow_html=True)
        # ----------------------------------------------------------------------

        x_kriteria_num = [str(i) for i in range(1, len(kriteria_labels) + 1)]

        # Helper Function Render Box Analisa Per Line (SUDAH DIPERBAIKI KEY'NYA)
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
                
                list_items_html = ""
                for k_name, act_val, tgt_val in ng_items:
                    # Nilai default jika kriteria tidak ditemukan di dictionary
                    rec_data = RCA_RECOMMENDATION.get(k_name, {
                        "cause": "Belum ada standar visual dan pengawasan rutin di area kerja.",
                        "action_operator": "Lakukan pembersihan total, rapikan penataan, dan pasang label petunjuk.",
                        "action_gl": "Monitoring kebersihan dan kerapian area harian.",
                        "action_foreman": "Buat standar penataan visual dan evaluasi mingguan.",
                        "action_sh": "Review ketercapaian standar 5S area secara periodik.",
                        "action_dh": "Dukung kebutuhan fasilitas dan sosialisasi budaya 5S."
                    })
                    
                    # Menggunakan kunci baru: action_operator, action_gl, dll.
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
                
                html_ng = (
                    f"<div class='summary-box' style='background-color: #fff5f5; border-left: 4px solid #ff5252; margin-top: 15px;'>"
                    f"<strong style='color: #c0392b;'>🔍 ANALISA & REKOMENDASI PERBAIKAN AREA {title_area.upper()}:</strong><br>"
                    f"Ditemukan <b>{len(ng_items)} kriteria</b> yang belum mencapai target:"
                    f"<ol style='margin: 5px 0 5px 15px; padding: 0; font-size: 12px;'>{list_items_html}</ol>"
                    f"</div>"
                )
                return html_ng
            else:
                return (
                    f"<div class='summary-box' style='background-color: #e8f5e9; border-left: 4px solid #2e7d32; margin-top: 15px;'>"
                    f"<strong style='color: #2e7d32;'>🎉 PERFORMA AREA {title_area.upper()} SANGAT BAIK:</strong><br>"
                    f"Seluruh kriteria penilaian 5S telah memenuhi atau melebihi target yang ditetapkan. Pertahankan konsistensi penataan dan kebersihan area kerja!"
                    f"</div>"
                )

        # Loop Menampilkan Grafik, Tabel, dan Analisa secara Berurutan Ke Bawah (10 Baris)
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

                # Header Area
                st.markdown(f"#### 🏭 {title_line} &nbsp; <span class='badge-level {css_val}'>Level: {lvl_val} ({avg_val:.2f})</span>", unsafe_allow_html=True)
                
                # Grafik full-width
                st.plotly_chart(create_exact_chart(x_kriteria_num[:len(t_k)], t_k, a_k, f"Kriteria Penilaian - {key_line}", is_kriteria=True), use_container_width=True)
                
                # Tabel full-width
                st.markdown(render_exact_table(kriteria_labels[:len(t_k)], t_k, a_k, "Kriteria"), unsafe_allow_html=True)
                
                # Analisa Perbaikan
                st.markdown(render_line_analysis(title_line, key_line, t_k, a_k), unsafe_allow_html=True)
                
                # Garis pemisah antar area
                st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px dashed #cbd5e1;'>", unsafe_allow_html=True)
      
# --- TAB 3: PARETO & AI RECOMMENDATION ---
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
        
        # Logic Kesimpulan Pareto Kriteria
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

    # ----------------- PANEL EDIT REKOMENDASI (MANUAL INTERAKTIF) -----------------
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Menyiapkan data Area Terendah terlebih dahulu
    area_p_names = []
    area_p_scores = []
    filtered_selected_areas = [a for a in selected_departments if not any(kw in a.lower() for kw in EXCLUDE_KEYWORDS)]
    JUMLAH_KRITERIA = len(kriteria_labels) if len(kriteria_labels) > 0 else 11

    for area in filtered_selected_areas:
        c_a = next((c for c in all_columns if area.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
        if c_a:
            total_score_area = df[c_a].dropna().sum()
            avg_area_score = total_score_area / JUMLAH_KRITERIA
            area_p_names.append(area)
            area_p_scores.append(avg_area_score)

    df_area_rank = pd.DataFrame({'Area': area_p_names, 'Rata_Skor': area_p_scores})
    df_area_rank = df_area_rank.sort_values(by='Rata_Skor', ascending=True).reset_index(drop=True)
    top_3_lowest_areas = df_area_rank.head(3).values.tolist()

    # Form Editor / Expander untuk mengubah isi rekomendasi manual
    with st.expander("⚙️ **KLIK DI SINI UNTUK MENGUBAH TEKS REKOMENDASI TINDAKAN (MANUAL)**"):
        st.info("Anda bisa mengubah teks rekomendasi di bawah ini secara langsung. Teks pada kartu di bawah akan otomatis berubah.")
        
        col_ed1, col_ed2 = st.columns(2)
        
        custom_rekom_kriteria = {}
        custom_rekom_area = {}

        def get_default_krit_rekom(krit_name):
            k_lower = krit_name.lower()
            if any(w in k_lower for w in ['ringkas', 'seiri', 'pemilahan', 'sort']):
                return "Gelar Red Tag Campaign (labeli barang tidak terpakai), tetapkan area karantina barang bekas, dan buat aturan retensi dokumen/alat."
            elif any(w in k_lower for w in ['rapi', 'seiton', 'penataan', 'layout', 'papan']):
                return "Buat Border Line / Demarkasi Area, pasang label/papan nama alat, dan terapkan prinsip '1 Tempat 1 Barang'."
            elif any(w in k_lower for w in ['resik', 'seiso', 'pembersihan', 'kebersihan', 'sapu']):
                return "Jadwalkan Piket Kebersihan 5 Menit Harian sebelum/sesudah shift, sediakan alat kebersihan memadai, dan isolasi sumber debu/bocor."
            elif any(w in k_lower for w in ['rawat', 'seiketsu', 'standar', 'sop', 'label']):
                return "Standarkan visual management (SOP visual, checklist audit harian) dan lakukan audit berkala oleh pimpinan area."
            elif any(w in k_lower for w in ['rajin', 'shitsuke', 'kedisiplinan', 'budaya', 'sikap']):
                return "Lakukan Morning Briefing rutin terkait 5S, berikan penghargaan (Reward) area terbaik, dan tindak lanjuti temuan NG secara disiplin."
            else:
                return "Lakukan analisis akar masalah (Fishbone/5-Why) bersama tim area dan buat Rencana Tindak Lanjut (CAPA) dengan target date yang jelas."

        with col_ed1:
            st.markdown("##### 🛠️ Edit Rekomendasi Kriteria")
            for idx, item in enumerate(top_3_lowest):
                k_name = item[0]
                def_val = get_default_krit_rekom(k_name)
                custom_rekom_kriteria[k_name] = st.text_area(
                    f"Rekomendasi untuk Kriteria: {k_name}",
                    value=def_val,
                    key=f"input_krit_{idx}",
                    height=80
                )

        default_area_rekom = [
            "Lakukan Red Tag Campaign secara menyeluruh, sortir barang yang tidak terpakai, dan prioritaskan pembersihan area kerja (Seiri & Seiso).",
            "Buat Standardized Work / Layout Signage yang jelas untuk penataan item serta atur jadwal piket rutin harian (Seiton & Seiketsu).",
            "Tingkatkan keterlibatan supervisor area untuk melakukan Patroli 5S Harian serta evaluasi kepatuhan prosedur (Shitsuke)."
        ]

        with col_ed2:
            st.markdown("##### 💡 Edit Rekomendasi Area")
            for idx, item in enumerate(top_3_lowest_areas):
                a_name = item[0]
                def_val_a = default_area_rekom[idx] if idx < len(default_area_rekom) else default_area_rekom[0]
                custom_rekom_area[a_name] = st.text_area(
                    f"Rekomendasi untuk Area: {a_name}",
                    value=def_val_a,
                    key=f"input_area_{idx}",
                    height=80
                )

    # ----------------- TAMPILAN ANALISA 3 KRITERIA TERENDAH -----------------
    st.markdown('<div class="section-header">ANALISA 3 KRITERIA TERENDAH & REKOMENDASI PERBAIKAN</div>', unsafe_allow_html=True)

    if top_3_lowest:
        cols_krit_lowest = st.columns(len(top_3_lowest))

        for i, item_krit in enumerate(top_3_lowest):
            krit_name = item_krit[0]
            krit_score = item_krit[1]
            rekom_krit = custom_rekom_kriteria.get(krit_name, "")

            with cols_krit_lowest[i]:
                st.markdown(f"""
                    <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-top: 4px solid #e65100; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
                        <span style="background-color: #e65100; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                            KRITERIA RANK {i+1} TERENDAH
                        </span>
                        <h4 style="margin: 8px 0 4px 0; color: #004d73; font-size: 14px;">{krit_name}</h4>
                        <p style="margin: 0 0 8px 0; font-size: 13px;">Skor Rata-Rata: <b style="color: #e65100;">{krit_score:.2f}</b></p>
                        <hr style="margin: 6px 0; border: 0; border-top: 1px solid #eee;">
                        <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #444;">
                            <b>🛠️ Rekomendasi Tindakan:</b><br>{rekom_krit}
                        </p>
                    </div>
                """, unsafe_allow_html=True)

    # ----------------- TAMPILAN ANALISA 3 AREA TERENDAH -----------------
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-header">ANALISA 3 AREA DENGAN PERFORMA TERENDAH & REKOMENDASI PERBAIKAN</div>', unsafe_allow_html=True)

    if top_3_lowest_areas:
        cols_lowest = st.columns(len(top_3_lowest_areas))

        for i, item_area in enumerate(top_3_lowest_areas):
            area_name = item_area[0]
            area_score = item_area[1]
            rekom_area = custom_rekom_area.get(area_name, "")

            with cols_lowest[i]:
                st.markdown(f"""
                    <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-top: 4px solid #c62828; border-radius: 6px; padding: 12px; margin-bottom: 10px;">
                        <span style="background-color: #c62828; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                            AREA RANK {i+1} TERENDAH
                        </span>
                        <h4 style="margin: 8px 0 4px 0; color: #004d73; font-size: 14px;">{area_name}</h4>
                        <p style="margin: 0 0 8px 0; font-size: 13px;">Skor Rata-Rata: <b style="color: #c62828;">{area_score:.2f}</b></p>
                        <hr style="margin: 6px 0; border: 0; border-top: 1px solid #eee;">
                        <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #444;">
                            <b>💡 Rekomendasi:</b><br>{rekom_area}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Data area tidak mencukupi untuk menampilkan analisis area terendah.")

  # =========================================================================
# --- TAB 4: CAPA TRACKING & LOG INPUT TEMUAN NG ---
# =========================================================================
with tab_action:
    st.markdown('<div class="section-header">TINDAKAN PERBAIKAN & CAPA TRACKING</div>', unsafe_allow_html=True)
    
    # 1. TAMPILAN REKOMENDASI RCA GLOBAL (ANALISA 5W1H)
    st.subheader("💡 1. Rekomendasi Solusi & Action Plan Berdasarkan RCA 5S")
    
    # Pilih Kriteria untuk Melihat Rekomendasi Standard
    selected_rca_kriteria = st.selectbox(
        "🎯 Pilih Kriteria Penilaian untuk Melihat Panduan Action Plan:",
        options=list(RCA_RECOMMENDATION.keys()) if 'RCA_RECOMMENDATION' in globals() else ["1S - Seiri (Ringkas)", "2S - Seiton (Rapi)", "3S - Seiso (Resik)", "4S - Seiketsu (Rawat)", "5S - Shitsuke (Rajin)"],
        key="select_rca_kriteria_tab4"
    )
    
    rec_info = RCA_RECOMMENDATION.get(selected_rca_kriteria, {}) if 'RCA_RECOMMENDATION' in globals() else {}
    
    st.markdown(f"""
        <div class="summary-box" style="background-color: #f9f9f9; border-left: 5px solid #2980b9; padding: 15px; border-radius: 5px; margin-bottom: 25px;">
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

    # 2. FORM INPUT TEMUAN PATROL 5S NG
    st.subheader("📝 2. Log Input Temuan Patrol NG & Penugasan Action Plan")
    
    with st.form(key="form_input_patrol_ng", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            input_area = st.selectbox("Area / Department Temuan:", options=[line[0] for line in lines_info] if 'lines_info' in globals() else ["Area Production", "Area Warehouse", "Area Office"])
            input_kriteria = st.selectbox("Kriteria 5S Bermasalah:", options=kriteria_labels if 'kriteria_labels' in globals() else ["1S - Seiri (Ringkas)", "2S - Seiton (Rapi)", "3S - Seiso (Resik)", "4S - Seiketsu (Rawat)", "5S - Shitsuke (Rajin)"])
            input_detail_problem = st.text_area("Detail Temuan Masalah (Kondisi Lapangan):", placeholder="Misal: Garis kuning pembatas terkelupas di dekat mesin A")
            input_pic = st.text_input("PIC / Penanggung Jawab Perbaikan:", placeholder="Nama Operator / Group Leader")
        
        with col_f2:
            input_target_date = st.date_input("Target Selesai Perbaikan:")
            input_priority = st.selectbox("Tingkat Prioritas Penanganan:", options=["High (Urgent)", "Medium (Standard)", "Low (Rutin)"])
            input_tier = st.selectbox("Penugasan Eksekusi Utama:", options=["Operator", "Group Leader", "Foreman", "Section Head", "Department Head"])
            input_status = st.selectbox("Status Penanganan Saat Ini:", options=["Open (Belum Ditindak)", "On Progress (Proses Pengerjaan)", "Closed (Selesai)"])
            
            # WIDGET UPLOAD FOTO TEMUAN NG
            uploaded_file = st.file_uploader("📷 Upload Foto Temuan NG (JPG/PNG):", type=["jpg", "jpeg", "png"])

        btn_submit_capa = st.form_submit_button("💾 Simpan Log Temuan & Action Plan")

    # Inisialisasi Data Session State jika Belum Ada
    if "capa_log_data" not in st.session_state:
        if 'load_capa_from_gsheets' in globals():
            st.session_state["capa_log_data"] = load_capa_from_gsheets()
        else:
            st.session_state["capa_log_data"] = []

    # Proses Simpan Data Form Baru
    if btn_submit_capa:
        if input_detail_problem.strip() == "":
            st.warning("⚠️ Mohon isi Detail Temuan Masalah sebelum menyimpan.")
        else:
            image_path = "-"
            
            # Proses Penyimpanan File Foto Temuan ke Folder Lokal
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
                "Foto Temuan": image_path  # Menyimpan Path File Gambar
            }
            st.session_state["capa_log_data"].append(new_entry)
            
            # SIMPAN OTOMATIS KE GOOGLE SHEETS
            try:
                if 'save_capa_to_gsheets' in globals():
                    save_capa_to_gsheets(st.session_state["capa_log_data"])
                    st.success(f"✅ Data temuan NG & Foto di area '{input_area}' berhasil disimpan!")
                else:
                    st.success(f"✅ Data temuan NG & Foto di area '{input_area}' berhasil disimpan secara lokal!")
            except Exception as e:
                st.error(f"Gagal menyimpan ke Google Sheets: {e}")

            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. TABEL AUDIT TRAIL / LOG CAPA TRACKING
    st.subheader("📋 3. Daftar Monitoring Action Plan (CAPA Log)")
    
    if st.session_state["capa_log_data"]:
        df_capa_log = pd.DataFrame(st.session_state["capa_log_data"])
        
        # --- KONVERSI TIPE DATA TANGGAL ---
        if "Target Selesai" in df_capa_log.columns:
            df_capa_log["Target Selesai"] = pd.to_datetime(df_capa_log["Target Selesai"], errors="coerce").dt.date
        
        # Filter Sederhana Status
        status_filter = st.multiselect(
            "Filter Status CAPA:",
            options=["Open (Belum Ditindak)", "On Progress (Proses Pengerjaan)", "Closed (Selesai)"],
            default=["Open (Belum Ditindak)", "On Progress (Proses Pengerjaan)", "Closed (Selesai)"]
        )
        
        df_filtered_capa = df_capa_log[df_capa_log["Status"].isin(status_filter)]

        st.caption("💡 **Tips:** Kamu bisa mengubah status, PIC, target tanggal, atau kolom lainnya secara langsung pada tabel di bawah ini.")

        # Data Editor Interaktif
        edited_df = st.data_editor(
            df_filtered_capa,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status Penanganan",
                    help="Ubah status progres penanganan CAPA",
                    options=[
                        "Open (Belum Ditindak)",
                        "On Progress (Proses Pengerjaan)",
                        "Closed (Selesai)"
                    ],
                    required=True,
                ),
                "Target Selesai": st.column_config.DateColumn(
                    "Target Selesai",
                    format="YYYY-MM-DD"
                ),
                "Prioritas": st.column_config.SelectboxColumn(
                    "Prioritas",
                    options=["High (Urgent)", "Medium (Standard)", "Low (Rutin)"]
                ),
                "Foto Temuan": st.column_config.TextColumn(
                    "Path Foto", 
                    disabled=True
                )
            },
            disabled=["Tanggal Input", "Area", "Kriteria 5S", "Detail Masalah"],
            use_container_width=True,
            num_rows="dynamic",
            key="capa_editor"
        )

        # Sinkronisasi Perubahan Kembali ke Session State & Google Sheets
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
            
            # SIMPAN OTOMATIS KE GOOGLE SHEETS
            try:
                if 'save_capa_to_gsheets' in globals():
                    save_capa_to_gsheets(st.session_state["capa_log_data"])
                    st.success("✅ Perubahan status CAPA Log berhasil diperbarui!")
                else:
                    st.success("✅ Perubahan status CAPA Log berhasil diperbarui secara lokal!")
            except Exception as e:
                st.error(f"Gagal memperbarui ke Google Sheets: {e}")
                
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        
# 4. GALERI FOTO TEMUAN NG
        st.subheader("🖼️ 4. Galeri Foto Temuan NG Lapangan")
        
        has_image = False
        cols_img = st.columns(3) # Grid tampilan 3 kolom
        col_idx = 0

        for item in st.session_state["capa_log_data"]:
            img_path = item.get("Foto Temuan", "-")
            
            # --- PERBAIKAN VALIDASI TIPE DATA GAMBAR ---
            # Memastikan img_path berupa string valid dan bukan NaN/None/kosong
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

        # Tombol Unduh Laporan CAPA
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
    grand_avg_score = (sum(avg_scores) / len(avg_scores)) if 'avg_scores' in globals() and avg_scores else 0.0
    global_level = get_level_5s(grand_avg_score)[0] if 'get_level_5s' in globals() else "N/A"
    
    top_lowest_kriteria = df_rank_p.head(2)['Kriteria'].tolist() if 'df_rank_p' in locals() else []
    top_lowest_str = " & ".join([f"<b>{k}</b>" for k in top_lowest_kriteria]) if top_lowest_kriteria else "tertentu"

    if 'ng_areas' in globals() and ng_areas:
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

    if 'df' in globals():
        with st.expander("📋 Lihat Raw Data Google Sheets"):
            st.dataframe(df, use_container_width=True)
        st.dataframe(df, use_container_width=True)
