import os
import fastf1
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from main import F1StrategyEngine

st.set_page_config(
    page_title="Pitwall — F1 Strategy & Telemetry",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DESIGN TOKENS & GLOBAL STYLE
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700;900&family=JetBrains+Mono:wght@400;500;700&family=Saira+Condensed:wght@600;700;800&display=swap');

:root {
    --bg-primary: #0A0C12;
    --bg-panel: #14161F;
    --bg-panel-alt: #1B1E2A;
    --accent-red: #E10600;
    --accent-red-dim: #6B0300;
    --accent-teal: #00D2C6;
    --text-primary: #F5F6FA;
    --text-muted: #A7ABBD;
    --border: #262A38;
    --soft: #DA291C;
    --medium: #FFD12E;
    --hard: #F0F0F0;
    --inter: #43B02A;
    --wet: #0067AD;
}

html, body, [class*="css"] { font-family: 'Titillium Web', sans-serif; color: var(--text-primary); }
.stApp { background-color: var(--bg-primary); color: var(--text-primary); }
#MainMenu, footer, header { visibility: hidden; }
h1, h2, h3, h4, h5, h6, p, span, label, div { color: var(--text-primary); }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--text-muted) !important; }

[data-testid="stSidebar"] {
    background-color: var(--bg-panel-alt);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stSelectbox label {
    color: var(--text-muted);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
}

/* ---- Wordmark (custom — not the official F1 or team mark) ---- */
.pw-wordmark { display: flex; align-items: baseline; gap: 10px; padding: 4px 0 18px 0; }
.pw-wordmark .mark {
    background: var(--accent-red);
    color: #fff;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 15px;
    padding: 3px 7px;
    border-radius: 4px;
}
.pw-wordmark .word { font-size: 20px; font-weight: 900; letter-spacing: 0.5px; color: var(--text-primary); }
.pw-wordmark .word .thin { font-weight: 400; color: var(--text-muted); }

/* ---- Sidebar section divider ---- */
.pw-sidebar-title {
    font-size: 13px; font-weight: 700; letter-spacing: 1px;
    color: var(--text-muted); text-transform: uppercase;
    margin: 2px 0 14px 0; padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}

/* ---- Section labels (used above tables/charts inside views) ---- */
.pw-section-label {
    font-family: 'Saira Condensed', sans-serif;
    color: var(--accent-teal); font-weight: 700; font-size: 20px;
    text-transform: uppercase; letter-spacing: 0.5px; margin: 4px 0 10px 0;
}

/* ---- Session header (the one bold gradient moment) ---- */
.pw-session-header {
    background: linear-gradient(120deg, var(--accent-red) 0%, var(--accent-red-dim) 55%, var(--bg-panel) 100%);
    border-radius: 10px;
    padding: 22px 28px;
    margin-bottom: 22px;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 10px 30px rgba(225, 6, 0, 0.15);
}
.pw-session-header .title {
    font-family: 'Saira Condensed', sans-serif;
    font-size: 32px; font-weight: 800; margin: 0; color: #fff;
    text-transform: uppercase; letter-spacing: 0.5px;
    transform: skewX(-6deg); display: inline-block;
}
.pw-session-header .subtitle { color: rgba(255,255,255,0.8); font-size: 13px; font-weight: 600; margin-top: 5px; letter-spacing: 1px; }
.pw-badge {
    font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 13px;
    background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.25);
    color: #fff; padding: 5px 12px; border-radius: 6px; margin-left: 8px;
}

/* ---- Empty state ---- */
.pw-empty {
    border: 1px dashed var(--border);
    border-radius: 10px;
    padding: 60px 30px;
    text-align: center;
    color: var(--text-muted);
    margin-top: 40px;
}
.pw-empty .checker {
    width: 120px; height: 14px; margin: 0 auto 22px auto;
    background-image: repeating-conic-gradient(var(--text-muted) 0% 25%, transparent 0% 50%);
    background-size: 14px 14px;
    opacity: 0.5;
}
.pw-empty h3 { color: var(--text-primary); font-weight: 700; margin-bottom: 6px; }
.pw-empty p { color: var(--text-muted); }

