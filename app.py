import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"
ENTITIES_PATH = PROJECT_DIR / "data" / "processed" / "rdb_tourism_entities_enriched.csv"

st.set_page_config(
    page_title="TourismGuard AI",
    page_icon=":material/travel_explore:",
    layout="wide",
)

dark_mode = True
page_palette = """
    --tg-page: #0b1213;
    --tg-surface: #131f20;
    --tg-surface-raised: #172522;
    --tg-text: #f2f7f5;
    --tg-muted: #c0d0cb;
    --tg-line: rgba(202, 231, 215, .2);
    --tg-glow: rgba(46, 112, 91, .13);
    --tg-header: rgba(11, 18, 19, .94);
    --tg-feature-law: #1c2938;
    --tg-feature-visit: #1b3027;
    --tg-feature-about: #29243a;
"""

st.html(
    """
    <style>
    :root {
        __PAGE_PALETTE__
        color-scheme: __COLOR_SCHEME__;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 8% 0%, var(--tg-glow), transparent 34rem),
            var(--tg-page);
        color: var(--tg-text);
        transition: background-color .25s ease, color .25s ease;
    }

    .stApp :is(h1, h2, h3, h4, p, label) {
        color: var(--tg-text);
    }

    .block-container {
        max-width: 1500px;
        padding: 1.1rem 1.1rem 1rem;
    }

    [data-testid="stHeader"] {
        background: var(--tg-header);
        backdrop-filter: blur(12px);
    }

    [data-testid="stSidebar"] {
        min-width: 178px;
        max-width: 205px;
        background: linear-gradient(180deg, #073a36 0%, #0b4c43 68%, #073630 100%);
        border-right: 1px solid rgba(255,255,255,.08);
        color: #f2faf6;
    }

    [data-testid="stSidebar"] :is(h1, h2, h3, h4, p, label, span) {
        color: #f2faf6;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button {
        justify-content: flex-start;
        border: 1px solid transparent;
        border-radius: 9px;
        background: transparent;
        color: #eff8f4;
        font-size: 13px;
        text-align: left;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button:hover,
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
        border-color: rgba(111, 212, 172, .28);
        background: rgba(41, 146, 107, .42);
        color: #fff;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button p {
        color: inherit;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] {
        margin-bottom: .22rem;
    }

    [data-testid="stChatMessage"] {
        border: 1px solid var(--tg-line);
        border-radius: 18px;
        background: var(--tg-surface);
        animation: tg-message-in .32s ease both;
    }

    [data-testid="stChatInput"] textarea {
        background: var(--tg-surface);
        color: var(--tg-text);
        border: 1px solid var(--tg-line);
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--tg-muted);
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: #168c83;
        box-shadow: 0 0 0 2px rgba(22, 140, 131, .18);
    }

    [data-testid="stChatInput"] > div {
        background: var(--tg-surface);
        border-color: var(--tg-line);
    }

    [data-testid="stButton"] button,
    [data-testid="stToggle"] label {
        transition: transform .16s ease, box-shadow .16s ease;
    }

    [data-testid="stButton"] button:hover {
        transform: translateY(-1px);
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] {
        color: var(--tg-text);
    }

    [data-testid="stCaptionContainer"] {
        opacity: 1;
    }

    [data-testid="stCaptionContainer"] p {
        color: var(--tg-muted);
    }

    [data-testid="stForm"] input::placeholder {
        color: var(--tg-muted);
        opacity: 1;
    }

    [data-testid="stButton"] button p {
        color: inherit;
    }

    [data-testid="stStatusWidget"] p,
    [data-testid="stStatusWidget"] span {
        color: var(--tg-text);
    }

    [data-testid="stExpander"] {
        border-color: var(--tg-line);
        border-radius: 16px;
        background: var(--tg-surface);
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--tg-line);
        border-radius: 12px;
        background: var(--tg-surface);
    }

    .st-key-question-card,
    .st-key-info-card,
    .st-key-about-card {
        border-color: var(--tg-line);
        box-shadow: 0 4px 18px rgba(0, 0, 0, .12);
    }

    .st-key-feature-law {
        background: var(--tg-feature-law);
        border-color: var(--tg-line);
    }

    .st-key-feature-visit {
        background: var(--tg-feature-visit);
        border-color: var(--tg-line);
    }

    .st-key-feature-about {
        background: var(--tg-feature-about);
        border-color: var(--tg-line);
    }

    [data-testid="stForm"] {
        border: 1.5px solid #23aa7d;
        border-radius: 12px;
        background: var(--tg-surface);
        box-shadow: 0 5px 16px rgba(18, 123, 91, .08);
    }

    [data-testid="stForm"] [data-testid="stTextInput"] input {
        border: 0;
        background: transparent;
        color: var(--tg-text);
        box-shadow: none;
    }

    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        min-height: 2.55rem;
        border-radius: 9px;
    }

    [data-testid="stMarkdownContainer"] h3 {
        font-size: 1.05rem;
    }

    [data-testid="stMarkdownContainer"] h4 {
        margin-bottom: .3rem;
        font-size: .91rem;
    }

    .sidebar-brand {
        display:flex;
        align-items:center;
        gap:10px;
        margin: .45rem 0 0;
        color:#fff;
        font-size:11px;
        line-height:1.35;
        letter-spacing:.08em;
    }

    .sidebar-brand strong { font-size:12px; }
    .sidebar-brand-icon {
        display:grid;
        place-items:center;
        width:35px;
        height:35px;
        border-radius:11px;
        background:#f1c846;
        color:#10483e;
        font-size:22px;
    }
    .sidebar-caption {
        margin: .65rem 0 1.25rem 45px;
        color:#a8d0bd;
        font-size:8px;
        letter-spacing:.13em;
    }
    .sidebar-bottom {
        margin-top: 25vh;
        padding: 0 5px;
        color:#e4f4ed;
    }
    .sidebar-landscape {
        height:70px;
        color:#53a68b;
        font-size:43px;
        letter-spacing:-.28em;
        opacity:.7;
    }
    .sidebar-bottom p { font-size:11px;line-height:1.55; }
    .sidebar-bottom span { color:#9fc9b7;font-size:8px;letter-spacing:.12em; }

    .robot-icon {
        display:grid;
        place-items:center;
        width:50px;
        height:50px;
        border-radius:16px;
        background:#eaf4ff;
        color:#1765b4;
        font-size:30px;
    }

    .app-footer {
        display:flex;
        justify-content:space-between;
        gap:12px;
        margin: 1rem -1.1rem -1rem;
        padding: 11px 18px;
        color:#e6f2ee;
        background:#0c2829;
        font-size:9px;
        text-align:center;
    }
    .app-footer i {
        display:inline-block;
        width:7px;
        height:7px;
        margin-right:4px;
        border-radius:50%;
        background:#27c68b;
    }

    @keyframes tg-message-in {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 760px) {
        .block-container {
            padding-top: .75rem;
        }
        .app-footer { flex-direction:column; }
        .sidebar-bottom { margin-top: 1rem; }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: .01ms !important;
        }
    }
    </style>
    """
    .replace("__PAGE_PALETTE__", page_palette)
    .replace("__COLOR_SCHEME__", "dark" if dark_mode else "light")
)

