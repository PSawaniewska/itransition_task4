import pandas as pd
import streamlit as st

from store import STORES, process_store

st.set_page_config(page_title="Bookstore Dashboard", page_icon="📚", layout="wide")


# data is processed once per store and then kept in memory
@st.cache_data
def get_results(store_dir):
    return process_store(store_dir)


with st.sidebar:
    st.header("📚 Bookstore Dashboard")
    store_dir = st.selectbox("Store", STORES, format_func=lambda path: path.split("/")[-1])

result = get_results(store_dir)
revenue = result["daily_revenue"]

st.title(store_dir.split("/")[-1])
st.caption(
    f"{revenue.index.min():%Y-%m-%d} to {revenue.index.max():%Y-%m-%d}  ·  "
    f"{result['orders']:,} orders  ·  ${revenue.sum():,.2f} total revenue"
)

tab_days, tab_metrics, tab_chart = st.tabs([
    ":material/calendar_month: Top 5 days",
    ":material/insights: Key metrics",
    ":material/show_chart: Daily revenue",
])

with tab_days:
    top_days = pd.DataFrame({
        "Date": result["top5_days"],
        "Revenue": [revenue[pd.Timestamp(day)] for day in result["top5_days"]],
    })
    table, _ = st.columns([3, 2])
    table.dataframe(
        top_days,
        hide_index=True,
        column_config={
            "Revenue": st.column_config.ProgressColumn(
                "Revenue (USD)", format="$%.2f", min_value=0, max_value=top_days["Revenue"].max()
            )
        },
    )

with tab_metrics:
    col1, col2 = st.columns(2)
    col1.metric("Unique users", f"{result['unique_users']:,}", border=True)
    col2.metric("Unique author sets", result["author_sets"], border=True)

    col3, col4 = st.columns(2)
    with col3.container(border=True):
        st.caption("Most popular author(s)")
        for authors in result["top_authors"]:
            st.markdown(f"#### {', '.join(authors)}")
    with col4.container(border=True):
        st.caption("Best buyer (all ids of the same person)")
        st.markdown(f"#### {result['best_buyer']}")

with tab_chart:
    chart = pd.DataFrame({
        "Daily revenue": revenue,
        "7-day average": revenue.rolling(7).mean(),
    })
    st.line_chart(chart, x_label="Date", y_label="Revenue (USD)", color=["#2E5F7A", "#4FC3F7"])