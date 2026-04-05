"""
app.py  ─  HyPER AgEnT: Spectral Life Simulator
==================================================
The complete Streamlit frontend, perfectly wired to:
  consciousness.py  →  HarmonicResonanceConsciousness, CognitionMode, ACTIONS, K_DIM, E
  agents.py         →  BioHyperAgent, to_dict(), soul_freqs, brain, action_counts, ...
  world.py          →  World, resources[x,y,r], artifacts, world_knowledge, events
  civilization.py   →  CivilizationManager, TechTree, Tribe
  evolution.py      →  EvolutionEngine, get_stats(), top_agents(), pop/energy/inv history

Run:  streamlit run app.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import time

# ── Page must be very first Streamlit call ────────────────────────────────────
st.set_page_config(
    page_title="HyPER AgEnT",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS  ─  deep-space dark theme
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
html, body, [class*="css"], .stApp, .main .block-container {
    background-color: #04040e !important;
    color: #c4c4d4 !important;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
}
h1 { color: #7DF9FF !important; letter-spacing: 2px; }
h2 { color: #9DECFF !important; }
h3 { color: #aef !important; font-size: 1em !important; letter-spacing: 1px; }

[data-testid="stSidebar"] {
    background: #080818 !important;
    border-right: 1px solid #1a1a3a;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #7DF9FF !important; }

[data-testid="stMetricValue"] {
    color: #7DF9FF !important;
    font-family: monospace;
    font-size: 1.3em !important;
    font-weight: bold;
}
[data-testid="stMetricLabel"] { color: #556 !important; font-size: 0.72em !important; }

.stTabs [data-baseweb="tab-list"] {
    background: #0a0a1e; border-radius: 8px; padding: 2px; gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    color: #556 !important; background: transparent !important;
    border-radius: 6px; padding: 6px 14px; font-size: 0.78em; letter-spacing: 0.5px;
}
.stTabs [aria-selected="true"] {
    color: #7DF9FF !important;
    background: #0d1a2e !important;
    border-bottom: 2px solid #7DF9FF !important;
}

.stButton > button {
    background: #0d1a2e !important; border: 1px solid #7DF9FF44 !important;
    color: #7DF9FF !important; border-radius: 6px !important;
    font-family: monospace !important; font-size: 0.82em !important;
    transition: all 0.15s;
}
.stButton > button:hover {
    background: #112244 !important; border-color: #7DF9FF !important;
    box-shadow: 0 0 8px #7DF9FF44;
}

.stSelectbox > div > div, .stSlider > div { background: #0a0a1e !important; }
label { color: #778 !important; font-size: 0.78em !important; }
hr { border-color: #1a1a3a !important; }

.kpi-card {
    background: #08081a; border: 1px solid #1a1a3a; border-radius: 8px;
    padding: 10px 14px; margin: 3px 0; font-family: monospace; font-size: 11px;
}
.agent-card {
    background: #08081a; border-left: 3px solid #7DF9FF;
    border-radius: 0 6px 6px 0; padding: 5px 10px; margin: 2px 0;
    font-family: monospace; font-size: 10.5px; color: #aab;
}
.event-line {
    background: #06060f; border-radius: 4px; padding: 2px 8px;
    margin: 1px 0; font-family: monospace; font-size: 10px;
}
.section-title {
    color: #7DF9FF; font-size: 0.82em; letter-spacing: 2px;
    text-transform: uppercase; border-bottom: 1px solid #1a1a3a;
    padding-bottom: 4px; margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIMULATION BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def build_simulation(seed: int = 42, world_size: int = 60):
    from world        import World
    from civilization import CivilizationManager
    from evolution    import EvolutionEngine
    world  = World(size=world_size, seed=seed)
    civ    = CivilizationManager(world_size=world_size)
    engine = EvolutionEngine(world_size=world_size, seed=seed)
    engine.initialize()
    return world, civ, engine


def _init_state():
    defaults = dict(ready=False, seed=42, world_size=60, auto_run=False, speed=3)
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

if not st.session_state.ready:
    with st.spinner("🌌 Igniting Spectral Life Field …"):
        world, civ, engine = build_simulation(
            seed=st.session_state.seed,
            world_size=st.session_state.world_size,
        )
        st.session_state.world  = world
        st.session_state.civ    = civ
        st.session_state.engine = engine
        st.session_state.ready  = True

W  = st.session_state.world
C  = st.session_state.civ
EN = st.session_state.engine


def run_steps(n: int):
    for _ in range(n):
        EN.process_step(W, C)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS  (match backend enums exactly)
# ══════════════════════════════════════════════════════════════════════════════
MODE_COLOR = {
    'explore':'#7DF9FF','survive':'#FF4455','socialize':'#98FB98',
    'invent':'#FFD700','reproduce':'#FF69B4','dominate':'#FF6600','meditate':'#9370DB',
}
MODE_ICON = {
    'explore':'🔍','survive':'🛡','socialize':'💬','invent':'💡',
    'reproduce':'❤','dominate':'⚔','meditate':'🧘',
}
EMOTION_NAMES  = ['Curiosity','Fear','Joy','Anger','Affection','Grief','Wonder']
EMOTION_COLORS = ['#7DF9FF','#FF4455','#FFD700','#FF6600','#FF69B4','#9370DB','#00FF88']
TECH_COLOR = {
    'physics':'#7DF9FF','tool':'#FFD700','language':'#98FB98',
    'math':'#DDA0DD','ideology':'#FF8C00','legacy':'#888','unknown':'#555',
}
TECH_ICON = {
    'physics':'⚛','tool':'🔧','language':'📜','math':'∑',
    'ideology':'🧠','legacy':'👻','unknown':'?',
}
EVT_COLOR = {
    'war':'#FF4455','alliance':'#44FF88','invention':'#FFD700',
    'new_tribe':'#7DF9FF','extinction':'#FF8800','abundance':'#98FB98',
    'scarcity':'#FF6600','anomaly':'#DDA0DD','plague':'#FF4455',
    'breakthrough':'#00FF88','schism':'#FF8C00',
}
R_COLORS = ['#44FF88','#FFD700','#DDA0DD','#FF8C00']
R_NAMES  = ['Food','Energy Crystal','Knowledge Ore','Rare Element']


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("#  HyPER AgEnT")
    st.markdown(
        "<div style='color:#334;font-size:0.72em;letter-spacing:1px;'>"
        "SPECTRAL LIFE · 96 HYPERAGENTS · K=32<br>"
        "HRC + Metacognition · Zero LLM"
        "</div>", unsafe_allow_html=True
    )
    st.divider()

    c1, c2, c3 = st.columns(3)
    step1  = c1.button("▶ ×1",   use_container_width=True)
    step10 = c2.button("▶▶ ×10", use_container_width=True)
    step50 = c3.button("×50",    use_container_width=True)

    auto = st.toggle("⚡ Auto-run", value=st.session_state.auto_run)
    st.session_state.auto_run = auto
    spd  = st.slider("Steps / frame", 1, 30, st.session_state.speed, key='spd_sl')
    st.session_state.speed = spd

    if st.button("🔄 Full Reset", use_container_width=True):
        build_simulation.clear()
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    with st.expander("⚙ Config"):
        new_seed = st.number_input("Seed", 0, 9999, st.session_state.seed)
        new_size = st.selectbox("World size", [40, 60, 80], index=1)
        if st.button("Rebuild"):
            build_simulation.clear()
            st.session_state.seed       = new_seed
            st.session_state.world_size = new_size
            st.session_state.ready      = False
            st.rerun()

    st.divider()

    # Pull live data for sidebar
    alive_agents = [a for a in EN.agents.values() if a.alive]
    n_alive      = len(alive_agents)
    estats       = EN.get_stats()
    cstats       = C.get_stats()

    st.markdown("### 🧬 Population")
    k1, k2 = st.columns(2)
    k1.metric("Alive",  n_alive)
    k2.metric("Gen",    estats.get('max_generation', 0))
    k1.metric("Born",   estats.get('total_born', 0))
    k2.metric("Died",   estats.get('total_died', 0))
    k1.metric("Avg E",  f"{estats.get('avg_energy',0):.2f}")
    k2.metric("MaxAge", estats.get('max_age', 0))

    st.markdown("### 🏛 Civilization")
    k1, k2 = st.columns(2)
    k1.metric("Tribes",   cstats.get('n_tribes', 0))
    k2.metric("⚔ Wars",  cstats.get('active_wars', 0))
    k1.metric("🤝 Ally",  cstats.get('active_alliances', 0))
    k2.metric("💡 Inv",   cstats.get('total_inventions', 0))
    k1.metric("Extinct",  cstats.get('extinctions', 0))
    k2.metric("Tech×",    f"{cstats.get('tech_bonus',1):.3f}")

    st.metric("⏱ Tick", W.step_count)

    # Mini population sparkline wired to EN.pop_history
    pop_h = estats.get('pop_history', [])
    if len(pop_h) > 3:
        mini = go.Figure(go.Scatter(
            y=pop_h, mode='lines',
            line=dict(color='#7DF9FF', width=1.5),
            fill='tozeroy', fillcolor='rgba(125,249,255,0.06)',
        ))
        mini.update_layout(
            paper_bgcolor='#06060f', plot_bgcolor='#06060f',
            height=65, margin=dict(l=0,r=0,t=0,b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
        )
        st.plotly_chart(mini, use_container_width=True, key='mini_pop')


# ── Execute steps ─────────────────────────────────────────────────────────────
if step1:  run_steps(1)
if step10: run_steps(10)
if step50: run_steps(50)
if auto:
    run_steps(st.session_state.speed)
    time.sleep(0.05)
    st.rerun()

# Re-pull after potential steps
alive_agents = [a for a in EN.agents.values() if a.alive]
n_alive      = len(alive_agents)
estats       = EN.get_stats()
cstats       = C.get_stats()


# ══════════════════════════════════════════════════════════════════════════════
# HEADLINE + KPI STRIP
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"<h1 style='margin-bottom:0;padding-bottom:2px;'> HyPER AgEnT</h1>"
    f"<div style='color:#223;font-size:0.74em;font-family:monospace;padding-bottom:10px;'>"
    f"tick {W.step_count:,} &nbsp;·&nbsp; {n_alive} alive "
    f"&nbsp;·&nbsp; {cstats.get('n_tribes',0)} tribes "
    f"&nbsp;·&nbsp; ⚔ {cstats.get('active_wars',0)} wars "
    f"&nbsp;·&nbsp; 🤝 {cstats.get('active_alliances',0)} alliances "
    f"&nbsp;·&nbsp; 💡 {cstats.get('total_inventions',0)} inventions "
    f"&nbsp;·&nbsp; Gen {estats.get('max_generation',0)}"
    f"&nbsp;·&nbsp; 🧠 {estats.get('total_meta_inv',0)} meta-inv"
    f"&nbsp;·&nbsp; 🌋 {estats.get('n_cambrian',0)} cambrian"
    f"</div>",
    unsafe_allow_html=True
)

wstats = W.get_stats()
m = st.columns(12)
m[0].metric("🧬 Alive",     n_alive)
m[1].metric("🐣 Born",      estats.get('total_born', 0))
m[2].metric("💀 Died",      estats.get('total_died', 0))
m[3].metric("⚡ Avg E",     f"{estats.get('avg_energy',0):.2f}")
m[4].metric("🔬 Inventions",estats.get('total_inv', 0))
m[5].metric("⚔ Kills",     estats.get('total_kills', 0))
m[6].metric("❤ Children",  estats.get('total_kids', 0))
m[7].metric("🧠 Meta-Inv",  estats.get('total_meta_inv', 0))
m[8].metric("🔮 Clades",    estats.get('n_clades', 0))
m[9].metric("📡 Tech×",    f"{cstats.get('tech_bonus',1):.4f}")
m[10].metric("🧲 Bonds",   wstats.get('n_bonds', 0))
m[11].metric("🌀 Season",   wstats.get('season', 'Summer'))


st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# MAIN NAVIGATION (Lazy-Loaded Button Routing)
# ══════════════════════════════════════════════════════════════════════════════
tab_names = [
    "🌍 WORLD MAP", "🧬 AGENTS", "🏛 CIVILIZATION", "💡 TECH TREE",
    "📊 ANALYTICS", "🔬 HRC BRAIN", "📡 EVENTS FEED", "🗺 RESOURCES",
    "🧠 META-MIND", "🔬 KNOWLEDGE",
    "🧬 v3.0 EMERGENCE",  # NEW: All 30 v3.0 features dashboard
]


if 'active_tab' not in st.session_state:
    st.session_state.active_tab = tab_names[0]

btn_cols = st.columns(len(tab_names))
for i, t_name in enumerate(tab_names):
    if btn_cols[i].button(t_name, use_container_width=True):
        st.session_state.active_tab = t_name
        st.rerun()

st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1  ─  WORLD MAP
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 1  ─  WORLD MAP
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.active_tab == "🌍 WORLD MAP":
    map_col, info_col = st.columns([2.8, 1])

    with map_col:
        st.markdown(
            "<div class='section-title'>Live World · Toroidal Field · Agents + Artifacts</div>",
            unsafe_allow_html=True
        )

        fig_map = go.Figure()

        # Background: W.resource_heatmap() → sum of all 4 resource layers
        res_grid = W.resource_heatmap()   # ndarray (size, size)
        fig_map.add_trace(go.Heatmap(
            z=res_grid.T,
            colorscale=[
                [0.00,'#02020a'],[0.25,'#061422'],
                [0.55,'#082818'],[0.80,'#0e4020'],[1.00,'#18682a'],
            ],
            showscale=False, opacity=0.90, hoverinfo='skip',
        ))

        # Artifacts: W.artifact_positions() → (xs, ys), W.artifacts[(x,y)] → dict
        art_xs, art_ys = W.artifact_positions()
        if art_xs:
            art_meta   = [W.artifacts.get((x, y), {}) for x, y in zip(art_xs, art_ys)]
            art_types  = [a.get('type','unknown') for a in art_meta]
            art_names  = [a.get('name','?')       for a in art_meta]
            art_colors = [TECH_COLOR.get(t,'#888') for t in art_types]
            art_hover  = [
                f"<b>{n}</b><br>Type: {t}<br>Creator: {a.get('creator','?')}<br>({x},{y})"
                for n, t, a, x, y in zip(art_names, art_types, art_meta, art_xs, art_ys)
            ]
            fig_map.add_trace(go.Scatter(
                x=art_xs, y=art_ys, mode='markers',
                marker=dict(symbol='star-dot', size=7,
                            color=art_colors, opacity=0.75,
                            line=dict(width=0.5, color='rgba(255,255,255,0.2)')),
                name='Artifacts',
                text=art_hover,
                hovertemplate='%{text}<extra></extra>',
            ))

        # Agents: BioHyperAgent.to_dict() gives id,x,y,energy,health,age,generation,
        #         tribe,mode,last_action,reputation,inventions,absorbed,kills,children,
        #         color,r,g,b,curiosity,wonder,fear
        if alive_agents:
            dicts = [a.to_dict() for a in alive_agents]
            df_ag = pd.DataFrame(dicts)
            sizes = np.clip(df_ag['energy'].values * 1.7, 5, 18).tolist()
            hover_texts = []
            for r in dicts:
                mi = MODE_ICON.get(r['mode'], '?')
                hover_texts.append(
                    f"<b>{r['id']}</b>  [{r['tribe']}] 🎭{r.get('role','?')}<br>"
                    f"{mi} {r['mode'].upper()}<br>"
                    f"E:{r['energy']}  hp:{r['health']:.2f}  age:{r['age']}  gen:{r['generation']}<br>"
                    f"💡{r['inventions']} ❤{r['children']} ⚔{r['kills']}  rep:{r['reputation']:+.1f}<br>"
                    f"cur:{r['curiosity']:.2f} wdr:{r['wonder']:.2f} fear:{r['fear']:.2f}<br>"
                    f"Φ:{r.get('phi',0):.3f} 🔄:{r.get('trade_count',0)} inv:{r.get('inventory','')}<br>"
                    f"last: {r['last_action']}"
                )

            fig_map.add_trace(go.Scatter(
                x=df_ag['x'], y=df_ag['y'],
                mode='markers',
                marker=dict(size=sizes, color=df_ag['color'].tolist(),
                            opacity=0.92,
                            line=dict(width=0.6, color='rgba(255,255,255,0.15)')),
                text=hover_texts,
                hovertemplate='%{text}<extra></extra>',
                name='Agents',
            ))

        fig_map.update_layout(
            paper_bgcolor='#04040e', plot_bgcolor='#04040e',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[-0.5, W.size+0.5]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[-0.5, W.size+0.5], scaleanchor='x', scaleratio=1),
            height=540, margin=dict(l=0,r=0,t=0,b=0),
            showlegend=True,
            legend=dict(x=0.01, y=0.99, font=dict(color='#556',size=9),
                        bgcolor='rgba(0,0,0,0.5)', bordercolor='#1a1a3a'),
        )
        st.plotly_chart(fig_map, use_container_width=True, key='world_map')

        # Population + Energy dual-axis sparklines
        pop_h = estats.get('pop_history', [])
        eng_h = estats.get('energy_history', [])
        if len(pop_h) > 4:
            xs = list(range(len(pop_h)))
            fig_hist = make_subplots(specs=[[{"secondary_y": True}]])
            fig_hist.add_trace(go.Scatter(
                x=xs, y=pop_h, name='Population',
                mode='lines', line=dict(color='#7DF9FF', width=1.5),
                fill='tozeroy', fillcolor='rgba(125,249,255,0.06)',
            ), secondary_y=False)
            if eng_h:
                fig_hist.add_trace(go.Scatter(
                    x=xs, y=eng_h, name='Avg Energy',
                    mode='lines', line=dict(color='#FFD700', width=1, dash='dot'),
                ), secondary_y=True)
            fig_hist.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=110, margin=dict(l=30,r=30,t=4,b=0),
                xaxis=dict(showgrid=False, showticklabels=False, color='#223'),
                yaxis=dict(gridcolor='#0d0d1e', color='#446', title='Pop'),
                yaxis2=dict(color='rgba(255, 215, 0, 0.4)', title='Energy'),
                legend=dict(font=dict(size=8,color='#445'), x=0.01, y=0.99,
                            bgcolor='rgba(0,0,0,0)'),
                font=dict(color='#334', size=9),
            )
            st.plotly_chart(fig_hist, use_container_width=True, key='pop_hist_map')

    with info_col:
        st.markdown("<div class='section-title'>World Events</div>", unsafe_allow_html=True)
        for evt in reversed(W.get_recent_events(12)):
            ec = EVT_COLOR.get(evt.get('type',''), '#446')
            pos = evt.get('pos', ('?','?'))
            st.markdown(
                f"<div class='event-line' style='color:{ec}'>"
                f"[{evt['step']}] {evt['desc']}</div>",
                unsafe_allow_html=True
            )

        st.divider()
        st.markdown("<div class='section-title'>Civ Events</div>", unsafe_allow_html=True)
        for evt in reversed(C.get_recent_events(18)):
            ec = EVT_COLOR.get(evt.get('type',''), '#446')
            st.markdown(
                f"<div class='event-line' style='color:{ec}'>"
                f"[{evt['step']}] {evt['desc']}</div>",
                unsafe_allow_html=True
            )

        st.divider()
        # World knowledge from W.world_knowledge dict
        wk = W.world_knowledge
        st.markdown("<div class='section-title'>World Knowledge</div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='kpi-card'>"
            f"<span style='color:#7DF9FF'>{len(wk)}</span> concepts in world field<br>"
            + "<br>".join(
                f"<span style='color:#334'>{n}</span>"
                for n in list(wk.keys())[-8:]
            ) + "</div>",
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2  ─  AGENTS
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 2  ─  AGENTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "🧬 AGENTS":
    st.markdown(
        "<div class='section-title'>BioHyperAgent Census · Live Population</div>",
        unsafe_allow_html=True
    )

    if not alive_agents:
        st.warning("No agents alive.")
    else:
        sc1, sc2 = st.columns([2, 2])
        sort_key = sc1.selectbox(
            "Sort by",
            ['energy','age','inventions','kills','children','reputation','wonder',
             'meta_inv','eigenspread'],
            key='ag_sort',
        )
        n_show = sc2.slider("Show top N", 10, min(80, n_alive), 30, key='ag_n')

        # EN.top_agents uses BioHyperAgent.to_dict() and sorts by requested key
        top_list = EN.top_agents(sort_key, n=n_show)

        table_col, chart_col = st.columns([3, 1])

        with table_col:
            rows_html = []
            for r in top_list:
                mi  = MODE_ICON.get(r['mode'], '?')
                mc  = MODE_COLOR.get(r['mode'], '#7DF9FF')
                ebar = '|' * min(10, int(r['energy']))
                rows_html.append(
                    f"<div class='agent-card' style='border-left-color:{r['color']}'>"
                    f"<span style='color:{r['color']};font-weight:bold'>{r['id']}</span> "
                    f"<span style='color:#334'>[{r['tribe']}]</span>  "
                    f"<span style='color:{mc}'>{mi}{r['mode'][:4]}</span>  "
                    f"<span style='color:#7DF9FF'>{ebar}</span> {r['energy']:.1f}e  "
                    f"hp:{r['health']:.2f} age:{r['age']} gen:{r['generation']}<br>"
                    f"<span style='color:#334'>last:{r['last_action']:<18} "
                    f"💡{r['inventions']} ❤{r['children']} ⚔{r['kills']} "
                    f"rep:{r['reputation']:+.1f} 📦{r['absorbed']}</span><br>"
                    f"<span style='color:#FF8C00'>⚙ meta-inv:{r.get('meta_inventions',0)} "
                    f"composed:{r.get('composed_actions',0)} "
                    f"eigen:{r.get('meta_eigenspread',0):.3f}</span><br>"
                    f"<span style='color:#aef'>🎭{r.get('role','?')} "
                    f"Φ:{r.get('phi',0):.3f} "
                    f"🔄:{r.get('trade_count',0)} "
                    f"inv:{r.get('inventory','-')}</span>"
                    f"</div>"
                )

            st.markdown("\n".join(rows_html), unsafe_allow_html=True)

        with chart_col:
            # Mode distribution donut — uses brain.get_dominant_mode()
            modes   = [a.brain.get_dominant_mode().value for a in alive_agents]
            mc_keys = list(set(modes))
            mc_vals = [modes.count(m) for m in mc_keys]
            fig_md  = go.Figure(go.Pie(
                labels=mc_keys, values=mc_vals, hole=0.5,
                marker=dict(colors=[MODE_COLOR.get(k,'#888') for k in mc_keys]),
                textfont=dict(size=8, color='#ccc'),
                hoverinfo='label+value+percent',
            ))
            fig_md.update_layout(
                paper_bgcolor='#04040e', height=210, margin=dict(l=0,r=0,t=20,b=0),
                title=dict(text='Mode Dist', font=dict(color='#556',size=10), x=0.5),
                showlegend=True,
                legend=dict(font=dict(size=7,color='#556'), orientation='v'),
                font=dict(color='#556', size=8),
            )
            st.plotly_chart(fig_md, use_container_width=True, key='mode_donut')

            # Collective emotion bar — brain.emotions[E.CURIOSITY..WONDER]
            avg_em = np.mean([a.brain.emotions for a in alive_agents], axis=0)
            fig_em = go.Figure(go.Bar(
                x=EMOTION_NAMES, y=avg_em.tolist(),
                marker=dict(color=EMOTION_COLORS, line=dict(width=0)),
            ))
            fig_em.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=195, margin=dict(l=0,r=0,t=20,b=0),
                title=dict(text='Avg Emotions', font=dict(color='#556',size=10), x=0.5),
                xaxis=dict(color='#445', tickfont=dict(size=7), tickangle=-30),
                yaxis=dict(gridcolor='#0d0d1e', color='#445', range=[-1,1]),
                font=dict(color='#445', size=8),
            )
            st.plotly_chart(fig_em, use_container_width=True, key='coll_em')

        st.divider()

        # Action heatmap wired to BioHyperAgent.action_counts dict
        st.markdown(
            "<div class='section-title'>Action Distribution Heatmap (top 20 by energy)</div>",
            unsafe_allow_html=True
        )
        from consciousness import ACTIONS
        top20     = sorted(alive_agents, key=lambda a: a.energy, reverse=True)[:20]
        heat_data = np.zeros((len(top20), len(ACTIONS)), dtype=float)
        for i, ag in enumerate(top20):
            total_acts = sum(ag.action_counts.values()) or 1
            for j, act in enumerate(ACTIONS):
                heat_data[i, j] = ag.action_counts.get(act, 0) / total_acts

        fig_heat = go.Figure(go.Heatmap(
            z=heat_data, x=ACTIONS, y=[a.id for a in top20],
            colorscale='Viridis', showscale=True,
            hovertemplate='Agent %{y}<br>Action %{x}<br>Freq %{z:.2%}<extra></extra>',
        ))
        fig_heat.update_layout(
            paper_bgcolor='#04040e', plot_bgcolor='#04040e',
            height=320, margin=dict(l=60,r=0,t=0,b=60),
            xaxis=dict(color='#556', tickangle=-45, tickfont=dict(size=8)),
            yaxis=dict(color='#556', tickfont=dict(size=8)),
            font=dict(color='#556', size=8),
        )
        st.plotly_chart(fig_heat, use_container_width=True, key='act_heat')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3  ─  CIVILIZATION
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 3  ─  CIVILIZATION
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "🏛 CIVILIZATION":
    civ_left, civ_right = st.columns([1.6, 1])

    with civ_left:
        st.markdown("<div class='section-title'>Tribe Leaderboard</div>", unsafe_allow_html=True)
        # C.tribe_leaderboard() → List[dict]: id, members, power, disc, wars, allies, color
        lb = C.tribe_leaderboard()

        if lb:
            tribe_ids    = [r['id']    for r in lb[:16]]
            tribe_powers = [r['power'] for r in lb[:16]]
            tribe_colors = [r['color'] for r in lb[:16]]

            fig_tpow = go.Figure()
            fig_tpow.add_trace(go.Bar(
                x=tribe_ids, y=tribe_powers,
                marker=dict(color=tribe_colors, line=dict(width=0)),
                hovertemplate='<b>%{x}</b><br>Power: %{y:.1f}<extra></extra>',
                name='Power',
            ))
            if tribe_powers:
                war_vals = [-r['wars'] * max(tribe_powers) * 0.06 for r in lb[:16]]
                fig_tpow.add_trace(go.Bar(
                    x=tribe_ids, y=war_vals,
                    marker=dict(color='rgba(255, 68, 85, 0.4)', line=dict(width=0)),
                    name='Wars (neg)', hoverinfo='skip',
                ))
            fig_tpow.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=230, margin=dict(l=0,r=0,t=0,b=0),
                xaxis=dict(color='#556', tickfont=dict(size=9)),
                yaxis=dict(gridcolor='#0d0d1e', color='#556', title='Power'),
                barmode='overlay',
                legend=dict(font=dict(size=8,color='#556')),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_tpow, use_container_width=True, key='tribe_pow')

            for r in lb[:20]:
                war_str  = "⚔" * min(r['wars'], 5)
                ally_str = "🤝" * min(r['allies'], 5)
                bar      = '█' * min(10, int(r['power'] / 5))
                st.markdown(
                    f"<div class='agent-card' style='border-left-color:{r['color']}'>"
                    f"<span style='color:{r['color']};font-weight:bold'>{r['id']}</span>  "
                    f"👥{r['members']}  pwr:{r['power']:.0f}  💡{r['disc']}  "
                    f"{war_str}{ally_str}<br>"
                    f"<span style='color:#334'>{bar}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No tribes yet.")

    with civ_right:
        st.markdown("<div class='section-title'>Diplomatic Status</div>", unsafe_allow_html=True)
        cs = C.get_stats()
        d1, d2 = st.columns(2)
        d1.metric("Active Wars",     cs['active_wars'])
        d2.metric("Active Alliances",cs['active_alliances'])
        d1.metric("Total Wars",      cs['total_wars'])
        d2.metric("Total Alliances", cs['total_alliances'])
        d1.metric("Extinctions",     cs['extinctions'])
        d2.metric("World Knowledge", cs['world_knowledge'])

        st.divider()

        wr = cs['total_wars'] or 0
        al = cs['total_alliances'] or 0
        if wr + al > 0:
            fig_dip = go.Figure(go.Pie(
                labels=['Wars','Alliances'], values=[wr, al], hole=0.5,
                marker=dict(colors=['#FF4455','#44FF88']),
                textfont=dict(size=10, color='#eee'),
            ))
            fig_dip.update_layout(
                paper_bgcolor='#04040e', height=200,
                margin=dict(l=0,r=0,t=20,b=0),
                title=dict(text='War vs Alliance', font=dict(color='#556',size=10), x=0.5),
                font=dict(color='#556', size=9),
            )
            st.plotly_chart(fig_dip, use_container_width=True, key='dip_pie')

        st.divider()

        # Tribe discovery comparison
        st.markdown("<div class='section-title'>Tribe Discoveries</div>", unsafe_allow_html=True)
        if lb:
            fig_disc = go.Figure(go.Bar(
                x=[r['id'] for r in lb[:12]],
                y=[r['disc'] for r in lb[:12]],
                marker=dict(color=[r['color'] for r in lb[:12]], line=dict(width=0)),
            ))
            fig_disc.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=160, margin=dict(l=0,r=0,t=0,b=0),
                xaxis=dict(color='#445', tickfont=dict(size=8)),
                yaxis=dict(gridcolor='#0d0d1e', color='#445'),
                font=dict(color='#445', size=8),
            )
            st.plotly_chart(fig_disc, use_container_width=True, key='tribe_disc')

        st.markdown("<div class='section-title'>Civ Events</div>", unsafe_allow_html=True)
        for evt in reversed(C.get_recent_events(16)):
            ec = EVT_COLOR.get(evt.get('type',''), '#446')
            st.markdown(
                f"<div class='event-line' style='color:{ec}'>"
                f"[{evt['step']}] {evt['desc']}</div>",
                unsafe_allow_html=True
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4  ─  TECH TREE
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 4  ─  TECH TREE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "💡 TECH TREE":
    tech = C.tech   # TechTree: .nodes dict, .edges list[tuple], .global_bonus, .summary_by_category()

    tt_left, tt_right = st.columns([1.6, 1])

    with tt_left:
        st.markdown(
            f"<div class='section-title'>"
            f"Technology Graph · {len(tech.nodes)} nodes · bonus {tech.global_bonus:.4f}×"
            f"</div>",
            unsafe_allow_html=True
        )
        nodes = list(tech.nodes.values())
        if nodes:
            node_x     = [float(n.get('signature',0)) % W.size for n in nodes]
            node_y     = [float(n.get('eigenmode',0)) * 5 % W.size for n in nodes]
            node_names = [n['name'] for n in nodes]
            node_hover = [
                f"<b>{n['name']}</b><br>Type: {n.get('type','?')}<br>"
                f"By: {n.get('discoverer','?')[:6]} [{n.get('tribe','?')}]<br>"
                f"Sig: {n.get('signature',0):.1f}  Wonder: {n.get('wonder',0):.2f}"
                for n in nodes
            ]

            fig_tree = go.Figure()

            # Edges from tech.edges list[tuple(src, dst)]
            name_to_idx = {name: i for i, name in enumerate(node_names)}
            for src, dst in tech.edges[:300]:
                si = name_to_idx.get(src)
                di = name_to_idx.get(dst)
                if si is not None and di is not None:
                    fig_tree.add_trace(go.Scatter(
                        x=[node_x[si], node_x[di], None],
                        y=[node_y[si], node_y[di], None],
                        mode='lines',
                        line=dict(color='#1a1a3a', width=1),
                        hoverinfo='skip', showlegend=False,
                    ))

            cat_summary = tech.summary_by_category()
            for cat in cat_summary:
                idxs = [i for i, n in enumerate(nodes) if n.get('type') == cat]
                if not idxs:
                    continue
                fig_tree.add_trace(go.Scatter(
                    x=[node_x[i] for i in idxs],
                    y=[node_y[i] for i in idxs],
                    mode='markers',
                    marker=dict(size=9, color=TECH_COLOR.get(cat,'#555'),
                                opacity=0.85,
                                line=dict(width=0.5,color='rgba(255,255,255,0.2)')),
                    name=f"{TECH_ICON.get(cat,'?')} {cat}",
                    text=[node_hover[i] for i in idxs],
                    hovertemplate='%{text}<extra></extra>',
                ))

            fig_tree.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=420, margin=dict(l=0,r=0,t=0,b=0),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                showlegend=True,
                legend=dict(font=dict(size=9,color='#556'), x=0.01, y=0.99,
                            bgcolor='rgba(0,0,0,0.5)'),
            )
            st.plotly_chart(fig_tree, use_container_width=True, key='tech_graph')
        else:
            st.info("No inventions yet. Run more ticks!")

    with tt_right:
        cat_counts = tech.summary_by_category()
        if cat_counts:
            fig_cat = go.Figure(go.Pie(
                labels=list(cat_counts.keys()),
                values=list(cat_counts.values()),
                hole=0.45,
                marker=dict(colors=[TECH_COLOR.get(k,'#888') for k in cat_counts]),
                textfont=dict(size=9, color='#eee'),
            ))
            fig_cat.update_layout(
                paper_bgcolor='#04040e', height=220,
                margin=dict(l=0,r=0,t=20,b=0),
                title=dict(text='By Category', font=dict(color='#556',size=10), x=0.5),
                font=dict(color='#556', size=9),
                legend=dict(font=dict(size=8,color='#556')),
            )
            st.plotly_chart(fig_cat, use_container_width=True, key='tech_pie')

        st.divider()
        st.markdown("<div class='section-title'>Latest Discoveries</div>", unsafe_allow_html=True)
        # tech.recent(n) → last n nodes from tech.nodes dict
        for node in reversed(tech.recent(24)):
            cat   = node.get('type','?')
            color = TECH_COLOR.get(cat,'#888')
            disc  = node.get('discoverer','?')[:6]
            tribe = node.get('tribe','?') or '?'
            st.markdown(
                f"<div class='event-line'>"
                f"<span style='color:{color}'>{TECH_ICON.get(cat,'?')} <b>{node['name']}</b></span>"
                f"<span style='color:#334'>  {cat} | {disc} [{tribe}]</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.divider()
        st.markdown(
            f"<div class='kpi-card'>Tech Multiplier  "
            f"<span style='color:#7DF9FF;font-size:1.4em'>{tech.global_bonus:.4f}×</span><br>"
            f"<span style='color:#334'>+0.3% per discovery · caps at 3.0×</span>"
            f"</div>",
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5  ─  ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 5  ─  ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "📊 ANALYTICS":
    st.markdown(
        "<div class='section-title'>Population & Civilization Analytics</div>",
        unsafe_allow_html=True
    )

    pop_h = estats.get('pop_history', [])
    eng_h = estats.get('energy_history', [])
    inv_h = estats.get('inv_history', [])

    an1, an2, an3 = st.columns(3)

    def sparkline(col, data, title, color, key):
        if not data:
            return
            
        # Dynamically convert standard hex to a Plotly-safe rgba string with 0.07 opacity (equivalent to hex '11')
        h = color.lstrip('#')
        rgba_fill = f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, 0.07)"

        fig = go.Figure(go.Scatter(
            y=data, mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy', fillcolor=rgba_fill,
        ))
        fig.update_layout(
            paper_bgcolor='#04040e', plot_bgcolor='#04040e',
            height=200, margin=dict(l=30,r=10,t=30,b=10),
            title=dict(text=title, font=dict(color=color, size=11)),
            xaxis=dict(showgrid=False, color='#334'),
            yaxis=dict(gridcolor='#0d0d1e', color='#445'),
            font=dict(color='#445', size=9),
        )
        col.plotly_chart(fig, use_container_width=True, key=key)

    sparkline(an1, pop_h, 'Population History',       '#7DF9FF', 'pop_an')
    sparkline(an2, eng_h, 'Avg Energy History',        '#FFD700', 'eng_an')
    sparkline(an3, inv_h, 'Total Inventions History',  '#DDA0DD', 'inv_an')

    # Meta analytics
    meta_h = estats.get('meta_inv_history', [])
    nov_h  = estats.get('novelty_history', [])
    an3b, an3c = st.columns(2)
    sparkline(an3b, meta_h, 'Meta-Inventions Over Time', '#FF8C00', 'meta_an')
    sparkline(an3c, nov_h,  'Novelty Index (Running Mean)', '#00FF88', 'nov_an')

    st.divider()

    an4, an5, an6 = st.columns(3)

    def histogram(col, data, title, color, key, nbins=20):
        if not data:
            return
        fig = go.Figure(go.Histogram(
            x=data, nbinsx=nbins,
            marker=dict(color=color, line=dict(color='#04040e', width=0.5)),
        ))
        fig.update_layout(
            paper_bgcolor='#04040e', plot_bgcolor='#04040e',
            height=200, margin=dict(l=30,r=10,t=30,b=10),
            title=dict(text=title, font=dict(color=color, size=11)),
            xaxis=dict(color='#445', gridcolor='#0d0d1e'),
            yaxis=dict(color='#445', gridcolor='#0d0d1e'),
            font=dict(color='#445', size=9),
        )
        col.plotly_chart(fig, use_container_width=True, key=key)

    if alive_agents:
        histogram(an4, [a.age        for a in alive_agents], 'Age Distribution',        '#9370DB', 'age_hist')
        histogram(an5, [a.energy     for a in alive_agents], 'Energy Distribution',      '#FFD700', 'edist')
        histogram(an6, [a.meta.eigenspread() for a in alive_agents
                        if hasattr(a,'meta') and a.meta],    'Meta Eigenspread Dist.',   '#FF8C00', 'eigen_hist')

    st.divider()

    an7, an8 = st.columns(2)

    with an7:
        # Curiosity vs Wonder scatter — from to_dict() curiosity, wonder, mode
        if alive_agents:
            dicts = [a.to_dict() for a in alive_agents]
            df_sc = pd.DataFrame(dicts)
            fig_sc = go.Figure()
            for mode in df_sc['mode'].unique():
                sub = df_sc[df_sc['mode'] == mode]
                fig_sc.add_trace(go.Scatter(
                    x=sub['curiosity'], y=sub['wonder'],
                    mode='markers', name=mode,
                    marker=dict(color=MODE_COLOR.get(mode,'#888'),
                                size=6, opacity=0.7, line=dict(width=0)),
                    text=sub['id'], hovertemplate='%{text}<extra></extra>',
                ))
            fig_sc.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=280, margin=dict(l=40,r=10,t=30,b=30),
                title=dict(text='Curiosity × Wonder (mode coloured)',
                           font=dict(color='#aef',size=11)),
                xaxis=dict(title='Curiosity', color='#445', gridcolor='#0d0d1e'),
                yaxis=dict(title='Wonder',    color='#445', gridcolor='#0d0d1e'),
                legend=dict(font=dict(size=8,color='#556'), x=0.01, y=0.99,
                            bgcolor='rgba(0,0,0,0.5)'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_sc, use_container_width=True, key='cw_scatter')

    with an8:
        # Generation distribution bar
        if alive_agents:
            gens   = [a.generation for a in alive_agents]
            max_g  = max(gens) if gens else 0
            gcounts = [gens.count(g) for g in range(max_g + 1)]
            fig_gen = go.Figure(go.Bar(
                x=list(range(max_g + 1)), y=gcounts,
                marker=dict(
                    color=[f'hsl({int(g / max(max_g,1) * 200 + 200)},80%,50%)'
                           for g in range(max_g + 1)],
                    line=dict(width=0),
                ),
            ))
            fig_gen.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=280, margin=dict(l=40,r=10,t=30,b=30),
                title=dict(text='Population by Generation',
                           font=dict(color='#aef',size=11)),
                xaxis=dict(title='Generation', color='#445', gridcolor='#0d0d1e'),
                yaxis=dict(title='Count',      color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_gen, use_container_width=True, key='gen_bar')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6  ─  HRC BRAIN INSPECTOR
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 6  ─  HRC BRAIN INSPECTOR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "🔬 HRC BRAIN":
    st.markdown(
        "<div class='section-title'>"
        "Harmonic Resonance Consciousness · Deep Brain Inspector"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div style='color:#223;font-size:0.76em;font-family:monospace;padding-bottom:8px'>"
        "ψ ∈ ℂᴷ wave function · Hermitian Hamiltonian H · Schrödinger evolution "
        "· Born-rule decisions · Riemannian learning · Eigenspace invention · Zero prior art"
        "</div>",
        unsafe_allow_html=True
    )

    if not alive_agents:
        st.warning("No agents alive.")
    else:
        sorted_by_e  = sorted(alive_agents, key=lambda a: a.energy, reverse=True)
        agent_id_lst = [a.id for a in sorted_by_e[:80]]

        br_c1, br_c2, br_c3 = st.columns([2, 1, 1])
        sel_id    = br_c1.selectbox("Select Agent", agent_id_lst, key='brain_sel')
        sel_agent = next((a for a in alive_agents if a.id == sel_id), None)

        if sel_agent:
            brain = sel_agent.brain     # HarmonicResonanceConsciousness
            d     = sel_agent.to_dict() # full serialised dict
            rgb   = (d['r'], d['g'], d['b'])

            br_c2.metric("Mode",   f"{MODE_ICON.get(d['mode'],'?')} {d['mode']}")
            br_c3.metric("Energy", d['energy'])

            # Full stats strip
            bs = st.columns(10)
            bs[0].metric("Health",    f"{d['health']:.2f}")
            bs[1].metric("Age",       d['age'])
            bs[2].metric("Gen",       d['generation'])
            bs[3].metric("Inventions",d['inventions'])
            bs[4].metric("Meta-Inv",  d.get('meta_inventions', 0))
            bs[5].metric("Composed",  d.get('composed_actions', 0))
            bs[6].metric("Eigensprd", f"{d.get('meta_eigenspread',0):.3f}")
            bs[7].metric("Comms",     brain.n_comms)
            bs[8].metric("Reward Σ",  f"{brain.total_reward:.2f}")
            bs[9].metric("Tribe",     d['tribe'])

            st.divider()

            hrc_l, hrc_r = st.columns(2)

            with hrc_l:
                # ── 1. ψ amplitude: brain.psi_magnitude_profile() → List[float]
                from consciousness import K_DIM
                psi_amps = brain.psi_magnitude_profile()
                k_labels = [f"k{i}" for i in range(K_DIM)]

                fig_psi = go.Figure(go.Bar(
                    x=k_labels, y=psi_amps,
                    marker=dict(
                        color=[f'rgba({rgb[0]},{rgb[1]},{rgb[2]},{max(0.15,a):.2f})'
                               for a in psi_amps],
                        line=dict(width=0),
                    ),
                ))
                fig_psi.update_layout(
                    paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                    height=190, margin=dict(l=30,r=10,t=32,b=10),
                    title=dict(text='ψ Wave Amplitude  |⟨kᵢ|ψ⟩|',
                               font=dict(color='#7DF9FF',size=11)),
                    xaxis=dict(color='#445', tickfont=dict(size=8)),
                    yaxis=dict(gridcolor='#0d0d1e', color='#445', range=[0,None]),
                    font=dict(color='#445', size=9),
                )
                st.plotly_chart(fig_psi, use_container_width=True, key='psi_amp')

                # ── 2. Eigenspectrum: brain._evals → ndarray
                evals = brain._evals.tolist()
                fig_ev = go.Figure(go.Bar(
                    x=k_labels, y=evals,
                    marker=dict(
                        color=['#7DF9FF' if v >= 0 else '#FF4455' for v in evals],
                        line=dict(width=0),
                    ),
                ))
                fig_ev.add_hline(y=0, line=dict(color='#226',width=1))
                fig_ev.update_layout(
                    paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                    height=190, margin=dict(l=30,r=10,t=32,b=10),
                    title=dict(text='Hamiltonian Eigenspectrum  λᵢ',
                               font=dict(color='#FFD700',size=11)),
                    xaxis=dict(color='#445', tickfont=dict(size=8)),
                    yaxis=dict(gridcolor='#0d0d1e', color='#445',
                               zeroline=True, zerolinecolor='#226'),
                    font=dict(color='#445', size=9),
                )
                st.plotly_chart(fig_ev, use_container_width=True, key='eig_spec')

                # ── 3. Soul frequencies: sel_agent.soul_freqs → ndarray (immutable identity)
                soul = sel_agent.soul_freqs.tolist()
                fig_soul = go.Figure(go.Scatter(
                    x=k_labels, y=soul,
                    mode='markers+lines',
                    marker=dict(color='#FF69B4', size=7,
                                line=dict(color='#04040e',width=1)),
                    line=dict(color='rgba(255, 105, 180, 0.4)', width=1.5, dash='dot'),
                ))
                fig_soul.add_hline(y=0, line=dict(color='#226',width=1))
                fig_soul.update_layout(
                    paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                    height=170, margin=dict(l=30,r=10,t=32,b=10),
                    title=dict(text='Soul Frequencies (Immutable Identity)',
                               font=dict(color='#FF69B4',size=11)),
                    xaxis=dict(color='#445', tickfont=dict(size=8)),
                    yaxis=dict(gridcolor='#0d0d1e', color='#445',
                               zeroline=True, zerolinecolor='#226'),
                    font=dict(color='#445', size=9),
                )
                st.plotly_chart(fig_soul, use_container_width=True, key='soul_freq')

            with hrc_r:
                # ── 4. Emotions: brain.emotions[0..6] matching E enum
                fig_emo = go.Figure(go.Bar(
                    x=EMOTION_NAMES, y=brain.emotions.tolist(),
                    marker=dict(color=EMOTION_COLORS, line=dict(width=0)),
                ))
                fig_emo.add_hline(y=0, line=dict(color='#226',width=1))
                fig_emo.update_layout(
                    paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                    height=190, margin=dict(l=30,r=10,t=32,b=10),
                    title=dict(text='Emotional State  εᵢ ∈ [−1,1]',
                               font=dict(color='#98FB98',size=11)),
                    xaxis=dict(color='#445', tickfont=dict(size=8), tickangle=-30),
                    yaxis=dict(gridcolor='#0d0d1e', color='#445', range=[-1,1]),
                    font=dict(color='#445', size=9),
                )
                st.plotly_chart(fig_emo, use_container_width=True, key='emo_bar')

                # ── 5. Hamiltonian H real part heatmap: brain.H.real
                H_real = brain.H.real
                fig_H = go.Figure(go.Heatmap(
                    z=H_real,
                    colorscale=[[0,'#FF4455'],[0.5,'#04040e'],[1,'#7DF9FF']],
                    showscale=True,
                    hovertemplate='H[%{y},%{x}] = %{z:.3f}<extra></extra>',
                ))
                fig_H.update_layout(
                    paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                    height=265, margin=dict(l=30,r=30,t=32,b=10),
                    title=dict(text='Hamiltonian H · Real Part (World Model)',
                               font=dict(color='#9370DB',size=11)),
                    xaxis=dict(color='#445', tickfont=dict(size=7)),
                    yaxis=dict(color='#445', tickfont=dict(size=7), autorange='reversed'),
                    font=dict(color='#445', size=8),
                )
                st.plotly_chart(fig_H, use_container_width=True, key='ham_heat')

                # ── 6. Episodic memory reward curve: brain.episodic_memory List[dict]
                mem = brain.episodic_memory   # [{reward, psi_peak, tick}, ...]
                if mem:
                    mem_r = [m['reward']   for m in mem]
                    mem_t = [m['tick']     for m in mem]
                    fig_mem = go.Figure()
                    fig_mem.add_trace(go.Scatter(
                        x=mem_t, y=mem_r, mode='lines+markers',
                        line=dict(color='#FFD700', width=1.5),
                        marker=dict(size=4,
                                    color=['#44FF88' if r >= 0 else '#FF4455' for r in mem_r]),
                        name='Reward',
                    ))
                    fig_mem.add_hline(y=0, line=dict(color='#334',width=1))
                    fig_mem.update_layout(
                        paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                        height=155, margin=dict(l=30,r=10,t=32,b=10),
                        title=dict(text='Episodic Memory · Reward Trace',
                                   font=dict(color='#FFD700',size=11)),
                        xaxis=dict(color='#445', showgrid=False),
                        yaxis=dict(gridcolor='#0d0d1e', color='#445',
                                   zeroline=True, zerolinecolor='#226'),
                        font=dict(color='#445', size=9),
                    )
                    st.plotly_chart(fig_mem, use_container_width=True, key='ep_mem')

            st.divider()

            disc_col, act_col = st.columns(2)

            with disc_col:
                st.markdown("<div class='section-title'>Personal Discoveries (Gödel Programs)</div>",
                            unsafe_allow_html=True)
                # brain.discoveries: name → {name, type, signature, godel, program, wonder, eigenmode, diversity}
                if brain.discoveries:
                    for name, inv in brain.discoveries.items():
                        cat   = inv.get('type','?')
                        color = TECH_COLOR.get(cat,'#888')
                        prog_str = " → ".join(inv.get('program',[])) if 'program' in inv else ''
                        st.markdown(
                            f"<div class='event-line'>"
                            f"<span style='color:{color}'>{TECH_ICON.get(cat,'?')} <b>{name}</b></span>"
                            f" <span style='color:#334'>G:{inv.get('godel',0)} | {prog_str}</span><br>"
                            f"<span style='color:#556'>wonder:{inv.get('wonder',0):.2f} "
                            f"div:{inv.get('diversity',0):.2f} mode:{inv.get('eigenmode',0)}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("No personal discoveries yet.")

                # Composed actions (new meta feature)
                if brain.composed_actions:
                    st.markdown("<div class='section-title' style='margin-top:8px'>Composed Actions</div>",
                                unsafe_allow_html=True)
                    for act_name, prog in list(brain.composed_actions.items())[-8:]:
                        prog_str = " → ".join(prog)
                        st.markdown(
                            f"<div class='event-line'>"
                            f"<span style='color:#FF8C00'>⚙ {act_name}</span>"
                            f" <span style='color:#334'>{prog_str}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

            with act_col:
                st.markdown("<div class='section-title'>Action History</div>",
                            unsafe_allow_html=True)
                ac = sel_agent.action_counts
                if ac:
                    total_a = sum(ac.values())
                    fig_ac  = go.Figure(go.Bar(
                        x=list(ac.keys()), y=list(ac.values()),
                        marker=dict(color='rgba(125, 249, 255, 0.53)', line=dict(width=0)),
                        text=[f"{v/total_a:.0%}" for v in ac.values()],
                        textposition='outside',
                        textfont=dict(size=7, color='#556'),
                    ))
                    fig_ac.update_layout(
                        paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                        height=210, margin=dict(l=0,r=0,t=0,b=50),
                        xaxis=dict(color='#445', tickangle=-45, tickfont=dict(size=7)),
                        yaxis=dict(gridcolor='#0d0d1e', color='#445'),
                        font=dict(color='#445', size=8),
                    )
                    st.plotly_chart(fig_ac, use_container_width=True, key='act_bar')
                else:
                    st.caption("No actions recorded yet.")

                # Meta-H eigenspectrum for selected agent
                if sel_agent.meta is not None:
                    meta_evals = sel_agent.meta._meta_evals.tolist()
                    k_meta_labels = [f"m{i}" for i in range(len(meta_evals))]
                    fig_meta_ev = go.Figure(go.Bar(
                        x=k_meta_labels, y=meta_evals,
                        marker=dict(
                            color=['#FF8C00' if v >= 0 else '#FF4455' for v in meta_evals],
                            line=dict(width=0),
                        ),
                    ))
                    fig_meta_ev.update_layout(
                        paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                        height=180, margin=dict(l=30,r=10,t=32,b=10),
                        title=dict(text='Meta-H Eigenspectrum (Learning Algorithm)',
                                   font=dict(color='#FF8C00',size=11)),
                        xaxis=dict(color='#445', tickfont=dict(size=7)),
                        yaxis=dict(gridcolor='#0d0d1e', color='#445'),
                        font=dict(color='#445', size=9),
                    )
                    st.plotly_chart(fig_meta_ev, use_container_width=True, key='meta_eig')

            # Absorbed inventions list
            st.markdown("<div class='section-title'>Absorbed Inventions (cultural diffusion)</div>",
                        unsafe_allow_html=True)
            if sel_agent.absorbed_inventions:
                absorbed_html = " · ".join(
                    f"<span style='color:#334'>{n}</span>"
                    for n in sel_agent.absorbed_inventions[-20:]
                )
                st.markdown(
                    f"<div class='kpi-card'>{absorbed_html}</div>",
                    unsafe_allow_html=True
                )
            else:
                st.caption("No absorbed inventions yet.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7  ─  EVENTS FEED
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 7  ─  EVENTS FEED
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "📡 EVENTS FEED":
    ev_l, ev_r = st.columns(2)

    with ev_l:
        st.markdown(
            "<div class='section-title'>Civilization Events (latest 40)</div>",
            unsafe_allow_html=True
        )
        # C.get_recent_events(n) → List[dict]: step, type, desc
        for evt in reversed(C.get_recent_events(40)):
            ec = EVT_COLOR.get(evt.get('type',''), '#446')
            st.markdown(
                f"<div class='event-line' style='color:{ec};padding:3px 8px'>"
                f"<span style='color:#223'>[{evt['step']:>6}]</span>  {evt['desc']}"
                f"</div>",
                unsafe_allow_html=True
            )

    with ev_r:
        st.markdown(
            "<div class='section-title'>World Physics Events</div>",
            unsafe_allow_html=True
        )
        # W.get_recent_events(n) → List[dict]: step, type, desc, pos
        for evt in reversed(W.get_recent_events(20)):
            ec  = EVT_COLOR.get(evt.get('type',''), '#446')
            pos = evt.get('pos', ('?','?'))
            st.markdown(
                f"<div class='event-line' style='color:{ec};padding:3px 8px'>"
                f"<span style='color:#223'>[{evt['step']:>6}]</span>  {evt['desc']}"
                f"  <span style='color:#1a1a2a'>@ ({pos[0]},{pos[1]})</span>"
                f"</div>",
                unsafe_allow_html=True
            )

        st.divider()

        # Event type frequency from C.civ_events
        all_civ = C.get_recent_events(60)
        if all_civ:
            etypes  = [e.get('type','?') for e in all_civ]
            etype_u = list(set(etypes))
            etype_c = [etypes.count(t) for t in etype_u]
            fig_etp = go.Figure(go.Pie(
                labels=etype_u, values=etype_c, hole=0.4,
                marker=dict(colors=[EVT_COLOR.get(t,'#555') for t in etype_u]),
                textfont=dict(size=9, color='#eee'),
            ))
            fig_etp.update_layout(
                paper_bgcolor='#04040e', height=210,
                margin=dict(l=0,r=0,t=20,b=0),
                title=dict(text='Event Type Distribution',
                           font=dict(color='#556',size=10), x=0.5),
                font=dict(color='#556', size=9),
                legend=dict(font=dict(size=8,color='#556')),
            )
            st.plotly_chart(fig_etp, use_container_width=True, key='evt_pie')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8  ─  RESOURCES
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 8  ─  RESOURCES
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "🗺 RESOURCES":
    st.markdown(
        "<div class='section-title'>Resource Field · Per-Layer Analysis</div>",
        unsafe_allow_html=True
    )

    # 4 resource heatmaps — W.resources[x, y, r_idx] for r_idx in 0..3
    r_cols = st.columns(4)
    # RGBA strings for midpoint at 0.27 alpha (approx 0x44)
    r_lows = [
        'rgba(68, 255, 136, 0.27)', 'rgba(255, 215, 0, 0.27)', 
        'rgba(221, 160, 221, 0.27)', 'rgba(255, 140, 0, 0.27)'
    ]
    for r_idx, (rcol, rname, rcol_str, r_low) in enumerate(zip(r_cols, R_NAMES, R_COLORS, r_lows)):
        layer = W.resources[:, :, r_idx]   # ndarray (size, size)
        cs_r  = [[0,'#04040e'],[0.4, r_low],[1.0, rcol_str]]
        fig_r = go.Figure(go.Heatmap(
            z=layer.T, colorscale=cs_r, showscale=False,
            hovertemplate=f'{rname}<br>(%{{x}},%{{y}}) = %{{z:.2f}}<extra></extra>',
        ))
        # Overlay agent positions
        if alive_agents:
            fig_r.add_trace(go.Scatter(
                x=[a.x for a in alive_agents],
                y=[a.y for a in alive_agents],
                mode='markers',
                marker=dict(size=3, color='white', opacity=0.3),
                hoverinfo='skip',
            ))
        fig_r.update_layout(
            paper_bgcolor='#04040e', plot_bgcolor='#04040e',
            height=220, margin=dict(l=0,r=0,t=28,b=0),
            title=dict(text=rname, font=dict(color=rcol_str, size=11), x=0.5),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                       scaleanchor='x'),
        )
        rcol.plotly_chart(fig_r, use_container_width=True, key=f'res_{r_idx}')

    st.divider()

    # Total supply bar — W.resources.sum over x,y per resource type
    r_totals = [float(W.resources[:, :, r].sum()) for r in range(4)]
    fig_rtot = go.Figure(go.Bar(
        x=R_NAMES, y=r_totals,
        marker=dict(color=R_COLORS, line=dict(width=0)),
        text=[f"{v:.0f}" for v in r_totals],
        textposition='outside',
        textfont=dict(size=10, color='#7DF9FF'),
    ))
    fig_rtot.update_layout(
        paper_bgcolor='#04040e', plot_bgcolor='#04040e',
        height=210, margin=dict(l=40,r=20,t=30,b=20),
        title=dict(text='Total Resource Supply (world-wide)',
                   font=dict(color='#aef',size=12), x=0.5),
        xaxis=dict(color='#556'),
        yaxis=dict(gridcolor='#0d0d1e', color='#445'),
        font=dict(color='#445', size=10),
    )
    st.plotly_chart(fig_rtot, use_container_width=True, key='res_total')

    st.divider()

    # Artifact breakdown — from W.artifacts dict
    art_types_all = [v.get('type','unknown') for v in W.artifacts.values()]
    if art_types_all:
        at_u = list(set(art_types_all))
        at_c = [art_types_all.count(t) for t in at_u]
        art_left, art_right = st.columns([1, 2])
        with art_left:
            fig_art = go.Figure(go.Pie(
                labels=at_u, values=at_c, hole=0.45,
                marker=dict(colors=[TECH_COLOR.get(t,'#888') for t in at_u]),
                textfont=dict(size=9, color='#eee'),
            ))
            fig_art.update_layout(
                paper_bgcolor='#04040e', height=230,
                margin=dict(l=0,r=0,t=20,b=0),
                title=dict(text=f'Artifacts ({len(W.artifacts)} placed)',
                           font=dict(color='#FFD700',size=11), x=0.5),
                font=dict(color='#556',size=9),
                legend=dict(font=dict(size=8,color='#556')),
            )
            st.plotly_chart(fig_art, use_container_width=True, key='art_pie')

        with art_right:
            st.markdown("<div class='section-title'>Recent Artifacts</div>",
                        unsafe_allow_html=True)
            # Show up to 20 most recent artifacts from W.artifacts
            recent_arts = list(W.artifacts.items())[-20:]
            for (ax, ay), art in reversed(recent_arts):
                atype  = art.get('type','?')
                acolor = TECH_COLOR.get(atype,'#888')
                aname  = art.get('name','?')
                cre    = art.get('creator','?')[:6]
                step   = art.get('step','?')
                st.markdown(
                    f"<div class='event-line'>"
                    f"<span style='color:{acolor}'>{TECH_ICON.get(atype,'?')} <b>{aname}</b></span>"
                    f"<span style='color:#334'>  by {cre} @ ({ax},{ay}) t:{step}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )



# ══════════════════════════════════════════════════════════════════════════════
# TAB 9  ─  META-MIND (NEW)
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# TAB 9  ─  META-MIND (NEW)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "🧠 META-MIND":
    st.markdown(
        "<div class='section-title'>🧠 Metacognitive Landscape · Self-Modifying Intelligence</div>",
        unsafe_allow_html=True
    )
    if not alive_agents:
        st.warning("No agents alive.")
    else:
        mm1, mm2 = st.columns(2)

        # ── Tribal meta-H eigenspectra ────────────────────────────────────────
        with mm1:
            st.markdown("<div class='section-title'>Tribal Epistemic Identities (meta-H eigenvalues)</div>",
                        unsafe_allow_html=True)
            fig_tribal = go.Figure()
            for tid, tribe in C.tribes.items():
                if tribe.tribal_meta_H is not None:
                    evals = np.linalg.eigvalsh(tribe.tribal_meta_H)
                    fig_tribal.add_trace(go.Scatter(
                        y=evals, mode='lines+markers', name=tid,
                        line=dict(width=1.5), marker=dict(size=4), opacity=0.85,
                    ))
            fig_tribal.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=300, margin=dict(l=30,r=10,t=10,b=10),
                title=dict(text='Each line = one tribe\'s learning paradigm',
                           font=dict(color='#FF8C00',size=10)),
                xaxis=dict(title='Eigenmode', color='#445', gridcolor='#0d0d1e'),
                yaxis=dict(title='Eigenvalue', color='#445', gridcolor='#0d0d1e'),
                legend=dict(font=dict(size=8,color='#556'), bgcolor='rgba(0,0,0,0.5)'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_tribal, use_container_width=True, key='tribal_meta')

        # ── Cognitive Clade Distribution ──────────────────────────────────────
        with mm2:
            st.markdown("<div class='section-title'>Cognitive Clade Distribution</div>",
                        unsafe_allow_html=True)
            phylo_stats = EN.phylo.get_stats()
            clade_sizes = phylo_stats.get('clade_sizes', {})
            if clade_sizes:
                fig_clades = go.Figure(go.Bar(
                    x=list(clade_sizes.keys()), y=list(clade_sizes.values()),
                    marker=dict(color='#9370DB', line=dict(width=0)),
                ))
                fig_clades.update_layout(
                    paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                    height=300, margin=dict(l=30,r=10,t=10,b=10),
                    title=dict(text=f'{len(clade_sizes)} cognitive clades by member count',
                               font=dict(color='#9370DB',size=10)),
                    xaxis=dict(color='#445', tickfont=dict(size=7), tickangle=-45),
                    yaxis=dict(title='Members', color='#445', gridcolor='#0d0d1e'),
                    font=dict(color='#445', size=9),
                )
                st.plotly_chart(fig_clades, use_container_width=True, key='clade_bar')
            else:
                st.info("Run more ticks for clade data.")

        st.divider()
        mm3, mm4 = st.columns(2)

        # ── Novelty Index ─────────────────────────────────────────────────────
        with mm3:
            st.markdown("<div class='section-title'>Discovery Novelty Index</div>",
                        unsafe_allow_html=True)
            ns = C.novelty_scorer.get_stats()
            recent_novelty = ns.get('recent_novelty', [])
            n_bk = ns.get('n_breakthroughs', 0)
            col_ns1, col_ns2, col_ns3 = st.columns(3)
            col_ns1.metric("Scored",       ns.get('total_scored', 0))
            col_ns2.metric("Breakthroughs",n_bk)
            col_ns3.metric("Running Mean", f"{ns.get('running_mean',0):.4f}")
            if recent_novelty:
                fig_nov = go.Figure(go.Scatter(
                    y=recent_novelty, mode='lines',
                    line=dict(color='#00FF88', width=2),
                    fill='tozeroy', fillcolor='rgba(0,255,136,0.06)',
                ))
                # Mark breakthroughs
                for bt in C.novelty_scorer.breakthroughs[-5:]:
                    idx = bt.get('index', 0) - max(0, len(C.novelty_scorer.known_godels) - len(recent_novelty))
                    if 0 <= idx < len(recent_novelty):
                        fig_nov.add_annotation(
                            x=idx, y=bt['novelty'], text="⭐",
                            showarrow=True, arrowhead=2, arrowcolor='#FFD700',
                            font=dict(size=12),
                        )
                fig_nov.update_layout(
                    paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                    height=220, margin=dict(l=30,r=10,t=30,b=10),
                    title=dict(text='Discovery Novelty (⭐ = Breakthrough)',
                               font=dict(color='#00FF88',size=11)),
                    xaxis=dict(color='#445', showgrid=False),
                    yaxis=dict(color='#445', gridcolor='#0d0d1e'),
                    font=dict(color='#445', size=9),
                )
                st.plotly_chart(fig_nov, use_container_width=True, key='novelty_chart')
            else:
                st.info("No novelty data yet.")

        # ── Cambrian Events + Top Breakthroughs ──────────────────────────────
        with mm4:
            st.markdown("<div class='section-title'>Cambrian Explosion Events</div>",
                        unsafe_allow_html=True)
            cambrian = EN.phylo.cambrian_events
            if cambrian:
                for evt in reversed(cambrian[-8:]):
                    st.markdown(
                        f"<div class='event-line' style='color:#FF8C00'>"
                        f"🌋 Tick {evt['step']} — novelty burst ×{evt['ratio']} "
                        f"({evt['n_clades']} clades)</div>",
                        unsafe_allow_html=True
                    )
            else:
                st.caption("No Cambrian events yet. Run more ticks!")

            st.divider()
            st.markdown("<div class='section-title'>Top Breakthroughs (Gödel Programs)</div>",
                        unsafe_allow_html=True)
            for bt in reversed(C.novelty_scorer.breakthroughs[-10:]):
                prog_str = " → ".join(bt.get('program', []))
                st.markdown(
                    f"<div class='event-line'>"
                    f"<span style='color:#00FF88'>⭐ G:{bt['godel']}</span>"
                    f" <span style='color:#334'>novelty:{bt['novelty']:.3f} | {prog_str}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.divider()
        # ── Clade history sparkline ───────────────────────────────────────────
        clade_h = phylo_stats.get('clade_history', [])
        if len(clade_h) > 3:
            fig_ch = go.Figure(go.Scatter(
                y=clade_h, mode='lines',
                line=dict(color='#9370DB', width=1.5),
                fill='tozeroy', fillcolor='rgba(147,112,219,0.08)',
            ))
            fig_ch.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=120, margin=dict(l=30,r=10,t=30,b=10),
                title=dict(text='Cognitive Clade Count Over Time',
                           font=dict(color='#9370DB',size=11)),
                xaxis=dict(color='#445', showgrid=False),
                yaxis=dict(color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_ch, use_container_width=True, key='clade_hist')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 10  ─  KNOWLEDGE PHYSICS (NEW)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "🔬 KNOWLEDGE":
    st.markdown(
        "<div class='section-title'>🔬 Knowledge Physics · Ambient Intelligence Field</div>",
        unsafe_allow_html=True
    )

    kp1, kp2 = st.columns(2)

    # ── Knowledge Field Heatmap ───────────────────────────────────────────────
    with kp1:
        st.markdown("<div class='section-title'>Knowledge Field Heatmap (diffusing)</div>",
                    unsafe_allow_html=True)
        kf = W.knowledge_field_heatmap()
        kf_flat = kf.flatten()
        fig_kf = go.Figure(go.Heatmap(
            z=kf.T,
            colorscale=[
                [0.0, '#04040e'], [0.3, '#0a1a2e'],
                [0.6, '#0d3060'], [1.0, '#00FF88'],
            ],
            showscale=True,
            hovertemplate='Knowledge Field<br>(%{x},%{y}) = %{z:.3f}<extra></extra>',
        ))
        if alive_agents:
            fig_kf.add_trace(go.Scatter(
                x=[a.x for a in alive_agents], y=[a.y for a in alive_agents],
                mode='markers',
                marker=dict(size=4, color='white', opacity=0.4),
                hoverinfo='skip', showlegend=False,
            ))
        fig_kf.update_layout(
            paper_bgcolor='#04040e', plot_bgcolor='#04040e',
            height=380, margin=dict(l=0,r=0,t=10,b=0),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, scaleanchor='x'),
        )
        st.plotly_chart(fig_kf, use_container_width=True, key='kf_heatmap')

        # Field stats
        st.markdown(
            f"<div class='kpi-card'>"
            f"Mean intensity: <span style='color:#00FF88'>{kf_flat.mean():.4f}</span><br>"
            f"Max hotspot: <span style='color:#7DF9FF'>{kf_flat.max():.4f}</span><br>"
            f"Non-zero cells: <span style='color:#FFD700'>{(kf_flat > 0.01).sum()}</span>"
            f" / {len(kf_flat)}<br>"
            f"Total artifacts: <span style='color:#DDA0DD'>{len(W.artifacts)}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    # ── Global Memory + Tribal Memories ──────────────────────────────────────
    with kp2:
        st.markdown("<div class='section-title'>Global Memory Matrix (spectral imprint)</div>",
                    unsafe_allow_html=True)
        gm_spec = W.global_memory.spectral_summary()
        if gm_spec.any():
            fig_gm = go.Figure(go.Bar(
                y=gm_spec.tolist(),
                marker=dict(color='#7DF9FF', line=dict(width=0)),
            ))
            fig_gm.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=200, margin=dict(l=30,r=10,t=30,b=10),
                title=dict(
                    text=f'Global Memory Eigenvalues ({W.global_memory.count} imprints)',
                    font=dict(color='#7DF9FF',size=11)
                ),
                xaxis=dict(color='#445'),
                yaxis=dict(color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_gm, use_container_width=True, key='gm_spec')
        else:
            st.info("No global memory yet.")

        st.divider()
        st.markdown("<div class='section-title'>Tribal Memory Matrices</div>",
                    unsafe_allow_html=True)
        for tid, tribe in list(C.tribes.items())[:6]:
            if tribe.tribal_memory and tribe.tribal_memory.count > 0:
                tm_spec = tribe.tribal_memory.spectral_summary()
                st.markdown(
                    f"<div class='kpi-card'>"
                    f"<span style='color:{tribe.color or '#7DF9FF'}'>{tid}</span>"
                    f" — {tribe.tribal_memory.count} imprints"
                    f" — max eigenval: {tm_spec.max():.3f}"
                    f"</div>",
                    unsafe_allow_html=True
                )

    st.divider()
    kp3, kp4 = st.columns(2)

    # ── Agent Meta-Eigenspread Distribution ──────────────────────────────────
    with kp3:
        st.markdown("<div class='section-title'>Agent Meta-Eigenspread Distribution</div>",
                    unsafe_allow_html=True)
        if alive_agents:
            eigenspreads = [
                a.meta.eigenspread() for a in alive_agents
                if hasattr(a, 'meta') and a.meta is not None
            ]
            avg_es = float(np.mean(eigenspreads)) if eigenspreads else 0.0
            st.metric("Avg Cognitive Diversity", f"{avg_es:.4f}")
            fig_es = go.Figure(go.Histogram(
                x=eigenspreads, nbinsx=25,
                marker=dict(color='#FF8C00', line=dict(color='#04040e', width=0.5)),
            ))
            fig_es.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=220, margin=dict(l=30,r=10,t=30,b=10),
                title=dict(text='Cognitive Diversity (meta-H eigenspread)',
                           font=dict(color='#FF8C00',size=11)),
                xaxis=dict(title='Eigenspread', color='#445', gridcolor='#0d0d1e'),
                yaxis=dict(title='Count', color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_es, use_container_width=True, key='eigenspread_hist')

    # ── Idea Interference / Artifact Map ─────────────────────────────────────
    with kp4:
        st.markdown("<div class='section-title'>Artifact Interference Map</div>",
                    unsafe_allow_html=True)
        art_types_all = [v.get('type', 'unknown') for v in W.artifacts.values()]
        if art_types_all:
            at_u = list(set(art_types_all))
            at_c = [art_types_all.count(t) for t in at_u]
            fig_art2 = go.Figure(go.Pie(
                labels=at_u, values=at_c, hole=0.45,
                marker=dict(colors=[TECH_COLOR.get(t,'#888') for t in at_u]),
                textfont=dict(size=9, color='#eee'),
            ))
            fig_art2.update_layout(
                paper_bgcolor='#04040e', height=240,
                margin=dict(l=0,r=0,t=20,b=0),
                title=dict(text=f'Artifacts by type ({len(W.artifacts)} total)',
                           font=dict(color='#FFD700',size=10), x=0.5),
                font=dict(color='#556', size=9),
                legend=dict(font=dict(size=8, color='#556')),
            )
            st.plotly_chart(fig_art2, use_container_width=True, key='art_pie2')
        else:
            st.info("No artifacts placed yet.")

        # Recent artifacts with Gödel info
        st.markdown("<div class='section-title'>Recent Artifacts (Gödel)</div>",
                    unsafe_allow_html=True)
        recent_arts = list(W.artifacts.items())[-12:]
        for (ax, ay), art in reversed(recent_arts):
            atype  = art.get('type', '?')
            acolor = TECH_COLOR.get(atype, '#888')
            aname  = art.get('name', '?')
            cre    = art.get('creator', '?')[:6]
            godel  = art.get('godel', '')
            prog   = " → ".join(art.get('program', [])) if 'program' in art else ''
            st.markdown(
                f"<div class='event-line'>"
                f"<span style='color:{acolor}'>{TECH_ICON.get(atype,'?')} <b>{aname}</b></span>"
                f" <span style='color:#334'>by {cre} G:{godel}</span><br>"
                f"<span style='color:#556'>{prog}</span>"
                f"</div>",
                unsafe_allow_html=True
            )



# ══════════════════════════════════════════════════════════════════════════════
# TAB 11  ─  v3.0 EMERGENCE DASHBOARD (ALL 30 NEW FEATURES)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_tab == "🧬 v3.0 EMERGENCE":
    st.markdown(
        "<div class='section-title'>🧬 v3.0 EMERGENCE DASHBOARD · All 30 GeNeSIS Features Live</div>",
        unsafe_allow_html=True
    )

    # ── Top KPI row: v3.0 specific metrics ────────────────────────────────────
    wstats_em = W.get_stats()
    ek = st.columns(8)
    ek[0].metric("🧲 Bonds",         wstats_em.get('n_bonds', 0))
    ek[1].metric("🌀 Kuramoto r",    f"{wstats_em.get('kuramoto_order', 0):.4f}")
    ek[2].metric("⚡ Pheromone",     f"{wstats_em.get('pheromone_activity', 0):.1f}")
    ek[3].metric("🎨 Meme activity", f"{wstats_em.get('meme_activity', 0):.1f}")
    ek[4].metric("🌟 Season",        wstats_em.get('season', 'Summer'))
    ek[5].metric("⛅ Weather amp",   f"{wstats_em.get('weather_amplitude', 1):.3f}")
    ek[6].metric("🏛 Structures",    wstats_em.get('n_structures', 0))
    ek[7].metric("💎 Mega-res",      wstats_em.get('n_mega_resources', 0))

    st.divider()

    # ── ROW 1: Meme Grid (black dark) + Pheromone Grid ────────────────────────
    mg_col, ph_col = st.columns(2)

    with mg_col:
        st.markdown("<div class='section-title'>🎨 Meme Grid (Stigmergy) · Cultural Memory Field</div>",
                    unsafe_allow_html=True)

        meme_ch_sel = st.radio(
            "Channel", ["Danger (red)", "Resource (green)", "Sacred (violet)", "Composite RGB"],
            horizontal=True, key='meme_ch_sel'
        )
        meme = W.meme_grid  # (size, size, 3)

        if meme_ch_sel == "Composite RGB":
            mg_img = np.zeros((W.size, W.size, 3), dtype=np.float32)
            mg_img[:, :, 0] = meme[:, :, 0]
            mg_img[:, :, 1] = meme[:, :, 1]
            mg_img[:, :, 2] = meme[:, :, 2]
            max_v = mg_img.max()
            if max_v > 1e-9:
                mg_img /= max_v
            fig_meme = go.Figure(go.Image(
                z=(np.clip(mg_img.transpose(1, 0, 2), 0, 1) * 255).astype(np.uint8),
            ))
        else:
            ch_map = {"Danger (red)": 0, "Resource (green)": 1, "Sacred (violet)": 2}
            ch_cs = {
                "Danger (red)":     [[0, '#000000'], [0.4, '#1a0008'], [1, '#FF0040']],
                "Resource (green)": [[0, '#000000'], [0.4, '#001a06'], [1, '#00FF88']],
                "Sacred (violet)":  [[0, '#000000'], [0.4, '#0d0018'], [1, '#CC44FF']],
            }
            ch = ch_map[meme_ch_sel]
            fig_meme = go.Figure(go.Heatmap(
                z=meme[:, :, ch].T,
                colorscale=ch_cs[meme_ch_sel],
                showscale=True,
                hovertemplate=f'Meme ({meme_ch_sel}) (%{{x}},%{{y}}) = %{{z:.4f}}<extra></extra>',
            ))

        if alive_agents:
            fig_meme.add_trace(go.Scatter(
                x=[a.x for a in alive_agents],
                y=[a.y for a in alive_agents],
                mode='markers',
                marker=dict(size=3, color='white', opacity=0.25),
                hoverinfo='skip', showlegend=False,
            ))

        fig_meme.update_layout(
            paper_bgcolor='#000000', plot_bgcolor='#000000',
            height=400, margin=dict(l=0, r=0, t=8, b=0),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                       range=[-0.5, W.size + 0.5]),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                       range=[-0.5, W.size + 0.5], scaleanchor='x'),
        )
        st.plotly_chart(fig_meme, use_container_width=True, key='meme_grid_v3')
        st.markdown(
            f"<div class='kpi-card'>"
            f"Danger: <span style='color:#FF0040'>{meme[:,:,0].mean():.5f}</span>  ·  "
            f"Resource: <span style='color:#00FF88'>{meme[:,:,1].mean():.5f}</span>  ·  "
            f"Sacred: <span style='color:#CC44FF'>{meme[:,:,2].mean():.5f}</span>"
            f"</div>", unsafe_allow_html=True
        )

    with ph_col:
        st.markdown("<div class='section-title'>🔴 Pheromone Grid · 8-Channel Chemical Stigmergy</div>",
                    unsafe_allow_html=True)

        ph_ch_sel = st.slider("Channel (0–7, or -1 = composite)", -1, 7, -1, key='ph_ch_v3')
        if ph_ch_sel == -1:
            ph_data = W.pheromone_grid.sum(axis=2)
            ph_title = "Composite (all 8 channels)"
        else:
            ph_data = W.pheromone_grid[:, :, ph_ch_sel]
            ph_title = f"Channel {ph_ch_sel}"

        fig_ph = go.Figure(go.Heatmap(
            z=ph_data.T,
            colorscale=[
                [0.00, '#000000'], [0.15, '#04040e'],
                [0.50, '#0a1030'], [0.80, '#2050cc'],
                [1.00, '#7DF9FF'],
            ],
            showscale=True,
            hovertemplate='Pheromone (%{x},%{y}) = %{z:.5f}<extra></extra>',
        ))
        if alive_agents:
            fig_ph.add_trace(go.Scatter(
                x=[a.x for a in alive_agents],
                y=[a.y for a in alive_agents],
                mode='markers',
                marker=dict(size=3, color='rgba(255,255,255,0.2)'),
                hoverinfo='skip', showlegend=False,
            ))
        fig_ph.update_layout(
            paper_bgcolor='#000000', plot_bgcolor='#000000',
            height=400, margin=dict(l=0, r=0, t=28, b=0),
            title=dict(text=ph_title, font=dict(color='#7DF9FF', size=11)),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, scaleanchor='x'),
        )
        st.plotly_chart(fig_ph, use_container_width=True, key='phero_v3')

    st.divider()

    # ── ROW 2: Kuramoto synchrony + Phi consciousness ─────────────────────────
    kur_col2, phi_col2 = st.columns(2)

    with kur_col2:
        st.markdown("<div class='section-title'>🌀 Kuramoto Phase Synchrony</div>",
                    unsafe_allow_html=True)
        if alive_agents:
            import math
            phases = [a.kuramoto_phase for a in alive_agents]
            r_order = wstats_em.get('kuramoto_order', 0)
            xs_k = [math.cos(p) for p in phases]
            ys_k = [math.sin(p) for p in phases]
            colors_k = [f"rgb{a.brain.spectral_rgb()}" for a in alive_agents]

            fig_kur2 = go.Figure()
            theta_ring = np.linspace(0, 2 * np.pi, 120)
            fig_kur2.add_trace(go.Scatter(
                x=np.cos(theta_ring).tolist(), y=np.sin(theta_ring).tolist(),
                mode='lines', line=dict(color='#1a1a3a', width=1),
                hoverinfo='skip', showlegend=False,
            ))
            fig_kur2.add_trace(go.Scatter(
                x=xs_k, y=ys_k, mode='markers',
                marker=dict(size=6, color=colors_k, opacity=0.85,
                            line=dict(width=0.5, color='rgba(255,255,255,0.15)')),
                text=[a.id for a in alive_agents],
                hovertemplate='%{text}<extra></extra>',
                name='Agents',
            ))
            mean_phase = float(np.angle(np.mean([np.exp(1j * p) for p in phases])))
            fig_kur2.add_trace(go.Scatter(
                x=[0, r_order * math.cos(mean_phase)],
                y=[0, r_order * math.sin(mean_phase)],
                mode='lines+markers',
                line=dict(color='#FFD700', width=3),
                marker=dict(size=[0, 10], color='#FFD700'),
                name=f'Order r={r_order:.4f}',
            ))
            fig_kur2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=320, margin=dict(l=10, r=10, t=30, b=10),
                title=dict(text=f'Kuramoto Order r = {r_order:.4f}  (1.0 = full sync)',
                           font=dict(color='#FFD700', size=11)),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                           range=[-1.25, 1.25]),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                           range=[-1.25, 1.25], scaleanchor='x'),
                legend=dict(font=dict(size=9, color='#556'),
                            bgcolor='rgba(0,0,0,0.5)'),
            )
            st.plotly_chart(fig_kur2, use_container_width=True, key='kuramoto_v3')

    with phi_col2:
        st.markdown("<div class='section-title'>Φ IIT Consciousness (Integrated Information Theory)</div>",
                    unsafe_allow_html=True)
        if alive_agents:
            phi_vals2 = [getattr(a, 'phi_value', 0.0) for a in alive_agents]
            strange2  = sum(1 for a in alive_agents if getattr(a, 'strange_loop_active', False))
            phi_arr2  = np.array(phi_vals2)
            verified  = sum(1 for v in phi_vals2 if v > 0.1)

            pc1, pc2, pc3, pc4 = st.columns(4)
            pc1.metric("Φ Mean",   f"{phi_arr2.mean():.4f}")
            pc2.metric("Φ Max",    f"{phi_arr2.max():.4f}")
            pc3.metric("🔁 Loops", strange2)
            pc4.metric("✅ Verified", verified)

            fig_phi2 = go.Figure(go.Histogram(
                x=phi_vals2, nbinsx=30,
                marker=dict(color='#DDA0DD', line=dict(color='#04040e', width=0.5)),
            ))
            fig_phi2.add_vline(x=0.1, line=dict(color='#FFD700', width=1.5, dash='dash'),
                               annotation_text="Φ_critical",
                               annotation_font_color='#FFD700')
            fig_phi2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=220, margin=dict(l=30, r=10, t=32, b=10),
                title=dict(text='Φ Distribution (IIT Consciousness)',
                           font=dict(color='#DDA0DD', size=11)),
                xaxis=dict(title='Φ', color='#445', gridcolor='#0d0d1e'),
                yaxis=dict(title='Agents', color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_phi2, use_container_width=True, key='phi_v3')

            fig_phi_e2 = go.Figure(go.Scatter(
                x=phi_vals2, y=[a.energy for a in alive_agents],
                mode='markers',
                marker=dict(size=5, color='#DDA0DD', opacity=0.60, line=dict(width=0)),
            ))
            fig_phi_e2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=110, margin=dict(l=30, r=10, t=20, b=20),
                title=dict(text='Φ vs Energy', font=dict(color='#aef', size=10)),
                xaxis=dict(title='Φ', color='#445', gridcolor='#0d0d1e'),
                yaxis=dict(title='Energy', color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_phi_e2, use_container_width=True, key='phi_energy_v3')

    st.divider()

    # ── ROW 3: Role Census + Social Economy ───────────────────────────────────
    role_col2, econ_col2 = st.columns(2)

    with role_col2:
        st.markdown("<div class='section-title'>🎭 Role / Caste System</div>", unsafe_allow_html=True)
        if alive_agents:
            ROLE_COLORS = {
                'Queen': '#FFD700', 'Warrior': '#FF4455',
                'Forager': '#44FF88', 'Processor': '#7DF9FF', 'Generalist': '#556'
            }
            roles2 = [getattr(a, 'role', 'Generalist') for a in alive_agents]
            role_u = list(set(roles2))
            role_c = [roles2.count(r) for r in role_u]
            fig_roles2 = go.Figure(go.Pie(
                labels=role_u, values=role_c, hole=0.5,
                marker=dict(colors=[ROLE_COLORS.get(r, '#888') for r in role_u]),
                textfont=dict(size=10, color='#eee'),
            ))
            fig_roles2.update_layout(
                paper_bgcolor='#04040e', height=240,
                margin=dict(l=0, r=0, t=20, b=0),
                title=dict(text=f'Caste Distribution ({len(alive_agents)} agents)',
                           font=dict(color='#aef', size=11), x=0.5),
                font=dict(color='#556', size=9),
                legend=dict(font=dict(size=9, color='#556')),
            )
            st.plotly_chart(fig_roles2, use_container_width=True, key='roles_v3')
            n_fertile2 = sum(1 for a in alive_agents if getattr(a, 'is_fertile', True))
            rc1, rc2 = st.columns(2)
            rc1.metric("👸 Fertile",  n_fertile2)
            rc2.metric("👑 Queens",   roles2.count('Queen'))

    with econ_col2:
        st.markdown("<div class='section-title'>🔄 Social Economy · Trade + Punish + Inventory</div>",
                    unsafe_allow_html=True)
        if alive_agents:
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("🔄 Trades",    cstats.get('total_trades', 0))
            sc2.metric("⚠ Punishments", sum(getattr(a, 'punish_count', 0) for a in alive_agents))
            sc3.metric("🧲 Bonds",     wstats_em.get('n_bonds', 0))

            inv_data2 = [getattr(a, 'inventory', [0, 0, 0]) for a in alive_agents]
            red2   = sum(v[0] for v in inv_data2)
            green2 = sum(v[1] for v in inv_data2)
            blue2  = sum(v[2] for v in inv_data2)
            fig_inv2 = go.Figure(go.Bar(
                x=['Red (Food)', 'Green (Mineral)', 'Blue (Knowledge)'],
                y=[red2, green2, blue2],
                marker=dict(color=['#FF4455', '#44FF88', '#7DF9FF'], line=dict(width=0)),
                text=[f"{v:,}" for v in [red2, green2, blue2]],
                textposition='outside', textfont=dict(size=10, color='#aef'),
            ))
            fig_inv2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=210, margin=dict(l=30, r=10, t=32, b=10),
                title=dict(text='Token Inventory (population total)',
                           font=dict(color='#aef', size=11)),
                xaxis=dict(color='#445'),
                yaxis=dict(color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_inv2, use_container_width=True, key='inventory_v3')

    st.divider()

    # ── ROW 4: Cultural Ratchet + Archetypes + Structures ─────────────────────
    cult_col2, arch_col2, struct_col2 = st.columns(3)

    with cult_col2:
        st.markdown("<div class='section-title'>🍞 Cultural Ratchet (Tradition)</div>",
                    unsafe_allow_html=True)
        continuity2 = estats.get('cultural_continuity', 0.0)
        tradition2  = estats.get('tradition_verified', False)
        cc1, cc2 = st.columns(2)
        cc1.metric("Continuity r", f"{continuity2:.4f}")
        cc2.metric("✔ Tradition",  "✅" if tradition2 else "❌")

        gen_arch2 = EN.gen_behavior_archive
        if len(gen_arch2) >= 2:
            keys2 = sorted(gen_arch2.keys())
            fig_cult2 = go.Figure()
            for i, key2 in enumerate(keys2[-6:]):
                profile2 = gen_arch2[key2]
                fig_cult2.add_trace(go.Scatter(
                    y=np.abs(profile2).tolist(),
                    mode='lines', name=f"Gen {key2}",
                    line=dict(width=1.2),
                    opacity=0.4 + 0.6 * (i / max(len(keys2[-6:]) - 1, 1)),
                ))
            fig_cult2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=180, margin=dict(l=30, r=10, t=10, b=10),
                xaxis=dict(color='#445', showgrid=False),
                yaxis=dict(color='#445', gridcolor='#0d0d1e'),
                legend=dict(font=dict(size=7, color='#556'), bgcolor='rgba(0,0,0,0.5)'),
                font=dict(color='#445', size=8),
            )
            st.plotly_chart(fig_cult2, use_container_width=True, key='cult_ratchet_v3')
        else:
            st.info("Run 50+ ticks for cultural data.")

    with arch_col2:
        st.markdown("<div class='section-title'>🔍 Behavioral Archetypes (KMeans)</div>",
                    unsafe_allow_html=True)
        arch_c2 = estats.get('archetype_counts', {})
        if arch_c2:
            ARCH_C = {'Explorer': '#7DF9FF', 'Builder': '#FFD700',
                      'Fighter': '#FF4455', 'Thinker': '#DDA0DD'}
            fig_arch2 = go.Figure(go.Bar(
                x=list(arch_c2.keys()), y=list(arch_c2.values()),
                marker=dict(color=[ARCH_C.get(k, '#888') for k in arch_c2],
                            line=dict(width=0)),
                text=list(arch_c2.values()),
                textposition='outside', textfont=dict(size=11, color='#aef'),
            ))
            fig_arch2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=210, margin=dict(l=30, r=10, t=24, b=10),
                title=dict(text='Behavior Archetypes', font=dict(color='#aef', size=11)),
                xaxis=dict(color='#445'),
                yaxis=dict(color='#445', gridcolor='#0d0d1e'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_arch2, use_container_width=True, key='archetypes_v3')
        else:
            st.info("Run 15+ ticks.")

    with struct_col2:
        st.markdown("<div class='section-title'>🏗 Structures on Field</div>",
                    unsafe_allow_html=True)
        structs2 = W.structures
        if structs2:
            SCOL = {'trap': '#FF4455', 'battery': '#FFD700', 'cultivator': '#44FF88'}
            stypes2 = list(set(s.struct_type for s in structs2.values()))
            fig_s2 = go.Figure()
            for stype in stypes2:
                xs_s2 = [pos[0] for pos, s in structs2.items() if s.struct_type == stype]
                ys_s2 = [pos[1] for pos, s in structs2.items() if s.struct_type == stype]
                durs2 = [s.durability for pos, s in structs2.items() if s.struct_type == stype]
                fig_s2.add_trace(go.Scatter(
                    x=xs_s2, y=ys_s2, mode='markers', name=stype,
                    marker=dict(size=11, symbol='square',
                                color=SCOL.get(stype, '#888'), opacity=0.9,
                                line=dict(width=1, color='rgba(255,255,255,0.25)')),
                    text=[f"{stype}<br>dur:{d:.0f}" for d in durs2],
                    hovertemplate='%{text}<extra></extra>',
                ))
            fig_s2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=225, margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                           range=[-0.5, W.size + 0.5]),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                           range=[-0.5, W.size + 0.5], scaleanchor='x'),
                legend=dict(font=dict(size=8, color='#556'), bgcolor='rgba(0,0,0,0.5)'),
            )
            st.plotly_chart(fig_s2, use_container_width=True, key='structs_v3')
        else:
            st.info("No structures yet — agents need more ticks to build.")

    st.divider()

    # ── ROW 5: Active Inference + GoL Scratchpad + DNA Export ─────────────────
    ai_col2, gol_col2, dna_col2 = st.columns(3)

    with ai_col2:
        st.markdown("<div class='section-title'>📐 Active Inference · Prediction Errors</div>",
                    unsafe_allow_html=True)
        if alive_agents:
            top_ai2 = sorted(alive_agents, key=lambda a: a.energy, reverse=True)[:5]
            fig_ai2 = go.Figure()
            for a in top_ai2:
                errors2 = a.brain.prediction_errors[-40:]
                if errors2:
                    fig_ai2.add_trace(go.Scatter(
                        y=errors2, mode='lines', name=a.id,
                        line=dict(width=1.5), opacity=0.8,
                    ))
            conf_vals2 = [a.brain.confidence for a in alive_agents]
            avg_conf2 = float(np.mean(conf_vals2)) if conf_vals2 else 0
            fig_ai2.update_layout(
                paper_bgcolor='#04040e', plot_bgcolor='#04040e',
                height=210, margin=dict(l=30, r=10, t=32, b=10),
                title=dict(text=f'Prediction Errors | avg conf={avg_conf2:.3f}',
                           font=dict(color='#aef', size=10)),
                xaxis=dict(color='#445', showgrid=False),
                yaxis=dict(color='#445', gridcolor='#0d0d1e'),
                legend=dict(font=dict(size=7, color='#556'), bgcolor='rgba(0,0,0,0.5)'),
                font=dict(color='#445', size=9),
            )
            st.plotly_chart(fig_ai2, use_container_width=True, key='active_inference_v3')

    with gol_col2:
        st.markdown("<div class='section-title'>🧩 GoL Scratchpad (Largest Writer)</div>",
                    unsafe_allow_html=True)
        if alive_agents:
            top_gol2 = max(alive_agents, key=lambda a: getattr(a, 'scratchpad_writes', 0))
            pad2 = top_gol2.scratchpad.astype(float)
            sw   = getattr(top_gol2, 'scratchpad_writes', 0)
            fig_gol2 = go.Figure(go.Heatmap(
                z=pad2.T,
                colorscale=[[0, '#000000'], [1, '#00FF88']],
                showscale=False, hoverinfo='skip',
            ))
            fig_gol2.update_layout(
                paper_bgcolor='#000000', plot_bgcolor='#000000',
                height=210, margin=dict(l=0, r=0, t=32, b=0),
                title=dict(text=f'{top_gol2.id} GoL · {sw} writes',
                           font=dict(color='#00FF88', size=10)),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, scaleanchor='x'),
            )
            st.plotly_chart(fig_gol2, use_container_width=True, key='gol_v3')

    with dna_col2:
        st.markdown("<div class='section-title'>🧬 Simulation DNA Export</div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div class='kpi-card'>"
            f"Tradition: <span style='color:#{'44FF88' if estats.get('tradition_verified') else '556'}'>"
            f"{'✅ Verified' if estats.get('tradition_verified') else '❌ Not yet'}</span><br>"
            f"Cultural r: <span style='color:#7DF9FF'>{estats.get('cultural_continuity',0):.4f}</span><br>"
            f"Archetypes: {', '.join(f'{k}:{v}' for k,v in estats.get('archetype_counts',{}).items()) or 'none yet'}<br>"
            f"Bonds: <span style='color:#FFD700'>{wstats_em.get('n_bonds',0)}</span><br>"
            f"Structures: <span style='color:#FF8C00'>{wstats_em.get('n_structures',0)}</span><br>"
            f"Mega-res: <span style='color:#DDA0DD'>{wstats_em.get('n_mega_resources',0)}</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        if st.button("🧬 Export DNA (JSON)", use_container_width=True, key='dna_export'):
            import json
            dna = EN.export_simulation_dna(civ=C, world=W)
            def _np_fix(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    return float(obj)
                if isinstance(obj, dict):
                    return {k: _np_fix(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [_np_fix(x) for x in obj]
                return obj
            dna_clean = _np_fix(dna)
            st.download_button(
                label="⬇ Download DNA.json",
                data=json.dumps(dna_clean, indent=2),
                file_name=f"hyperagent_dna_tick{W.step_count}.json",
                mime="application/json",
                use_container_width=True,
                key='dna_download',
            )


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown(
    "<div style='text-align:center;font-family:monospace;font-size:10px;"
    "color:#151530;padding:8px'>"
    "HyPER AgEnT v3.0 · HyperAgent Edition · K_DIM=32 · 96 Agents · 30 GeNeSIS Features<br>"
    "Metacognitive Self-Modification · Stigmergy · Pheromones · Gödel-Encoded Inventions · Zero LLM<br>"
    "Invented by Devanik &amp; Claude (Xylia) · 2025–2026"
    "</div>",
    unsafe_allow_html=True
)