TRAVEL_HERO = st.components.v2.component(
    "tourismguard_rwanda_hero",
    html="""
    <br><br>
    <section class="travel-hero" aria-label="Discover Rwanda">
      <div class="hero-copy">
        <div class="brand-lockup">
          <svg class="brand-mark" viewBox="0 0 72 72" aria-hidden="true">
            <circle cx="36" cy="36" r="34" fill="#fff"/>
            <path d="M8 41 25 23l12 11 11-12 18 20-17-9-11 9-12-8-13 10Z" fill="#164a43"/>
            <path d="M16 47c11-6 22-7 39-3-8 4-15 11-20 18-6-3-13-8-19-15Z" fill="#35a47e"/>
            <path d="M19 13 31 7l5 8-12 5Zm18-7 14 5-1 9-13-5Zm18 11 9 10-7 6-8-10Z" fill="#f3c63e"/>
          </svg>
          <div class="brand-name">
            <strong>Rwanda<br/>TourismGuard AI</strong>
            <span>Rwanda tourism law and RDB-listed entities</span>
          </div>
        </div> <br>
       
      </div>
      <div class="hero-art">
        <svg class="rwanda-scene" viewBox="0 0 1200 320"
             preserveAspectRatio="xMidYMid slice" role="img"
             aria-label="Vector landscape of Rwanda's Virunga volcanoes, including Mount Karisimbi and Mount Bisoke">
          <defs>
            <linearGradient id="volcano-sky" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stop-color="#668c8b"/>
              <stop offset=".58" stop-color="#b6c8b7"/>
              <stop offset="1" stop-color="#e0d9b9"/>
            </linearGradient>
            <linearGradient id="volcano-rock" x1="0" y1="0" x2=".8" y2="1">
              <stop offset="0" stop-color="#899c86"/>
              <stop offset=".48" stop-color="#607e6e"/>
              <stop offset="1" stop-color="#354f48"/>
            </linearGradient>
            <linearGradient id="volcano-forest" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stop-color="#456e57"/>
              <stop offset="1" stop-color="#183e35"/>
            </linearGradient>
            <linearGradient id="volcano-mist" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stop-color="#e5e5d1" stop-opacity=".02"/>
              <stop offset="1" stop-color="#d8dfca" stop-opacity=".68"/>
            </linearGradient>
            <filter id="ridge-soften" x="-10%" y="-10%" width="120%" height="120%">
              <feGaussianBlur stdDeviation="1.4"/>
            </filter>
            <clipPath id="virunga-frame">
              <rect width="1200" height="320" rx="20"/>
            </clipPath>
          </defs>
          <g clip-path="url(#virunga-frame)">
            <rect width="1200" height="320" fill="url(#volcano-sky)"/>
            <circle cx="925" cy="72" r="34" fill="#f0d39a" opacity=".82"/>
            <circle cx="925" cy="72" r="58" fill="#f0d39a" opacity=".12"/>

            <path d="M0 184 104 131l86 31 126-72 89 66 101-30 102 49 112-83 95 39 85-43 100 57 100-42v125H0Z"
                  fill="#a3b4a2" opacity=".68"/>
            <path d="M0 206 119 169l96 29 104-43 101 38 121-36 95 44 111-40 100 35 113-48 111 48 129-30v115H0Z"
                  fill="#829985" opacity=".74"/>

            <path d="M86 264 226 218l71-46 66 14 75-67 67-87 49 70 48 69 69 39 67-34 58-48 48 24 70-17 73 48 96-31 100 41v132H86Z"
                  fill="url(#volcano-rock)"/>
            <path d="m363 186 75-67 67-87 49 70 48 69-51-26-38-55-16 44-33-18-25 45Z"
                  fill="#c0c5ab" opacity=".72"/>
            <path d="m465 119 40-87 49 70-39-24-13 31-17-12-9 27Z"
                  fill="#d9d8c0" opacity=".83"/>
            <path d="M86 264 226 218l71-46 66 14 75-67 67-87 49 70 48 69 69 39"
                  fill="none" stroke="#d0cdb1" stroke-width="3" opacity=".42"/>

            <path d="m662 229 75-38 46-52 34-68 37 54 40 52 54 34 55-18 57-37 55 29 85-18v154H662Z"
                  fill="#526f5e" opacity=".93"/>
            <path d="m817 139 34-68 37 54-32-19-12 29-12-11-11 24Z"
                  fill="#d5d3bc" opacity=".72"/>
            <path d="M0 240c115-41 191-18 290-32 95-14 173 10 258 27 92 18 167-27 263-14 108 15 176-4 389 27v92H0Z"
                  fill="url(#volcano-mist)" filter="url(#ridge-soften)"/>

            <path d="M0 248c106-26 185-7 280 4 108 13 170-13 270-8 103 5 151 37 260 17 120-22 219-20 390 8v83H0Z"
                  fill="#54745e"/>
            <path d="M0 278c120-29 187 1 285 12 106 12 183-24 275-12 112 15 167 38 279 16 122-24 220-16 361 6v55H0Z"
                  fill="url(#volcano-forest)"/>
            <path d="M0 301c119-18 202 9 299 12 116 4 183-23 285-11 120 14 201 29 304 10 113-20 208-8 312 7v36H0Z"
                  fill="#17392f"/>

            <g fill="#183d32" opacity=".94">
              <path d="m48 307 17-55 18 55h-12v21H60v-21Zm61 4 13-42 14 42h-9v17h-9v-17Zm953-4 16-51 17 51h-11v23h-10v-23Zm63 6 12-39 13 39h-9v17h-8v-17Z"/>
            </g>
            <path d="M0 0h1200v320H0Z" fill="none" stroke="#fff" stroke-opacity=".2" stroke-width="2"/>
          </g>
        </svg>
        <div class="rdb-mark"><strong>RDB</strong><span>RWANDA DEVELOPMENT BOARD</span></div>
      </div>
      <div class="hero-glow"></div>
    </section>
    """,
    css="""
    :host { display:block; }
    .travel-hero {
      --px: 0px;
      --py: 0px;
      position:relative;
      display:grid;
      grid-template-columns: minmax(290px, .9fr) minmax(390px, 1.5fr);
      align-items:center;
      min-height: 122px;
      overflow:hidden;
      isolation:isolate;
      padding: 12px 18px;
      border:1px solid #dfe9e8;
      border-radius:0 0 0 18px;
      color:#143c39;
      background:linear-gradient(110deg,#fff 0%,#f6fbff 42%,#d8edf5 100%);
      box-shadow:0 8px 24px rgba(27,64,78,.08);
      font-family:inherit;
    }
    .hero-copy {
      position:relative; z-index:2; display:flex;align-items:center;justify-content:space-between;
      gap:14px;padding:0 10px 0 2px;
    }
    .brand-lockup { display:flex;align-items:center;gap:12px;min-width:0; }
    .brand-mark { flex:none;width:58px;height:58px;filter:drop-shadow(0 4px 7px #17483b20); }
    .brand-name { max-width:195px; }
    .brand-name strong { display:block;color:#123d39;font-size:clamp(15px,1.8vw,22px);line-height:1.02;letter-spacing:-.035em; }
    .brand-name span { display:block;margin-top:6px;color:#355953;font-size:9px;line-height:1.35; }
    .brand-slogan { position:relative;z-index:2;flex:none;text-align:center;padding:0 8px; }
    .brand-slogan strong { display:block;color:#087361;font:italic 600 20px Georgia,serif; }
    .brand-slogan span { display:block;margin-top:3px;color:#15564d;font-size:9px; }
    .brand-slogan i { display:block;width:44px;height:8px;margin:5px auto 0;border-top:2px solid #1b9c72;border-radius:50%;transform:rotate(-5deg); }
    .hero-art {
      position:relative;align-self:stretch;min-height:100px;margin:-12px -18px -12px 0;
      transform:translate3d(var(--px),var(--py),0);transition:transform .18s ease-out;
    }
    .rwanda-scene { position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(.92); }
    .sun-halo { position:absolute;width:90px;height:90px;right:23%;top:-22px;border:1px solid #fff8;border-radius:50%;box-shadow:0 0 0 14px #ffffff38,0 0 0 27px #ffffff1a; }
    .bird { transform-origin:435px 100px;animation:bird-drift 5s ease-in-out infinite; }
    .tree { transform-origin:center bottom;animation:hill-sway 6s ease-in-out infinite alternate; }
    .rdb-mark { position:absolute;top:12px;right:17px;display:flex;align-items:center;gap:6px;padding:5px 8px;color:#fff;background:#117caeD9;border-radius:4px;box-shadow:0 4px 10px #173e5535; }
    .rdb-mark strong { font-size:14px;letter-spacing:-.04em; }
    .rdb-mark span { max-width:74px;font-size:6px;line-height:1.1; }
    .travel-hero[data-theme="dark"] {
      border-color:#294d47;
      background:linear-gradient(110deg,#182e2a 0%,#203b36 42%,#284c47 100%);
      color:#eef7f1;
    }
    .travel-hero[data-theme="dark"] .brand-name strong { color:#f2f8f3; }
    .travel-hero[data-theme="dark"] .brand-name span { color:#bfd3cb; }
    .travel-hero[data-theme="dark"] .brand-slogan span { color:#c4e1d5; }
    .hero-glow { position:absolute;z-index:-1;width:180px;height:180px;right:-70px;top:-100px;border-radius:50%;background:#b1d97725;filter:blur(3px); }
    @keyframes bird-drift { 0%,100% { transform:translate(0,0); } 50% { transform:translate(5px,-5px); } }
    @media(max-width:760px) {
      .travel-hero { grid-template-columns:1fr 1fr;min-height:105px;padding:8px 10px; }
      .hero-copy { display:block;padding:0; }
      .brand-mark { width:39px;height:39px; }
      .brand-lockup { gap:7px; }
      .brand-name { max-width:150px; }
      .brand-name strong { font-size:14px; }
      .brand-name span { font-size:7px; }
      .brand-slogan { display:none; }
      .hero-art { min-height:85px;margin:-8px -10px -8px 0; }
      .rdb-mark { top:6px;right:8px; }
    }
    @media(prefers-reduced-motion:reduce) {
      *,*::before,*::after { animation-duration:.01ms!important;animation-iteration-count:1!important;transition-duration:.01ms!important; }
    }
    """,
    js="""
    export default function (component) {
      const { data } = component
      const hero = component.parentElement.querySelector(".travel-hero")
      if (!hero) return
      hero.dataset.theme = data?.dark ? "dark" : "light"
      if (hero.dataset.parallaxReady) return
      hero.dataset.parallaxReady = "true"

      const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)")
      if (reducedMotion.matches) return

      let frame = 0
      hero.addEventListener("pointermove", (event) => {
        if (event.pointerType === "touch" || frame) return
        frame = window.requestAnimationFrame(() => {
          const bounds = hero.getBoundingClientRect()
          const x = (event.clientX - bounds.left) / bounds.width - 0.5
          const y = (event.clientY - bounds.top) / bounds.height - 0.5
          hero.style.setProperty("--px", `${x * 7}px`)
          hero.style.setProperty("--py", `${y * 5}px`)
          frame = 0
        })
      })
      hero.addEventListener("pointerleave", () => {
        hero.style.setProperty("--px", "0px")
        hero.style.setProperty("--py", "0px")
      })
    }
    """,
)


