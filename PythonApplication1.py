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
    
    # Исправляем ошибку 'Year': переименовываем 'Год' в 'Year', а 'Всего' в 'Inflation_Rate'
    # Проверяем, как называются колонки в твоем файле
    if 'Год' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Год': 'Year'})
    if 'Всего' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
        
    inf_annual = inf_df[['Year', 'Inflation_Rate']].copy()

    # 2. Загрузка зарплат
    xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
    df_old = pd.read_excel(xls, '2000-2016 гг.', skiprows=1)
    df_new = pd.read_excel(xls, 'с 2017 г.', skiprows=2)
    
    # Чистим названия отраслей от лишних пробелов
    df_old.iloc[:, 0] = df_old.iloc[:, 0].str.strip()
    df_new.iloc[:, 0] = df_new.iloc[:, 0].str.strip()
    
    return df_old, df_new, inf_annual

try:
    df_old, df_new, inf_annual = load_data()

    # Список всех отраслей для выбора
    all_industries = sorted(list(df_old.iloc[:, 0].dropna().unique()))
    selected_industries = st.multiselect(
        "Выберите отрасли:", 
        options=all_industries, 
        default=[all_industries[0]] if all_industries else None
    )

    if selected_industries:
        combined_data = []

        for ind in selected_industries:
            # Данные 2000-2016
            row_old = df_old[df_old.iloc[:, 0] == ind]
            # Данные 2017-2023 (ищем по частичному совпадению названия)
            row_new = df_new[df_new.iloc[:, 0].str.contains(str(ind)[:10], na=False)]

            if not row_old.empty and not row_new.empty:
                # Собираем 2000-2016
                for yr in range(2000, 2017):
                    if yr in df_old.columns:
                        combined_data.append({'Year': yr, 'Salary': row_old[yr].values[0], 'Industry': ind})
                
                # Собираем 2017-2023
                for yr in range(2017, 2024):
                    # Ищем колонку, в названии которой есть год
                    col = [c for c in df_new.columns if str(yr) in str(c)]
                    if col:
                        combined_data.append({'Year': yr, 'Salary': row_new[col[0]].values[0], 'Industry': ind})

        if combined_data:
            final_df = pd.DataFrame(combined_data)
            
            # Приводим типы к числам, чтобы merge сработал
            final_df['Year'] = final_df['Year'].astype(int)
            inf_annual['Year'] = inf_annual['Year'].astype(int)
            
            final_df = pd.merge(final_df, inf_annual, on='Year', how='left')

            # Расчеты роста
            final_df['Salary'] = pd.to_numeric(final_df['Salary'], errors='coerce')
            final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
            final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
            final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

            # Графики
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Номинальные зарплаты")
                fig1, ax1 = plt.subplots()
                sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
                st.pyplot(fig1)

            with col2:
                st.subheader("Реальный рост (за вычетом инфляции), %")
                fig2, ax2 = plt.subplots()
                sns.barplot(data=final_df[final_df['Year'] > 2000], x='Year', y='Real_Growth', hue='Industry')
                plt.axhline(0, color='red', linestyle='--')
                plt.xticks(rotation=45)
                st.pyplot(fig2)
                
            st.write("Данные для анализа:", final_df)
        else:
            st.warning("Не удалось сопоставить данные для выбранных отраслей.")

except Exception as e:
    st.error(f"Произошла ошибка: {e}")
    st.info("Проверьте, что названия колонок в Excel не изменились.")