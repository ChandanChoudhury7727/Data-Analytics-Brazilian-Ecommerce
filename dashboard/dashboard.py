import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import io
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error



# Set Streamlit dark layout
st.set_page_config(page_title="Sales Performance Dashboard", page_icon=":bar_chart:", layout="wide")

# Load dataset
all_df = pd.read_csv(r'C:\Users\Chandan Choudhury\Desktop\New Project\Data-Analytics-Brazilian-Ecommerce\data\all_data.csv')
all_df["order_purchase_timestamp"] = pd.to_datetime(all_df["order_purchase_timestamp"])
all_df["customer_segment"].fillna("Mid Value Customers", inplace=True)

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

BAR_COLOR = "#00FFB3"  # Bright teal

# --- Prediction Inputs ---
def prediction_inputs():
    customer_state = st.selectbox("Customer State", all_df['customer_state'].unique())
    seller_state = st.selectbox("Seller State", all_df['customer_city'].unique())
    product_weight = st.number_input("Product Weight (g)", min_value=0)
    freight_value = st.number_input("Freight Value", min_value=0.0)
    price = st.number_input("Price", min_value=0.0)
    return customer_state, seller_state, product_weight, freight_value, price

def filter_data(all_df):
    with st.sidebar:
        st.markdown("<h3 style='color:#00FFB3;'>🎯 Filter Your Data</h3>", unsafe_allow_html=True)

        city = st.multiselect(
            "🏙️ Select the City:",
            options=all_df["customer_city"].unique(),
            default=["sao paulo"],
        )

        st.markdown("👤 Customer Segment: **Mid Value Customers**")
        customer_type = ["Mid Value Customers"]


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

def train_model(X_train, y_train):
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5],
        'learning_rate': [0.05, 0.1]
    }

    grid_search = GridSearchCV(
        estimator=xgb.XGBRegressor(),
        param_grid=param_grid,
        cv=3,
        n_jobs=-1,
        scoring='neg_mean_squared_error'
    )
    grid_search.fit(X_train_scaled, y_train)

    best_model = grid_search.best_estimator_
    return best_model, scaler



def make_predictions(model, input_data):
    return model.predict(input_data)

