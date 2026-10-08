import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ----------------- KONFIGURASI HALAMAN -----------------
st.set_page_config(
    page_title="Dashboard Patrol 5S",
    page_icon="🧹",
    layout="wide"
)

# Custom Styling
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

# ----------------- LINK GOOGLE SHEETS -----------------
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

# ----------------- CONSTANTS -----------------
DEFAULT_KRITERIA_LIST = [
    "Sekitar area kerja", 
    "Penyimpanan Cairan B3 :", 
    "Penyimpanan RM/WIP/FG",
    "Penyimpanan Consumable, Spare Part", 
    "Area Kerja di Lapangan", 
    "Mesin, Peralatan pendukung Produksi, Peralatan Kerja",
    "Penyimpanan Master Work", 
    "Informasi Terdokumentasi", 
    "Tempat istirahat",
    "Meja Kerja Leader", 
    "Penempatan Dokumen"
]

ALL_MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
TARGET_AREAS = ["PVC", "SMS", "STEX", "BTEX", "DFAS", "PPEX", "WH", "SHP", "QA/QC", "MTC"]

# REKOMENDASI RCA LENGKAP UNTUK ALL 11 KRITERIA
RCA_RECOMMENDATION = {
    "Sekitar area kerja": {
        "cause": "(1) Garis pembatas area kotor/pudar. (2) Terdapat ceceran debu/sampah.",
        "action_operator": "Melakukan pembersihan berkala sebelum & sesudah shift.",
        "action_gl": "Patroli kebersihan area kerja harian.",
        "action_foreman": "Pengajuan perbaikan garis demarkasi yang pudar."
    },
    "Penyimpanan Cairan B3 :": {
        "cause": "(1) Sekunder containment berdebu/ada genangan. (2) Simbol B3 tidak terlihat.",
        "action_operator": "Pastikan cairan B3 tertutup rapat dan ditempatkan sesuai label.",
        "action_gl": "Inspeksi mingguan ketersediaan MSDS & kondisi tempat B3.",
        "action_foreman": "Audit ketaatan regulasi penanganan B3."
    },
    "Penyimpanan RM/WIP/FG": {
        "cause": "(1) Penataan material tidak rapi. (2) Melebihi kapasitas garis batas tumpukan.",
        "action_operator": "Menata material sesuai tempat & garis batas tumpukan.",
        "action_gl": "Pemeriksaan keteraturan tumpukan stok WIP/FG.",
        "action_foreman": "Review penataan layout area penyimpanan."
    },
    "Penyimpanan Consumable, Spare Part": {
        "cause": "(1) Rak sparepart berantakan. (2) Tidak ada kartu kontrol/label item.",
        "action_operator": "Mengembalikan sparepart ke rak asal setelah digunakan.",
        "action_gl": "Verifikasi kerapian rak consumable tiap akhir minggu.",
        "action_foreman": "Standardisasi sistem penataan sparepart."
    },
    "Area Kerja di Lapangan": {
        "cause": "(1) Terdapat barang yang tidak terpakai di area kerja. (2) Penataan janggal.",
        "action_operator": "Pilah barang yang tidak terpakai dan sisihkan ke tempat khusus.",
        "action_gl": "Monitoring pelaksanaan Red Tag bulanan.",
        "action_foreman": "Persetujuan pembuangan/peminjaman barang tak terpakai."
    },
    "Mesin, Peralatan pendukung Produksi, Peralatan Kerja": {
        "cause": "(1) Mesin/peralatan beroli & berdebu. (2) Tool tidak diletakkan di shadow board.",
        "action_operator": "Bersihkan mesin & kembalikan tool ke shadow board.",
        "action_gl": "Cek kesesuaian checklist kebersihan mesin.",
        "action_foreman": "Penjadwalan perawatan berkala (Preventive Maintenance)."
    },
    "Penyimpanan Master Work": {
        "cause": "(1) Jig/Master work berdebu. (2) Posisi simpan tidak pada nomor lokasinya.",
        "action_operator": "Lap master work & letakkan tepat di nomor raknya.",
        "action_gl": "Pengecekan kelengkapan & lokasi master work.",
        "action_foreman": "Penyediaan fasilitas rak master work yang lebih layak."
    },
    "Informasi Terdokumentasi": {
        "cause": "(1) Papan informasi kusam. (2) Dokumen yang tertempel sudah expired.",
        "action_operator": "Merawat papan informasi dan melepas dokumen lama.",
        "action_gl": "Update dokumen & instruksi kerja di papan informasi.",
        "action_foreman": "Audit ketersediaan dokumen instruksi kerja terbaru."
    },
    "Tempat istirahat": {
        "cause": "(1) Sisa makanan/minuman tidak dibuang. (2) Kursi/meja tidak tertata.",
        "action_operator": "Jaga kebersihan tempat istirahat bersama.",
        "action_gl": "Pengecekan tempat istirahat seusai jam istirahat.",
        "action_foreman": "Fasilitasi sarana tempat sampah yang memadai."
    },
    "Meja Kerja Leader": {
        "cause": "(1) Meja tumpukan kertas tidak teratur. (2) Alat tulis berhamburan.",
        "action_operator": "Rapikan dokumen dan alat tulis di meja.",
        "action_gl": "Terapkan filing system pada meja kerja.",
        "action_foreman": "Evaluasi kerapian area kerja Group Leader."
    },
    "Penempatan Dokumen": {
        "cause": "(1) Bider/folder dokumen tidak berlabel. (2) Posisi rak dokumen tidak urut.",
        "action_operator": "Posisikan binder sesuai urutan nomor/kategori.",
        "action_gl": "Pastikan label identitas binder terpasang jelas.",
        "action_foreman": "Standardisasi sistem kearsipan dokumen."
    }
}

