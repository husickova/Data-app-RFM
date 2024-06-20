import streamlit as st
import pandas as pd
from datetime import datetime

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
    elif repeat_count == 21:
        return '04. Recent Customers'
    elif repeat_count == 14:
        return '05. Promising'
    elif repeat_count == 13:
        return '06. Need Attention'
    elif 11 <= repeat_count <= 12:
        return '07. About to Sleep'
    elif repeat_count == 25:
        return '08. Can\'t Lose'
    elif 13 <= repeat_count <= 14:
        return '09. At Risk'
    elif 12 <= repeat_count <= 11:
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
        
        # Vytvoření interaktivních polí pro výběr datumu
        start_date = st.date_input('Start date', df['date'].min().date())
        end_date = st.date_input('End date', df['date'].max().date())
        
        # Tlačítka pro výběr měsíce
        if st.button('Leden'):
            start_date = datetime(start_date.year, 1, 1)
            end_date = datetime(start_date.year, 1, 31)
        if st.button('Únor'):
            start_date = datetime(start_date.year, 2, 1)
            end_date = datetime(start_date.year, 2, 28) if start_date.year % 4 != 0 else datetime(start_date.year, 2, 29)
        if st.button('Březen'):
            start_date = datetime(start_date.year, 3, 1)
            end_date = datetime(start_date.year, 3, 31)
        if st.button('Duben'):
            start_date = datetime(start_date.year, 4, 1)
            end_date = datetime(start_date.year, 4, 30)
        if st.button('Květen'):
            start_date = datetime(start_date.year, 5, 1)
            end_date = datetime(start_date.year, 5, 31)
        if st.button('Červen'):
            start_date = datetime(start_date.year, 6, 1)
            end_date = datetime(start_date.year, 6, 30)
        if st.button('Červenec'):
            start_date = datetime(start_date.year, 7, 1)
            end_date = datetime(start_date.year, 7, 31)
        if st.button('Srpen'):
            start_date = datetime(start_date.year, 8, 1)
            end_date = datetime(start_date.year, 8, 31)
        if st.button('Září'):
            start_date = datetime(start_date.year, 9, 1)
            end_date = datetime(start_date.year, 9, 30)
        if st.button('Říjen'):
            start_date = datetime(start_date.year, 10, 1)
            end_date = datetime(start_date.year, 10, 31)
        if st.button('Listopad'):
            start_date = datetime(start_date.year, 11, 1)
            end_date = datetime(start_date.year, 11, 30)
        if st.button('Prosinec'):
            start_date = datetime(start_date.year, 12, 1)
            end_date = datetime(start_date.year, 12, 31)
        
        # Filtrování dat podle vybraných dat
        filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
        
        # Počet opakování ID
        id_counts = filtered_df['id'].value_counts().reset_index()
        id_counts.columns = ['id', 'count']
        
        # Přiřazení kategorií
        id_counts['Category'] = id_counts['count'].apply(assign_category)
        
        # Spočítání řádků v jednotlivých kategoriích
        category_counts = id_counts['Category'].value_counts().sort_index()

        # Vytvoření grafu pomocí Streamlit
        st.bar_chart(category_counts)
        
except FileNotFoundError:
    st.error(f"Soubor na cestě {csv_path} nebyl nalezen.")
except Exception as e:
    st.error(f"Došlo k chybě při načítání souboru: {e}")