def download_results(results):
    csv = results.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='prediction_results.csv',
        mime='text/csv',
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        results.to_excel(writer, index=False, sheet_name='Sheet1')
        
        processed_data = output.getvalue()

    st.download_button(
        label="Download data as Excel",
        data=processed_data,
        file_name='prediction_results.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

def main():
    # Title
    st.markdown(
        "<h1 style='text-align: center; color: #00FFB3;'>📊 Sales Performance Dashboard</h1><br>",
        unsafe_allow_html=True,
    )

    df_selection = filter_data(all_df)
    display_kpis(df_selection)
    plot_charts(df_selection)

    # Get prediction inputs
    customer_state, seller_state, product_weight, freight_value, price = prediction_inputs()

    # Use inputs to predict Total Price (Model Example)
    input_data = pd.DataFrame({
        'freight_value': [freight_value],
        'price': [price],
    })

    model, scaler = train_model(df_selection[['freight_value', 'price']], df_selection['total_price'])
    scaled_input = scaler.transform(input_data)
    predictions = make_predictions(model, scaled_input)


    st.markdown(f"Predicted Total Order Price: R$ {predictions[0]:,.2f}")

    X_eval = df_selection[['freight_value', 'price']]
    y_eval = df_selection['total_price']
    X_eval_scaled = scaler.transform(X_eval)
    y_pred = model.predict(X_eval_scaled)

    
    mae = mean_absolute_error(y_eval, y_pred)

    st.markdown(f"📉 **Model Evaluation Metrics:**")
    
    st.markdown(f"- MAE: `{mae:.2f}`")

    # Display Prediction Results
    prediction_results = pd.DataFrame({
        'customer_state': [customer_state],
        'seller_state': [seller_state],
        'product_weight': [product_weight],
        'freight_value': [freight_value],
        'price': [price],
        'predicted_total_price': predictions
    })
        # ----- Delivery Time Prediction -----
    # Ensure date columns are in datetime format
    df_selection["order_purchase_timestamp"] = pd.to_datetime(df_selection["order_purchase_timestamp"])
    df_selection["order_delivered_customer_date"] = pd.to_datetime(df_selection["order_delivered_customer_date"])

# Calculate delivery_time_days
    df_selection["delivery_time_days"] = (df_selection["order_delivered_customer_date"] - df_selection["order_purchase_timestamp"]).dt.days

    delivery_df = df_selection.dropna(subset=["delivery_time_days"])

    # Encode categorical variables
    encoded_df = pd.get_dummies(delivery_df[["customer_state"]])

    X_delivery = pd.concat([
        encoded_df,
        delivery_df[["product_weight_g", "freight_value", "price"]]
    ], axis=1)

    y_delivery = delivery_df["delivery_time_days"]

    # Train model
    delivery_model = RandomForestRegressor()
    delivery_model.fit(X_delivery, y_delivery)

    # Prepare input
    input_encoded = pd.get_dummies(pd.DataFrame({
    'customer_state': [customer_state]
}))

    input_encoded = input_encoded.reindex(columns=encoded_df.columns, fill_value=0)


    input_delivery_data = pd.concat([input_encoded, pd.DataFrame({
        "product_weight_g": [product_weight],
        "freight_value": [freight_value],
        "price": [price]
    })], axis=1)

    # Predict delivery time
    delivery_time_pred = delivery_model.predict(input_delivery_data)[0]

    # Show result
    st.markdown(f"📦 **Predicted Delivery Time:** {int(round(delivery_time_pred))} days")

    # Add to results table
    prediction_results["predicted_delivery_days"] = [int(round(delivery_time_pred))]

    # --- Review Score Classification ---
    if 'review_score' in df_selection:
        review_df = df_selection.dropna(subset=["review_score"])

        X_review = review_df[["freight_value", "price"]]
        y_review = review_df["review_score"].astype(int)

        scaler_review = StandardScaler()
        X_review_scaled = scaler_review.fit_transform(X_review)

        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier()
        clf.fit(X_review_scaled, y_review)

        input_review_scaled = scaler_review.transform(input_data)
        predicted_review = clf.predict(input_review_scaled)[0]

        st.markdown(f"📝 **Predicted Review Score:** {predicted_review} ⭐")

        prediction_results["predicted_review_score"] = [predicted_review]


    st.dataframe(prediction_results)

    # Allow exporting results
    download_results(prediction_results)

    # 📅 Monthly Sales Forecasting (LSTM)
    st.subheader("📅 Monthly Sales Forecasting (LSTM)")

    # Step 1: Prepare data
    sales_df = df_selection.copy()
    sales_df["order_purchase_timestamp"] = pd.to_datetime(sales_df["order_purchase_timestamp"], errors='coerce')
    sales_df = sales_df.dropna(subset=["order_purchase_timestamp", "total_price"])

    # Group by Month
    monthly_sales = sales_df.groupby(sales_df["order_purchase_timestamp"].dt.to_period("M"))["total_price"].sum().reset_index()
    monthly_sales["order_purchase_timestamp"] = monthly_sales["order_purchase_timestamp"].dt.to_timestamp()
    monthly_sales = monthly_sales.rename(columns={"order_purchase_timestamp": "date", "total_price": "sales"})

    # Step 2: Normalize and create sequences
    from sklearn.preprocessing import MinMaxScaler
    scaler_lstm = MinMaxScaler()
    scaled_sales = scaler_lstm.fit_transform(monthly_sales[["sales"]])

    # Create sequences
    import numpy as np
    X_lstm, y_lstm = [], []
    seq_len = 3

    for i in range(seq_len, len(scaled_sales)):
        X_lstm.append(scaled_sales[i-seq_len:i])
        y_lstm.append(scaled_sales[i])

    X_lstm, y_lstm = np.array(X_lstm), np.array(y_lstm)

    # Step 3: Build and train LSTM model
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense

    model_lstm = Sequential()
    model_lstm.add(LSTM(units=50, activation='relu', input_shape=(X_lstm.shape[1], 1)))
    model_lstm.add(Dense(1))
    model_lstm.compile(optimizer='adam', loss='mse')
    model_lstm.fit(X_lstm, y_lstm, epochs=100, verbose=0)

    # Step 4: Predict next month's sales
    last_seq = scaled_sales[-seq_len:].reshape((1, seq_len, 1))
    predicted_scaled = model_lstm.predict(last_seq, verbose=0)
    predicted_sales = scaler_lstm.inverse_transform(predicted_scaled)[0][0]

    # Step 5: Display results
    last_month = monthly_sales["date"].iloc[-1].strftime("%B %Y")
    next_month = (monthly_sales["date"].iloc[-1] + pd.DateOffset(months=1)).strftime("%B %Y")

    st.markdown(f"📆 Last Month: **{last_month}**")
    st.markdown(f"🔮 **Predicted Sales for {next_month}:** R$ `{predicted_sales:,.2f}`")

    # Optional: show sales trend
    import matplotlib.pyplot as plt

    monthly_sales["Predicted"] = np.nan
    monthly_sales.loc[len(monthly_sales)] = [pd.to_datetime(next_month), predicted_sales, predicted_sales]

    fig, ax = plt.subplots()
    ax.plot(monthly_sales["date"], monthly_sales["sales"], label="Historical Sales")
    ax.plot(monthly_sales["date"], monthly_sales["Predicted"], linestyle="--", marker='o', color='red', label="Predicted")
    ax.set_title("Monthly Sales Forecast")
    ax.set_ylabel("Sales (R$)")
    ax.set_xlabel("Date")
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)

 
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
