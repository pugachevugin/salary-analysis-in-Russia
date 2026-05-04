import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

st.set_page_config(page_title="Анализ зарплат РФ", layout="wide")
st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_simple_data():
    # 1. Загрузка инфляции
    inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
    inf_df.columns = [str(c).strip() for c in inf_df.columns]
    if 'Год' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Год': 'Year'})
    if 'Всего' in inf_df.columns:
        inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
    
    # 2. Загрузка зарплат
    xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
    df = pd.read_excel(xls, 'с 2017 г.', skiprows=2)
    
    # Очистка колонок от лишнего текста, оставляем только годы
    new_cols = []
    for col in df.columns:
        year_match = re.search(r'20\d{2}', str(col))
        new_cols.append(year_match.group() if year_match else str(col).strip())
    df.columns = new_cols
    
    # Очистка названий отраслей
    df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
    return df, inf_df[['Year', 'Inflation_Rate']]

try:
    df_salary, df_inf = load_simple_data()

    # Фильтруем список отраслей: убираем сноски и пустые строки
    all_industries = sorted([
        x for x in df_salary.iloc[:, 0].unique() 
        if len(x) > 5 and not x.startswith('1)') and 'Unnamed' not in x
    ])
    
    selected = st.multiselect(
        "Выберите отрасли для анализа:",
        options=all_industries,
        default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]]
    )

    if selected:
        plot_data = []
        for ind in selected:
            row = df_salary[df_salary.iloc[:, 0] == ind]
            years = [str(y) for y in range(2017, 2024) if str(y) in df_salary.columns]
            
            for yr in years:
                val = row[yr].values[0]
                # КРИТИЧЕСКИЙ МОМЕНТ: Пытаемся превратить в число, если не выходит — игнорируем
                try:
                    clean_val = float(str(val).replace(' ', '').replace(',', '.'))
                    plot_data.append({
                        'Year': int(yr),
                        'Salary': clean_val,
                        'Industry': ind
                    })
                except ValueError:
                    continue # Это была сноска или текст, просто пропускаем
        
        if plot_data:
            final_df = pd.DataFrame(plot_data)
            df_inf['Year'] = df_inf['Year'].astype(int)
            final_df = pd.merge(final_df, df_inf, on='Year', how='left')

            final_df = final_df.sort_values(['Industry', 'Year'])
            final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
            final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
            final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

            tab1, tab2 = st.tabs(["Визуализация", "Данные"])
            
            with tab1:
                st.subheader("Динамика номинальных зарплат (руб.)")
                fig1, ax1 = plt.subplots(figsize=(10, 5))
                sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
                plt.grid(True, alpha=0.2)
                st.pyplot(fig1)

                st.subheader("Реальный годовой прирост (за вычетом инфляции), %")
                fig2, ax2 = plt.subplots(figsize=(10, 5))
                sns.barplot(data=final_df.dropna(subset=['Real_Growth']), x='Year', y='Real_Growth', hue='Industry')
                plt.axhline(0, color='red', lw=1.5, ls='--')
                st.pyplot(fig2)
            
            with tab2:
                st.dataframe(final_df)
        else:
            st.warning("В выбранных строках не найдено числовых данных.")

except Exception as e:
    st.error(f"Произошла ошибка: {e}")
