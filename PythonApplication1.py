import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.title("📊 Мониторинг зарплат РФ")

@st.cache_data
def load_data():
    # Читаем CSV файлы (разделитель - запятая)
    df_inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    df_zpl_wide = pd.read_csv('tab3-zpl_2025_2.csv')
    
    # Трансформируем таблицу
    df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
    df_zpl['Year'] = df_zpl['Year'].astype(int)
    df_inf['Year'] = df_inf['Year'].astype(int)
    
    return pd.merge(df_zpl, df_inf, on='Year', how='left')

try:
    df = load_data()
    selected = st.multiselect("Выберите отрасли:", df['Industry'].unique(), default=["Всего по экономике"])
    
    if selected:
        res = df[df['Industry'].isin(selected)].sort_values(['Industry', 'Year'])
        res['Nominal_Growth'] = res.groupby('Industry')['Salary'].pct_change() * 100
        res['Real_Growth'] = res['Nominal_Growth'] - res['Inflation']

        # Графики
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=res, x='Year', y='Salary', hue='Industry', marker='o')
        st.pyplot(fig1)

        st.write("### Таблица данных")
        st.dataframe(res)
except Exception as e:
    st.error(f"Файлы .csv не найдены в репозитории: {e}")
