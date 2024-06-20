import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Titulek aplikace s barevným textem
st.markdown("""
# RFM for <span style="color:dodgerblue">Keboola</span> by <span style="color:purple">Bytegarden</span>
""", unsafe_allow_html=True)

# Funkce pro přiřazení kategorií na základě RFM skóre
def assign_category(rfm_score):
    if rfm_score >= 555:
        return '01. Champions'
    elif rfm_score >= 455:
        return '02. Loyal Customers'
    elif rfm_score >= 355:
        return '03. Potential Loyalists'
    elif rfm_score >= 255:
        return '04. Recent Customers'
    elif rfm_score >= 155:
        return '05. Promising'
    elif rfm_score >= 115:
        return '06. Need Attention'
    elif rfm_score >= 105:
        return '07. About to Sleep'
    elif rfm_score >= 75:
        return '08. Can\'t Lose'
    elif rfm_score >= 55:
        return '09. At Risk'
    elif rfm_score >= 15:
        return '10. Hibernating'
    else:
        return '11. Lost'

# Načtení CSV souboru
csv_path = "/mnt/data/rfm-data.csv"
try:
    df = pd.read_csv(csv_path)
    
    # Převod sloupce 'date' na typ datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Vytvoření interaktivních polí pro výběr datumu v postranním panelu
    start_date = st.sidebar.date_input('Start date', df['date'].min().date())
    end_date = st.sidebar.date_input('End date', df['date'].max().date())
    
    # Filtrování dat podle vybraných dat
    filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    
    # Vypočítání RFM hodnot
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
    
    # Normalizace RFM hodnot s dynamickým počtem popisků
    recency_bins = pd.qcut(rfm_df['Recency'], q=5, duplicates='drop').cat.categories.size
    frequency_bins = pd.qcut(rfm_df['Frequency'], q=5, duplicates='drop').cat.categories.size
    monetary_bins = pd.qcut(rfm_df['Monetary'], q=5, duplicates='drop').cat.categories.size
    
    rfm_df['R_rank'] = pd.qcut(rfm_df['Recency'], q=recency_bins, labels=[str(i) for i in range(recency_bins, 0, -1)])
    rfm_df['F_rank'] = pd.qcut(rfm_df['Frequency'], q=frequency_bins, labels=[str(i) for i in range(1, frequency_bins + 1)])
    rfm_df['M_rank'] = pd.qcut(rfm_df['Monetary'], q=monetary_bins, labels=[str(i) for i in range(1, monetary_bins + 1)])
    
    rfm_df['RFM_Score'] = rfm_df['R_rank'].astype(str) + rfm_df['F_rank'].astype(str) + rfm_df['M_rank'].astype(str)

    # Kategorie na základě RFM skóre
    rfm_df['Category'] = rfm_df['RFM_Score'].apply(lambda x: assign_category(int(x[0] + x[1])))

    # Spočítání řádků v jednotlivých kategoriích
    category_counts = rfm_df['Category'].value_counts().sort_index().reset_index()
    category_counts.columns = ['Category', 'Count']
    
    # Vytvoření sloupců pro tlačítka
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

    # Zobrazení grafu na základě vybraného tlačítka
    if selected_button == 'Recency':
        fig = px.histogram(rfm_df, x='Recency', title='Recency')
        st.plotly_chart(fig)

    if selected_button == 'Frequency':
        fig = px.histogram(rfm_df, x='Frequency', title='Frequency')
        st.plotly_chart(fig)

    if selected_button == 'Monetary':
        fig = px.histogram(rfm_df, x='Monetary', title='Monetary')
        st.plotly_chart(fig)

    # Vytvoření hlavního grafu pomocí Plotly
    fig = px.bar(category_counts, x='Category', y='Count', title='How many customers are in each category', labels={'Count': 'Count', 'Category': 'Category'})
    
    # Zobrazení hlavního grafu ve Streamlit
    st.plotly_chart(fig)

except FileNotFoundError:
    st.error(f"Soubor na cestě {csv_path} nebyl nalezen.")
except Exception as e:
    st.error(f"Došlo k chybě při načítání souboru: {e}")
