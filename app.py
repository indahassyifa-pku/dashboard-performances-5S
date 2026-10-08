import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import datetime
from groq import Groq
from streamlit_gsheets import GSheetsConnection
import os

# ----------------- KONFIGURASI HALAMAN -----------------
st.set_page_config(
    page_title="Dashboard Patrol 5S",
    page_icon="🧹",
    layout="wide"
)

# Custom Styling Adaptif
st.markdown("""
    <style>
    .dashboard-title { color: var(--primary-color, #1370a6); font-size: 28px; font-weight: 800; margin-bottom: 5px; }
    .dashboard-subtitle { color: var(--text-color); opacity: 0.7; font-size: 14px; margin-bottom: 20px; }
    .section-header {
        color: var(--primary-color, #1370a6); font-size: 18px; font-weight: 700; letter-spacing: 0.5px;
        border-bottom: 2px solid var(--primary-color, #1370a6); padding-bottom: 5px; margin-top: 20px; margin-bottom: 15px;
    }
    .table-5s {
        width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 15px; font-size: 12px;
        text-align: center; background-color: var(--secondary-background-color, rgba(255, 255, 255, 0.05));
        border-radius: 8px; overflow: hidden;
    }
    .table-5s th { background-color: var(--primary-color, #1370a6); color: #ffffff !important; padding: 10px 6px; font-weight: 600; border: 1px solid rgba(128, 128, 128, 0.2); }
    .table-5s td { border: 1px solid rgba(128, 128, 128, 0.2); padding: 8px 6px; color: var(--text-color); }
    .bg-label { background-color: rgba(128, 128, 128, 0.1); font-weight: bold; color: var(--text-color); text-align: left; padding-left: 10px !important; }
    .judge-ok { background-color: rgba(46, 125, 50, 0.2); color: #2e7d32; font-weight: bold; }
    .judge-ng { background-color: rgba(198, 40, 40, 0.2); color: #c62828; font-weight: bold; }
    .summary-box {
        background-color: var(--secondary-background-color, rgba(255, 255, 255, 0.05));
        border-left: 4px solid var(--primary-color, #1370a6); border-radius: 6px; padding: 14px 18px;
        margin-top: 12px; font-size: 13px; color: var(--text-color); line-height: 1.6; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .summary-box-global {
        background-color: rgba(46, 125, 50, 0.1); border-left: 5px solid #2e7d32; padding: 15px 20px;
        border-radius: 8px; margin-top: 25px; font-size: 14px; color: var(--text-color); line-height: 1.6;
    }
    .badge-level { padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 11px; display: inline-block; color: white !important; }
    .lvl-black { background-color: #374151; }
    .lvl-bronze { background-color: #d97706; }
    .lvl-silver { background-color: #6b7280; }
    .lvl-gold { background-color: #eab308; }
    .analysis-card {
        background-color: var(--secondary-background-color, #ffffff); border: 1px solid rgba(128, 128, 128, 0.2);
        border-top: 4px solid #d32f2f; border-radius: 6px; padding: 15px; margin-top: 10px; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- LINK GOOGLE SHEETS -----------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQU_jpdzrymx_0mJKGVDopip0DPhnmDLIbsTHgVnqgaJZZayJUp-UPF1MF6H6soCA/pub?output=csv"

@st.cache_data(ttl=10)
def load_data(url):
    try:
        df_loaded = pd.read_csv(url)
        df_loaded.columns = df_loaded.columns.astype(str).str.strip()
        return df_loaded
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
        return pd.DataFrame()

df = load_data(SHEET_URL)

# ----------------- STORAGE LOKAL CSV -----------------
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

DEFAULT_KRITERIA_LIST = [
    "Sekitar area kerja", "Penyimpanan Cairan B3", "Penyimpanan RM/WIP/FG", "Penyimpanan Consumable",
    "Area Kerja di Lapangan", "Peralatan Kerja", "Penyimpanan Master Work", "Informasi Terdokumentasi",
    "Tempat Istirahat", "Meja Kerja Leader", "Penempatan Dokumen"
]

RCA_RECOMMENDATION = {
    "Sekitar area kerja": {
        "cause": "(1) Garis kuning pembatas rusak. (2) Lantai kotor. (3) Trolley lewat sembarangan.",
        "action_operator": "(1) Dilarang lewat jalur lain. (2) Rapikan trolley.",
        "action_gl": "Patroli harian jalur hijau.", "action_foreman": "Buat Work Order perbaikan.",
        "action_sh": "Evaluasi alur Material Handling.", "action_dh": "Disetujui anggaran pemeliharaan."
    }
}

def get_level_5s(avg_score):
    if avg_score >= 5.0: return "Gold", "lvl-gold"
    elif avg_score >= 4.0: return "Silver", "lvl-silver"
    elif avg_score >= 3.0: return "Bronze", "lvl-bronze"
    else: return "Black", "lvl-black"

def create_exact_chart(x_labels, target_vals, actual_vals, title, is_kriteria=False):
    fig = go.Figure()
    bar_colors = []
    for act, tgt in zip(actual_vals, target_vals):
        try:
            act_num = float(act)
            tgt_num = float(tgt)
            if act_num >= tgt_num: bar_colors.append('#a8f087')
            else: bar_colors.append('#ff5252')
        except (ValueError, TypeError): bar_colors.append('#e0e0e0')
    
    fig.add_trace(go.Bar(
        x=x_labels, y=actual_vals, name='Aktual', marker_color=bar_colors,
        text=actual_vals, textposition='auto', width=0.45 if is_kriteria else 0.55
    ))
    fig.add_trace(go.Scatter(
        x=x_labels, y=target_vals, name='Target', mode='lines+markers',
        line=dict(color='#0099ff', width=3, shape='spline'), marker=dict(size=9, color='#0099ff')
    ))
    clean_targets = [float(v) for v in target_vals if str(v).replace('.','',1).isdigit()]
    clean_actuals = [float(v) for v in actual_vals if str(v).replace('.','',1).isdigit()]
    max_val = max(max(clean_targets, default=10), max(clean_actuals, default=10))
    
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(size=14, color='#004d73')),
        height=300, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, type='category'), yaxis=dict(title="Nilai Patrol", showgrid=True, gridcolor='#e2e8f0', range=[0, max_val * 1.25])
    )
    return fig

def render_exact_table(columns_header, targets, actuals, first_col_label="Line"):
    html = '<table class="table-5s"><tr><th style="width: 10%;">' + first_col_label + '</th>'
    for col in columns_header: html += f'<th>{col}</th>'
    html += '</tr><tr><td class="bg-label">Target</td>'
    for t in targets: html += f'<td>{t if t is not None and str(t) != "" else "-"}</td>'
    html += '</tr><tr><td class="bg-label">Aktual</td>'
    for a in actuals: html += f'<td>{a if a is not None and str(a) != "" else "-"}</td>'
    html += '</tr><tr><td class="bg-label">Judge</td>'
    for a, t in zip(actuals, targets):
        try:
            if float(a) >= float(t): html += '<td class="judge-ok">OK</td>'
            else: html += '<td class="judge-ng">NG</td>'
        except (ValueError, TypeError): html += '<td>-</td>'
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
        height=380, margin=dict(l=20, r=20, t=40, b=80), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, tickangle=-30)
    )
    fig.update_yaxes(title_text="Rata-rata Nilai Kriteria", secondary_y=False, showgrid=True, gridcolor='#e2e8f0')
    fig.update_yaxes(title_text="Persentase Kumulatif (%)", secondary_y=True, range=[0, 110], showgrid=False)
    return fig

# ----------------- PROCESS SPREADSHEET -----------------
if df.empty:
    st.error("Data Google Sheets kosong.")
else:
    col_b = df.columns[1]

    # Pemisahan Bagian Kriteria (Gambar 1)
    df_kriteria = df[df[col_b].astype(str).str.contains(
        "Sekitar area|Penyimpanan|Area Kerja|Peralatan|Informasi|Tempat|Meja|Penempatan|Mesin", 
        case=False, na=False
    )].copy()
    df_kriteria.columns = [c.replace('.1', '').strip() for c in df_kriteria.columns]

    # Pemisahan Bagian Bulanan (Gambar 2)
    df_bulanan = df[df[col_b].astype(str).str.contains(
        "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Mei|Jun|Jul|Aug|Sep|Oct|Nov|Dec", 
        case=False, na=False
    )].copy()
    df_bulanan.columns = [c.replace('.1', '').strip() for c in df_bulanan.columns]

    all_columns = df_kriteria.columns.tolist()
    ALL_MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    months_data = df_bulanan[df_bulanan.columns[1]].dropna().tolist() if not df_bulanan.empty else ALL_MONTHS
    
    EXCLUDE_KEYWORDS = ['by area', 'by_area', 'total', 'summary', 'all area']
    lines_info = []
    
    for col in all_columns:
        if 'target' in col.lower() and not ('month' in col.lower()):
            clean_name = col.replace('Target', '').replace('target', '').strip()
            if clean_name and not any(kw in clean_name.lower() for kw in EXCLUDE_KEYWORDS):
                lines_info.append((clean_name, clean_name))
    
    ALL_AREAS = list(dict.fromkeys([info[1] for info in lines_info]))

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
    
    col_title, col_export = st.columns([3, 1])
    with col_title:
        st.markdown('<div class="dashboard-title">🧹 DASHBOARD PERFORMANCE PATROL 5S</div>', unsafe_allow_html=True)
        st.markdown('<div class="dashboard-subtitle">Monitoring Real-time Pencapaian Patrol 5S Terintegrasi Full Data Google Sheets</div>', unsafe_allow_html=True)
    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Download Excel Report", data=generate_excel_download(df),
            file_name="Laporan_Patrol_5S_Realtime.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    st.markdown("---")
    
    tab_summary, tab_details, tab_monthly_area, tab_pareto, tab_action = st.tabs([
        "📊 Executive Summary (By Month & By Area)", "🏭 Detail 11 Kriteria Penilaian (By Line)", 
        "📅 Tren Bulanan Per Area (Jan - Dec)", "📈 Pareto Analisis Kriteria Rendah", "🛠️ CAPA Tracking"
    ])
    
    kriteria_labels = DEFAULT_KRITERIA_LIST
    IMAGE_DIR = "uploaded_images"
    if not os.path.exists(IMAGE_DIR): os.makedirs(IMAGE_DIR)

    # --- TAB 1: SUMMARY ---
    with tab_summary:
        total_actual_sum = 0.0
        total_target_sum = 0.0
        filtered_selected_areas = [a for a in selected_departments if not any(kw in a.lower() for kw in EXCLUDE_KEYWORDS)]
        
        area_targets = []
        area_actuals = []

        for area in filtered_selected_areas:
            c_t = next((c for c in df_kriteria.columns if area.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in df_kriteria.columns if area.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            
            # AMAN DARI DUPLIKASI KOLOM & AGREGASI
            sum_t = pd.to_numeric(df_kriteria[c_t].iloc[:, 0] if isinstance(df_kriteria[c_t], pd.DataFrame) else df_kriteria[c_t], errors='coerce').sum() if c_t else 0.0
            sum_a = pd.to_numeric(df_kriteria[c_a].iloc[:, 0] if isinstance(df_kriteria[c_a], pd.DataFrame) else df_kriteria[c_a], errors='coerce').sum() if c_a else 0.0
            
            area_targets.append(sum_t)
            area_actuals.append(sum_a)
            total_actual_sum += sum_a
            total_target_sum += sum_t
                
        JUMLAH_AREA = len(filtered_selected_areas) if filtered_selected_areas else 10
        JUMLAH_KRITERIA = len(kriteria_labels)
        avg_actual = total_actual_sum / (JUMLAH_AREA * JUMLAH_KRITERIA) if (JUMLAH_AREA * JUMLAH_KRITERIA) > 0 else 0.0
        avg_target = total_target_sum / (JUMLAH_AREA * JUMLAH_KRITERIA) if total_target_sum > 0 else 4.0
        overall_level, level_css = get_level_5s(avg_actual)
        
        if overall_level in ["Gold", "Silver"]:
            status_summary = "<span style='color: #2e7d32; font-weight: bold;'>SANGAT BAIK (PERTAHANKAN)</span>"
            action_summary = "Performa 5S secara keseluruhan berada pada standar tinggi. Pertahankan budaya kerja ini."
        elif overall_level == "Bronze":
            status_summary = "<span style='color: #e65100; font-weight: bold;'>BUTUH PERBAIKAN FOKUS</span>"
            action_summary = "Beberapa kriteria/area belum mencapai target. Segera tindak lanjuti temuan NG."
        else:
            status_summary = "<span style='color: #c62828; font-weight: bold;'>PERLU TINDAKAN DARURAT (CRITICAL)</span>"
            action_summary = "Pencapaian 5S berada di bawah standar minimum."
            
        st.markdown(f"""
            <div class="summary-box" style="background-color: var(--secondary-background-color, #ffffff); border-left: 5px solid #004d73; margin-bottom: 20px;">
                <h4 style="margin: 0 0 8px 0; color: #004d73; font-size: 15px;">📋 RANGKUMAN & KESIMPULAN EXECUTIVE SUMMARY</h4>
                <table style="width: 100%; border-collapse: collapse; font-size: 13px; line-height: 1.6;">
                    <tr><td style="width: 25%; font-weight: bold;">Status Performa 5S</td><td>: {status_summary}</td></tr>
                    <tr><td style="font-weight: bold;">Ketercapaian Skor Akhir</td><td>: Skor Akhir <b>{avg_actual:.2f}</b> dari Target <b>{avg_target:.2f}</b> (Level <b>{overall_level}</b>)</td></tr>
                    <tr><td style="font-weight: bold;">Formula Perhitungan</td><td>: Total Nilai ({total_actual_sum:.1f}) ÷ {JUMLAH_AREA} Area ÷ {JUMLAH_KRITERIA} Kriteria = <b>{avg_actual:.2f}</b></td></tr>
                    <tr><td style="font-weight: bold;">Rekomendasi Tindakan</td><td>: {action_summary}</td></tr>
                </table>
            </div>
        """, unsafe_allow_html=True)
        
        if filtered_selected_areas:
            st.plotly_chart(create_exact_chart(filtered_selected_areas, area_targets, area_actuals, "PENCAPAIAN PER AREA / DEPARTMENT"), use_container_width=True)
            st.markdown(render_exact_table(filtered_selected_areas, area_targets, area_actuals, "Area"), unsafe_allow_html=True)

    # --- TAB 2: DETAIL 11 KRITERIA ---
    with tab_details:
        st.markdown('<div class="section-header">BY KRITERIA PENILAIAN & ANALISA PERBAIKAN</div>', unsafe_allow_html=True)
        
        TARGET_AREAS = ["PVC", "SMS", "STEX", "BTEX", "DFAS", "PPEX", "WH", "SHP", "QA/QC", "MTC"]
        lines_info_t2 = []
        for area_code in TARGET_AREAS:
            c_t = next((c for c in df_kriteria.columns if area_code.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in df_kriteria.columns if area_code.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            if c_t and c_a:
                lines_info_t2.append((area_code, c_t, c_a))

        available_area_names = [info[0] for info in lines_info_t2]
        selected_tab2_lines = st.multiselect("🎯 Pilih Area / Line:", options=available_area_names, default=available_area_names, key="filter_tab2_lines")
        filtered_lines_t2 = [info for info in lines_info_t2 if info[0] in selected_tab2_lines]
        
        x_kriteria_num = [str(i) for i in range(1, len(kriteria_labels) + 1)]

        for area_code, col_tgt, col_act in filtered_lines_t2:
            s_tgt = df_kriteria[col_tgt].iloc[:, 0] if isinstance(df_kriteria[col_tgt], pd.DataFrame) else df_kriteria[col_tgt]
            s_act = df_kriteria[col_act].iloc[:, 0] if isinstance(df_kriteria[col_act], pd.DataFrame) else df_kriteria[col_act]
            
            t_k = s_tgt.dropna().tolist()
            a_k = s_act.dropna().tolist()
            
            clean_act = [float(x) for x in a_k if str(x).replace('.', '', 1).isdigit()]
            avg_val = (sum(clean_act) / len(clean_act)) if clean_act else 0.0
            lvl_val, css_val = get_level_5s(avg_val)

            st.markdown(f"#### 🏭 AREA {area_code} &nbsp; <span class='badge-level {css_val}'>Level: {lvl_val} ({avg_val:.2f})</span>", unsafe_allow_html=True)
            st.plotly_chart(create_exact_chart(x_kriteria_num[:len(t_k)], t_k, a_k, f"Kriteria Penilaian 5S - {area_code}", is_kriteria=True), use_container_width=True)
            st.markdown(render_exact_table(kriteria_labels[:len(t_k)], t_k, a_k, "Kriteria"), unsafe_allow_html=True)
            st.markdown("<hr style='margin: 30px 0; border: 0; border-top: 2px dashed #cbd5e1;'>", unsafe_allow_html=True)

    # --- TAB 3: TREN BULANAN ---
    with tab_monthly_area:
        st.markdown('<div class="section-header">REKAPITULASI TREN PENCAPAIAN 5S PER AREA (JANUARI - DESEMBER)</div>', unsafe_allow_html=True)
        TARGET_AREAS = ["PVC", "SMS", "STEX", "BTEX", "DFAS", "PPEX", "WH", "SHP", "QA/QC", "MTC"]
        
        area_pairs_t3 = []
        for area_code in TARGET_AREAS:
            c_t = next((c for c in df_bulanan.columns if area_code.lower() in c.lower() and 'target' in c.lower()), None)
            c_a = next((c for c in df_bulanan.columns if area_code.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual', 'score', 'nilai'])), None)
            if c_t and c_a:
                area_pairs_t3.append((area_code, c_t, c_a))

        filtered_pairs_t3 = [p for p in area_pairs_t3 if not selected_departments or any(sd.lower() in p[0].lower() for sd in selected_departments)]

        if not df_bulanan.empty and filtered_pairs_t3:
            col_bulan_name = df_bulanan.columns[1]
            months_label_g2 = df_bulanan[col_bulan_name].dropna().tolist()

            for i in range(0, len(filtered_pairs_t3), 2):
                cols_m = st.columns(2)
                area_name1, col_t1, col_a1 = filtered_pairs_t3[i]
                
                s_t1 = df_bulanan[col_t1].iloc[:, 0] if isinstance(df_bulanan[col_t1], pd.DataFrame) else df_bulanan[col_t1]
                s_a1 = df_bulanan[col_a1].iloc[:, 0] if isinstance(df_bulanan[col_a1], pd.DataFrame) else df_bulanan[col_a1]
                
                with cols_m[0]:
                    st.plotly_chart(create_exact_chart(months_label_g2[:len(s_a1)], s_t1.dropna().tolist(), s_a1.dropna().tolist(), f"REKAP TREN BULANAN 5S - {area_name1.upper()}"), use_container_width=True)
                    st.markdown(render_exact_table(months_label_g2[:len(s_a1)], s_t1.dropna().tolist(), s_a1.dropna().tolist(), "Bulan"), unsafe_allow_html=True)
                
                if i + 1 < len(filtered_pairs_t3):
                    area_name2, col_t2, col_a2 = filtered_pairs_t3[i+1]
                    s_t2 = df_bulanan[col_t2].iloc[:, 0] if isinstance(df_bulanan[col_t2], pd.DataFrame) else df_bulanan[col_t2]
                    s_a2 = df_bulanan[col_a2].iloc[:, 0] if isinstance(df_bulanan[col_a2], pd.DataFrame) else df_bulanan[col_a2]
                    
                    with cols_m[1]:
                        st.plotly_chart(create_exact_chart(months_label_g2[:len(s_a2)], s_t2.dropna().tolist(), s_a2.dropna().tolist(), f"REKAP TREN BULANAN 5S - {area_name2.upper()}"), use_container_width=True)
                        st.markdown(render_exact_table(months_label_g2[:len(s_a2)], s_t2.dropna().tolist(), s_a2.dropna().tolist(), "Bulan"), unsafe_allow_html=True)

    # --- TAB 4 & 5 UTUH ---
    with tab_pareto:
        st.markdown('<div class="section-header">DIAGRAM PARETO</div>', unsafe_allow_html=True)
        kriteria_scores = {k: [] for k in kriteria_labels}
        for _, key_line in lines_info:
            c_act_p = next((c for c in df_kriteria.columns if key_line.lower() in c.lower() and any(k in c.lower() for k in ['aktual', 'actual'])), None)
            if c_act_p:
                s_p = df_kriteria[c_act_p].iloc[:, 0] if isinstance(df_kriteria[c_act_p], pd.DataFrame) else df_kriteria[c_act_p]
                vals = s_p.dropna().tolist()
                for idx_k, val_k in enumerate(vals):
                    if idx_k < len(kriteria_labels) and str(val_k).replace('.', '', 1).isdigit():
                        kriteria_scores[kriteria_labels[idx_k]].append(float(val_k))

        avg_scores = [(sum(kriteria_scores[k]) / len(kriteria_scores[k])) if kriteria_scores[k] else 0.0 for k in kriteria_labels]
        st.plotly_chart(create_pareto_chart(kriteria_labels, avg_scores), use_container_width=True)

    with tab_action:
        st.markdown('<div class="section-header">CAPA TRACKING</div>', unsafe_allow_html=True)
        st.info("Fitur CAPA Log Aktif.")
