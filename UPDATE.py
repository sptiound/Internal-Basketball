import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# ==============================================================================
# 1. KONFIGURASI HALAMAN
# ==============================================================================
st.set_page_config(
    page_title="Nusantara Basketball Internal Competition",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================================================================
# 2. PANEL KONTROL PANITIA (EDIT BAGIAN INI DI GITHUB SAAT HARI H)
# ==============================================================================

# --- A. STATUS LAPANGAN / FORCE MAJEURE ---
# Pilihan STATUS_LAPANGAN: "NORMAL" atau "DELAY"
STATUS_LAPANGAN = "NORMAL"
PESAN_DELAY = "⚠️ INFO LAPANGAN: Pertandingan ditunda sementara karena hujan. Mohon seluruh tim & panitia standby menunggu informasi lanjutan."

# --- B. DATA BAGAN KATEGORI PUTRI (PI) ---
DATA_PI = {
    "TIM_A": "Tim A (Seed 1)",
    "TIM_B": "Tim B",
    "TIM_C": "Tim C",
    "TIM_D": "Tim D",
    "TIM_E": "Tim E",
    "TIM_F": "Tim F (Seed 2)",
    "G1": [15, 20],   # Tim B vs Tim C (Upper R1)
    "G2": [0, 0],   # Tim D vs Tim E (Upper R1)
    "G3": [0, 0],   # Tim A vs Win Game 1 (Upper R2)
    "G4": [0, 0],   # Win Game 2 vs Tim F (Upper R2)
    "G5": [0, 0],   # Win Game 3 vs Win Game 4 (Upper Final)
    "G6": [0, 0],   # Lose Game 1 vs Lose Game 3 (Lower R1)
    "G7": [0, 0],   # Lose Game 2 vs Lose Game 4 (Lower R1)
    "G8": [0, 0],   # Lose Game 5 vs Win Game 6 (Lower R2)
    "G9": [0, 0],   # Win Game 8 vs Win Game 7 (Lower Final)
    "G10": [0, 0],  # Win Game 5 (Atas) vs Win Game 9 (Bawah) -> Grand Final
}

# --- C. DATA BAGAN KATEGORI PUTRA (PA) ---
DATA_PA = {
    "TIM_A": "Tim A (Seed 1)",
    "TIM_B": "Tim B",
    "TIM_C": "Tim C",
    "TIM_D": "Tim D",
    "TIM_E": "Tim E",
    "TIM_F": "Tim F (Seed 2)",
    "G1": [0, 0],   # Tim B vs Tim C (Upper R1)
    "G2": [20, 21],   # Tim D vs Tim E (Upper R1)
    "G3": [0, 0],   # Tim A vs Win Game 1 (Upper R2)
    "G4": [0, 0],   # Win Game 2 vs Tim F (Upper R2)
    "G5": [0, 0],   # Win Game 3 vs Win Game 4 (Upper Final)
    "G6": [0, 0],   # Lose Game 1 vs Lose Game 3 (Lower R1)
    "G7": [0, 0],   # Lose Game 2 vs Lose Game 4 (Lower R1)
    "G8": [0, 0],   # Lose Game 5 vs Win Game 6 (Lower R2)
    "G9": [0, 0],   # Win Game 8 vs Win Game 7 (Lower Final)
    "G10": [0, 0],  # Win Game 5 (Atas) vs Win Game 9 (Bawah) -> Grand Final
}

# ==============================================================================
# 3. KONFIGURASI LINK GOOGLE SPREADSHEET RUNDOWN
# ==============================================================================
SPREADSHEET_ID = "1n8_ACUbdFqhG__-DxVz442SEkz9ylLgKDMTMvuvfV6M"
GID = "0"

GSHEET_VIEW_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit?gid={GID}#gid={GID}"
GSHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={GID}"

# ==============================================================================
# 4. STYLING HALAMAN UTAMA
# ==============================================================================
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}
header[data-testid="stHeader"] {
    background: transparent;
}
[data-testid="collapsedControl"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 5. PARSER RUNDOWN DARI GOOGLE SPREADSHEET
# ==============================================================================
@st.cache_data(ttl=15)
def load_rundown_per_hari(csv_url):
    try:
        raw_df = pd.read_csv(csv_url, header=None)
        days_data = {}
        current_day = None
        
        for _, row in raw_df.iterrows():
            vals = [str(x).strip() if pd.notna(x) else "" for x in row.tolist()]
            col_b = vals[1] if len(vals) > 1 else ""
            col_c = vals[2] if len(vals) > 2 else ""
            col_d = vals[3] if len(vals) > 3 else ""
            col_e = vals[4] if len(vals) > 4 else ""

            if col_b.upper().startswith("DAY "):
                current_day = col_b
                days_data[current_day] = []
                continue

            if current_day is None:
                continue
            if col_b.upper() in ["PANITIA", "WAKTU", ""]:
                continue

            days_data[current_day].append({
                "Waktu": col_b,
                "Durasi": col_c,
                "Agenda": col_d if col_d else "-",
                "Keterangan": col_e if col_e else "-"
            })

        return {k: pd.DataFrame(v) for k, v in days_data.items() if len(v) > 0}
    except Exception:
        return {}

# ==============================================================================
# 6. FUNGSI LOGIKA & RENDER BAGAN DENGAN PANAH SVG
# ==============================================================================
def get_win_lose(t1, s1, t2, s2, game_label):
    if s1 > s2:
        return t1, t2
    elif s2 > s1:
        return t2, t1
    return f"Win {game_label}", f"Lose {game_label}"

def match_card_html(title, t1, s1, t2, s2):
    w1 = "winner" if s1 > s2 else ""
    w2 = "winner" if s2 > s1 else ""
    return f'<div class="match-card"><div class="match-header">{title}</div><div class="team-row {w1}"><span>{t1}</span><span>{s1}</span></div><div class="team-row {w2}"><span>{t2}</span><span>{s2}</span></div></div>'

def render_double_elim_bracket(b):
    win_g1, lose_g1 = get_win_lose(b["TIM_B"], b["G1"][0], b["TIM_C"], b["G1"][1], "Game 1")
    win_g2, lose_g2 = get_win_lose(b["TIM_D"], b["G2"][0], b["TIM_E"], b["G2"][1], "Game 2")

    win_g3, lose_g3 = get_win_lose(b["TIM_A"], b["G3"][0], win_g1, b["G3"][1], "Game 3")
    win_g4, lose_g4 = get_win_lose(win_g2, b["G4"][0], b["TIM_F"], b["G4"][1], "Game 4")

    win_g5, lose_g5 = get_win_lose(win_g3, b["G5"][0], win_g4, b["G5"][1], "Game 5")

    win_g6, _ = get_win_lose(lose_g1, b["G6"][0], lose_g3, b["G6"][1], "Game 6")
    win_g7, _ = get_win_lose(lose_g2, b["G7"][0], lose_g4, b["G7"][1], "Game 7")
    win_g8, _ = get_win_lose(lose_g5, b["G8"][0], win_g6, b["G8"][1], "Game 8")
    win_g9, _ = get_win_lose(win_g8, b["G9"][0], win_g7, b["G9"][1], "Game 9")

    champion, _ = get_win_lose(win_g5, b["G10"][0], win_g9, b["G10"][1], "Game 10")
    if b["G10"][0] == 0 and b["G10"][1] == 0:
        champion = "Menunggu Hasil Grand Final"

    st.caption("💡 *Jika dibuka lewat HP, geser bagan ke kanan/kiri untuk melihat seluruh alur panah pertandingan.*")

    w1_gf = "winner" if b["G10"][0] > b["G10"][1] else ""
    w2_gf = "winner" if b["G10"][1] > b["G10"][0] else ""

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        body {{
            background-color: transparent;
            color: #F8FAFC;
        }}
        .bracket-scroll-container {{
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 12px;
        }}
        .bracket-canvas {{
            position: relative;
            width: 1000px;
            height: 570px;
            margin: 0 auto;
        }}
        .bracket-svg {{
            position: absolute;
            top: 0;
            left: 0;
            width: 1000px;
            height: 570px;
            z-index: 1;
            pointer-events: none;
        }}
        .section-badge {{
            position: absolute;
            font-size: 14px;
            font-weight: 700;
            padding-bottom: 4px;
            border-bottom: 1px solid #334155;
            width: 710px;
            z-index: 2;
        }}
        .round-tag {{
            position: absolute;
            font-size: 11px;
            font-weight: 600;
            color: #94A3B8;
            z-index: 2;
        }}
        .card-slot {{
            position: absolute;
            width: 210px;
            z-index: 2;
        }}
        .match-card {{
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 9px 12px;
            color: #F8FAFC;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25);
        }}
        .match-header {{
            font-size: 11px;
            font-weight: 700;
            color: #94A3B8;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #334155;
            padding-bottom: 3px;
        }}
        .team-row {{
            display: flex;
            justify-content: space-between;
            padding: 2px 0;
            font-size: 13px;
            gap: 8px;
        }}
        .winner {{
            font-weight: bold;
            color: #4ADE80;
        }}
        .gf-slot {{
            position: absolute;
            left: 760px;
            top: 195px;
            width: 230px;
            z-index: 2;
        }}
        .grand-final-card {{
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 2px solid #F59E0B;
            border-radius: 10px;
            padding: 14px;
            color: #F8FAFC;
            box-shadow: 0 10px 15px -3px rgba(245, 158, 11, 0.25);
        }}
        .champion-box {{
            background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
            color: #FFFFFF;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 13px;
            margin-top: 10px;
        }}
    </style>
    </head>
    <body>
        <div class="bracket-scroll-container">
            <div class="bracket-canvas">
                
                <!-- LAPISAN GARIS PANAH SVG -->
                <svg class="bracket-svg" viewBox="0 0 1000 570">
                    <defs>
                        <!-- Satu warna seragam untuk panah Upper & Lower -->
                        <marker id="arrow-main" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 1 L 10 5 L 0 9 z" fill="#94A3B8"/>
                        </marker>
                        <!-- Warna emas khusus menuju Grand Final -->
                        <marker id="arrow-gold" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                            <path d="M 0 1 L 10 5 L 0 9 z" fill="#F59E0B"/>
                        </marker>
                    </defs>

                    <!-- UPPER BRACKET ARROWS -->
                    <line x1="220" y1="98" x2="256" y2="98" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow-main)"/>
                    <line x1="220" y1="203" x2="256" y2="203" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow-main)"/>
                    <polyline points="470,98 490,98 490,140 506,140" fill="none" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow-main)"/>
                    <polyline points="470,203 490,203 490,162 506,162" fill="none" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow-main)"/>

                    <!-- LOWER BRACKET ARROWS -->
                    <line x1="220" y1="368" x2="256" y2="368" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow-main)"/>
                    <polyline points="470,368 490,368 490,425 506,425" fill="none" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow-main)"/>
                    <line x1="220" y1="473" x2="506" y2="473" stroke="#94A3B8" stroke-width="2" marker-end="url(#arrow-main)"/>

                    <!-- GRAND FINAL ARROWS -->
                    <polyline points="720,151 740,151 740,242 756,242" fill="none" stroke="#F59E0B" stroke-width="2.2" marker-end="url(#arrow-gold)"/>
                    <polyline points="720,448 740,448 740,285 756,285" fill="none" stroke="#F59E0B" stroke-width="2.2" marker-end="url(#arrow-gold)"/>
                </svg>

                <!-- JUDUL & KARTU UPPER BRACKET -->
                <div class="section-badge" style="left: 10px; top: 5px; color: #38BDF8;">🔼 UPPER BRACKET</div>
                <div class="round-tag" style="left: 10px; top: 36px;">Round 1 (Upper)</div>
                <div class="round-tag" style="left: 260px; top: 36px;">Round 2 (Upper)</div>
                <div class="round-tag" style="left: 510px; top: 88px;">Upper Final</div>

                <div class="card-slot" style="left: 10px; top: 55px;">
                    {match_card_html("GAME 1", b["TIM_B"], b["G1"][0], b["TIM_C"], b["G1"][1])}
                </div>
                <div class="card-slot" style="left: 10px; top: 160px;">
                    {match_card_html("GAME 2", b["TIM_D"], b["G2"][0], b["TIM_E"], b["G2"][1])}
                </div>
                <div class="card-slot" style="left: 260px; top: 55px;">
                    {match_card_html("GAME 3", b["TIM_A"], b["G3"][0], win_g1, b["G3"][1])}
                </div>
                <div class="card-slot" style="left: 260px; top: 160px;">
                    {match_card_html("GAME 4", win_g2, b["G4"][0], b["TIM_F"], b["G4"][1])}
                </div>
                <div class="card-slot" style="left: 510px; top: 108px;">
                    {match_card_html("GAME 5", win_g3, b["G5"][0], win_g4, b["G5"][1])}
                </div>

                <!-- JUDUL & KARTU LOWER BRACKET -->
                <div class="section-badge" style="left: 10px; top: 275px; color: #F87171;">🔽 LOWER BRACKET</div>
                <div class="round-tag" style="left: 10px; top: 306px;">Lower Round 1</div>
                <div class="round-tag" style="left: 260px; top: 306px;">Lower Round 2</div>
                <div class="round-tag" style="left: 510px; top: 385px;">Lower Final</div>

                <div class="card-slot" style="left: 10px; top: 325px;">
                    {match_card_html("GAME 6", lose_g1, b["G6"][0], lose_g3, b["G6"][1])}
                </div>
                <div class="card-slot" style="left: 10px; top: 430px;">
                    {match_card_html("GAME 7", lose_g2, b["G7"][0], lose_g4, b["G7"][1])}
                </div>
                <div class="card-slot" style="left: 260px; top: 325px;">
                    {match_card_html("GAME 8", lose_g5, b["G8"][0], win_g6, b["G8"][1])}
                </div>
                <div class="card-slot" style="left: 510px; top: 405px;">
                    {match_card_html("GAME 9", win_g8, b["G9"][0], win_g7, b["G9"][1])}
                </div>

                <!-- GRAND FINAL (TENGAH VERTIKAL) -->
                <div class="gf-slot">
                    <div class="grand-final-card">
                        <div class="match-header" style="color:#FBBF24;">🏆 GAME 10 • GRAND FINAL</div>
                        <div class="team-row {w1_gf}">
                            <span>{win_g5}</span><span>{b["G10"][0]}</span>
                        </div>
                        <div style="text-align:center; font-size:12px; color:#94A3B8; margin:5px 0; font-weight:bold;">VS</div>
                        <div class="team-row {w2_gf}">
                            <span>{win_g9}</span><span>{b["G10"][1]}</span>
                        </div>
                        <div class="champion-box">
                            👑 {champion}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </body>
    </html>
    """
    components.html(full_html, height=585, scrolling=False)

# ==============================================================================
# 7. TAMPILAN UTAMA APLIKASI
# ==============================================================================
st.title("🏀 Nusantara Basketball Internal Competition")
st.caption("Portal Resmi Jadwal Pertandingan & Bagan Upper / Lower Bracket")

# Banner Pengumuman Lapangan
if STATUS_LAPANGAN.upper() != "NORMAL":
    st.error(PESAN_DELAY)
else:
    st.success("✅ Kondisi lapangan kondusif. Pertandingan berjalan sesuai jadwal.")

tab_rundown, tab_bagan = st.tabs(["📅 Rundown Per Hari", "🏆 Bagan Pertandingan (Upper / Lower)"])

with tab_rundown:
    col_head, col_link = st.columns([3, 1.2])
    with col_head:
        st.subheader("Jadwal Kegiatan & Pertandingan")
    with col_link:
        st.link_button(
            "📄 Buka Spreadsheet Keseluruhan (Day 1–4)",
            GSHEET_VIEW_URL,
            use_container_width=True
        )

    days_dict = load_rundown_per_hari(GSHEET_CSV_URL)

    if days_dict:
        day_names = list(days_dict.keys())
        short_labels = [name.split(",")[0].strip() for name in day_names]
        sub_tabs = st.tabs([f"📌 {lbl}" for lbl in short_labels])

        for idx, day_full_title in enumerate(day_names):
            with sub_tabs[idx]:
                st.markdown(f"**{day_full_title}**")
                st.dataframe(
                    days_dict[day_full_title],
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.warning("⚠️ Data belum terbaca dari Google Sheets. Pastikan akses Share pada Spreadsheet sudah diatur ke **'Anyone with the link can view'**.")
        st.link_button("Buka Google Spreadsheet", GSHEET_VIEW_URL)

with tab_bagan:
    sub_pi, sub_pa = st.tabs(["👩 Kategori Putri (PI)", "👨 Kategori Putra (PA)"])

    with sub_pi:
        render_double_elim_bracket(DATA_PI)

    with sub_pa:
        render_double_elim_bracket(DATA_PA)
