import os
import fastf1
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="F1 Pitwall Strategy App",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Titillium+Web:wght@400;600;700;900&family=JetBrains+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Titillium Web', sans-serif;
    }

    .stApp {
        background-color: #15151e;
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background-color: #1f1f27;
        border-right: 1px solid #2e2e38;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .f1-header {
        background: linear-gradient(135deg, #e10600 0%, #a80400 100%);
        padding: 20px 30px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(225, 6, 0, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .f1-title {
        font-size: 32px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 0;
        color: #ffffff;
        text-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }
    
    .f1-badge {
        background-color: #000000;
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 14px;
        border: 1px solid #383844;
        text-transform: uppercase;
    }

    .stMetric {
        background-color: #1f1f27;
        border: 1px solid #2e2e38;
        border-left: 4px solid #e10600;
        padding: 15px;
        border-radius: 8px;
    }

    div[data-baseweb="tab-list"] {
        background-color: #1f1f27;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #2e2e38;
        gap: 8px;
    }

    div[data-baseweb="tab"] {
        border-radius: 6px;
        color: #a0a0b0;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 14px;
        padding: 10px 20px;
    }

    div[aria-selected="true"] {
        background-color: #e10600 !important;
        color: #ffffff !important;
    }

    .stButton>button {
        background-color: #e10600;
        color: white;
        font-weight: 700;
        border: none;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background-color: #ff1e15;
        box-shadow: 0 4px 12px rgba(225, 6, 0, 0.4);
    }

    [data-testid="stDataFrame"] {
        background-color: #1f1f27;
        border: 1px solid #2e2e38;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

if not os.path.exists('cache_dir'):
    os.makedirs('cache_dir')

fastf1.Cache.enable_cache('cache_dir')

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
        return ["R", "Q", "FP1", "FP2", "FP3"]
    
    event_format = event.iloc[0]['EventFormat']
    
    if event_format in ['sprint', 'sprint_shootout', 'sprint_qualifying']:
        return ["R", "Q", "S", "SQ", "FP1"]
    else:
        return ["R", "Q", "FP1", "FP2", "FP3"]

@st.cache_resource(show_spinner=False)
def load_f1_session(year: int, grand_prix: str, session_type: str = 'R'):
    session = fastf1.get_session(year, grand_prix, session_type)
    session.load()
    
    laps = session.laps.copy()
    laps['LapTimeSeconds'] = laps['LapTime'].dt.total_seconds()
    clean_laps = laps.pick_accurate().pick_wo_box()
    
    return session, laps, clean_laps

st.sidebar.markdown("<h2 style='color: #e10600; font-weight: 900; letter-spacing: 1px;'>PITWALL CONTROL</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

years = list(range(2026, 2017, -1))
selected_year = st.sidebar.selectbox("SEASON", years, index=1)

available_gps = get_season_schedule(selected_year)
selected_gp = st.sidebar.selectbox("GRAND PRIX", available_gps, index=0)

available_sessions = get_available_sessions(selected_year, selected_gp)
selected_session = st.sidebar.selectbox("SESSION", available_sessions, index=0)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
load_btn = st.sidebar.button("LOAD SESSION DATA", use_container_width=True)

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if load_btn or not st.session_state.data_loaded:
    with st.spinner("Connecting to telemetry feed..."):
        try:
            session, laps, clean_laps = load_f1_session(selected_year, selected_gp, selected_session)
            st.session_state.session = session
            st.session_state.laps = laps
            st.session_state.clean_laps = clean_laps
            st.session_state.drivers = sorted(laps['Driver'].unique().tolist())
            st.session_state.current_gp = selected_gp
            st.session_state.current_year = selected_year
            st.session_state.current_session = selected_session
            st.session_state.data_loaded = True
        except Exception as e:
            st.error(f"Telemetry error: {e}")
            st.stop()

st.markdown(f"""
<div class="f1-header">
    <div>
        <div class="f1-title">{st.session_state.current_gp}</div>
        <div style="color: #d0d0d0; font-size: 14px; font-weight: 600; margin-top: 4px;">OFFICIAL TELEMETRY & STRATEGY HUB</div>
    </div>
    <div>
        <span class="f1-badge">{st.session_state.current_year}</span>
        <span class="f1-badge" style="background-color: #e10600; border: none; margin-left: 6px;">{st.session_state.current_session}</span>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["TELEMETRY & DEGRADATION", "PIT STRATEGY SIMULATOR", "HEAD-TO-HEAD PACE"])

plot_template = {
    "layout": {
        "paper_bgcolor": "#1f1f27",
        "plot_bgcolor": "#1f1f27",
        "font": {"color": "#ffffff", "family": "Titillium Web"},
        "xaxis": {"gridcolor": "#2e2e38", "zerolinecolor": "#2e2e38"},
        "yaxis": {"gridcolor": "#2e2e38", "zerolinecolor": "#2e2e38"}
    }
}

with tab1:
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown("<h4 style='color: #e10600; font-weight: 700;'>DRIVER SELECTION</h4>", unsafe_allow_html=True)
        selected_driver = st.selectbox("DRIVER", st.session_state.drivers, index=0)
        fuel_correction = st.slider("Fuel Correction (s/lap):", min_value=0.00, max_value=0.08, value=0.035, step=0.005)
        
        drv_laps = st.session_state.clean_laps[st.session_state.clean_laps['Driver'] == selected_driver]
        stint_summary = []
        
        for (stint, compound), group in drv_laps.groupby(['Stint', 'Compound']):
            if len(group) >= 3:
                x = group['LapNumber'].values
                y_raw = group['LapTimeSeconds'].values
                y_corr = y_raw + (x * fuel_correction)
                
                raw_deg, _ = np.polyfit(x, y_raw, 1)
                corr_deg, _ = np.polyfit(x, y_corr, 1)
                
                stint_summary.append({
                    "Stint": int(stint),
                    "Compound": compound,
                    "Laps": len(group),
                    "Raw Deg": f"{round(raw_deg, 3)}s",
                    "Corr Deg": f"{round(corr_deg, 3)}s"
                })
        
        st.markdown("<br><h4 style='color: #e10600; font-weight: 700;'>STINT SUMMARY</h4>", unsafe_allow_html=True)
        if stint_summary:
            st.dataframe(pd.DataFrame(stint_summary), hide_index=True, use_container_width=True)
        else:
            st.info("No clean stint data available.")

    with col2:
        if not drv_laps.empty:
            fig_laps = px.line(
                drv_laps, 
                x="LapNumber", 
                y="LapTimeSeconds", 
                color="Stint",
                markers=True,
                title=f"LAP TIME EVOLUTION — {selected_driver}",
                labels={"LapNumber": "LAP", "LapTimeSeconds": "LAP TIME (s)", "Stint": "STINT"}
            )
            fig_laps.update_layout(template=plot_template, height=480)
            st.plotly_chart(fig_laps, use_container_width=True)

with tab2:
    col_sim1, col_sim2 = st.columns([1, 2])
    
    with col_sim1:
        st.markdown("<h4 style='color: #e10600; font-weight: 700;'>SIMULATION CONFIG</h4>", unsafe_allow_html=True)
        sim_driver = st.selectbox("TARGET DRIVER", st.session_state.drivers, index=0, key="sim_drv")
        
        pit_laps_df = st.session_state.laps[
            (st.session_state.laps['Driver'] == sim_driver) & 
            (st.session_state.laps['PitInTime'].notna())
        ]
        
        actual_pits = pit_laps_df['LapNumber'].astype(int).tolist()
        default_actual_pit = actual_pits[0] if actual_pits else 20
        
        actual_pit_lap = st.number_input("ACTUAL PIT LAP:", min_value=1, max_value=70, value=int(default_actual_pit))
        target_pit_lap = st.number_input("SIMULATED PIT LAP:", min_value=1, max_value=70, value=max(1, actual_pit_lap - 3))
        pit_loss = st.number_input("BASELINE PIT LOSS (s):", value=20.0, step=0.5)
        
        run_sim = st.button("RUN SIMULATION", use_container_width=True)

    with col_sim2:
        drv_clean = st.session_state.clean_laps[st.session_state.clean_laps['Driver'] == sim_driver].sort_values('LapNumber')
        
        if drv_clean.empty:
            st.warning("Insufficient telemetry for simulation.")
        else:
            start_l = min(actual_pit_lap, target_pit_lap) - 1
            end_l = max(actual_pit_lap, target_pit_lap) + 2
            window = drv_clean[(drv_clean['LapNumber'] >= start_l) & (drv_clean['LapNumber'] <= end_l)]
            
            if window.empty or len(window) < 2:
                fresh_pace = drv_clean['LapTimeSeconds'].min()
                degr_pace = drv_clean['LapTimeSeconds'].median()
            else:
                fresh_pace = np.percentile(window['LapTimeSeconds'], 20)
                degr_pace = np.percentile(window['LapTimeSeconds'], 80)
            
            tyre_delta = float(np.clip(degr_pace - fresh_pace, 0.4, 3.5))
            lap_diff = actual_pit_lap - target_pit_lap
            total_gain = lap_diff * tyre_delta
            
            m1, m2, m3 = st.columns(3)
            m1.metric("STRATEGY TYPE", "UNDERCUT" if lap_diff > 0 else ("OVERCUT" if lap_diff < 0 else "NEUTRAL"))
            m2.metric("TYRE DELTA / LAP", f"{round(tyre_delta, 3)} s")
            m3.metric("NET TIME ADVANTAGE", f"{round(total_gain, 2)} s", delta=f"{round(total_gain, 2)} s")
            
            fig_sim = go.Figure()
            
            fig_sim.add_trace(go.Scatter(
                x=drv_clean['LapNumber'], y=drv_clean['LapTimeSeconds'],
                mode='lines+markers', name='Actual Lap Times',
                line=dict(color='#a0a0b0', dash='dash')
            ))
            
            fig_sim.add_vline(x=actual_pit_lap, line_width=2, line_dash="solid", line_color="#e10600", annotation_text="Actual Pit")
            fig_sim.add_vline(x=target_pit_lap, line_width=2, line_dash="dot", line_color="#00d2be", annotation_text="Simulated Pit")
            
            fig_sim.update_layout(
                title=f"PIT WINDOW DELTA ANALYSIS ({sim_driver})",
                xaxis_title="LAP", yaxis_title="LAP TIME (s)",
                template=plot_template, height=400
            )
            st.plotly_chart(fig_sim, use_container_width=True)

with tab3:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        d1 = st.selectbox("DRIVER A", st.session_state.drivers, index=0)
    with col_p2:
        d2 = st.selectbox("DRIVER B", st.session_state.drivers, index=min(1, len(st.session_state.drivers)-1))
        
    if d1 != d2:
        laps_a = st.session_state.clean_laps[st.session_state.clean_laps['Driver'] == d1][['LapNumber', 'LapTimeSeconds']]
        laps_b = st.session_state.clean_laps[st.session_state.clean_laps['Driver'] == d2][['LapNumber', 'LapTimeSeconds']]
        
        comp = pd.merge(laps_a, laps_b, on='LapNumber', suffixes=(f'_{d1}', f'_{d2}'))
        comp['Delta_s'] = comp[f'LapTimeSeconds_{d2}'] - comp[f'LapTimeSeconds_{d1}']
        
        fig_comp = px.bar(
            comp, x="LapNumber", y="Delta_s",
            title=f"PACE DELTA: {d1} vs {d2} (Positive = {d1} Faster)",
            labels={"Delta_s": "DELTA (SECONDS)", "LapNumber": "LAP"},
            color="Delta_s", color_continuous_scale="RdYlGn"
        )
        fig_comp.update_layout(template=plot_template, height=450)
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.warning("Select two different drivers to perform head-to-head comparison.")