/* ---- Segmented control (replaces st.tabs — keeps selection via session_state key) ---- */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    background-color: var(--bg-panel-alt);
    padding: 5px;
    border-radius: 9px;
    border: 1px solid var(--border);
    gap: 4px;
    flex-direction: row;
    flex-wrap: wrap;
}
div[data-testid="stRadio"] label {
    background: transparent;
    border-radius: 6px;
    padding: 9px 16px !important;
    margin: 0 !important;
    font-weight: 700;
    font-size: 13px;
    color: var(--text-muted);
    transition: background-color 0.15s ease, color 0.15s ease;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background-color: var(--accent-red);
    color: #fff;
}
div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p { margin: 0; color: inherit; }
div[data-testid="stRadio"] input[type="radio"] { position: absolute; opacity: 0; pointer-events: none; }
div[data-testid="stRadio"] label > div:first-child { display: none; }

/* ---- Panels / metrics ---- */
.stMetric, [data-testid="stMetric"] {
    background-color: var(--bg-panel);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-teal);
    padding: 14px 16px;
    border-radius: 8px;
}
[data-testid="stMetricLabel"] p { color: var(--text-muted) !important; }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; }
.stButton>button {
    background-color: var(--accent-red);
    color: #fff; font-weight: 700; border: none; border-radius: 6px;
    letter-spacing: 0.4px;
}
.stButton>button:hover { background-color: #ff241c; color: #fff; }
.stButton>button:disabled { background-color: var(--bg-panel-alt); color: var(--text-muted); }

.pw-compound-pill {
    font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 12px;
    padding: 2px 9px; border-radius: 10px; color: #111;
}

/* ---- Custom HTML tables (Stint Summary / Results / Standings) ----
   st.dataframe renders onto an HTML canvas internally, which plain CSS
   cannot restyle — so anywhere we need guaranteed white-on-dark text and
   team-colour accents, we build a real HTML <table> instead. */
.pw-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.pw-table th {
    text-align: left; font-family: 'Saira Condensed', sans-serif;
    font-size: 13px; letter-spacing: 0.5px; text-transform: uppercase;
    color: var(--text-muted); font-weight: 700;
    padding: 8px 12px; border-bottom: 1px solid var(--border);
}
.pw-table td {
    padding: 9px 12px; color: var(--text-primary);
    border-bottom: 1px solid var(--border);
}
.pw-table tr:hover td { background-color: var(--bg-panel-alt); }
.pw-table .team-chip {
    display: inline-block; width: 4px; height: 16px; border-radius: 2px;
    margin-right: 10px; vertical-align: middle;
}
.pw-table .mono { font-family: 'JetBrains Mono', monospace; }
.pw-table .muted { color: var(--text-muted); }
.pw-table-wrap { overflow-x: auto; width: 100%; }

/* ---- Selectbox dropdown popup (BaseWeb portal) ----
   This popup is not inside our dark containers and keeps its own light
   background by default. The global `div, span, p, label { color: white }`
   rule above made its option text white-on-white — fixing by darkening the
   popup itself rather than loosening that rule. */
div[data-baseweb="popover"] ul,
div[data-baseweb="popover"] li,
ul[role="listbox"] {
    background-color: var(--bg-panel) !important;
    border-color: var(--border) !important;
}
li[role="option"] {
    background-color: var(--bg-panel) !important;
    color: var(--text-primary) !important;
}
li[role="option"]:hover,
li[aria-selected="true"] {
    background-color: var(--bg-panel-alt) !important;
}
</style>
""", unsafe_allow_html=True)

COMPOUND_COLORS = {
    "SOFT": "#DA291C", "MEDIUM": "#FFD12E", "HARD": "#F0F0F0",
    "INTERMEDIATE": "#43B02A", "WET": "#0067AD",
    "UNKNOWN": "#9B9B9B", "TEST_UNKNOWN": "#9B9B9B",
}

# NOTE: `fig.update_layout(template=...)` only works with a real
# go.layout.Template (or a registered template name) — a plain dict is
# silently ignored, which is why charts were falling back to Plotly's
# default white theme. This builds an actual Template object.
PLOT_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="#14161F",
        plot_bgcolor="#14161F",
        font=dict(color="#F5F6FA", family="Titillium Web"),
        xaxis=dict(gridcolor="#262A38", zerolinecolor="#262A38"),
        yaxis=dict(gridcolor="#262A38", zerolinecolor="#262A38"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        coloraxis_colorbar=dict(tickfont=dict(color="#F5F6FA"), title_font=dict(color="#F5F6FA")),
    )
)

SESSION_LABELS = {
    "R": "Race", "Q": "Qualifying", "S": "Sprint", "SQ": "Sprint Qualifying",
    "FP1": "Practice 1", "FP2": "Practice 2", "FP3": "Practice 3",
}
QUALI_TYPES = {"Q", "SQ"}

# Fallback team colours for the Standings view — Ergast (unlike FastF1's own
# session.results) doesn't provide TeamColor, so this covers the well-known
# recent-era liveries. Anything not listed falls back to a neutral grey
# rather than guessing.
TEAM_COLOR_FALLBACK = {
    "Red Bull": "#3671C6", "Ferrari": "#E8002D", "Mercedes": "#27F4D2",
    "McLaren": "#FF8000", "Aston Martin": "#229971", "Alpine F1 Team": "#FF87BC",
    "Alpine": "#FF87BC", "Williams": "#64C4FF", "RB F1 Team": "#6692FF",
    "AlphaTauri": "#6692FF", "Racing Bulls": "#6692FF", "Kick Sauber": "#52E252",
    "Sauber": "#52E252", "Alfa Romeo": "#C92D4B", "Haas F1 Team": "#B6BABD",
    "Renault": "#FFF500", "Racing Point": "#F596C8", "Force India": "#F596C8",
    "Toro Rosso": "#469BFF", "Lotus F1": "#FFB800",
}


def hex_color(value, fallback="#8A8FA3"):
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        return fallback
    v = str(value).strip()
    return v if v.startswith("#") else f"#{v}"


def fmt_td(td):
    """Format a pandas Timedelta as m:ss.mmm, blank if missing."""
    if td is None or pd.isna(td):
        return ""
    total = td.total_seconds()
    m, s = divmod(total, 60)
    return f"{int(m)}:{s:06.3f}" if m >= 1 else f"{s:.3f}"


def render_html_table(headers, rows_html):
    """rows_html: list of already-built <tr>...</tr> strings. Wrapped in a
    horizontally-scrollable container so a table wider than its column
    scrolls instead of visually overflowing into whatever sits next to it."""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(rows_html)
    st.markdown(
        f'<div class="pw-table-wrap"><table class="pw-table"><thead><tr>{head}</tr></thead>'
        f'<tbody>{body}</tbody></table></div>',
        unsafe_allow_html=True
    )

if not os.path.exists('cache_dir'):
    os.makedirs('cache_dir')
fastf1.Cache.enable_cache('cache_dir')


# =============================================================================
# CACHED DATA HELPERS
# =============================================================================
@st.cache_data(show_spinner=False)
def get_season_schedule(year: int):
    schedule = fastf1.get_event_schedule(year)
    schedule = schedule[schedule['EventFormat'] != 'testing']
    return schedule['EventName'].tolist()


@st.cache_data(show_spinner=False)
def get_available_sessions(year: int, grand_prix: str):
    schedule = fastf1.get_event_schedule(year)
    event = schedule[schedule['EventName'] == grand_prix]
    if event.empty:
        codes = ["R", "Q", "FP1", "FP2", "FP3"]
    else:
        event_format = event.iloc[0]['EventFormat']
        if event_format in ['sprint', 'sprint_shootout', 'sprint_qualifying']:
            codes = ["R", "Q", "S", "SQ", "FP1"]
        else:
            codes = ["R", "Q", "FP1", "FP2", "FP3"]
    return codes


@st.cache_resource(show_spinner=False)
def load_f1_session(year: int, grand_prix: str, session_type: str):
    return F1StrategyEngine(year, grand_prix, session_type)


@st.cache_data(show_spinner=False)
def get_standings(year: int):
    """Returns (driver_standings_df, constructor_standings_df) for the most
    recent completed round of `year`, or (None, None) if Ergast has nothing
    for that season yet (e.g. season hasn't started)."""
    from fastf1.ergast import Ergast
    ergast = Ergast(result_type='pandas', auto_cast=True)

    drivers_resp = ergast.get_driver_standings(season=year, round='last')
    constructors_resp = ergast.get_constructor_standings(season=year, round='last')

    drivers_df = drivers_resp.content[0] if drivers_resp.content else None
    constructors_df = constructors_resp.content[0] if constructors_resp.content else None
    return drivers_df, constructors_df


# =============================================================================
# WORDMARK (custom design — the real F1 / team logos are trademarked, so this
# is a built typographic mark, not a reproduction of either)
# =============================================================================
def render_wordmark(container):
    container.markdown("""
        <div class="pw-wordmark">
            <span class="mark">PW</span>
            <span class="word">PIT<span class="thin">WALL</span></span>
        </div>
    """, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR — cascading Year -> Grand Prix -> Session, nothing auto-loads
# =============================================================================
render_wordmark(st.sidebar)
st.sidebar.markdown('<div class="pw-sidebar-title">Session Select</div>', unsafe_allow_html=True)

years = list(range(2026, 2017, -1))
selected_year = st.sidebar.selectbox("Season", years, index=None, placeholder="Choose a year")

selected_gp = None
if selected_year:
    available_gps = get_season_schedule(selected_year)
    selected_gp = st.sidebar.selectbox("Grand Prix", available_gps, index=None, placeholder="Choose a race")

selected_session = None
if selected_year and selected_gp:
    available_sessions = get_available_sessions(selected_year, selected_gp)
    selected_session = st.sidebar.selectbox(
        "Session", available_sessions, index=None, placeholder="Choose a session",
        format_func=lambda c: SESSION_LABELS.get(c, c)
    )

st.sidebar.markdown("<br>", unsafe_allow_html=True)
ready_to_load = bool(selected_year and selected_gp and selected_session)
load_clicked = st.sidebar.button(
    "Load session data", width='stretch', disabled=not ready_to_load
)

if "engine" not in st.session_state:
    st.session_state.engine = None
    st.session_state.meta = None

if load_clicked and ready_to_load:
    with st.spinner(f"Pulling {selected_year} {selected_gp} ({SESSION_LABELS.get(selected_session, selected_session)}) telemetry..."):
        try:
            engine = load_f1_session(selected_year, selected_gp, selected_session)
            st.session_state.engine = engine
            st.session_state.drivers = sorted(engine.laps['Driver'].dropna().unique().tolist())
            st.session_state.meta = (selected_year, selected_gp, selected_session)
        except Exception as e:
            st.session_state.engine = None
            st.error(f"Couldn't load that session: {e}")

# =============================================================================
# EMPTY STATE — shown until the user explicitly loads a session
# =============================================================================
if st.session_state.engine is None:
    render_wordmark(st)
    st.markdown("""
        <div class="pw-empty">
            <div class="checker"></div>
            <h3>No session loaded</h3>
            <p>Choose a season, race and session in the sidebar, then hit
            <b>Load session data</b> to bring up telemetry, degradation and strategy tools.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

engine = st.session_state.engine
year, gp, session_type = st.session_state.meta

# =============================================================================
# SESSION HEADER
# =============================================================================
st.markdown(f"""
    <div class="pw-session-header">
        <div>
            <p class="title">{gp}</p>
            <p class="subtitle">TELEMETRY &amp; STRATEGY HUB</p>
        </div>
        <div>
            <span class="pw-badge">{year}</span>
            <span class="pw-badge">{SESSION_LABELS.get(session_type, session_type)}</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# =============================================================================
# NAVIGATION — st.radio bound to session_state via `key`, so it survives any
# rerun triggered by widgets inside a view (this is what fixes the old
# st.tabs() behaviour of snapping back to the first tab on interaction).
# =============================================================================
VIEWS = ["Telemetry & Degradation", "Pit Strategy Simulator", "Head-to-Head Pace", "Session Results", "Championship Standings"]
if "active_view" not in st.session_state:
    st.session_state.active_view = VIEWS[0]

active_view = st.radio(
    "View", VIEWS, key="active_view", horizontal=True, label_visibility="collapsed"
)


# =============================================================================
# VIEW: TELEMETRY — degradation view for Race/Sprint, Q1/Q2/Q3 split for Quali
# =============================================================================
def render_quali_segment(engine, selected_driver, seg_laps, label):
    st.markdown(f"<div class='pw-section-label'>{label}</div>", unsafe_allow_html=True)
    if seg_laps is None:
        st.markdown("<p class='muted' style='color:var(--text-muted);'>Session not run.</p>", unsafe_allow_html=True)
        return
    drv_seg = seg_laps[(seg_laps['Driver'] == selected_driver) & seg_laps['LapTime'].notna()]
    if drv_seg.empty:
        st.markdown("<p style='color:var(--text-muted);'>Not reached.</p>", unsafe_allow_html=True)
        return
    drv_seg = drv_seg.copy()
    drv_seg['Attempt'] = range(1, len(drv_seg) + 1)
    best = drv_seg['LapTimeSeconds'].min()
    fig = px.bar(
        drv_seg, x="Attempt", y="LapTimeSeconds",
        color=drv_seg['LapTimeSeconds'].eq(best).map({True: "Best", False: "Other"}),
        color_discrete_map={"Best": "#00D2C6", "Other": "#8A8FA3"},
        labels={"LapTimeSeconds": "Lap time (s)", "Attempt": "Attempt"},
    )
    fig.update_layout(template=PLOT_TEMPLATE, height=300, showlegend=False, yaxis_range=[best - 1, drv_seg['LapTimeSeconds'].max() + 0.5])
    st.plotly_chart(fig, width='stretch', theme=None)
    st.markdown(f"<p class='mono' style='color:var(--text-primary); font-family:JetBrains Mono, monospace;'>Best: {round(best,3)}s</p>", unsafe_allow_html=True)


def render_telemetry_view(engine, session_type):
    if session_type in QUALI_TYPES:
        st.markdown("<div class='pw-section-label'>Driver</div>", unsafe_allow_html=True)
        selected_driver = st.selectbox("Driver", st.session_state.drivers, index=0, label_visibility="collapsed")
        q1, q2, q3 = engine.laps.split_qualifying_sessions()
        c1, c2, c3 = st.columns(3)
        with c1:
            render_quali_segment(engine, selected_driver, q1, "Q1")
        with c2:
            render_quali_segment(engine, selected_driver, q2, "Q2")
        with c3:
            render_quali_segment(engine, selected_driver, q3, "Q3")
        return

    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown("<div class='pw-section-label'>Driver</div>", unsafe_allow_html=True)
        selected_driver = st.selectbox("Driver", st.session_state.drivers, index=0, label_visibility="collapsed")
        fuel_correction = st.slider("Fuel correction (s/lap)", min_value=0.00, max_value=0.08, value=0.035, step=0.005)

        drv_laps = engine.clean_laps[engine.clean_laps['Driver'] == selected_driver]

        stint_summary = []
        for (stint, compound), group in drv_laps.groupby(['Stint', 'Compound']):
            if len(group) < 3:
                continue
            x = group['LapNumber'].values
            y_raw = group['LapTimeSeconds'].values
            y_corr = y_raw + (x * fuel_correction)
            raw_deg, _ = np.polyfit(x, y_raw, 1)
            corr_deg, _ = np.polyfit(x, y_corr, 1)
            stint_summary.append((int(stint), compound, len(group), round(raw_deg, 3), round(corr_deg, 3)))

        st.markdown("<br><div class='pw-section-label'>Stint Summary</div>", unsafe_allow_html=True)
        if stint_summary:
            rows = []
            for stint, compound, n, raw_deg, corr_deg in stint_summary:
                chip = hex_color(COMPOUND_COLORS.get(compound, "#8A8FA3"))
                rows.append(
                    f"<tr><td><span class='team-chip' style='background:{chip};'></span>{stint}</td>"
                    f"<td>{compound}</td><td>{n}</td>"
                    f"<td class='mono'>{raw_deg}s</td><td class='mono'>{corr_deg}s</td></tr>"
                )
            render_html_table(["Stint", "Compound", "Laps", "Raw", "Corr"], rows)
        else:
            st.info("No clean stint data for this driver.")

    with col2:
        if not drv_laps.empty:
            fig = px.line(
                drv_laps, x="LapNumber", y="LapTimeSeconds", color="Compound",
                color_discrete_map=COMPOUND_COLORS, markers=True,
                title=f"Lap time evolution — {selected_driver}",
                labels={"LapNumber": "Lap", "LapTimeSeconds": "Lap time (s)"}
            )
            fig.update_layout(template=PLOT_TEMPLATE, height=480, legend_title_text="Compound")
            st.plotly_chart(fig, width='stretch', theme=None)


# =============================================================================
# VIEW: PIT STRATEGY SIMULATOR (reuses engine.simulate_what_if_pit)
# =============================================================================
def render_strategy_view(engine):
    col_sim1, col_sim2 = st.columns([1, 2])

    with col_sim1:
        st.markdown("<h4 style='color: var(--accent-teal); font-weight: 700;'>Simulation config</h4>", unsafe_allow_html=True)
        sim_driver = st.selectbox("Target driver", st.session_state.drivers, index=0, key="sim_drv")

        pit_laps_df = engine.laps[(engine.laps['Driver'] == sim_driver) & (engine.laps['PitInTime'].notna())]
        actual_pits = pit_laps_df['LapNumber'].astype(int).tolist()
        default_actual_pit = actual_pits[0] if actual_pits else 20

        actual_pit_lap = st.number_input("Actual pit lap", min_value=1, max_value=70, value=int(default_actual_pit))
        target_pit_lap = st.number_input("Simulated pit lap", min_value=1, max_value=70, value=max(1, actual_pit_lap - 3))
        pit_loss = st.number_input("Baseline pit loss (s)", value=20.0, step=0.5)

    with col_sim2:
        result = engine.simulate_what_if_pit(sim_driver, actual_pit_lap, target_pit_lap, pit_loss)

        if "Error" in result:
            st.warning(result["Error"])
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Strategy type", result["ScenarioType"])
            m2.metric("Tyre delta / lap", f"{result['EstimatedTyreDeltaPerLap_s']} s")
            m3.metric("Net time advantage", f"{result['EstimatedTimeDelta_s']} s", delta=f"{result['EstimatedTimeDelta_s']} s")

            drv_clean = engine.clean_laps[engine.clean_laps['Driver'] == sim_driver].sort_values('LapNumber')
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=drv_clean['LapNumber'], y=drv_clean['LapTimeSeconds'],
                mode='lines+markers', name='Actual lap times',
                line=dict(color='#8A8FA3', dash='dash')
            ))
            fig.add_vline(x=actual_pit_lap, line_width=2, line_color="#E10600", annotation_text="Actual pit")
            fig.add_vline(x=target_pit_lap, line_width=2, line_dash="dot", line_color="#00D2C6", annotation_text="Simulated pit")
            fig.update_layout(
                title=f"Pit window delta analysis — {sim_driver}",
                xaxis_title="Lap", yaxis_title="Lap time (s)",
                template=PLOT_TEMPLATE, height=420
            )
            st.plotly_chart(fig, width='stretch', theme=None)


# =============================================================================
# VIEW: HEAD-TO-HEAD PACE (reuses engine.compare_driver_pace)
# =============================================================================
def render_headtohead_view(engine):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        d1 = st.selectbox("Driver A", st.session_state.drivers, index=0, key="h2h_a")
    with col_p2:
        d2 = st.selectbox("Driver B", st.session_state.drivers, index=min(1, len(st.session_state.drivers) - 1), key="h2h_b")

    if d1 == d2:
        st.warning("Select two different drivers to compare.")
        return

    comp = engine.compare_driver_pace(d1, d2)
    if comp.empty:
        st.info("No overlapping clean laps between these two drivers.")
        return

    st.caption(f"{len(comp)} lap(s) with clean-lap data available for both drivers in this session.")

    fig = px.bar(
        comp, x="LapNumber", y="PaceDelta_s",
        title=f"Pace delta: {d1} vs {d2} (positive = {d1} faster)",
        labels={"PaceDelta_s": "Delta (s)", "LapNumber": "Lap"},
        color="PaceDelta_s",
        color_continuous_scale=["#E10600", "#8A8FA3", "#00D2C6"],
        color_continuous_midpoint=0,  # zero must sit at the midpoint regardless of the data's own min/max,
                                       # otherwise two same-sign deltas can render as opposite colors
    )
    fig.update_layout(template=PLOT_TEMPLATE, height=450)
    st.plotly_chart(fig, width='stretch', theme=None)


# =============================================================================
# VIEW: SESSION RESULTS — final classification for a session that has
# already happened. FastF1's session.results carries TeamColor directly, so
# these accents are the *real* per-event colour, not the static fallback map.
# =============================================================================
def render_results_view(engine, session_type):
    st.markdown("<div class='pw-section-label'>Session Results</div>", unsafe_allow_html=True)
    results = engine.session.results

    if results is None or results.empty:
        st.info("No official results available for this session.")
        return

    if session_type in QUALI_TYPES:
        rows = []
        for _, r in results.sort_values('Position').iterrows():
            chip = hex_color(r.get('TeamColor'))
            rows.append(
                f"<tr><td class='mono'>{int(r['Position']) if pd.notna(r['Position']) else '-'}</td>"
                f"<td><span class='team-chip' style='background:{chip};'></span>"
                f"<b>{r.get('Abbreviation','')}</b> <span class='muted'>{r.get('TeamName','')}</span></td>"
                f"<td class='mono'>{fmt_td(r.get('Q1'))}</td>"
                f"<td class='mono'>{fmt_td(r.get('Q2'))}</td>"
                f"<td class='mono'>{fmt_td(r.get('Q3'))}</td></tr>"
            )
        render_html_table(["Pos", "Driver", "Q1", "Q2", "Q3"], rows)

    elif session_type in ("R", "S"):
        rows = []
        for _, r in results.sort_values('Position').iterrows():
            chip = hex_color(r.get('TeamColor'))
            rows.append(
                f"<tr><td class='mono'>{int(r['Position']) if pd.notna(r['Position']) else '-'}</td>"
                f"<td><span class='team-chip' style='background:{chip};'></span>"
                f"<b>{r.get('Abbreviation','')}</b> <span class='muted'>{r.get('TeamName','')}</span></td>"
                f"<td>{r.get('Status','')}</td>"
                f"<td class='mono'>{fmt_td(r.get('Time'))}</td>"
                f"<td class='mono'>{r.get('Points', 0)}</td></tr>"
            )
        render_html_table(["Pos", "Driver", "Status", "Time", "Pts"], rows)

    else:
        # Practice sessions have no official classification — rank by best clean lap instead.
        st.caption("Practice sessions aren't officially classified — ranked here by best clean lap.")
        best_laps = (
            engine.clean_laps.groupby('Driver')['LapTimeSeconds'].min()
            .sort_values().reset_index()
        )
        team_lookup = results.set_index('Abbreviation')['TeamColor'].to_dict() if 'Abbreviation' in results.columns else {}
        team_name_lookup = results.set_index('Abbreviation')['TeamName'].to_dict() if 'Abbreviation' in results.columns else {}
        rows = []
        for i, row in best_laps.iterrows():
            chip = hex_color(team_lookup.get(row['Driver']))
            team = team_name_lookup.get(row['Driver'], '')
            rows.append(
                f"<tr><td class='mono'>{i+1}</td>"
                f"<td><span class='team-chip' style='background:{chip};'></span>"
                f"<b>{row['Driver']}</b> <span class='muted'>{team}</span></td>"
                f"<td class='mono'>{round(row['LapTimeSeconds'], 3)}s</td></tr>"
            )
        render_html_table(["Pos", "Driver", "Best Lap"], rows)


# =============================================================================
# VIEW: CHAMPIONSHIP STANDINGS (WDC + Constructors, via Ergast)
# =============================================================================
def render_standings_view(year):
    st.markdown("<div class='pw-section-label'>Championship Standings</div>", unsafe_allow_html=True)
    try:
        drivers_df, constructors_df = get_standings(year)
    except Exception as e:
        st.warning(f"Couldn't fetch standings for {year}: {e}")
        return

    if drivers_df is None or constructors_df is None:
        st.info(f"No standings data available yet for {year}.")
        return

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<p style='color:var(--text-muted); font-weight:700; letter-spacing:0.5px;'>DRIVERS</p>", unsafe_allow_html=True)
        rows = []
        for _, r in drivers_df.iterrows():
            team = r.get('constructorNames', [''])[0] if isinstance(r.get('constructorNames'), list) else r.get('constructorNames', '')
            chip = TEAM_COLOR_FALLBACK.get(team, "#8A8FA3")
            rows.append(
                f"<tr><td class='mono'>{r.get('position','')}</td>"
                f"<td><span class='team-chip' style='background:{chip};'></span>"
                f"<b>{r.get('givenName','')} {r.get('familyName','')}</b></td>"
                f"<td class='mono'>{r.get('points','')}</td></tr>"
            )
        render_html_table(["Pos", "Driver", "Pts"], rows)

    with col_b:
        st.markdown("<p style='color:var(--text-muted); font-weight:700; letter-spacing:0.5px;'>CONSTRUCTORS</p>", unsafe_allow_html=True)
        rows = []
        for _, r in constructors_df.iterrows():
            chip = TEAM_COLOR_FALLBACK.get(r.get('constructorName', ''), "#8A8FA3")
            rows.append(
                f"<tr><td class='mono'>{r.get('position','')}</td>"
                f"<td><span class='team-chip' style='background:{chip};'></span>"
                f"<b>{r.get('constructorName','')}</b></td>"
                f"<td class='mono'>{r.get('points','')}</td></tr>"
            )
        render_html_table(["Pos", "Constructor", "Pts"], rows)
    st.caption("Standings via Ergast — team colours are an approximate reference map, not live per-event data.")


if active_view == VIEWS[0]:
    render_telemetry_view(engine, session_type)
elif active_view == VIEWS[1]:
    render_strategy_view(engine)
elif active_view == VIEWS[2]:
    render_headtohead_view(engine)
elif active_view == VIEWS[3]:
    render_results_view(engine, session_type)
else:
    render_standings_view(year)