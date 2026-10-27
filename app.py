
# ============================================
# TRADING JOURNAL - WITH IMAGE UPLOADS
# Python + Streamlit + SQLite + Pandas
# ============================================

import sqlite3
from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image


# --------------------------------------------
# 1. APP SETTINGS
# --------------------------------------------

st.set_page_config(
    page_title="My Trading Journal",
    page_icon="📈",
    layout="wide"
)

DB_NAME = "trades.db"

st.title("📈 My Trading Journal")
st.caption("Track your trades, save chart screenshots, and review your performance.")


# --------------------------------------------
# 2. DATABASE
# --------------------------------------------

def get_connection():
    """Open a connection to the local SQLite database."""
    return sqlite3.connect(DB_NAME)


def setup_database():
    """Create the tables if they do not exist."""

    with get_connection() as conn:

        # Each row represents one manually recorded trade.
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

        # Each trade can have multiple attached screenshots.
        # Images are stored as binary data in SQLite.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                image_data BLOB NOT NULL,
                FOREIGN KEY (trade_id)
                    REFERENCES trades(id)
                    ON DELETE CASCADE
            )
        """)


setup_database()


# --------------------------------------------
# 3. LOAD TRADES
# --------------------------------------------

def load_trades():
    """Load all trade records, newest first."""

    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT *
            FROM trades
            ORDER BY trade_date DESC, id DESC
            """,
            conn
        )


# --------------------------------------------
# 4. ADD A TRADE
# --------------------------------------------

st.sidebar.header("➕ Add a Trade")

with st.sidebar.form("add_trade_form", clear_on_submit=True):

    trade_date = st.date_input(
        "Trade date",
        value=date.today()
    )

    # Choose a common pair or type ANY custom symbol.
    common_pairs = [
        "XAUUSD",
        "EURUSD",
        "GBPUSD",
        "USDJPY",
        "GBPJPY",
        "NAS100",
        "US30",
        "BTCUSD",
        "Other / custom"
    ]

    selected_pair = st.selectbox(
        "Choose a pair or instrument",
        common_pairs
    )

    if selected_pair == "Other / custom":
        symbol = st.text_input(
            "Enter your pair or instrument",
            placeholder="e.g. AUDUSD, ETHUSD"
        ).strip().upper()
    else:
        symbol = selected_pair

    direction = st.selectbox(
        "Direction",
        ["Buy / Long", "Sell / Short"]
    )

    setup = st.selectbox(
        "Trading setup",
        [
            "ICT / CRT",
            "MSNR / Support & Resistance",
            "Liquidity Sweep",
            "Market Structure Shift",
            "Breakout",
            "Trend Continuation",
            "Other"
        ]
    )

    # Manual trade details.
    entry = st.number_input(
        "Entry price",
        min_value=0.0,
        value=0.0,
        format="%.5f"
    )

    exit_price = st.number_input(
        "Exit price",
        min_value=0.0,
        value=0.0,
        format="%.5f"
    )

    lot_size = st.number_input(
        "Lot size",
        min_value=0.0,
        value=0.01,
        step=0.01
    )

    risk_amount = st.number_input(
        "Risk amount",
        min_value=0.0,
        value=0.0,
        step=1.0
    )

    pnl = st.number_input(
        "Realized P/L",
        value=0.0,
        step=1.0,
        help="Enter your actual profit or loss after fees."
    )

    notes = st.text_area(
        "Trade notes and lessons",
        placeholder=(
            "Why did I take this trade?\n"
            "Was my entry valid?\n"
            "Did I follow my rules?\n"
            "What did I learn?"
        )
    )

    # Upload one or more screenshots from your phone or computer.
    screenshots = st.file_uploader(
        "Upload chart screenshots",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        help="Attach before-entry, entry, or exit screenshots."
    )

    submitted = st.form_submit_button(
        "Save Trade",
        use_container_width=True
    )


# --------------------------------------------
# 5. SAVE THE TRADE AND ITS IMAGES
# --------------------------------------------

