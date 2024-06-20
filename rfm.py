import streamlit as st
import pandas as pd
import re

# Titulek aplikace s barevným textem
st.markdown("""
# RFM for <span style="color:dodgerblue">Keboola</span> by <span style="color:purple">Bytegarden</span>
""", unsafe_allow_html=True)

# Funkce pro přiřazení kategorií na základě num_of_events
def assign_category(num_of_events):
    patterns = {
        r'5[4-5]': '01. Champions',
        r'[3-4][4-5]': '02. Loyal Customers',
        r'[4-5][2-3]': '03. Potential Loyalists',
        r'51': '04. Recent Customers',
        r'41': '05. Promising',
        r'33': '06. Need Attention',
        r'3[1-2]': '07. About to Sleep',
        r'[1-2][5]': '08. Can\'t Lose',
        r'[1-2][3-4]': '09. At Risk',
        r'2[1-2]': '10. Hibernating',
        r'1[1-2]': '11. Lost',
    }
    
    for pattern, category in patterns.items():
        if re.match(pattern, str(num_of_events)):
            return category
    return 'Uncategorized'

# Načtení CSV souboru
csv_path = "rfm-data.csv"  # relativní cesta, pokud je skript ve stejné složce
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
        
        # Filtrování dat podle vybraných dat
        filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
        
        # Přiřazení kategorií
        if 'num_of_events' in filtered_df.columns:
            filtered_df['Category'] = filtered_df['num_of_events'].apply(assign_category)
        else:
            st.error("DataFrame neobsahuje sloupec 'num_of_events'.")
        
        # Zobrazení filtrované a kategorizované tabulky
        st.dataframe(filtered_df)
        
except FileNotFoundError:
    st.error(f"Soubor na cestě {csv_path} nebyl nalezen.")
except Exception as e:
    st.error(f"Došlo k chybě při načítání souboru: {e}")
