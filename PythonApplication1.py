import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Анализ зарплат РФ", layout="wide")

st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_simple_data():
    # 1. Загрузка инфляции
    inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
    # Переименовываем для удобства
    inf_df.columns = [str(c).strip() for c in inf_df.columns]
    if 'Год' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Год': 'Year'})
    if 'Всего' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
    
    # 2. Загрузка зарплат (только актуальный лист с 2017)
    xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
    df = pd.read_excel(xls, 'с 2017 г.', skiprows=2)
    
    # Чистим названия колонок (года)
    new_cols = []
    for col in df.columns:
        # Ищем 4 цифры года в названии колонки
        import re
        year_match = re.search(r'20\d{2}', str(col))
        if year_match:
            new_cols.append(year_match.group())
        else:
            new_cols.append(col)
    df.columns = new_cols
    
    # Чистим названия отраслей
    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
    # Убираем пустые строки
    df = df.dropna(subset=[df.columns[0]])
    
    return df, inf_df[['Year', 'Inflation_Rate']]

try:
    df_salary, df_inf = load_simple_data()

    # Список отраслей (только из новой таблицы, чтобы не было ошибок сопоставления)
    all_industries = sorted(df_salary.iloc[:, 0].unique())
    
    selected = st.multiselect(
        "Выберите отрасли для анализа (данные с 2017 года):",
        options=all_industries,
        default=[all_industries[0]] if all_industries else None
    )

    if selected:
        plot_data = []
        for ind in selected:
            row = df_salary[df_salary.iloc[:, 0] == ind]
            # Года, которые есть в таблице
            years = [str(y) for y in range(2017, 2024) if str(y) in df_salary.columns]
            
            for yr in years:
                val = row[yr].values[0]
                # Очистка значения от сносок или пробелов
                if isinstance(val, str):
                    val = val.replace(' ', '').replace(',', '.')
                
                plot_data.append({
                    'Year': int(yr),
                    'Salary': float(val),
                    'Industry': ind
                })
        
        final_df = pd.DataFrame(plot_data)
        df_inf['Year'] = df_inf['Year'].astype(int)
        final_df = pd.merge(final_df, df_inf, on='Year', how='left')

        # Расчет реальных показателей
        final_df = final_df.sort_values(['Industry', 'Year'])
        final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
        final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
        final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

        # Графики
        tab1, tab2 = st.tabs(["Графики", "Таблица данных"])
        
        with tab1:
            st.subheader("Динамика номинальных зарплат")
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='s')
            plt.grid(True, alpha=0.2)
            st.pyplot(fig1)

            st.subheader("Реальный прирост (зарплата опережает инфляцию?), %")
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            sns.barplot(data=final_df.dropna(), x='Year', y='Real_Growth', hue='Industry')
            plt.axhline(0, color='red', linestyle='--')
            st.pyplot(fig2)

        with tab2:
            st.dataframe(final_df)

except Exception as e:
    st.error(f"Ошибка: {e}")
    st.info("Попробуйте обновить страницу или проверить файлы.")
