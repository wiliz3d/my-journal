# ============================================
# TRADING JOURNAL - neon green / red edition
# Python + Streamlit + SQLite + Pandas + Altair
# Pair with .streamlit/config.toml (dark theme)
# The whole UI glows GREEN when you are net profitable
# and RED when you are net negative.
# ============================================

import html
import sqlite3
from datetime import date
from io import BytesIO

import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image


# --------------------------------------------
# 1. APP SETTINGS AND PALETTE
# --------------------------------------------

st.set_page_config(
    page_title="Trading Journal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_NAME = "trades.db"

GREEN, RED, MUTED = "#2bff88", "#ff3b5c", "#8a979a"
RGB = {GREEN: "43,255,136", RED: "255,59,92"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');
:root{--acc:__ACC__;--rgb:__RGB__;--g:#2bff88;--r:#ff3b5c;--bg:#07090b;--card:rgba(255,255,255,.04);--line:rgba(255,255,255,.09);--text:#f4f7f5;--muted:#8a979a;}
html,body,.stApp{font-family:'Inter',sans-serif;}
.stApp{background:radial-gradient(1000px 520px at 85% -8%,rgba(var(--rgb),.17),transparent 60%),radial-gradient(700px 440px at -5% 45%,rgba(var(--rgb),.07),transparent 60%),var(--bg);color:var(--text);}
[data-testid="stHeader"]{background:transparent;}
footer,[data-testid="stDecoration"]{display:none;}
.block-container{padding-top:1.8rem;max-width:1380px;}
:where(.stApp p,.stApp label,.stApp li){color:var(--text);}

/* sidebar + form */
[data-testid="stSidebar"]{background:rgba(10,14,16,.92);border-right:1px solid rgba(var(--rgb),.25);}
[data-testid="stForm"]{border:0;padding:0;}
.side-title{font-family:'Sora',sans-serif;font-size:1.5rem;font-weight:800;letter-spacing:-.02em;}
.side-sub{color:var(--muted);font-size:.85rem;margin:.1rem 0 1rem;}

/* inputs */
div[data-baseweb="input"],div[data-baseweb="select"]>div,div[data-baseweb="textarea"]{background:rgba(255,255,255,.05)!important;border:1px solid var(--line)!important;border-radius:12px!important;}
div[data-baseweb="input"]:focus-within,div[data-baseweb="select"]>div:focus-within,div[data-baseweb="textarea"]:focus-within{border-color:var(--acc)!important;box-shadow:0 0 0 3px rgba(var(--rgb),.2)!important;}
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.03);border:1.5px dashed rgba(var(--rgb),.45);border-radius:14px;}

/* buttons */
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--text);font-weight:600;transition:all .15s;}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--acc);color:var(--acc);box-shadow:0 0 20px rgba(var(--rgb),.2);}
[data-testid="stFormSubmitButton"]>button{background:linear-gradient(135deg,#2bff88,#00c46a);border:0;color:#04130b;font-weight:700;padding:.6rem 1rem;box-shadow:0 8px 28px rgba(43,255,136,.3);}
[data-testid="stFormSubmitButton"]>button:hover{color:#04130b;filter:brightness(1.1);}

/* pill tabs */
.stTabs [data-baseweb="tab-list"]{gap:6px;background:var(--card);padding:6px;border-radius:16px;border:1px solid var(--line);width:fit-content;}
.stTabs [data-baseweb="tab"]{height:40px;padding:0 20px;border-radius:11px;color:var(--muted);font-weight:600;background:transparent;}
.stTabs [aria-selected="true"]{background:rgba(var(--rgb),.16);color:var(--acc);}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}

/* top bar */
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.1rem;}
.brand{font-family:'Sora',sans-serif;font-size:1.7rem;font-weight:800;letter-spacing:-.03em;}
.live{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--acc);box-shadow:0 0 12px var(--acc);margin-right:10px;}
.today{color:var(--muted);font-size:.9rem;}

