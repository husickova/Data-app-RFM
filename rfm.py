import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import re

# Application title with colored text
st.markdown("""
# RFM for <span style="color:dodgerblue">Keboola</span> by <span style="color:purple">Bytegarden</span>
""", unsafe_allow_html=True)

# Function to assign categories based on R and F scores using regex
def assign_category(r, f):
    rfm_score = f"{r}{f}"
    if re.match(r'5[4-5]', rfm_score):
        return '01. Champions'
    elif re.match(r'[3-4][4-5]', rfm_score):
        return '02. Loyal Customers'
    elif re.match(r'[4-5][2-3]', rfm_score):
        return '03. Potential Loyalists'
    elif re.match(r'51', rfm_score):
        return '04. Recent Customers'
    elif re.match(r'41', rfm_score):
        return '05. Promising'
    elif re.match(r'33', rfm_score):
        return '06. Need Attention'
    elif re.match(r'3[1-2]', rfm_score):
        return '07. About to Sleep'
    elif re.match(r'[1-2][5]', rfm_score):
        return '08. Can\'t Lose'
    elif re.match(r'[1-2][3-4]', rfm_score):
        return '09. At Risk'
    elif re.match(r'2[1-2]', rfm_score):
        return '10. Hibernating'
    elif re.match(r'1[1-2]', rfm_score):
        return '11. Lost'
    else:
        return 'Uncategorized'

# Load CSV file
csv_path = "rfm-data.csv"
try:
    df = pd.read_csv(csv_path)
    
    # Convert 'date' column to datetime type
    df['date'] = pd.to_datetime(df['date'])
    
    # Create interactive date selection fields in the sidebar
    start_date = st.sidebar.date_input('Start date', df['date'].min().date())
    end_date = st.sidebar.date_input('End date', df['date'].max().date())
    
    # Filter data based on selected dates
    filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    
    # Calculate RFM values
    max_date = filtered_df['date'].max() + timedelta(days=1)
    rfm_df = filtered_df.groupby('id').agg({
        'date': lambda x: (max_date - x.max()).days,
        'id': 'count',
        'value': 'sum'
    }).rename(columns={
        'date': 'Recency',
        'id': 'Frequency',
        'value': 'Monetary'
    }).reset_index()
    
    # Normalize RFM values using pd.cut
    rfm_df['R_rank'] = pd.cut(rfm_df['Recency'], bins=5, labels=['5', '4', '3', '2', '1'])
    rfm_df['F_rank'] = pd.cut(rfm_df['Frequency'], bins=5, labels=['1', '2', '3', '4', '5'])
    rfm_df['M_rank'] = pd.cut(rfm_df['Monetary'], bins=5, labels=['1', '2', '3', '4', '5'])
    
    rfm_df['RFM_Score'] = rfm_df['R_rank'].astype(str) + rfm_df['F_rank'].astype(str) + rfm_df['M_rank'].astype(str)

    # Assign categories based on R and F scores using regex
    rfm_df['Category'] = rfm_df.apply(lambda x: assign_category(x['R_rank'], x['F_rank']), axis=1)

    # Create a selectbox for category selection
    category_options = ['All'] + rfm_df['Category'].unique().tolist()
    selected_category = st.sidebar.selectbox('Select a category to display:', category_options)
    
    # Filter data based on the selected category
    if selected_category != 'All':
        filtered_category_df = rfm_df[rfm_df['Category'] == selected_category]
    else:
        filtered_category_df = rfm_df

    # Create columns for buttons
    col1, col2, col3 = st.columns(3)

    selected_button = None

    with col1:
        if st.button('Recency'):
            selected_button = 'Recency'
    with col2:
        if st.button('Frequency'):
            selected_button = 'Frequency'
    with col3:
        if st.button('Monetary'):
            selected_button = 'Monetary'

    # Display the graph based on the selected button
    if selected_button == 'Recency':
        fig = px.histogram(filtered_category_df, x='Recency', title='Recency', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig)
        st.markdown("<p style='font-size: small;'>Recency shows how recently each customer made a purchase.</p>", unsafe_allow_html=True)

    if selected_button == 'Frequency':
        fig = px.histogram(filtered_category_df, x='Frequency', title='Frequency', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig)
        st.markdown("<p style='font-size: small;'>Frequency shows how often each customer makes a purchase.</p>", unsafe_allow_html=True)

    if selected_button == 'Monetary':
        fig = px.histogram(filtered_category_df, x='Monetary', title='Monetary', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig)
        st.markdown("<p style='font-size: small;'>Monetary shows how much money each customer spends.</p>", unsafe_allow_html=True)

except FileNotFoundError:
    st.error(f"File not found at path {csv_path}.")
except Exception as e:
    st.error(f"An error occurred while loading the file: {e}")
