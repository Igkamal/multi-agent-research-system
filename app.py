import re
import time

import streamlit as st

from agents import build_search_agent, writer_chain, critic_chain
from tools import scrape_url

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="Multi Agent Research Lab",
    page_icon="🧠",
    layout="wide",
)

# ==================================================
# CUSTOM CSS (animations, glass cards, gradients)
# ==================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ---------- Animated background ---------- */
.stApp {
    background: linear-gradient(-45deg, #0b1020, #1b1445, #10213f, #1a0f33);
    background-size: 400% 400%;
    animation: bgShift 18s ease infinite;
}
@keyframes bgShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1200px; }

/* ---------- Hero ---------- */
.hero { text-align: center; padding: 1.2rem 0 0.6rem 0; animation: fadeUp 0.9s ease both; }
.hero-badge {
    display: inline-block; padding: 6px 16px; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600; letter-spacing: 0.08em;
    color: #c4b5fd; background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.45);
    animation: glowPulse 3s ease-in-out infinite;
}
.hero-title {
    font-size: 3.2rem; font-weight: 800; margin: 0.8rem 0 0.2rem 0; line-height: 1.1;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6, #60a5fa);
    background-size: 300% 100%;
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; color: transparent;
    animation: textShine 6s linear infinite;
}
.hero-sub { color: #9ca3af; font-size: 1.05rem; margin-bottom: 0.5rem; }
@keyframes textShine { to { background-position: 300% 0; } }
@keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.0); }
    50%      { box-shadow: 0 0 18px 2px rgba(139, 92, 246, 0.45); }
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ---------- Inputs & buttons ---------- */
.stTextInput input {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(167, 139, 250, 0.35) !important;
    border-radius: 14px !important; color: #fff !important;
    padding: 0.85rem 1rem !important; font-size: 1.05rem !important;
    transition: all 0.25s ease;
}
.stTextInput input:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.25), 0 0 24px rgba(167, 139, 250, 0.25) !important;
}
.stButton > button {
    border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.05); color: #e5e7eb;
    transition: all 0.25s ease; font-weight: 500;
}
.stButton > button:hover {
    transform: translateY(-2px); border-color: #a78bfa; color: #fff;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
    background-size: 200% 100%; border: none; color: #fff;
    font-weight: 700; padding: 0.7rem 1rem; font-size: 1.05rem;
    animation: btnFlow 5s ease infinite;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-3px) scale(1.01);
    box-shadow: 0 10px 30px rgba(139, 92, 246, 0.55);
}
@keyframes btnFlow {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ---------- Pipeline tracker ---------- */
.step-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 1.2rem 0; }
@media (max-width: 800px) { .step-grid { grid-template-columns: repeat(2, 1fr); } }
.step-card {
    position: relative; padding: 1.1rem 1rem; border-radius: 18px; text-align: center;
    background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.4s ease; animation: fadeUp 0.7s ease both;
}
.step-card:nth-child(2) { animation-delay: 0.1s; }
.step-card:nth-child(3) { animation-delay: 0.2s; }
.step-card:nth-child(4) { animation-delay: 0.3s; }
.step-icon { font-size: 2rem; margin-bottom: 0.3rem; }
.step-title { color: #f3f4f6; font-weight: 700; font-size: 1rem; }
.step-sub { color: #9ca3af; font-size: 0.8rem; margin-bottom: 0.6rem; }
.step-badge {
    display: inline-flex; align-items: center; gap: 6px; padding: 3px 12px;
    border-radius: 999px; font-size: 0.75rem; font-weight: 600;
    background: rgba(255, 255, 255, 0.08); color: #9ca3af;
}
.step-card.pending { opacity: 0.55; }
.step-card.running {
    border-color: #8b5cf6; transform: translateY(-4px);
    animation: runGlow 1.4s ease-in-out infinite;
}
.step-card.running .step-icon { animation: bounce 1s ease-in-out infinite; }
.step-card.running .step-badge { background: rgba(139, 92, 246, 0.2); color: #c4b5fd; }
.step-card.done { border-color: rgba(52, 211, 153, 0.6); }
.step-card.done .step-badge { background: rgba(52, 211, 153, 0.15); color: #6ee7b7; }
.step-card.warn { border-color: rgba(251, 191, 36, 0.6); }
.step-card.warn .step-badge { background: rgba(251, 191, 36, 0.15); color: #fcd34d; }
.step-card.error { border-color: rgba(248, 113, 113, 0.7); }
.step-card.error .step-badge { background: rgba(248, 113, 113, 0.15); color: #fca5a5; }
@keyframes runGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.0); }
    50%      { box-shadow: 0 0 28px 4px rgba(139, 92, 246, 0.55); }
}
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-6px); }
}
.spinner {
    width: 11px; height: 11px; border-radius: 50%;
    border: 2px solid rgba(196, 181, 253, 0.3); border-top-color: #c4b5fd;
    animation: spin 0.8s linear infinite; display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ---------- Metric cards ---------- */
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 1rem 0 1.4rem 0; }
@media (max-width: 800px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } }
.metric-card {
    padding: 1rem; border-radius: 16px; text-align: center;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.18), rgba(236, 72, 153, 0.12));
    border: 1px solid rgba(255, 255, 255, 0.1);
    animation: fadeUp 0.8s ease both; transition: transform 0.25s ease;
}
.metric-card:hover { transform: translateY(-4px) scale(1.02); }
.metric-value { font-size: 1.8rem; font-weight: 800; color: #fff; }
.metric-label { font-size: 0.78rem; color: #a5b4fc; letter-spacing: 0.06em; text-transform: uppercase; }

/* ---------- Tabs & result panel ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.05); border-radius: 12px 12px 0 0;
    padding: 0.5rem 1rem; transition: background 0.2s ease;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(139, 92, 246, 0.2); }
.stTabs [aria-selected="true"] { background: rgba(139, 92, 246, 0.3) !important; }
.stTabs [data-baseweb="tab-panel"] { animation: fadeUp 0.5s ease both; padding-top: 1rem; }

section[data-testid="stSidebar"] {
    background: rgba(10, 12, 28, 0.85); backdrop-filter: blur(12px);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
.sidebar-title { font-weight: 700; color: #c4b5fd; margin-bottom: 0.4rem; }
.stDownloadButton > button {
    border-radius: 12px; border: 1px solid #34d399; color: #6ee7b7;
    background: rgba(52, 211, 153, 0.08); transition: all 0.25s ease;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px); box-shadow: 0 6px 20px rgba(52, 211, 153, 0.35);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ==================================================
# CONSTANTS & SESSION STATE
# ==================================================
STEPS = [
    ("🔎", "Search Agent", "Finding sources"),
    ("🕸️", "Reader", "Scraping a page"),
    ("✍️", "Writer", "Drafting report"),
    ("🧐", "Critic", "Reviewing report"),
]

EXAMPLES = [
    "Impact of quantum computing on cryptography",
    "Future of renewable energy in India",
    "How do large language models work",
    "Rise of esports in India",
]

for key, default in {
    "result": None,
    "topic_input": "",
    "history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ==================================================
# HELPERS
# ==================================================
def set_topic(value: str):
    st.session_state.topic_input = value


def load_history(index: int):
    st.session_state.result = st.session_state.history[index]
    st.session_state.topic_input = st.session_state.history[index]["topic"]


def extract_urls(text: str) -> list:
    urls = re.findall(r"https?://[^\s\)\]\">]+", str(text))
    seen, unique = set(), []
    for u in urls:
        u = u.rstrip(".,;")
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def call_scrape(url: str) -> str:
    """Works whether scrape_url is a LangChain @tool or a plain function."""
    if hasattr(scrape_url, "invoke"):
        return scrape_url.invoke({"url": url})
    return scrape_url(url)


def render_tracker(placeholder, statuses, timings):
    cards = []
    for i, (icon, title, sub) in enumerate(STEPS):
        s = statuses[i]
        if s == "pending":
            badge = "Waiting"
        elif s == "running":
            badge = '<span class="spinner"></span> Working...'
        elif s == "done":
            badge = f"✓ Done · {timings[i]:.1f}s"
        elif s == "warn":
            badge = f"⚠ No content · {timings[i]:.1f}s"
        else:
            badge = "✕ Failed"
        cards.append(
            f'<div class="step-card {s}"><div class="step-icon">{icon}</div>'
            f'<div class="step-title">{title}</div><div class="step-sub">{sub}</div>'
            f'<div class="step-badge">{badge}</div></div>'
        )
    placeholder.markdown(
        '<div class="step-grid">' + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def render_metrics(result):
    words = len(str(result["report"]).split())
    scrape_label = "OK" if result["scrape_ok"] else "Failed"
    items = [
        (str(result["sources"]), "Sources found"),
        (f"{words:,}", "Report words"),
        (f"{result['total_time']:.1f}s", "Total time"),
        (scrape_label, "Scraping"),
    ]
    html = "".join(
        f'<div class="metric-card"><div class="metric-value">{v}</div>'
        f'<div class="metric-label">{l}</div></div>'
        for v, l in items
    )
    st.markdown(f'<div class="metric-grid">{html}</div>', unsafe_allow_html=True)


# ==================================================
# PIPELINE STEPS
# ==================================================
def step_search(state, topic, min_len):
    agent = build_search_agent()
    res = agent.invoke({
        "messages": [(
            "user",
            f"Research this topic: {topic}. "
            "Find 3 reliable sources. Return each source's "
            "title, URL, and a short relevant snippet. "
            "Keep the response concise. Do not invent facts."
        )]
    })
    state["search_results"] = res["messages"][-1].content
    return "done"


def step_read(state, topic, min_len):
    # Scrape in plain Python (no LLM) so a mistyped tool name can't crash the run.
    for url in extract_urls(state["search_results"]):
        try:
            content = call_scrape(url)
        except Exception:
            continue
        if isinstance(content, str) and len(content.strip()) > min_len:
            state["scraped_content"] = f"SOURCE: {url}\n{content}"
            state["scrape_ok"] = True
            return "done"

    state["scraped_content"] = (
        "SCRAPING FAILED: No usable content was returned by scrape_url. "
        "Search snippets are not verified webpage content."
    )
    state["scrape_ok"] = False
    return "warn"


def step_write(state, topic, min_len):
    research = (
        f"SEARCH RESULTS:\n{state['search_results']}\n\n"
        f"SCRAPED CONTENT:\n{state['scraped_content']}\n\n"
        "REPORTING RULES:\n"
        "- Distinguish search snippets from scraped content.\n"
        "- Do not invent facts, dates, statistics, or sources.\n"
        "- If scraping failed, disclose that limitation.\n"
        "- Include the source URLs found in the research.\n"
        "- Clearly identify claims that the evidence cannot verify.\n"
        "- Keep the report detailed but concise."
    )
    state["report"] = writer_chain.invoke({"topic": topic, "research": research})
    return "done"


def step_critic(state, topic, min_len):
    state["feedback"] = critic_chain.invoke({"report": state["report"]})
    return "done"


PIPELINE = [step_search, step_read, step_write, step_critic]


def run_pipeline(topic, tracker_ph, min_len):
    state = {}
    statuses = ["pending"] * 4
    timings = [0.0] * 4
    start = time.time()
    render_tracker(tracker_ph, statuses, timings)

    for i, fn in enumerate(PIPELINE):
        statuses[i] = "running"
        render_tracker(tracker_ph, statuses, timings)
        t0 = time.time()
        try:
            outcome = fn(state, topic, min_len)
        except Exception:
            statuses[i] = "error"
            timings[i] = time.time() - t0
            render_tracker(tracker_ph, statuses, timings)
            raise
        timings[i] = time.time() - t0
        statuses[i] = outcome
        render_tracker(tracker_ph, statuses, timings)

    state.update(
        topic=topic,
        statuses=statuses,
        timings=timings,
        total_time=time.time() - start,
        sources=len(extract_urls(state["search_results"])),
    )
    return state


# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ Settings</div>', unsafe_allow_html=True)
    min_len = st.slider(
        "Min. scraped characters",
        100, 2000, 300, step=100,
        help="Pages returning less than this are skipped (usually JavaScript-rendered pages).",
    )
    celebrate = st.toggle("Celebrate when done 🎈", value=True)

    st.divider()
    st.markdown('<div class="sidebar-title">🕘 History</div>', unsafe_allow_html=True)
    if not st.session_state.history:
        st.caption("Your past researches will appear here.")
    for idx in reversed(range(len(st.session_state.history))):
        item = st.session_state.history[idx]
        label = item["topic"][:34] + ("…" if len(item["topic"]) > 34 else "")
        st.button(f"📂 {label}", key=f"hist_{idx}", on_click=load_history,
                  args=(idx,), use_container_width=True)

    if st.session_state.history or st.session_state.result:
        st.divider()
        if st.button("🗑️ Clear everything", use_container_width=True):
            st.session_state.history = []
            st.session_state.result = None
            st.session_state.topic_input = ""
            st.rerun()

# ==================================================
# HERO
# ==================================================
st.markdown(
    """
<div class="hero">
  <div class="hero-badge">⚡ MULTI-AGENT AI</div>
  <div class="hero-title">Multi Agent Research Lab</div>
  <div class="hero-sub">Four AI agents search, read, write and critique, so you get a verified report.</div>
</div>
""",
    unsafe_allow_html=True,
)

# ==================================================
# INPUT AREA
# ==================================================
st.text_input(
    "Research topic",
    key="topic_input",
    placeholder="What do you want to research today?",
    label_visibility="collapsed",
)

st.caption("✨ Try one of these:")
chip_cols = st.columns(len(EXAMPLES))
for col, ex in zip(chip_cols, EXAMPLES):
    col.button(ex, key=f"chip_{ex}", on_click=set_topic, args=(ex,), use_container_width=True)

launch = st.button("🚀 Launch research", type="primary", use_container_width=True)

# ==================================================
# TRACKER + RUN
# ==================================================
tracker_ph = st.empty()

if launch:
    topic = st.session_state.topic_input.strip()
    if not topic:
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.result = None
        try:
            result = run_pipeline(topic, tracker_ph, min_len)
            st.session_state.result = result
            st.session_state.history.append(result)
            st.toast("Research complete!", icon="✅")
            if celebrate:
                st.balloons()
        except Exception as e:
            st.error(f"Pipeline failed: {e}")
elif st.session_state.result:
    r = st.session_state.result
    render_tracker(tracker_ph, r["statuses"], r["timings"])
else:
    render_tracker(tracker_ph, ["pending"] * 4, [0.0] * 4)

# ==================================================
# RESULTS
# ==================================================
result = st.session_state.result

if result:
    st.markdown(f"### 📌 {result['topic']}")
    render_metrics(result)

    tab_report, tab_review, tab_search, tab_scraped = st.tabs(
        ["📄 Final Report", "🧐 Critic Review", "🔗 Sources", "🕸️ Scraped Content"]
    )

    with tab_report:
        st.markdown(result["report"])
        st.download_button(
            "⬇️ Download report (.md)",
            data=str(result["report"]),
            file_name="research_report.md",
            mime="text/markdown",
        )

    with tab_review:
        st.markdown(result["feedback"])

    with tab_search:
        st.markdown(result["search_results"])

    with tab_scraped:
        if not result["scrape_ok"]:
            st.warning(result["scraped_content"])
        else:
            st.text_area(
                "Raw scraped output",
                value=result["scraped_content"],
                height=400,
                label_visibility="collapsed",
            )