/* hero */
.hero{border-radius:26px;padding:30px 36px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;gap:28px;flex-wrap:wrap;border:1px solid rgba(var(--rgb),.4);background:linear-gradient(135deg,rgba(var(--rgb),.22),rgba(var(--rgb),.04) 60%,transparent);box-shadow:0 24px 70px rgba(var(--rgb),.12);}
.hero .t{color:var(--muted);font-weight:600;}
.hero .n{font-family:'Sora',sans-serif;font-size:4.2rem;font-weight:800;letter-spacing:-.045em;line-height:1.05;color:var(--acc);text-shadow:0 0 44px rgba(var(--rgb),.5);font-variant-numeric:tabular-nums;}
.hero .mini{display:flex;gap:34px;flex-wrap:wrap;}
.hero .mini span{display:block;color:var(--muted);font-size:.8rem;margin-bottom:2px;}
.hero .mini b{font-family:'Sora',sans-serif;font-size:1.4rem;font-variant-numeric:tabular-nums;}

/* kpi cards */
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:6px;}
.kpi{position:relative;overflow:hidden;padding:20px 22px;border-radius:20px;background:var(--card);border:1px solid var(--line);}
.kpi:after{content:"";position:absolute;right:-30px;top:-30px;width:110px;height:110px;border-radius:50%;background:var(--c,var(--acc));opacity:.13;filter:blur(18px);}
.kpi .l{color:var(--muted);font-size:.85rem;font-weight:500;}
.kpi .v{font-family:'Sora',sans-serif;font-size:1.9rem;font-weight:700;margin-top:4px;color:var(--c,var(--text));font-variant-numeric:tabular-nums;}
.kpi .s{color:var(--muted);font-size:.78rem;margin-top:2px;}
.pos{color:var(--g);}.neg{color:var(--r);}

.sec{font-family:'Sora',sans-serif;font-size:1.15rem;font-weight:700;margin:1.6rem 0 .6rem;}
.sec small{font-family:'Inter',sans-serif;color:var(--muted);font-size:.85rem;font-weight:500;margin-left:.7rem;}

/* charts, tables, images */
[data-testid="stVegaLiteChart"],[data-testid="stArrowVegaLiteChart"]{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:16px;}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:16px;overflow:hidden;}
[data-testid="stImage"] img{border-radius:16px;border:1px solid var(--line);}

/* latest trades */
.row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;margin-bottom:9px;border-radius:16px;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--c);}
.row .sym{font-weight:700;font-size:1.02rem;}
.row .meta{color:var(--muted);font-size:.8rem;margin-top:2px;}
.row .amt{font-family:'Sora',sans-serif;font-weight:700;font-size:1.1rem;color:var(--c);font-variant-numeric:tabular-nums;}
.tag{font-size:.72rem;font-weight:700;margin-left:.6rem;padding:2px 9px;border-radius:999px;background:rgba(255,255,255,.07);}
.empty{text-align:center;padding:3.5rem 1rem;border:1.5px dashed rgba(var(--rgb),.4);border-radius:22px;color:var(--muted);}
.empty b{display:block;font-family:'Sora',sans-serif;font-size:1.4rem;color:var(--text);margin-bottom:.3rem;}
</style>
"""


def render(markup):
    """Render HTML; blank lines and indentation are stripped so Markdown never breaks it."""
    cleaned = "\n".join(l.strip() for l in markup.splitlines() if l.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def wide(fn, *args, **kwargs):
    """Stretch a widget to full width on both new and older Streamlit versions."""
    try:
        return fn(*args, width="stretch", **kwargs)
    except Exception:
        return fn(*args, use_container_width=True, **kwargs)


def money(value, signed=False):
    text = f"${abs(value):,.2f}"
    if value < 0:
        return "-" + text
    return "+" + text if signed and value > 0 else text


def tone(value):
    return "pos" if value > 0 else "neg" if value < 0 else ""


def color_of(value):
    return GREEN if value >= 0 else RED


# --------------------------------------------
# 2. DATABASE
# --------------------------------------------

def get_connection():
    """Open a connection to the local SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_database():
    """Create the tables if they do not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                setup TEXT,
                entry REAL,
                exit_price REAL,
                lot_size REAL,
                risk_amount REAL,
                pnl REAL NOT NULL,
                notes TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                image_data BLOB NOT NULL,
                FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
            )
        """)


setup_database()