@st.cache_resource
def load_rag():
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    import rag

    return rag


def answer_question(question):
    rag = load_rag()
    return rag.answer(question)


@st.cache_data
def load_dashboard_data():
    return pd.read_csv(ENTITIES_PATH, dtype=str).fillna("")


def render_message(message):
    entity_table = message.get("entity_table")
    if entity_table and entity_table["kind"] == "entity":
        st.subheader(entity_table["name"])
        st.table(
            pd.DataFrame(entity_table["details"], columns=["Field", "Value"])
        )
        for link in entity_table["links"]:
            st.link_button(link["label"], link["url"])
    elif entity_table and entity_table["kind"] == "entity_list":
        st.markdown(message["content"])
        st.dataframe(
            pd.DataFrame(entity_table["rows"]),
            column_config={
                "Website": st.column_config.LinkColumn("Website"),
                "RDB profile": st.column_config.LinkColumn("RDB profile"),
            },
            hide_index=True,
            width="stretch",
            height=420,
        )
    else:
        st.markdown(message["content"])
    if message.get("seconds") is not None:
        details = f"Answered in {message['seconds']:.2f} seconds"
        sources = message.get("sources", [])
        if sources:
            details += " · Sources: " + ", ".join(sources)
        st.caption(details)


def queue_question(question):
    st.session_state["pending_question"] = question


