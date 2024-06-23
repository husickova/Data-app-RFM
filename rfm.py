import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
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

    # CSS for styling buttons
    st.markdown("""
    <style>
    .stButton > button {
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .custom-button {
        background-color: lightgray;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .stMarkdown > div > div > div > div > div:first-child > div {
        display: flex;
        flex-wrap: wrap;
    }
    .stMarkdown > div > div > div > div > div:first-child > div > div {
        flex-grow: 0;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create buttons
    buttons = [
        ("Segmentation", "About categories"),
        ("Recency", "Recency"),
        ("Frequency", "Frequency"),
        ("Monetary", "Monetary"),
        ("Scatter Recency vs Frequency", "Scatter Recency vs Frequency"),
        ("Scatter Frequency vs Monetary", "Scatter Frequency vs Monetary"),
        ("Scatter Recency vs Monetary", "Scatter Recency vs Monetary"),
        ("3D Scatter Plot", "3D Scatter Plot"),
        ("Pareto Chart", "Pareto Chart"),
        ("Heatmap R & F", "Heatmap R & F")
    ]

    selected_button = None

    for button_text, button_value in buttons:
        if st.button(button_text, key=button_value):
            selected_button = button_value

    # Display the graph based on the selected button
    if selected_button is None:
        selected_button = 'About categories'

    # Filter data based on the selected categories
    filtered_category_df = rfm_df

    if selected_button == 'Recency':
        fig1 = px.histogram(filtered_category_df, x='Recency', title='Histogram Recency', color='Category', category_orders={'Category': category_order})
        fig2 = px.box(filtered_category_df, y='Recency', title='Boxplot Recency', color='Category', category_orders={'Category': category_order})
        st.plotly_chart(fig1)
        st.plotly_chart(fig2)
        st.markdown("<p style='font-size: small;'>Recency shows how recently each customer made a purchase.</p>", unsafe_allow_html=True)

    if selected_button == 'Frequency':
        fig1 = px.histogram(filtered_category_df, x='Frequency', title='Histogram Frequency', color='Category', category_orders={'Category': category_order})
        fig2 = px.box(filtered_category_df, y='Frequency', title='Boxplot Frequency', color='Category', category_orders={'Category': category_order})
        st.plotly_chart(fig1)
        st.plotly_chart(fig2)
        st.markdown("<p style='font-size: small;'>Frequency shows how often each customer makes a purchase.</p>", unsafe_allow_html=True)

    if selected_button == 'Monetary':
        fig1 = px.histogram(filtered_category_df, x='Monetary', title='Histogram Monetary', color='Category', category_orders={'Category': category_order})
        fig2 = px.box(filtered_category_df, y='Monetary', title='Boxplot Monetary', color='Category', category_orders={'Category': category_order})
        st.plotly_chart(fig1)
        st.plotly_chart(fig2)
        st.markdown("<p style='font-size: small;'>Monetary shows how much money each customer spends.</p>", unsafe_allow_html=True)

    if selected_button == 'Scatter Recency vs Frequency':
        fig = px.scatter(filtered_category_df, x='Recency', y='Frequency', title='Scatter Recency vs Frequency', color='Category', category_orders={'Category': category_order})
        st.plotly_chart(fig)

    if selected_button == 'Scatter Frequency vs Monetary':
        fig = px.scatter(filtered_category_df, x='Frequency', y='Monetary', title='Scatter Frequency vs Monetary', color='Category', category_orders={'Category': category_order})
        st.plotly_chart(fig)

    if selected_button == 'Scatter Recency vs Monetary':
        fig = px.scatter(filtered_category_df, x='Recency', y='Monetary', title='Scatter Recency vs Monetary', color='Category', category_orders={'Category': category_order})
        st.plotly_chart(fig)

    if selected_button == '3D Scatter Plot':
        fig = px.scatter_3d(filtered_category_df, x='Recency', y='Frequency', z='Monetary',
                            color='Category', 
                            title='3D Scatter Plot of Recency, Frequency, and Monetary',
                            height=800, category_orders={'Category': category_order})  # Increase height for better visualization
        fig.update_traces(marker=dict(size=5))  # Adjust marker size
        st.plotly_chart(fig)

    if selected_button == 'Pareto Chart':
        filtered_category_df_sorted = filtered_category_df.sort_values('Monetary', ascending=False)
        
        # Aggregating data into 11 categories for readability
        aggregated_df = filtered_category_df_sorted.groupby('Category').agg({
            'Monetary': 'sum'
        }).reset_index()

        # Calculate the percentage of total revenue for each category
        total_revenue = aggregated_df['Monetary'].sum()
        aggregated_df['Percentage of Total Revenue'] = 100 * aggregated_df['Monetary'] / total_revenue

        fig = go.Figure()

        # Bar chart for Monetary
        fig.add_trace(go.Bar(
            x=aggregated_df['Category'], 
            y=aggregated_df['Monetary'], 
            name='Monetary',
            marker_color='dodgerblue'
        ))

        # Line chart for Percentage of Total Revenue
        fig.add_trace(go.Scatter(
            x=aggregated_df['Category'], 
            y=aggregated_df['Percentage of Total Revenue'], 
            name='Percentage of Total Revenue', 
            yaxis='y2',
            mode='lines+markers',
            marker=dict(color='red', size=8, symbol='circle')
        ))

        # Create a secondary y-axis
        fig.update_layout(
            title='Pareto Chart',
            xaxis_title='Category',
            yaxis=dict(
                title='Monetary',
                side='left'
            ),
            yaxis2=dict(
                title='Percentage of Total Revenue',
                side='right',
                overlaying='y',
                range=[0, 110]  # Extend the range a bit beyond 100%
            ),
            legend=dict(
                x=0.1,
                y=1.1,
                bgcolor='rgba(255,255,255,0)',
                bordercolor='rgba(255,255,255,0)'
            )
        )

        st.plotly_chart(fig)
        st.markdown("<p style='font-size: small;'>Pareto chart shows the percentage contribution of each customer category to the total revenue.</p>", unsafe_allow_html=True)


    if selected_button == 'About categories':
        # Customizing the display for "About categories"
        fig = px.treemap(
            rfm_df, 
            path=['Category'], 
            values='Monetary', 
            color='Category', 
            color_discrete_sequence=px.colors.qualitative.Pastel, 
            title='Customer Distribution by RFM Categories'
        )
        st.plotly_chart(fig)

    if selected_button == 'Heatmap R & F':
        heatmap_data = rfm_df.pivot_table(index='R_rank', columns='F_rank', values='Monetary', aggfunc='mean').fillna(0)
        fig = px.imshow(heatmap_data, title='Heatmap of Recency and Frequency', color_continuous_scale='Blues')
        st.plotly_chart(fig)

except FileNotFoundError:
    st.error(f"File not found at path {csv_path}.")
except Exception as e:
    st.error(f"An error occurred while loading the file: {e}")