def load_trades():
    """Load all trade records, newest first."""
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT * FROM trades ORDER BY trade_date DESC, id DESC", conn
        )


# Theme accent follows your account: green when profitable, red when not.
trades = load_trades()
net_pnl = trades["pnl"].sum() if not trades.empty else 0.0
ACC = color_of(net_pnl)
render(CSS.replace("__ACC__", ACC).replace("__RGB__", RGB[ACC]))

if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"), icon="✅")


# --------------------------------------------
# 3. SIDEBAR: ADD A TRADE
# --------------------------------------------

with st.sidebar:
    render("""
    <div class="side-title">Log a trade</div>
    <div class="side-sub">Fill in the details and attach your charts.</div>
    """)

    with st.form("add_trade_form", clear_on_submit=True):
        trade_date = st.date_input("Trade date", value=date.today())

        common_pairs = [
            "XAUUSD", "EURUSD", "GBPUSD", "USDJPY", "GBPJPY",
            "NAS100", "US30", "BTCUSD", "Other / custom",
        ]
        selected_pair = st.selectbox("Pair or instrument", common_pairs)

        if selected_pair == "Other / custom":
            symbol = st.text_input(
                "Custom pair or instrument", placeholder="e.g. AUDUSD, ETHUSD"
            ).strip().upper()
        else:
            symbol = selected_pair

        direction = st.radio("Direction", ["Buy / Long", "Sell / Short"], horizontal=True)

        setup = st.selectbox(
            "Trading setup",
            [
                "ICT / CRT",
                "MSNR / Support & Resistance",
                "Liquidity Sweep",
                "Market Structure Shift",
                "Breakout",
                "Trend Continuation",
                "Other",
            ],
        )

        c1, c2 = st.columns(2)
        entry = c1.number_input("Entry price", min_value=0.0, value=0.0, format="%.5f")
        exit_price = c2.number_input("Exit price", min_value=0.0, value=0.0, format="%.5f")

        c3, c4 = st.columns(2)
        lot_size = c3.number_input("Lot size", min_value=0.0, value=0.01, step=0.01)
        risk_amount = c4.number_input("Risk amount", min_value=0.0, value=0.0, step=1.0)

        pnl = st.number_input(
            "Realized P/L",
            value=0.0,
            step=1.0,
            help="Enter your actual profit or loss after fees.",
        )

        notes = st.text_area(
            "Trade notes and lessons",
            placeholder=(
                "Why did I take this trade?\n"
                "Was my entry valid?\n"
                "Did I follow my rules?\n"
                "What did I learn?"
            ),
        )

        screenshots = st.file_uploader(
            "Chart screenshots",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            help="Attach before-entry, entry, or exit screenshots.",
        )

        submitted = wide(st.form_submit_button, "Save trade")


# --------------------------------------------
# 4. SAVE THE TRADE AND ITS IMAGES
# --------------------------------------------

if submitted:
    saved = False

    if not symbol:
        st.sidebar.error("Enter a trading pair or instrument.")

    elif entry <= 0:
        st.sidebar.error("Enter a valid entry price.")

    else:
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO trades (
                        trade_date, symbol, direction, setup,
                        entry, exit_price, lot_size, risk_amount, pnl, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trade_date.isoformat(), symbol, direction, setup,
                        entry, exit_price, lot_size, risk_amount, pnl, notes,
                    ),
                )
                trade_id = cursor.lastrowid

                for uploaded_file in screenshots or []:
                    image_bytes = uploaded_file.getvalue()

                    # Limit each upload to 5 MB.
                    if len(image_bytes) > 5 * 1024 * 1024:
                        raise ValueError(f"{uploaded_file.name} exceeds 5 MB.")

                    # Confirm the file really is an image before storing it.
                    Image.open(BytesIO(image_bytes)).verify()

                    conn.execute(
                        "INSERT INTO trade_images (trade_id, filename, image_data) VALUES (?, ?, ?)",
                        (trade_id, uploaded_file.name, sqlite3.Binary(image_bytes)),
                    )

            st.session_state["flash"] = (
                f"Trade #{trade_id} saved with {len(screenshots or [])} screenshot(s)."
            )
            saved = True

        except Exception as error:
            st.sidebar.error(f"Could not save trade: {error}")

    if saved:
        st.rerun()


