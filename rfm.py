import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# Titulek aplikace s barevným textem
st.markdown("""
# RFM for <span style="color:dodgerblue">Keboola</span> by <span style="color:purple">Bytegarden</span>
""", unsafe_allow_html=True)

# Funkce pro přiřazení kategorií na základě počtu opakování ID
def assign_category(repeat_count):
    if repeat_count >= 54:
        return '01. Champions'
    elif 34 <= repeat_count <= 53:
        return '02. Loyal Customers'
    elif 24 <= repeat_count <= 33:
        return '03. Potential Loyalists'
    elif 15 <= repeat_count <= 23:
        return '04. Recent Customers'
    elif 10 <= repeat_count <= 15:
        return '05. Promising'
    elif 7 <= repeat_count <= 10:
        return '06. Need Attention'
    elif 5 <= repeat_count <= 6:
        return '07. About to Sleep'
    elif repeat_count == 4:
        return '08. Can\'t Lose'
    elif 3 <= repeat_count <= 4:
        return '09. At Risk'
    elif 2 <= repeat_count <= 1:
        return '10. Hibernating'
    else:
        return '11. Lost'

# Načtení CSV souboru
csv_path = "rfm-data.csv"
try:
    df = pd.read_csv(csv_path)
    
    # Kontrola, zda DataFrame obsahuje sloupec s datem
    if 'date' not in df.columns:
        st.error("DataFrame neobsahuje sloupec 'date'.")
    else:
        # Převod sloupce 'date' na typ datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Vytvoření interaktivních polí pro výběr datumu v postranním panelu
        start_date = st.sidebar.date_input('Start date', df['date'].min().date())
        end_date = st.sidebar.date_input('End date', df['date'].max().date())
        
        # Filtrování dat podle vybraných dat
        filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
        
        # Počet opakování ID
        id_counts = filtered_df['id'].value_counts().reset_index()
        id_counts.columns = ['id', 'count']
        
        # Přiřazení kategorií
        id_counts['Category'] = id_counts['count'].apply(assign_category)
        
        # Spočítání řádků v jednotlivých kategoriích
        category_counts = id_counts['Category'].value_counts().sort_index().reset_index()
        category_counts.columns = ['Category', 'Count']

        # Vytvoření grafu pomocí Plotly
        fig = px.bar(category_counts, x='Category', y='Count', title='How many customers are in each category', labels={'Count': 'Count', 'Category': 'Category'})
        
        # Zobrazení grafu ve Streamlit
        st.plotly_chart(fig)
        
except FileNotFoundError:
    st.error(f"Soubor na cestě {csv_path} nebyl nalezen.")
except Exception as e:
    st.error(f"Došlo k chybě při načítání souboru: {e}")
