import streamlit as st
import pandas as pd
from xgboost import XGBRegressor
import matplotlib.pyplot as plt
import seaborn as sns
import utils
from millify import millify
import datetime
import pickle as pkl
import seaborn.objects as so


PRICE_PER_KWH = 415

# Load data
# @st.cache
def load_data():
    data = pd.read_csv("dataset/electricity_consumption.csv")
    return data

df = load_data()
df = utils.data_preprocessing(df)
xgb_model_loaded = pkl.load(open('model/xgb_reg.pkl', "rb"))

# Sidebar
st.sidebar.title("Options")
min_date = df["Timestamp"].min()
max_date = df["Timestamp"].max()
selected_date = st.sidebar.date_input("Select date", value=max_date.date(), min_value=min_date, max_value=max_date)
selected_month = selected_date.month
selected_year = selected_date.year

# Predict Remaining Date of The Month
df_remaining_date = utils.create_remaining_date_dataframe(selected_date)
pred = xgb_model_loaded.predict(df_remaining_date)
df_remaining_date['prediction'] = pd.DataFrame(data=pred, index=df_remaining_date.index, columns=["prediction"])
df_remaining_date.reset_index(inplace=True)

# Current Year Usage
current_year_usage = df[(df['Timestamp'].dt.year == selected_year)]["W"].sum()

# Previous Year Usage
previous_year_usage = df[(df['Timestamp'].dt.year == selected_year-1)]["W"].sum()

# Current Month Usage
current_month_usage = df[(df['Timestamp'].dt.month == selected_month) & (df['Timestamp'].dt.year == selected_year)]["W"].sum()

# Remaining Date of The Month Usage
remaining_date_usage = df_remaining_date['prediction'].sum()

# Previous Month Usage
if selected_month == 1:  # If the current month is January, the previous month is December of the previous year
    previous_month = 12
    previous_year = selected_year - 1
else:
    previous_month = selected_month - 1
    previous_year = selected_year

previous_month_usage = df[(df['Timestamp'].dt.month == previous_month) & (df['Timestamp'].dt.year == previous_year)]["W"].sum()

# Today's Usage
current_date_usage = df[(df['Timestamp'].dt.date == selected_date)]["W"].sum()
previous_date_usage = df[(df['Timestamp'].dt.date == selected_date-datetime.timedelta(days=1))]["W"].sum()

# Electricity Bill
current_month_bill = current_month_usage * PRICE_PER_KWH / 1000
remaining_date_bill = remaining_date_usage * PRICE_PER_KWH / 1000
previous_month_bill = previous_month_usage * PRICE_PER_KWH / 1000

# Main content
st.title("ElectriCast Monitoring Dashboard")

# Current Electricity Usage (Score Card)
col1, col2, col3 = st.columns(3)
col1.metric(label="Current Month Usage", value=f"{millify(current_month_usage)}Wh", delta=f"{millify(current_month_usage-previous_month_usage)}Wh", delta_color='inverse')
col2.metric(label="Predicted Remaining Date Usage", value=f"{millify(remaining_date_usage)}Wh")
col3.metric(label="Predicted This Month's Bill", value=f"Rp{millify(current_month_bill + remaining_date_bill)}", delta=f"Rp{millify(current_month_bill + remaining_date_bill - previous_month_bill)}", delta_color='inverse')

# Predicted Future Usage (Line Plot)
st.subheader("Current Month Usage")

# Assuming you have a function to predict future usage using your XGBoost model
fig, ax = plt.subplots(figsize=(18, 6))

data = df[(df['Timestamp'].dt.month == selected_month) &
           (df['Timestamp'].dt.year == selected_year) &
           (df['Timestamp'].dt.date <= selected_date)].groupby(df['Timestamp'].dt.day).agg({'W': 'sum'})

sns.pointplot(data=data, x="Timestamp", y="W", ax=ax, label='Actual')
sns.pointplot(data=df_remaining_date, x=df_remaining_date["Timestamp"].dt.day, y="prediction", ax=ax, linestyles='--', label='Predicted')
plt.xlabel("Date")
plt.ylabel("Electricity Usage (Wh)")
st.pyplot(fig)

# Proportion of Usage per Device (Pie Chart)
device_usage = df[df["Timestamp"].dt.date == selected_date].groupby("Device")["W"].sum()
st.subheader("Usage per Device")
fig, ax = plt.subplots(1,2,figsize=(18, 6), gridspec_kw={'width_ratios': [3, 1]})
ax[1].pie(device_usage, labels=device_usage.index, autopct='%1.1f%%', startangle=90)
ax[1].axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

# Plot hourly trend all devices
data = df[df["Timestamp"].dt.date == selected_date]
sns.pointplot(data=data, x=data['Timestamp'].dt.hour, hue='Device', y='W', ax=ax[0])
ax[0].set_xlabel('Hour')
st.pyplot(fig)

# Past Usage (Line Plot)
st.subheader("All Time Usage")

df_daily_consumption = df.groupby(['Device', pd.Grouper(key='Timestamp', freq='1D')]).agg({'W': 'sum'})
df_daily_consumption.reset_index(inplace=True)

fig, ax = plt.subplots(figsize=(18, 6))
sns.lineplot(data=df_daily_consumption, x="Timestamp", y="W", hue="Device",ax=ax)
plt.xlabel("Date")
plt.ylabel("Electricity Usage (Wh)")
st.pyplot(fig)