# --------------------------------------------
# 5. HEADER AND TABS
# --------------------------------------------

render(f"""
<div class="top">
<div class="brand"><span class="live"></span>Trading Journal</div>
<div class="today">{date.today():%A, %d %B %Y}</div>
</div>
""")

tab_dash, tab_hist, tab_shots, tab_manage = st.tabs(
    ["📊 Dashboard", "📚 History", "🖼️ Screenshots", "⚙️ Manage"]
)


# --------------------------------------------
# 6. CHART HELPERS
# --------------------------------------------

def style_chart(chart, height=300):
    """Transparent chart that blends into the glass card behind it."""
    return (
        chart.properties(height=height)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            labelColor=MUTED, titleColor=MUTED,
            gridColor="rgba(255,255,255,0.07)",
            domainColor="rgba(255,255,255,0.15)",
            tickColor="rgba(255,255,255,0.15)",
            labelFont="Inter", titleFont="Inter",
            labelFontSize=11, titleFontSize=11, titleFontWeight=500,
        )
        .configure_legend(labelColor=MUTED, titleColor=MUTED, labelFont="Inter")
    )


def sign_color():
    return alt.condition("datum.pnl >= 0", alt.value(GREEN), alt.value(RED))


def kpi(label, value, sub="", color=None):
    style = f' style="--c:{color}"' if color else ""
    return (f'<div class="kpi"{style}><div class="l">{label}</div>'
            f'<div class="v">{value}</div><div class="s">{sub}</div></div>')


# --------------------------------------------
# 7. DASHBOARD
# --------------------------------------------

