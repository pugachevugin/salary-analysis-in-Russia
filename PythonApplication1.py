import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Настройка страницы
st.set_page_config(page_title="Мониторинг зарплат РФ", layout="wide")
st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_data():
    # Загружаем уже чистые файлы
    df_inf = pd.read_excel('Statistic_Inflatio_Russia_2.xlsx')
    df_zpl_wide = pd.read_excel('tab3-zpl_2025_2.xlsx')
    
    # Переводим таблицу зарплат из широкого формата в длинный (tidy data)
    # Было: Industry | 2017 | 2018... Стало: Industry | Year | Salary
    df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
    
    # Приводим типы данных
    df_zpl['Year'] = df_zpl['Year'].astype(int)
    df_inf['Year'] = df_inf['Year'].astype(int)
    
    # Объединяем зарплаты с инфляцией по году
    df = pd.merge(df_zpl, df_inf, on='Year', how='left')
    return df

try:
    df = load_data()
    
    # Боковая панель с выбором отраслей
    all_industries = sorted(df['Industry'].unique())
    default_choice = ["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]]
    
    selected = st.multiselect("Выберите отрасли для сравнения:", all_industries, default=default_choice)

    if selected:
        # Фильтруем и считаем рост
        filtered = df[df['Industry'].isin(selected)].sort_values(['Industry', 'Year'])
        
        # Расчет показателей: pct_change() дает изменение в долях, умножаем на 100 для %
        filtered['Nominal_Growth'] = filtered.groupby('Industry')['Salary'].pct_change() * 100
        filtered['Real_Growth'] = filtered['Nominal_Growth'] - filtered['Inflation']

        # Блок графиков
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Динамика зарплат (руб.)")
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.lineplot(data=filtered, x='Year', y='Salary', hue='Industry', marker='o', linewidth=2)
            plt.grid(True, alpha=0.3)
            st.pyplot(fig1)

        with col2:
            st.subheader("Реальный рост за год (%)")
            st.caption("С учетом инфляции. Если выше 0 — покупательная способность выросла.")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            plot_data = filtered.dropna(subset=['Real_Growth'])
            if not plot_data.empty:
                sns.barplot(data=plot_data, x='Year', y='Real_Growth', hue='Industry')
                plt.axhline(0, color='black', linewidth=1)
            st.pyplot(fig2)

        # Таблица внизу
        st.divider()
        with st.expander("Посмотреть детальные данные"):
            st.dataframe(filtered.style.format(subset=['Salary', 'Inflation', 'Nominal_Growth', 'Real_Growth'], precision=2))
    else:
        st.warning("Выберите хотя бы одну отрасль в списке выше.")

except Exception as e:
    st.error(f"Ошибка загрузки данных: {e}")
    st.info("Убедитесь, что файлы 'tab3-zpl_2025_2.xlsx' и 'Statistic_Inflatio_Russia_2.xlsx' лежат в корне репозитория.")
