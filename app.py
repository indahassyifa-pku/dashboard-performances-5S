import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import datetime

# ----------------- KONFIGURASI HALAMAN -----------------
st.set_page_config(
    page_title="Dashboard Patrol 5S",
    page_icon="🧹",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    
    .dashboard-title {
        color: #004d73;
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .dashboard-subtitle {
        color: #555555;
        font-size: 14px;
        margin-bottom: 20px;
    }
    
    .section-header {
        color: #004d73;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #004d73;
        padding-bottom: 5px;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    .table-5s {
        width: 100%;
        border-collapse: collapse;
        margin-top: 12px;
        margin-bottom: 10px;
        font-size: 12px;
        text-align: center;
        font-family: Arial, sans-serif;
    }
    .table-5s th {
        background-color: #004d73;
        color: white;
        padding: 8px 4px;
        border: 1px solid #003350;
        font-weight: bold;
    }
    .table-5s td {
        border: 1px solid #cccccc;
        padding: 6px 4px;
        color: #333333;
    }
    .bg-label { background-color: #f0f4f8; font-weight: bold; color: #111; text-align: left; padding-left: 10px !important; }
    
    .judge-ok { background-color: #a8f087; color: #1e5a00; font-weight: bold; }
    .judge-ng { background-color: #ff5252; color: #ffffff; font-weight: bold; }

    /* Box Kesimpulan Per-Grafik */
    .summary-box {
        background-color: #eef7fc;
        border-left: 4px solid #004d73;
        padding: 12px 15px;
        border-radius: 4px;
        margin-top: 10px;
        font-size: 13px;
        color: #1a3038;
        line-height: 1.5;
    }

    /* Badge Level 5S */
    .badge-level {
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
        font-size: 11px;
        display: inline-block;
        color: white;
    }
    .lvl-black { background-color: #2b2b2b; }
    .lvl-bronze { background-color: #cd7f32; }
    .lvl-silver { background-color: #8a9ba8; }
    .lvl-gold { background-color: #d4af37; }

    /* Card Box Analisa */
    .analysis-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-top: 4px solid #d32f2f;
        border-radius: 6px;
        padding: 15px;
        margin-top: 10px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- LINK GOOGLE SHEETS -----------------
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

# Initialize Session State untuk menyimpan data Action Plan Temuan
if "action_plans" not in st.session_state:
    st.session_state.action_plans = pd.DataFrame(columns=[
        "ID", "Area / Line", "Kriteria", "Temuan NG", "Akar Masalah (Root Cause)", 
        "Tindakan Perbaikan (Action Plan)", "PIC", "Target Selesai", "Status"
    ])

# State untuk melacak status klik tombol "Tindak Lanjut" tiap area
if "show_analysis_state" not in st.session_state:
    st.session_state.show_analysis_state = {}

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

    tab_summary, tab_details, tab_pareto, tab_action = st.tabs([
        "📊 Executive Summary (By Month & By Area)", 
        "🏭 Detail 11 Kriteria Penilaian (By Line)", 
        "📈 Pareto Analisis Kriteria Rendah",
        "🛠️ CAPA Tracking"
    ])

    if 'Kriteria' in all_columns and not df['Kriteria'].dropna().empty:
        kriteria_labels = df['Kriteria'].dropna().tolist()
    else:
        kriteria_labels = DEFAULT_KRITERIA_LIST

    ng_areas = []
    ok_areas = []

    # --- TAB 1: SUMMARY ---
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

        col_m, col_a = st.columns(2)
        
        with col_m:
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

        with col_a:
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

        # FUNGSI DENGAN CONTROL FLOW KETAT (ANALISA HANYA DIRENDER SAAT DIKLIK)
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
                
                btn_key = f"btn_tl_{key_area}"
                
                # Inisialisasi status tombol di session_state
                if btn_key not in st.session_state.show_analysis_state:
                    st.session_state.show_analysis_state[btn_key] = False

                is_active = st.session_state.show_analysis_state[btn_key]
                button_label = f"📋 Sembunyikan Analisa ({len(ng_items)} Temuan NG)" if is_active else f"🔍 Tindak Lanjut Analisa & Rekomendasi ({len(ng_items)} Temuan NG)"
                
                # 1. Tampilkan Tombol Terlebih Dahulu
                if st.button(button_label, key=btn_key):
                    st.session_state.show_analysis_state[btn_key] = not is_active
                    st.rerun()

                # 2. SELURUH RENDERING HTML DITARUH DI DALAM BLOK IF INI
                if st.session_state.show_analysis_state[btn_key]:
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
                            f"❌ <b>Akar Masalah:</b> {rec_data['cause']}<br>"
                            f"🛠️ <b>Rekomendasi Perbaikan Bertingkat:</b>"
                            f"<ul style='margin-top: 4px; margin-bottom: 4px; padding-left: 20px; font-size: 12px;'>"
                            f"<li><b>Operator:</b> {rec_data['action_operator']}</li>"
                            f"<li><b>Group Leader (GL):</b> {rec_data['action_gl']}</li>"
                            f"<li><b>Foreman:</b> {rec_data['action_foreman']}</li>"
                            f"<li><b>Section Head (SH):</b> {rec_data['action_sh']}</li>"
                            f"<li><b>Dept Head (DH):</b> {rec_data['action_dh']}</li>"
                            f"</ul>"
                            f"</li>"
                        )
                    
                    html_card = f"""
                    <div class="analysis-card">
                        <h5 style="color: #b71c1c; margin-top: 0; font-weight: 700;">🔍 ANALISA & REKOMENDASI PERBAIKAN AREA {title_area.upper()}:</h5>
                        <p style="font-size: 13px; margin-bottom: 8px;">Ditemukan <b>{len(ng_items)} kriteria</b> yang belum mencapai target:</p>
                        <ol style="padding-left: 20px; font-size: 13px; color: #333;">
                            {list_items_html}
                        </ol>
                    </div>
                    """
                    st.markdown(html_card, unsafe_allow_html=True)
            else:
                st.success(f"🎉 Luar Biasa! Area {title_area} memenuhi seluruh kriteria target 5S (100% OK).")

        # Rendering Grid 2 Kolom untuk Area
        for i in range(0, len(filtered_lines), 2):
            cols = st.columns(2)
            
            # Area Pertama
            title_1, key_1 = filtered_lines[i]
            c_t1 = next((c for c in all_columns if key_1.lower() in c.lower() and 'target' in c.lower()), None)
            c_a1 = next((c for c in all_columns if key_1.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            
            t_list1 = df[c_t1].tolist() if c_t1 else []
            a_list1 = df[c_a1].tolist() if c_a1 else []
            
            with cols[0]:
                if t_list1 and a_list1:
                    avg_a1 = sum([float(v) for v in a_list1 if str(v).replace('.','',1).isdigit()]) / len(a_list1) if a_list1 else 0
                    lvl_name1, lvl_css1 = get_level_5s(avg_a1)
                    
                    st.markdown(f"### {title_1} <span class='badge-level {lvl_css1}'>Level {lvl_name1} ({avg_a1:.2f})</span>", unsafe_allow_html=True)
                    st.plotly_chart(create_exact_chart(x_kriteria_num, t_list1, a_list1, f"Detail 11 Kriteria - {title_1}", is_kriteria=True), use_container_width=True)
                    st.markdown(render_exact_table(x_kriteria_num, t_list1, a_list1, "Kriteria"), unsafe_allow_html=True)
                    render_line_analysis(title_1, key_1, t_list1, a_list1)
                else:
                    st.warning(f"Data tidak lengkap untuk {title_1}")

            # Area Kedua (jika ada)
            if i + 1 < len(filtered_lines):
                title_2, key_2 = filtered_lines[i+1]
                c_t2 = next((c for c in all_columns if key_2.lower() in c.lower() and 'target' in c.lower()), None)
                c_a2 = next((c for c in all_columns if key_2.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
                
                t_list2 = df[c_t2].tolist() if c_t2 else []
                a_list2 = df[c_a2].tolist() if c_a2 else []
                
                with cols[1]:
                    if t_list2 and a_list2:
                        avg_a2 = sum([float(v) for v in a_list2 if str(v).replace('.','',1).isdigit()]) / len(a_list2) if a_list2 else 0
                        lvl_name2, lvl_css2 = get_level_5s(avg_a2)
                        
                        st.markdown(f"### {title_2} <span class='badge-level {lvl_css2}'>Level {lvl_name2} ({avg_a2:.2f})</span>", unsafe_allow_html=True)
                        st.plotly_chart(create_exact_chart(x_kriteria_num, t_list2, a_list2, f"Detail 11 Kriteria - {title_2}", is_kriteria=True), use_container_width=True)
                        st.markdown(render_exact_table(x_kriteria_num, t_list2, a_list2, "Kriteria"), unsafe_allow_html=True)
                        render_line_analysis(title_2, key_2, t_list2, a_list2)
                    else:
                        st.warning(f"Data tidak lengkap untuk {title_2}")

    # --- TAB 3: DIAGRAM PARETO ---
    with tab_pareto:
        st.markdown('<div class="section-header">ANALISIS DIAGRAM PARETO (KRITERIA TERENDAH DI SELURUH AREA)</div>', unsafe_allow_html=True)
        
        kriteria_scores = []
        for idx, k_name in enumerate(kriteria_labels):
            scores_for_k = []
            for title, key in lines_info:
                if key in selected_departments:
                    c_a = next((c for c in all_columns if key.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
                    if c_a and idx < len(df[c_a]):
                        val = df[c_a].iloc[idx]
                        try:
                            scores_for_k.append(float(val))
                        except (ValueError, TypeError):
                            pass
            avg_k = sum(scores_for_k) / len(scores_for_k) if scores_for_k else 0
            kriteria_scores.append(avg_k)

        if kriteria_scores:
            fig_pareto = create_pareto_chart(kriteria_labels, kriteria_scores)
            st.plotly_chart(fig_pareto, use_container_width=True)

            st.markdown("""
                <div class="summary-box">
                    <strong>💡 Petunjuk Analisa Pareto 80/20:</strong><br>
                    Grafik di atas diurutkan dari kriteria dengan pencapaian nilai <b>paling rendah (paling kritis)</b> di sebelah kiri. 
                    Fokuskan program perbaikan, pelatihan, dan alokasi sumber daya pada 20% kriteria teratas di sebelah kiri untuk memberikan dampak perbaikan 5S sebesar 80% secara efektif.
                </div>
            """, unsafe_allow_html=True)

    # --- TAB 4: CAPA TRACKING ---
    with tab_action:
        st.markdown('<div class="section-header">CAPA TRACKING (CORRECTIVE & PREVENTIVE ACTION)</div>', unsafe_allow_html=True)
        
        st.subheader("➕ Input Form Perbaikan Temuan 5S")
        with st.form("form_capa", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                capa_area = st.selectbox("Area / Line:", options=ALL_AREAS)
                capa_kriteria = st.selectbox("Kriteria Penilaian:", options=kriteria_labels)
                capa_temuan = st.text_area("Deskripsi Temuan NG:", placeholder="Contoh: Oli menumpuk di lantai tanpa penampung spill tray.")
                capa_rca = st.text_area("Akar Masalah (Root Cause):", placeholder="Contoh: Wadah penampung bocor dan belum ada jadwal maintenance wadah.")
            
            with col_f2:
                capa_action = st.text_area("Tindakan Perbaikan (Action Plan):", placeholder="Contoh: Mengganti wadah B3 dan memasang spill tray baru.")
                capa_pic = st.text_input("Person in Charge (PIC):", placeholder="Nama / Jabatan PIC")
                capa_target = st.date_input("Target Selesai:", value=datetime.date.today() + datetime.timedelta(days=7))
                capa_status = st.selectbox("Status:", options=["Open", "In Progress", "Closed"])

            submit_capa = st.form_submit_button("💾 Simpan Action Plan")
            
            if submit_capa:
                new_id = len(st.session_state.action_plans) + 1
                new_data = pd.DataFrame([{
                    "ID": f"CAPA-{new_id:03d}",
                    "Area / Line": capa_area,
                    "Kriteria": capa_kriteria,
                    "Temuan NG": capa_temuan,
                    "Akar Masalah (Root Cause)": capa_rca,
                    "Tindakan Perbaikan (Action Plan)": capa_action,
                    "PIC": capa_pic,
                    "Target Selesai": capa_target.strftime("%Y-%m-%d"),
                    "Status": capa_status
                }])
                st.session_state.action_plans = pd.concat([st.session_state.action_plans, new_data], ignore_index=True)
                st.success("Tindakan Perbaikan berhasil ditambahkan!")

        st.markdown("---")
        st.subheader("📋 Daftar Monitoring Corrective Action Plan")
        
        if not st.session_state.action_plans.empty:
            st.dataframe(st.session_state.action_plans, use_container_width=True)
            
            # Export CAPA
            capa_csv = st.session_state.action_plans.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export CAPA to CSV",
                data=capa_csv,
                file_name="CAPA_Tracking_5S.csv",
                mime="text/csv"
            )
        else:
            st.info("Belum ada data temuan/action plan yang diinputkan.")