def select_history(message_index):
    st.session_state["selected_history_index"] = message_index


def get_history_pairs(messages):
    pairs = []
    pending_user = None
    for index, message in enumerate(messages):
        if message["role"] == "user":
            pending_user = (index, message)
        elif message["role"] == "assistant" and pending_user is not None:
            pairs.append((pending_user[0], pending_user[1], message))
            pending_user = None
    return pairs


def open_entity_directory():
    st.session_state["open_entity_directory"] = True


if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_history_index" not in st.session_state:
    st.session_state.selected_history_index = None

TRAVEL_HERO(key="tourismguard-hero", data={"dark": True})

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <span class="sidebar-brand-icon">✦</span>
          <span>RWANDA<br/><strong>TOURISM GUARD</strong></span>
        </div>
        <div class="sidebar-caption">RWANDA TOURISM INFORMATION</div>
        """,
        unsafe_allow_html=True,
    )
    st.button(
        "Ask about tourism law",
        icon=":material/chat_bubble:",
        type="primary",
        width="stretch",
        key="nav_ask",
        on_click=queue_question,
        args=("What are the licensing rules for tour operators?",),
    )
    st.button(
        "Browse entity directory",
        icon=":material/hotel:",
        width="stretch",
        key="nav_directory",
        on_click=open_entity_directory,
    )
    history_panel = st.sidebar.container()
    st.markdown(
        """
        <div class="sidebar-bottom">
          <div class="sidebar-landscape" aria-hidden="true">⌁⌁⌁</div>
          <p>Explore Rwanda<br/>Tourism law<br/>Entity directory</p>
          <span>RWANDA&nbsp; · &nbsp;TOURISM&nbsp; · &nbsp;TRUST</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

