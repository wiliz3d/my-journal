# ============================================
# TRADING JOURNAL - modern edition
# Python + Streamlit + SQLite + Pandas + Altair
# Pair with .streamlit/config.toml (dark theme)
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

AMBER, MINT, CORAL, MUTED = "#f2b84b", "#4fd1a1", "#ff7a70", "#8fb0ae"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Manrope:wght@400;500;600;700&display=swap');
:root{--bg:#0b1c20;--panel:#112a30;--panel2:#163239;--line:#24464e;--text:#e9f2f0;--muted:#8fb0ae;--amber:#f2b84b;--mint:#4fd1a1;--coral:#ff7a70;}
html,body,.stApp{font-family:'Manrope',sans-serif;}
.stApp{background:var(--bg);color:var(--text);}
[data-testid="stHeader"]{background:transparent;}
footer,[data-testid="stDecoration"]{display:none;}
.block-container{padding-top:2.2rem;max-width:1360px;}
:where(.stApp p,.stApp label,.stApp li){color:var(--text);}

/* sidebar + form */
[data-testid="stSidebar"]{background:var(--panel);border-right:1px solid var(--line);}
[data-testid="stForm"]{border:0;padding:0;}
.side-title{font-family:'Fraunces',serif;font-size:1.5rem;font-weight:600;margin:0 0 .15rem;}
.side-sub{color:var(--muted);font-size:.85rem;margin-bottom:1rem;}

/* inputs */
div[data-baseweb="input"],div[data-baseweb="select"]>div,div[data-baseweb="textarea"]{background:var(--bg)!important;border:1px solid var(--line)!important;border-radius:10px!important;}
div[data-baseweb="input"]:focus-within,div[data-baseweb="select"]>div:focus-within,div[data-baseweb="textarea"]:focus-within{border-color:var(--amber)!important;box-shadow:0 0 0 3px rgba(242,184,75,.16)!important;}
[data-testid="stFileUploaderDropzone"]{background:var(--bg);border:1.5px dashed var(--line);border-radius:12px;}

/* buttons */
.stButton>button,.stDownloadButton>button,[data-testid="stFormSubmitButton"]>button{border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font-weight:600;transition:border-color .15s,background .15s;}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--amber);color:var(--amber);}
[data-testid="stFormSubmitButton"]>button{background:var(--amber);border:0;color:#1a1305;padding:.55rem 1rem;}
[data-testid="stFormSubmitButton"]>button:hover{background:#ffcb66;color:#1a1305;}

/* tabs: quiet underline */
.stTabs [data-baseweb="tab-list"]{gap:1.6rem;border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{padding:.6rem 0;color:var(--muted);font-weight:600;background:transparent;}
.stTabs [aria-selected="true"]{color:var(--text);}
.stTabs [data-baseweb="tab-highlight"]{background:var(--amber);height:2px;}
.stTabs [data-baseweb="tab-border"]{display:none;}

/* header */
.hero{display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;flex-wrap:wrap;margin-bottom:1.4rem;}
.title{font-family:'Fraunces',serif;font-size:2.6rem;font-weight:600;letter-spacing:-.02em;line-height:1.1;}
.hero p{color:var(--muted);margin:.35rem 0 0;}
.today{color:var(--muted);font-size:.9rem;}

/* ledger panel (the one bold element) */
.ledger{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:26px 26px 14px;height:100%;}
.ledger .lbl{color:var(--muted);font-size:.9rem;}
.big{font-family:'Fraunces',serif;font-size:3.1rem;font-weight:600;letter-spacing:-.02em;line-height:1.1;margin:.15rem 0 1rem;font-variant-numeric:tabular-nums;}
.line{display:flex;justify-content:space-between;align-items:baseline;padding:.65rem 0;border-top:1px dashed var(--line);}
.line span{color:var(--muted);font-size:.9rem;}
.line b{font-variant-numeric:tabular-nums;font-weight:700;}
.pos{color:var(--mint);}.neg{color:var(--coral);}

/* section headings */
.sec{font-family:'Fraunces',serif;font-size:1.3rem;font-weight:500;margin:1.6rem 0 .6rem;}
.sec small{font-family:'Manrope',sans-serif;color:var(--muted);font-size:.85rem;margin-left:.6rem;}

/* charts, tables, images */
[data-testid="stVegaLiteChart"],[data-testid="stArrowVegaLiteChart"]{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:16px;}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;}
[data-testid="stImage"] img{border-radius:14px;border:1px solid var(--line);}

/* latest trades list */
.row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:.8rem 0;border-bottom:1px solid var(--line);}
.row .sym{font-weight:700;}
.row .meta{color:var(--muted);font-size:.8rem;margin-top:2px;}
.row .amt{font-weight:700;font-variant-numeric:tabular-nums;}
.tag{font-size:.72rem;font-weight:700;margin-left:.5rem;}
.empty{text-align:center;padding:3.5rem 1rem;border:1.5px dashed var(--line);border-radius:20px;color:var(--muted);}
.empty b{display:block;font-family:'Fraunces',serif;font-size:1.4rem;color:var(--text);margin-bottom:.3rem;}
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


render(CSS)


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

        direction = st.selectbox("Direction", ["Buy / Long", "Sell / Short"])

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
# 5. HEADER
# --------------------------------------------

render(f"""
<div class="hero">
<div>
<div class="title">Trading journal</div>
<p>Log every trade, keep the charts, and see what is actually working.</p>
</div>
<div class="today">{date.today():%A, %d %B %Y}</div>
</div>
""")

trades = load_trades()
tab_dash, tab_hist, tab_shots, tab_manage = st.tabs(
    ["Dashboard", "Trade history", "Screenshots", "Manage"]
)


# --------------------------------------------
# 6. CHART STYLING HELPER
# --------------------------------------------

def style_chart(chart, height=300):
    """Transparent, quiet chart that blends into the card behind it."""
    return (
        chart.properties(height=height)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(
            labelColor=MUTED, titleColor=MUTED,
            gridColor="rgba(143,176,174,0.12)",
            domainColor="rgba(143,176,174,0.25)",
            tickColor="rgba(143,176,174,0.25)",
            labelFont="Manrope", titleFont="Manrope",
            labelFontSize=11, titleFontSize=11, titleFontWeight=500,
        )
    )


def sign_color():
    return alt.condition("datum.pnl >= 0", alt.value(MINT), alt.value(CORAL))


# --------------------------------------------
# 7. DASHBOARD
# --------------------------------------------

with tab_dash:
    if trades.empty:
        render("""
        <div class="empty"><b>Your journal is empty</b>
        Add your first trade from the sidebar to see your stats here.</div>
        """)
    else:
        win_df = trades[trades["pnl"] > 0]
        loss_df = trades[trades["pnl"] < 0]
        wins, losses = len(win_df), len(loss_df)
        decided = wins + losses

        net_pnl = trades["pnl"].sum()
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

        left, right = st.columns([2, 3], gap="large")

        with left:
            render(f"""
            <div class="ledger">
            <div class="lbl">Net profit / loss</div>
            <div class="big {tone(net_pnl)}">{money(net_pnl, True)}</div>
            <div class="line"><span>Win rate</span><b>{win_rate:.1f}%</b></div>
            <div class="line"><span>Profit factor</span><b>{profit_factor}</b></div>
            <div class="line"><span>Trades</span><b>{len(trades)} ({wins} won, {losses} lost)</b></div>
            <div class="line"><span>Average win</span><b class="pos">{money(avg_win)}</b></div>
            <div class="line"><span>Average loss</span><b class="neg">{money(avg_loss)}</b></div>
            <div class="line"><span>Best trade</span><b class="{tone(best)}">{money(best, True)}</b></div>
            <div class="line"><span>Worst trade</span><b class="{tone(worst)}">{money(worst, True)}</b></div>
            </div>
            """)

        with right:
            render('<div class="sec" style="margin-top:0">Equity curve</div>')
            fade = alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="rgba(242,184,75,0.02)", offset=0),
                    alt.GradientStop(color="rgba(242,184,75,0.35)", offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0,
            )
            base = alt.Chart(ordered).encode(
                x=alt.X("n:Q", title="Trade #", axis=alt.Axis(tickMinStep=1, format="d")),
                y=alt.Y("equity:Q", title="Cumulative P/L"),
                tooltip=tips + [alt.Tooltip("equity:Q", title="Equity", format=",.2f")],
            )
            curve = base.mark_area(
                line={"color": AMBER, "strokeWidth": 2.5},
                color=fade, interpolate="monotone",
            ) + base.mark_circle(color=AMBER, size=55)
            wide(st.altair_chart, style_chart(curve, 330), theme=None)

        a, b = st.columns(2, gap="large")

        with a:
            render('<div class="sec">Profit and loss per trade</div>')
            bars = alt.Chart(ordered).mark_bar(
                cornerRadiusTopLeft=3, cornerRadiusTopRight=3
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
                cornerRadiusTopRight=4, cornerRadiusBottomRight=4
            ).encode(
                y=alt.Y("setup:N", sort="-x", title=None),
                x=alt.X("pnl:Q", title="Total P/L"),
                color=sign_color(),
                tooltip=[alt.Tooltip("setup:N", title="Setup"),
                         alt.Tooltip("pnl:Q", title="P/L", format=",.2f")],
            )
            wide(st.altair_chart, style_chart(setup_bars, 280), theme=None)

        render('<div class="sec">Latest trades</div>')
        rows = []
        for r in trades.head(6).itertuples():
            is_long = "Long" in r.direction
            tag_cls, tag = ("pos", "Long") if is_long else ("neg", "Short")
            rows.append(
                f'<div class="row"><div><div class="sym">{html.escape(str(r.symbol))}'
                f'<span class="tag {tag_cls}">{tag}</span></div>'
                f'<div class="meta">{r.trade_date} - {html.escape(str(r.setup or "No setup"))}</div></div>'
                f'<div class="amt {tone(r.pnl)}">{money(r.pnl, True)}</div></div>'
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

        render(
            f'<div class="sec">Trades<small>{len(filtered)} shown, '
            f'{money(filtered["pnl"].sum(), True)} total</small></div>'
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
            return f"color: {MINT if v > 0 else CORAL}; font-weight: 700"

        styled = view.style.format(
            {"Entry": "{:.5f}", "Exit": "{:.5f}", "Lot size": "{:.2f}",
             "Risk": "{:,.2f}", "P/L": "{:+,.2f}"},
            na_rep="-",
        )
        paint = styled.map if hasattr(styled, "map") else styled.applymap
        styled = paint(pnl_color, subset=["P/L"])

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
