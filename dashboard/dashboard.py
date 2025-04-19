import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# Set Streamlit dark layout
st.set_page_config(page_title="Sales Performance Dashboard", page_icon=":bar_chart:", layout="wide")

# Load dataset
all_df = pd.read_csv(r'C:\Users\Chandan Choudhury\Desktop\New Project\Data-Analytics-Brazilian-Ecommerce\data\all_data.csv')
all_df["order_purchase_timestamp"] = pd.to_datetime(all_df["order_purchase_timestamp"])
all_df["customer_segment"].fillna("Mid Value Customers", inplace=True)

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

BAR_COLOR = "#00FFB3"  # Bright teal

def filter_data(all_df):
    with st.sidebar:
        st.markdown("<h3 style='color:#00FFB3;'>🎯 Filter Your Data</h3>", unsafe_allow_html=True)

        city = st.multiselect(
            "🏙️ Select the City:",
            options=all_df["customer_city"].unique(),
            default=["sao paulo"],
        )

        customer_type = st.multiselect(
            "👤 Select Customer Segment:",
            options=all_df["customer_segment"].unique(),
            default=["Mid Value Customers"],
        )

        date_range = st.date_input(
            "📅 Select Date Range:",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date,
        )

    df_selection = all_df.query(
        "customer_city == @city & customer_segment == @customer_type & order_purchase_timestamp >= @date_range[0] & order_purchase_timestamp <= @date_range[1]"
    )

    if not df_selection.empty:
        df_selection["order_purchase_day"] = df_selection["order_purchase_timestamp"].dt.day
    else:
        df_selection = pd.DataFrame({"order_purchase_timestamp": pd.date_range(start='1/1/2017', periods=31)})
        df_selection["order_purchase_day"] = df_selection["order_purchase_timestamp"].dt.day

    return df_selection

def display_kpis(all_df):
    total_sales = int(all_df["total_price"].sum()) if "total_price" in all_df else 0
    average_rating = round(all_df["review_score"].mean(), 1) if "review_score" in all_df else 0
    star_rating = "⭐" * int(round(average_rating, 0)) if not np.isnan(average_rating) else ""

    average_sales = round(all_df["total_price"].mean(), 2) if "total_price" in all_df else 0

    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.metric(label="💰 Total Sales", value=f"R$ {total_sales:,}")

    with middle_column:
        st.metric(label="⭐ Avg Rating", value=f"{average_rating}", delta=star_rating)

    with right_column:
        st.metric(label="📦 Avg Sales/Order", value=f"R$ {average_sales:,}")

    st.markdown("<hr style='border: 1px solid #444;'>", unsafe_allow_html=True)

def plot_charts(df):
    sales_by_product_line = df.groupby(by=["product_category_name_english"])[["total_price"]].sum().sort_values(by="total_price")

    fig_product_sales = px.bar(
        sales_by_product_line,
        x="total_price",
        y=sales_by_product_line.index,
        orientation="h",
        title="🛍️ Sales by Product Line",
        color_discrete_sequence=[BAR_COLOR] * len(sales_by_product_line),
        template="plotly_dark",
    )

    df["order_purchase_day"] = df["order_purchase_timestamp"].dt.day
    sales_by_day = df.groupby(by=["order_purchase_day"])[["total_price"]].sum().reset_index()

    fig_daily_sales = px.bar(
        sales_by_day,
        x="order_purchase_day",
        y="total_price",
        title="📅 Daily Sales",
        color_discrete_sequence=[BAR_COLOR] * len(sales_by_day),
        template="plotly_dark",
    )
    fig_daily_sales.update_layout(
        xaxis=dict(tickmode="linear"),
        xaxis_title="Day",
        yaxis_title="Sales",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(showgrid=False),
    )

    left_column, right_column = st.columns(2)
    left_column.plotly_chart(fig_daily_sales, use_container_width=True)
    right_column.plotly_chart(fig_product_sales, use_container_width=True)

def main():
    # Title
    st.markdown(
        "<h1 style='text-align: center; color: #00FFB3;'>📊 Sales Performance Dashboard</h1><br>",
        unsafe_allow_html=True,
    )

    df_selection = filter_data(all_df)
    display_kpis(df_selection)
    plot_charts(df_selection)

    # Custom CSS for dark mode
    dark_css = """
    <style>
        .stApp {
            background-color: #121212;
            color: #F0F0F0;
        }
        .css-1d391kg {
            background-color: #1E1E1E !important;
            border-radius: 10px;
            padding: 1rem;
        }
        .stMetric {
            background-color: #222;
            padding: 1em;
            border-radius: 10px;
            color: #00FFB3;
        }
        .stSidebar {
            background-color: #1C1C1C;
        }
        h1, h3, h4, h5 {
            color: #00FFB3;
        }
        .css-17eq0hr {
            background-color: #1c1c1c !important;
        }
        footer, header, #MainMenu {
            visibility: hidden;
        }
    </style>
    """
    st.markdown(dark_css, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