main_column, info_column = st.columns([2.12, 0.92], gap="small")
question_submitted = False
question_text = ""
with main_column:
    with st.container(border=True, key="question-card"):
        greet_column, greeting_text = st.columns([0.72, 8], vertical_alignment="center")
        with greet_column:
            st.markdown(
                '<div class="robot-icon">🤖</div>',
                unsafe_allow_html=True,
            )
        with greeting_text:
            st.markdown("### Hello! 👋")
            st.markdown("#### I’m Rwanda TourismGuard AI")
            st.caption(
                "Ask about Rwanda’s tourism law, operating licences, or "
                "businesses in the project’s tourism-entity directory."
            )

        st.warning(
            "Informational only—not legal advice. The law and entity data may "
            "be incomplete or out of date; verify important details with "
            "official sources."
        )

        entities_data = load_dashboard_data()

        with st.form("question_form", clear_on_submit=True, border=False):
            input_column, send_column = st.columns([10, 1], vertical_alignment="bottom")
            with input_column:
                question_text = st.text_input(
                    "Your question",
                    key="question_input",
                    label_visibility="collapsed",
                    placeholder="Ask about Rwanda’s tourism law or a listed tourism business…",
                )
            with send_column:
                question_submitted = st.form_submit_button(
                    "Send",
                    icon=":material/send:",
                    type="primary",
                    width="stretch",
                )

        trust_columns = st.columns(4)
        trust_columns[0].caption(":material/verified_user: Grounded in local data")
        trust_columns[1].caption(":material/article: Sources included")
        trust_columns[2].caption(":material/block: Out-of-scope safeguards")
        trust_columns[3].caption(":material/lock: Local model inference")

    pending_question = st.session_state.pop("pending_question", "")
    active_question = pending_question or (
        question_text.strip() if question_submitted else ""
    )
    if active_question:
        st.session_state.selected_history_index = None
        st.session_state.messages.append(
            {"role": "user", "content": active_question}
        )
        with st.status("Finding a helpful answer…", expanded=False) as status:
            try:
                result = answer_question(active_question)
            except Exception as error:
                status.update(label="Could not answer this question", state="error")
                st.error(f"TourismGuard could not complete the request: {error}")
                result = None
            else:
                status.update(label="Answer ready", state="complete")
        if result is not None:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "seconds": float(result["seconds"]),
                    "sources": result.get("sources", []),
                    "entity_table": result.get("entity_table"),
                }
            )

    history_pairs = get_history_pairs(st.session_state.messages)
    with history_panel:
        with st.expander(
            f"Session history ({len(history_pairs)})",
            expanded=bool(history_pairs),
            icon=":material/history:",
        ):
            if not history_pairs:
                st.caption(
                    "Questions and answers from this session will appear here."
                )
            else:
                for message_index, user_message, _ in reversed(history_pairs):
                    question_label = (
                        user_message["content"].strip().replace("\n", " ")
                    )
                    if len(question_label) > 42:
                        question_label = question_label[:39] + "..."
                    st.button(
                        question_label,
                        key=f"history-{message_index}",
                        width="stretch",
                        on_click=select_history,
                        args=(message_index,),
                    )

    if st.session_state.messages:
        selected_history_index = st.session_state.selected_history_index
        selected_pair = next(
            (
                (user_message, assistant_message)
                for message_index, user_message, assistant_message
                in get_history_pairs(st.session_state.messages)
                if message_index == selected_history_index
            ),
            None,
        )
        visible_messages = (
            [selected_pair[0], selected_pair[1]]
            if selected_pair is not None
            else st.session_state.messages[-8:]
        )
        with st.container(border=True, key="conversation-card"):
            if selected_pair is not None:
                st.caption("Viewing a saved question from this session.")
            for message in visible_messages:
                with st.chat_message(message["role"]):
                    render_message(message)

    st.markdown("### Explore with TourismGuard")
    feature_columns = st.columns(3)
    feature_cards = [
        (
            "Tourism rules & law",
            "Understand Rwanda’s tourism laws and licensing requirements.",
            "Ask about the law",
            ":material/balance:",
            "What are the licensing rules for tour operators?",
            "feature-law",
        ),
        (
            "Tourism entity directory",
            "Find listed tourism businesses by category and district.",
            "Browse entities",
            ":material/hotel:",
            "Which hotels are in Musanze?",
            "feature-entities",
        ),
        (
            "Entity details",
            "Check a listed business’s location, licence status, and available details.",
            "Find entity details",
            ":material/business:",
            "Where is GORILLA HUB SAFARIS LTD located?",
            "feature-entity-details",
        ),
    ]
    for card_column, (title, detail, button, icon, query, key) in zip(
        feature_columns, feature_cards
    ):
        with card_column:
            with st.container(border=True, key=key):
                st.markdown(f"### {icon}")
                st.markdown(f"#### {title}")
                st.caption(detail)
                st.button(
                    button,
                    key=f"{key}-button",
                    icon=":material/arrow_forward:",
                    width="stretch",
                    on_click=queue_question,
                    args=(query,),
                )

    directory_expanded = st.session_state.get("open_entity_directory", False)
    with st.expander(
        "Browse the tourism-entity directory",
        expanded=directory_expanded,
        icon=":material/manage_search:",
    ):
        st.caption(
            "Filter the project’s saved entity records by name, category, "
            "district, and licence status."
        )
        search_column, category_column, district_column, status_column = st.columns(
            [2, 1, 1, 1]
        )
        with search_column:
            entity_search = st.text_input(
                "Search business name",
                key="dashboard_entity_search",
                placeholder="e.g. Serena",
            ).strip()
        with category_column:
            selected_category = st.selectbox(
                "Category",
                ["All"] + sorted(entities_data["category"].unique().tolist()),
                key="dashboard_entity_category",
            )
        with district_column:
            selected_district = st.selectbox(
                "District",
                ["All"] + sorted(entities_data["district"].unique().tolist()),
                key="dashboard_entity_district",
            )
        with status_column:
            selected_status = st.selectbox(
                "Licence status",
                ["All"] + sorted(entities_data["status"].unique().tolist()),
                key="dashboard_entity_status",
            )

        filtered_entities = entities_data
        if entity_search:
            filtered_entities = filtered_entities[
                filtered_entities["entity_name"].str.contains(
                    entity_search, case=False, regex=False, na=False
                )
            ]
        if selected_category != "All":
            filtered_entities = filtered_entities[
                filtered_entities["category"] == selected_category
            ]
        if selected_district != "All":
            filtered_entities = filtered_entities[
                filtered_entities["district"] == selected_district
            ]
        if selected_status != "All":
            filtered_entities = filtered_entities[
                filtered_entities["status"] == selected_status
            ]

        st.caption(
            f"Showing {len(filtered_entities):,} of {len(entities_data):,} records"
        )
        if filtered_entities.empty:
            st.info("No tourism entities match these filters.")
        else:
            directory_columns = [
                "entity_name",
                "sub_category",
                "district",
                "province",
                "status",
            ]
            st.dataframe(
                filtered_entities[directory_columns],
                hide_index=True,
                width="stretch",
                height=340,
                column_config={
                    "entity_name": "Business",
                    "sub_category": "Type",
                    "district": "District",
                    "province": "Province",
                    "status": "Licence status",
                },
            )

            selected_index = st.selectbox(
                "View a business profile",
                list(range(len(filtered_entities))),
                format_func=lambda index: (
                    f"{filtered_entities.iloc[index]['entity_name']} — "
                    f"{filtered_entities.iloc[index]['district']} "
                    f"({filtered_entities.iloc[index]['sub_category']})"
                ),
                key="dashboard_entity_profile",
            )
            selected_entity = filtered_entities.iloc[selected_index]
            detail_columns = st.columns(3)
            detail_columns[0].markdown(
                f"**Category**  \n{selected_entity['category']}"
            )
            detail_columns[1].markdown(
                f"**Location**  \n{selected_entity['district']}, "
                f"{selected_entity['province']}"
            )
            detail_columns[2].markdown(
                f"**Licence status**  \n{selected_entity['status']}"
            )
            if selected_entity["description"]:
                st.write(selected_entity["description"])
            if "guide" not in selected_entity["sub_category"].lower():
                contact = []
                if selected_entity["Phone"]:
                    contact.append(f"Phone: {selected_entity['Phone']}")
                if selected_entity["Email"]:
                    contact.append(f"Email: {selected_entity['Email']}")
                if contact:
                    st.caption(" · ".join(contact))
            if selected_entity["Website"]:
                st.caption(f"Website: {selected_entity['Website']}")
            if selected_entity["profile_url"]:
                st.link_button(
                    "Open tourism portal record",
                    selected_entity["profile_url"],
                    icon=":material/open_in_new:",
                )

    st.markdown("### Try an example question")
    examples = [
        "Who can temporarily suspend an operating licence?",
        "What are the penalties for operating without a licence?",
        "Which hotels are in Musanze?",
        "Where is GORILLA HUB SAFARIS LTD located?",
    ]
    for row_start in range(0, len(examples), 2):
        example_columns = st.columns(2)
        for column, example in zip(
            example_columns, examples[row_start:row_start + 2]
        ):
            with column:
                st.button(
                    example,
                    key=f"example-{row_start}-{example}",
                    width="stretch",
                    on_click=queue_question,
                    args=(example,),
                )