with tab_dash:
    if trades.empty:
        render("""
        <div class="empty"><b>Your journal is empty</b>
        Add your first trade from the sidebar to light this dashboard up.</div>
        """)
    else:
        win_df = trades[trades["pnl"] > 0]
        loss_df = trades[trades["pnl"] < 0]
        wins, losses = len(win_df), len(loss_df)
        decided = wins + losses

        win_rate = wins / decided * 100 if decided else 0
        gross_win = win_df["pnl"].sum()
        gross_loss = abs(loss_df["pnl"].sum())
        if gross_loss:
            profit_factor = f"{gross_win / gross_loss:.2f}"
        else:
            profit_factor = "∞" if gross_win else "-"
        avg_win = win_df["pnl"].mean() if wins else 0
        avg_loss = loss_df["pnl"].mean() if losses else 0
        best, worst = trades["pnl"].max(), trades["pnl"].min()

        ordered = trades.sort_values(["trade_date", "id"]).reset_index(drop=True)
        ordered["n"] = ordered.index + 1
        ordered["equity"] = ordered["pnl"].cumsum()
        ordered["setup"] = ordered["setup"].fillna("Other")

        tips = [
            alt.Tooltip("n:Q", title="Trade #"),
            alt.Tooltip("trade_date:N", title="Date"),
            alt.Tooltip("symbol:N", title="Pair"),
            alt.Tooltip("pnl:Q", title="P/L", format=",.2f"),
        ]

        # Hero
        render(f"""
        <div class="hero">
        <div><div class="t">Net profit / loss</div><div class="n">{money(net_pnl, True)}</div></div>
        <div class="mini">
        <div><span>Trades</span><b>{len(trades)}</b></div>
        <div><span>Best trade</span><b class="{tone(best)}">{money(best, True)}</b></div>
        <div><span>Worst trade</span><b class="{tone(worst)}">{money(worst, True)}</b></div>
        </div>
        </div>
        """)

        # KPI cards
        render('<div class="kpis">' + "".join([
            kpi("Win rate", f"{win_rate:.1f}%", f"{wins} won, {losses} lost",
                GREEN if win_rate >= 50 else RED),
            kpi("Profit factor", profit_factor, "Gross win / gross loss"),
            kpi("Average win", money(avg_win), "Per winning trade", GREEN),
            kpi("Average loss", money(avg_loss), "Per losing trade", RED),
        ]) + "</div>")

        # Equity curve + win/loss donut
        left, right = st.columns([3, 2], gap="large")

        with left:
            render('<div class="sec">Equity curve</div>')
            fade = alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(0,0,0,0)", offset=0),
                    alt.GradientStop(color=f"rgba({RGB[ACC]},0.38)", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            )
            base = alt.Chart(ordered).encode(
                x=alt.X("n:Q", title="Trade #", axis=alt.Axis(tickMinStep=1, format="d")),
                y=alt.Y("equity:Q", title="Cumulative P/L"),
                tooltip=tips + [alt.Tooltip("equity:Q", title="Equity", format=",.2f")],
            )
            curve = base.mark_area(
                line={"color": ACC, "strokeWidth": 3},
                color=fade, interpolate="monotone",
            ) + base.mark_circle(color=ACC, size=60)
            wide(st.altair_chart, style_chart(curve, 320), theme=None)

        with right:
            render('<div class="sec">Win / loss split</div>')
            if decided:
                split = pd.DataFrame({"Result": ["Wins", "Losses"], "Trades": [wins, losses]})
                donut = alt.Chart(split).mark_arc(
                    innerRadius=70, cornerRadius=7, padAngle=0.04
                ).encode(
                    theta="Trades:Q",
                    color=alt.Color(
                        "Result:N", title=None,
                        scale=alt.Scale(domain=["Wins", "Losses"], range=[GREEN, RED]),
                        legend=alt.Legend(orient="bottom"),
                    ),
                    tooltip=["Result:N", "Trades:Q"],
                )
                wide(st.altair_chart, style_chart(donut, 320), theme=None)
            else:
                st.info("No winning or losing trades yet.")

        # Per-trade bars + setup bars
        a, b = st.columns(2, gap="large")

        with a:
            render('<div class="sec">Profit and loss per trade</div>')
            bars = alt.Chart(ordered).mark_bar(
                cornerRadiusTopLeft=4, cornerRadiusTopRight=4
            ).encode(
                x=alt.X("n:O", title="Trade #", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("pnl:Q", title="P/L"),
                color=sign_color(),
                tooltip=tips,
            )
            wide(st.altair_chart, style_chart(bars, 280), theme=None)

        with b:
            render('<div class="sec">Results by setup</div>')
            by_setup = ordered.groupby("setup", as_index=False)["pnl"].sum()
            setup_bars = alt.Chart(by_setup).mark_bar(
                cornerRadiusTopRight=5, cornerRadiusBottomRight=5
            ).encode(
                y=alt.Y("setup:N", sort="-x", title=None),
                x=alt.X("pnl:Q", title="Total P/L"),
                color=sign_color(),
                tooltip=[alt.Tooltip("setup:N", title="Setup"),
                         alt.Tooltip("pnl:Q", title="P/L", format=",.2f")],
            )
            wide(st.altair_chart, style_chart(setup_bars, 280), theme=None)

        # Latest trades
        render('<div class="sec">Latest trades</div>')
        rows = []
        for r in trades.head(6).itertuples():
            tag = "▲ Long" if "Long" in r.direction else "▼ Short"
            rows.append(
                f'<div class="row" style="--c:{color_of(r.pnl)}"><div>'
                f'<div class="sym">{html.escape(str(r.symbol))}<span class="tag">{tag}</span></div>'
                f'<div class="meta">{r.trade_date} - {html.escape(str(r.setup or "No setup"))}</div></div>'
                f'<div class="amt">{money(r.pnl, True)}</div></div>'
            )
        render("".join(rows))


# --------------------------------------------
# 8. TRADE HISTORY
# --------------------------------------------

with tab_hist:
    if trades.empty:
        render('<div class="empty"><b>No trades yet</b>Saved trades appear here.</div>')
    else:
        f1, f2 = st.columns(2)
        selected_symbol = f1.selectbox(
            "Pair or instrument", ["All"] + sorted(trades["symbol"].unique().tolist())
        )
        selected_setup = f2.selectbox(
            "Setup", ["All"] + sorted(trades["setup"].dropna().unique().tolist())
        )

        filtered = trades.copy()
        if selected_symbol != "All":
            filtered = filtered[filtered["symbol"] == selected_symbol]
        if selected_setup != "All":
            filtered = filtered[filtered["setup"] == selected_setup]

        total = filtered["pnl"].sum()
        render(
            f'<div class="sec">Trades<small>{len(filtered)} shown, total '
            f'<span class="{tone(total)}">{money(total, True)}</span></small></div>'
        )

        view = filtered[[
            "id", "trade_date", "symbol", "direction", "setup",
            "entry", "exit_price", "lot_size", "risk_amount", "pnl", "notes",
        ]].copy()
        view["direction"] = view["direction"].map(
            lambda d: "▲ Long" if "Long" in d else "▼ Short"
        )
        view = view.rename(columns={
            "id": "Trade ID", "trade_date": "Date", "symbol": "Pair",
            "direction": "Direction", "setup": "Setup", "entry": "Entry",
            "exit_price": "Exit", "lot_size": "Lot size", "risk_amount": "Risk",
            "pnl": "P/L", "notes": "Notes",
        })

        def pnl_color(v):
            if pd.isna(v) or v == 0:
                return ""
            return f"color: {GREEN if v > 0 else RED}; font-weight: 700"

        def dir_color(v):
            return f"color: {GREEN if 'Long' in str(v) else RED}; font-weight: 600"

        styled = view.style.format(
            {"Entry": "{:.5f}", "Exit": "{:.5f}", "Lot size": "{:.2f}",
             "Risk": "{:,.2f}", "P/L": "{:+,.2f}"},
            na_rep="-",
        )
        paint = styled.map if hasattr(styled, "map") else styled.applymap
        styled = paint(pnl_color, subset=["P/L"])
        paint = styled.map if hasattr(styled, "map") else styled.applymap
        styled = paint(dir_color, subset=["Direction"])

        wide(
            st.dataframe, styled, hide_index=True,
            column_config={"Notes": st.column_config.TextColumn("Notes", width="large")},
        )

        st.download_button(
            "Download as CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="trading_journal.csv",
            mime="text/csv",
        )


# --------------------------------------------
# 9. SCREENSHOTS
# --------------------------------------------

with tab_shots:
    if trades.empty:
        render('<div class="empty"><b>No screenshots yet</b>Attach charts when you log a trade.</div>')
    else:
        trade_options = {
            f"#{int(row['id'])} | {row['trade_date']} | {row['symbol']} | P/L {row['pnl']:.2f}":
            int(row["id"])
            for _, row in trades.iterrows()
        }
        selected_label = st.selectbox(
            "Choose a trade", list(trade_options.keys()), key="image_trade"
        )
        selected_trade_id = trade_options[selected_label]

        with get_connection() as conn:
            images = conn.execute(
                "SELECT id, filename, image_data FROM trade_images WHERE trade_id = ? ORDER BY id",
                (selected_trade_id,),
            ).fetchall()

        if images:
            cols = st.columns(2, gap="large")
            for index, (image_id, filename, image_data) in enumerate(images):
                with cols[index % 2]:
                    wide(st.image, bytes(image_data), caption=filename)
                    st.download_button(
                        "Download screenshot",
                        data=bytes(image_data),
                        file_name=filename,
                        key=f"download_image_{image_id}",
                    )
        else:
            st.info("No screenshots are attached to this trade yet.")


# --------------------------------------------
# 10. MANAGE (DELETE)
# --------------------------------------------

with tab_manage:
    if trades.empty:
        render('<div class="empty"><b>Nothing to manage</b>Your trades will show up here.</div>')
    else:
        render('<div class="sec">Delete a trade</div>')
        delete_id = st.selectbox("Trade ID to delete", trades["id"].astype(int).tolist())
        confirm = st.checkbox(f"I understand that trade #{delete_id} and its screenshots will be deleted.")

        if st.button("Delete trade"):
            if confirm:
                with get_connection() as conn:
                    conn.execute("DELETE FROM trade_images WHERE trade_id = ?", (delete_id,))
                    conn.execute("DELETE FROM trades WHERE id = ?", (delete_id,))
                st.session_state["flash"] = f"Trade #{delete_id} and its screenshots were deleted."
                st.rerun()
            else:
                st.warning("Tick the confirmation box before deleting.")

st.caption("Manual record keeping. Back up trades.db before you deploy.")
