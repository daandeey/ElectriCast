import pandas as pd
import datetime

def data_preprocessing(df):
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])

    df.rename(columns={'Voltage (V)': 'V',
                   'Ampere (A)': 'A',
                   'Device ID': 'Device'}, inplace=True)
    
    df['W'] = df['V'] * df['A']

    return df

def create_time_features(df):
    df["hour"] = df.index.hour
    df["day_of_week"] = df.index.day_of_week
    df["quarter"] = df.index.quarter
    df["month"] = df.index.month
    df["year"] = df.index.year
    df["day_of_year"] = df.index.dayofyear

def remaining_dates_until_end_of_month(date):
    # Get the end of the month for the given date
    end_of_month = pd.Timestamp(date).to_period('M').to_timestamp('M')
    
    # Generate date range from the given date to the end of the month
    remaining_dates = pd.date_range(start=date+datetime.timedelta(days=1), end=end_of_month)
    
    return remaining_dates

def create_remaining_date_dataframe(date):
    generated_date = remaining_dates_until_end_of_month(date)
    df_generated_date = pd.DataFrame(generated_date, columns=['Timestamp']).set_index('Timestamp')
    create_time_features(df_generated_date)

    return df_generated_date