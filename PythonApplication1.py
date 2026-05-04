import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Анализ зарплат в РФ", layout="wide")

st.title("📊 Анализ номинальных и реальных зарплат в РФ")

@st.cache_data
def load_data():
    # 1. Загрузка инфляции
    inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
    if 'Год' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Год': 'Year'})
    if 'Всего' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
    inf_annual = inf_df[['Year', 'Inflation_Rate']].copy()

    # 2. Загрузка зарплат
    xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
    df_old = pd.read_excel(xls, '2000-2016 гг.', skiprows=1)
    df_new = pd.read_excel(xls, 'с 2017 г.', skiprows=2)
    
    # Базовая очистка названий
    df_old.iloc[:, 0] = df_old.iloc[:, 0].astype(str).str.strip()
    df_new.iloc[:, 0] = df_new.iloc[:, 0].astype(str).str.strip()
    
    return df_old, df_new, inf_annual

try:
    df_old, df_new, inf_annual = load_data()

    # Берем список отраслей из старой таблицы (с ними проще работать)
    # Фильтруем пустые строки и технические заголовки
    raw_list = df_old.iloc[:, 0].dropna().unique()
    all_industries = [x for x in raw_list if len(x) > 5 and 'Unnamed' not in x]

    selected_industries = st.multiselect(
        "Выберите отрасли для анализа:", 
        options=all_industries, 
        default=["Всего по  экономике"] if "Всего по  экономике" in all_industries else [all_industries[0]]
    )

    if selected_industries:
        combined_data = []

        for ind in selected_industries:
            # 1. Ищем данные в старой таблице
            row_old = df_old[df_old.iloc[:, 0] == ind]
            
            # 2. Ищем данные в новой таблице (по частичному вхождению строки)
            # Берем первые 20 символов названия для поиска, так как в новых таблицах названия длиннее
            search_term = ind[:20].lower()
            row_new = df_new[df_new.iloc[:, 0].str.lower().str.contains(search_term, na=False)]

            if not row_old.empty and not row_new.empty:
                # Сбор данных 2000-2016
                for yr in range(2000, 2017):
                    # В df_old колонки с годами могут быть числами или строками
                    col = next((c for c in df_old.columns if str(yr) in str(c)), None)
                    if col:
                        val = row_old[col].values[0]
                        if pd.notnull(val) and not isinstance(val, str):
                            combined_data.append({'Year': int(yr), 'Salary': float(val), 'Industry': ind})
                
                # Сбор данных 2017-2023
                for yr in range(2017, 2024):
                    col = next((c for c in df_new.columns if str(yr) in str(c)), None)
                    if col:
                        val = row_new[col].values[0]
                        if pd.notnull(val) and not isinstance(val, str):
                            combined_data.append({'Year': int(yr), 'Salary': float(val), 'Industry': ind})

        if combined_data:
            final_df = pd.DataFrame(combined_data)
            
            # Объединяем с инфляцией
            inf_annual['Year'] = inf_annual['Year'].astype(int)
            final_df = pd.merge(final_df, inf_annual, on='Year', how='left')

            # Расчеты
            final_df = final_df.sort_values(['Industry', 'Year'])
            final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
            final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
            final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

            # Визуализация
            st.subheader("Динамика номинальных зарплат (руб.)")
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
            plt.grid(True, alpha=0.3)
            st.pyplot(fig1)

            st.subheader("Реальный рост за год (за вычетом инфляции), %")
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            sns.barplot(data=final_df[final_df['Year'] > 2000], x='Year', y='Real_Growth', hue='Industry')
            plt.axhline(0, color='black', lw=1)
            plt.xticks(rotation=45)
            st.pyplot(fig2)
            
            with st.expander("Посмотреть итоговую таблицу"):
                st.dataframe(final_df)
        else:
            st.error("Данные не найдены. Попробуйте выбрать другую отрасль.")
            st.write("Отладочная информация: поиск велся по ключевым словам:", [x[:20] for x in selected_industries])

except Exception as e:
    st.error(f"Критическая ошибка: {e}")