with info_column:
    with st.container(border=True, key="info-card"):
        st.markdown("### :material/psychology: Rwanda-focused AI")
        st.caption("Answers grounded in the project’s local tourism-law sources.")
        st.divider()
        st.markdown("**Topics you can ask about**")
        st.caption(":material/balance: Tourism law and licensing")
        st.caption(":material/hotel: RDB-listed tourism entities")
        st.caption(":material/search: Entity location and contact details")
        st.divider()
        st.markdown("**Designed for privacy**")
        st.caption("Inference uses model files stored with this project.")

    with st.container(border=True, key="about-card"):
        st.markdown("### :material/eco: Rwanda TourismGuard AI")
        st.caption(
            "A local assistant for answers about Rwanda’s tourism law and "
            "businesses in the included tourism-entity directory."
        )
        st.caption("🇷🇼  Rwanda  ·  Tourism  ·  Trust")

st.markdown(
    """
    <footer class="app-footer">
      <span>Rwanda TourismGuard AI&nbsp;&nbsp; | &nbsp;&nbsp;Powered by local data
      &nbsp;&nbsp; | &nbsp;&nbsp;Built with Python &amp; Streamlit</span>
      <span><i></i> Local model inference&nbsp; | &nbsp; Project data</span>
    </footer>
    """,
    unsafe_allow_html=True,
)