if submitted:

    if not symbol:
        st.sidebar.error("Enter a trading pair or instrument.")

    elif entry <= 0:
        st.sidebar.error("Enter a valid entry price.")

    else:
        try:
            with get_connection() as conn:

                # Save the trade first and get its database ID.
                cursor = conn.execute(
                    """
                    INSERT INTO trades (
                        trade_date, symbol, direction, setup,
                        entry, exit_price, lot_size, risk_amount,
                        pnl, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trade_date.isoformat(),
                        symbol,
                        direction,
                        setup,
                        entry,
                        exit_price,
                        lot_size,
                        risk_amount,
                        pnl,
                        notes
                    )
                )

                trade_id = cursor.lastrowid

                # Save every screenshot against that trade ID.
                for uploaded_file in screenshots or []:

                    image_bytes = uploaded_file.getvalue()

                    # Check that the file is a valid image and
                    # limit individual uploads to 5 MB.
                    if len(image_bytes) > 5 * 1024 * 1024:
                        raise ValueError(
                            f"{uploaded_file.name} exceeds 5 MB."
                        )

                    # Re-encode as JPEG to validate image content
                    # and avoid saving arbitrary uploaded file data.
                    image = Image.open(BytesIO(image_bytes))
                    image.verify()

                    conn.execute(
                        """
                        INSERT INTO trade_images (
                            trade_id, filename, image_data
                        )
                        VALUES (?, ?, ?)
                        """,
                        (
                            trade_id,
                            uploaded_file.name,
                            sqlite3.Binary(image_bytes)
                        )
                    )

            st.sidebar.success(
                f"Trade #{trade_id} saved with "
                f"{len(screenshots or [])} screenshot(s)."
            )

            st.rerun()

        except Exception as error:
            st.sidebar.error(f"Could not save trade: {error}")


# --------------------------------------------
# 6. DASHBOARD
# --------------------------------------------

trades = load_trades()

if trades.empty:

    st.info(
        "Your journal is empty. Add your first trade "
        "using the form in the sidebar."
    )

else:

    total_trades = len(trades)
    wins = int((trades["pnl"] > 0).sum())
    losses = int((trades["pnl"] < 0).sum())

    decided = wins + losses

    win_rate = wins / decided * 100 if decided else 0
    net_pnl = trades["pnl"].sum()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Trades", total_trades)
    col2.metric("Win Rate", f"{win_rate:.1f}%")
    col3.metric("Winning Trades", wins)
    col4.metric("Net P/L", f"${net_pnl:,.2f}")

    st.subheader("📊 P/L History")

    chart = trades.sort_values("trade_date").copy()
    chart["Trade"] = (
        chart["trade_date"].astype(str)
        + " #"
        + chart["id"].astype(str)
    )

    st.bar_chart(
        chart.set_index("Trade")["pnl"],
        y_label="P/L"
    )


# --------------------------------------------
# 7. TRADE HISTORY AND FILTERING
# --------------------------------------------

st.divider()
st.subheader("📚 Trade History")

if not trades.empty:

    symbols = ["All"] + sorted(trades["symbol"].unique().tolist())

    selected_symbol = st.selectbox(
        "Filter by pair or instrument",
        symbols
    )

    filtered = trades.copy()

    if selected_symbol != "All":
        filtered = filtered[
            filtered["symbol"] == selected_symbol
        ]

    # Show the trade records without the internal database fields.
    display_columns = [
        "id", "trade_date", "symbol", "direction", "setup",
        "entry", "exit_price", "lot_size",
        "risk_amount", "pnl", "notes"
    ]

    st.dataframe(
        filtered[display_columns].rename(columns={
            "id": "Trade ID",
            "trade_date": "Date",
            "symbol": "Pair / Instrument",
            "direction": "Direction",
            "setup": "Setup",
            "entry": "Entry",
            "exit_price": "Exit",
            "lot_size": "Lot Size",
            "risk_amount": "Risk",
            "pnl": "P/L",
            "notes": "Notes"
        }),
        use_container_width=True,
        hide_index=True
    )

    # Export the currently selected trades as CSV.
    st.download_button(
        "📥 Download Trade History (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="trading_journal.csv",
        mime="text/csv"
    )


# --------------------------------------------
# 8. VIEW SCREENSHOTS FOR ANY TRADE
# --------------------------------------------

st.divider()
st.subheader("🖼️ Trade Screenshots")

if not trades.empty:

    trade_options = {
        f"#{int(row['id'])} | {row['trade_date']} | "
        f"{row['symbol']} | P/L {row['pnl']:.2f}":
        int(row["id"])
        for _, row in trades.iterrows()
    }

    selected_trade_label = st.selectbox(
        "Choose a trade to view its screenshots",
        list(trade_options.keys()),
        key="image_trade"
    )

    selected_trade_id = trade_options[selected_trade_label]

    with get_connection() as conn:
        images = conn.execute(
            """
            SELECT id, filename, image_data
            FROM trade_images
            WHERE trade_id = ?
            ORDER BY id
            """,
            (selected_trade_id,)
        ).fetchall()

    if images:

        # Display screenshots in columns.
        columns = st.columns(2)

        for index, (image_id, filename, image_data) in enumerate(images):

            with columns[index % 2]:

                st.image(
                    bytes(image_data),
                    caption=filename,
                    use_container_width=True
                )

                # Allow downloading each original image.
                st.download_button(
                    "Download screenshot",
                    data=bytes(image_data),
                    file_name=filename,
                    key=f"download_image_{image_id}"
                )

    else:
        st.info("No screenshots have been attached to this trade yet.")


# --------------------------------------------
# 9. DELETE A TRADE AND ITS SCREENSHOTS
# --------------------------------------------

st.divider()
st.subheader("🗑️ Delete a Trade")

if not trades.empty:

    delete_id = st.selectbox(
        "Trade ID to delete",
        trades["id"].astype(int).tolist()
    )

    confirm = st.checkbox(
        f"I understand that trade #{delete_id} will be deleted."
    )

    if st.button("Delete Trade"):

        if confirm:
            with get_connection() as conn:

                # Explicit deletion keeps this reliable even if
                # SQLite foreign-key enforcement isn't enabled.
                conn.execute(
                    "DELETE FROM trade_images WHERE trade_id = ?",
                    (delete_id,)
                )

                conn.execute(
                    "DELETE FROM trades WHERE id = ?",
                    (delete_id,)
                )

            st.success("Trade and its screenshots deleted.")
            st.rerun()

        else:
            st.warning("Confirm the deletion before continuing.")


# --------------------------------------------
# 10. FOOTER
# --------------------------------------------

st.divider()

st.caption(
    "Trading Journal • Manual record keeping • "
    "Always back up your records before deployment."
)