# ----------------- 1. LOAD DATA UTAMA -----------------
df = load_data(SHEET_URL)

# ----------------- 2. LOGIKA PEMISAHAN DATA (GAMBAR 1 VS GAMBAR 2) -----------------
if not df.empty:
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
    selected_departments = st.sidebar.multiselect("🏢 Filter Department / Line:", options=TARGET_AREAS, default=TARGET_AREAS)

    # Header
    col_title, col_export = st.columns([3, 1])
    with col_title:
        st.markdown('<div class="dashboard-title">🧹 DASHBOARD PERFORMANCE PATROL 5S</div>', unsafe_allow_html=True)
        st.markdown('<div class="dashboard-subtitle">Monitoring Real-time Pencapaian Patrol 5S Terintegrasi Data Google Sheets</div>', unsafe_allow_html=True)

    st.markdown("---")

    # UNIFIED TABS
    tab_summary, tab_details, tab_monthly_area, tab_pareto = st.tabs([
        "📊 Executive Summary", 
        "🏭 Detail 11 Kriteria Penilaian (Gambar 1)", 
        "📅 Tren Bulanan Per Area (Gambar 2)",
        "📈 Pareto Analisis"
    ])

    kriteria_labels = DEFAULT_KRITERIA_LIST

    # =========================================================================
    # --- TAB 1: SUMMARY ---
    # =========================================================================
    with tab_summary:
        st.markdown('<div class="section-header">PENCAPAIAN 5S PER AREA (GAMBAR 1 SUMMARY)</div>', unsafe_allow_html=True)
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

        if selected_departments:
            st.plotly_chart(create_exact_chart(selected_departments, area_targets, area_actuals, "PENCAPAIAN PER AREA / DEPARTMENT"), use_container_width=True)
            st.markdown(render_exact_table(selected_departments, area_targets, area_actuals, "Area"), unsafe_allow_html=True)

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

        # HELPER ANALISIS TEMUAN NG (TAB 2)
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
                        # Cari rekomendasi RCA berdasarkan pencocokan nama
                        rec_data = next((v for k, v in RCA_RECOMMENDATION.items() if k.lower() in k_name.lower() or k_name.lower() in k.lower()), {
                            "cause": "Belum ada catatan detail.",
                            "action_operator": "Pembersihan & penataan ulang.",
                            "action_gl": "Monitoring area harian.",
                            "action_foreman": "Evaluasi & audit berkala."
                        })
                        
                        list_items_html += (
                            f"<li style='margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #ffcdd2;'>"
                            f"<b>{k_name}</b> (Nilai: <span style='color:#d32f2f; font-weight:bold;'>{act_val:.1f}</span> / Target: {tgt_val:.1f})<br>"
                            f"&bull; <i>Penyebab Utama:</i> {rec_data.get('cause', '-')}<br>"
                            f"<div style='margin-top: 4px; padding-left: 8px; border-left: 2px solid #e57373;'>"
                            f"&bull; <b>Tindakan Operator:</b> <span style='color:#1b5e20;'>{rec_data.get('action_operator', '-')}</span><br>"
                            f"&bull; <b>Tindakan Group Leader:</b> <span style='color:#0d47a1;'>{rec_data.get('action_gl', '-')}</span><br>"
                            f"&bull; <b>Tindakan Foreman:</b> <span style='color:#e65100;'>{rec_data.get('action_foreman', '-')}</span><br>"
                            f"</div>"
                            f"</li>"
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
                
                # TAMPILKAN POP-OVER ANALISIS
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
    # --- TAB 4: PARETO ---
    # =========================================================================
    with tab_pareto:
        st.markdown('<div class="section-header">DIAGRAM PARETO EVALUASI KRITERIA</div>', unsafe_allow_html=True)
        kriteria_scores = {k: [] for k in kriteria_labels}
        for area_code in TARGET_AREAS:
            c_act_p = next((c for c in df_kriteria.columns if area_code.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            if c_act_p:
                vals = df_kriteria[c_act_p].dropna().tolist()
                for idx_k, val_k in enumerate(vals):
                    if idx_k < len(kriteria_labels) and str(val_k).replace('.', '', 1).isdigit():
                        kriteria_scores[kriteria_labels[idx_k]].append(float(val_k))

        avg_scores = [(sum(kriteria_scores[k]) / len(kriteria_scores[k])) if kriteria_scores[k] else 0.0 for k in kriteria_labels]
        st.plotly_chart(create_pareto_chart(kriteria_labels, avg_scores), use_container_width=True)
else:
    st.error("Data Google Sheets kosong.")
