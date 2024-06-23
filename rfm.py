import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import re

# Application title with colored text
st.markdown("""
# RFM by <span style="color:dodgerblue">Keboola</span>
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
    
    # Normalize RFM values using percentiles to create quantiles
    rfm_df['R_rank'] = pd.qcut(rfm_df['Recency'], q=5, labels=False, duplicates='drop') + 1
    rfm_df['F_rank'] = pd.qcut(rfm_df['Frequency'], q=5, labels=False, duplicates='drop') + 1
    rfm_df['M_rank'] = pd.qcut(rfm_df['Monetary'], q=5, labels=False, duplicates='drop') + 1

    # Convert ranks to str for concatenation
    rfm_df['R_rank'] = (6 - rfm_df['R_rank']).astype(str)  # Reverse the R rank
    rfm_df['F_rank'] = rfm_df['F_rank'].astype(str)
    rfm_df['M_rank'] = rfm_df['M_rank'].astype(str)
    
    rfm_df['RFM_Score'] = rfm_df['R_rank'] + rfm_df['F_rank'] + rfm_df['M_rank']

    # Assign categories based on R and F scores using regex
    rfm_df['Category'] = rfm_df.apply(lambda x: assign_category(x['R_rank'], x['F_rank']), axis=1)

    # Sort categories by numeric order
    category_order = [
        '01. Champions', '02. Loyal Customers', '03. Potential Loyalists',
        '04. Recent Customers', '05. Promising', '06. Need Attention',
        '07. About to Sleep', '08. Can\'t Lose', '09. At Risk',
        '10. Hibernating', '11. Lost'
    ]
    rfm_df['Category'] = pd.Categorical(rfm_df['Category'], categories=category_order, ordered=True)

    # Create a multiselect for category selection with an "All" option
    all_categories = ['All'] + category_order
    selected_categories = st.sidebar.multiselect('Select categories to display:', all_categories, default=['All'])

    # Filter data based on the selected categories
    if 'All' in selected_categories:
        filtered_category_df = rfm_df
    else:
        filtered_category_df = rfm_df[rfm_df['Category'].isin(selected_categories)]

    # Create columns for buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    col6, col7, col8, col9, col10 = st.columns(5)

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
    with col4:
        if st.button('Scatter Recency vs Frequency'):
            selected_button = 'Scatter Recency vs Frequency'
    with col5:
        if st.button('Scatter Frequency vs Monetary'):
            selected_button = 'Scatter Frequency vs Monetary'
    with col6:
        if st.button('Scatter Recency vs Monetary'):
            selected_button = 'Scatter Recency vs Monetary'
    with col7:
        if st.button('Pareto Chart'):
            selected_button = 'Pareto Chart'
    with col8:
        if st.button('About categories'):
            category_counts = rfm_df['Category'].value_counts().reindex(category_order, fill_value=0).reset_index()
            category_counts.columns = ['Category', 'Count']
            fig = px.bar(category_counts, x='Category', y='Count', title='Category Distribution', color_discrete_sequence=['dodgerblue'])
            st.plotly_chart(fig)
            st.write(category_counts)

    # Display the graph based on the selected button
    if selected_button == 'Recency':
        fig1 = px.histogram(filtered_category_df, x='Recency', title='Histogram Recency', color_discrete_sequence=['dodgerblue'])
        fig2 = px.box(filtered_category_df, y='Recency', title='Boxplot Recency', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig1)
        st.plotly_chart(fig2)
        st.markdown("<p style='font-size: small;'>Recency shows how recently each customer made a purchase.</p>", unsafe_allow_html=True)

    if selected_button == 'Frequency':
        fig1 = px.histogram(filtered_category_df, x='Frequency', title='Histogram Frequency', color_discrete_sequence=['dodgerblue'])
        fig2 = px.box(filtered_category_df, y='Frequency', title='Boxplot Frequency', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig1)
        st.plotly_chart(fig2)
        st.markdown("<p style='font-size: small;'>Frequency shows how often each customer makes a purchase.</p>", unsafe_allow_html=True)

    if selected_button == 'Monetary':
        fig1 = px.histogram(filtered_category_df, x='Monetary', title='Histogram Monetary', color_discrete_sequence=['dodgerblue'])
        fig2 = px.box(filtered_category_df, y='Monetary', title='Boxplot Monetary', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig1)
        st.plotly_chart(fig2)
        st.markdown("<p style='font-size: small;'>Monetary shows how much money each customer spends.</p>", unsafe_allow_html=True)

    if selected_button == 'Scatter Recency vs Frequency':
        fig = px.scatter(filtered_category_df, x='Recency', y='Frequency', title='Scatter Recency vs Frequency', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig)

    if selected_button == 'Scatter Frequency vs Monetary':
        fig = px.scatter(filtered_category_df, x='Frequency', y='Monetary', title='Scatter Frequency vs Monetary', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig)

    if selected_button == 'Scatter Recency vs Monetary':
        fig = px.scatter(filtered_category_df, x='Recency', y='Monetary', title='Scatter Recency vs Monetary', color_discrete_sequence=['dodgerblue'])
        st.plotly_chart(fig)

    if selected_button == 'Pareto Chart':
        filtered_category_df_sorted = filtered_category_df.sort_values('Monetary', ascending=False)
        filtered_category_df_sorted['Cumulative Sum'] = filtered_category_df_sorted['Monetary'].cumsum()
        filtered_category_df_sorted['Cumulative Percentage'] = 100 * filtered_category_df_sorted['Cumulative Sum'] / filtered_category_df_sorted['Monetary'].sum()
        
        fig = px.bar(filtered_category_df_sorted, x='id', y='Monetary', title='Pareto Chart', color_discrete_sequence=['dodgerblue'])
        fig.add_scatter(x=filtered_category_df_sorted['id'], y=filtered_category_df_sorted['Cumulative Percentage'], mode='lines+markers', name='Cumulative Percentage', marker=dict(color='red', size=8, symbol='circle'))
        st.plotly_chart(fig)
        st.markdown("<p style='font-size: small;'>Pareto chart shows the cumulative contribution of each customer to the total revenue.</p>", unsafe_allow_html=True)

except FileNotFoundError:
    st.error(f"File not found at path {csv_path}.")
except Exception as e:
    st.error(f"An error occurred while loading the file: {e}")
