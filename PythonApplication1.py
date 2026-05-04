import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Настройка страницы Streamlit
st.set_page_config(page_title="Анализ зарплат в РФ", layout="wide")

st.title("📊 Анализ номинальных и реальных зарплат в России (2000-2023)")
st.markdown("""
Это приложение анализирует данные Росстата по зарплатам и сопоставляет их с уровнем инфляции.
""")

@st.cache_data
def load_and_clean_data():
    # 1. Загрузка данных об инфляции
    inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
    # Берем годовую инфляцию (столбец 'Всего')
    inf_annual = inf_df[['Год', 'Всего']].copy()
    inf_annual.columns = ['Year', 'Inflation_Rate']
    
    # 2. Загрузка данных о зарплатах
    xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
    df_old = pd.read_excel(xls, '2000-2016 гг.', skiprows=1)
    df_new = pd.read_excel(xls, 'с 2017 г.', skiprows=2)
    
    # Очистка названий отраслей
    df_old.iloc[:, 0] = df_old.iloc[:, 0].str.strip()
    df_new.iloc[:, 0] = df_new.iloc[:, 0].str.strip()
    
    return df_old, df_new, inf_annual

try:
    df_old, df_new, inf_annual = load_and_clean_data()

    # Интерфейс выбора отраслей
    all_industries = sorted(list(set(df_old.iloc[:, 0].dropna().unique())))
    selected_industries = st.multiselect(
        "Выберите отрасли для анализа:", 
        options=all_industries, 
        default=["Всего по  экономике", "Добыча полезных ископаемых"]
    )

    if selected_industries:
        combined_data = []

        for ind in selected_industries:
            # Извлекаем данные за 2000-2016
            row_old = df_old[df_old.iloc[:, 0] == ind]
            # Извлекаем данные за 2017-2023
            row_new = df_new[df_new.iloc[:, 0].str.contains(ind[:15], na=False)] # Поиск по части названия

            if not row_old.empty and not row_new.empty:
                # Собираем года (с 2000 по 2023)
                for yr in range(2000, 2017):
                    combined_data.append({
                        'Year': yr, 
                        'Salary': row_old[yr].values[0], 
                        'Industry': ind
                    })
                # В новой таблице колонки могут быть строками или числами
                years_new = [2017, 2018, 2019, 2020, 2021, 2022, 2023]
                for yr in years_new:
                    # Пытаемся найти колонку (обработка специфики Excel)
                    col = next((c for c in df_new.columns if str(yr) in str(c)), None)
                    if col:
                        combined_data.append({
                            'Year': yr, 
                            'Salary': row_new[col].values[0], 
                            'Industry': ind
                        })

        final_df = pd.DataFrame(combined_data)
        final_df = pd.merge(final_df, inf_annual, on='Year', how='left')

        # Расчет реальной зарплаты (базовый год - 2000)
        # Для простоты в задании 4 просят сравнение с предыдущим годом
        final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
        final_df['Nominal_Growth_%'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
        final_df['Real_Growth_%'] = final_df['Nominal_Growth_%'] - final_df['Inflation_Rate']

        # ВИЗУАЛИЗАЦИЯ 1: Номинальные зарплаты
        st.subheader("1. Динамика номинальных зарплат")
        fig1, ax1 = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o', ax=ax1)
        plt.grid(True, alpha=0.3)
        st.pyplot(fig1)

        # ВИЗУАЛИЗАЦИя 2: Реальный рост
        st.subheader("2. Реальный рост зарплат (за вычетом инфляции)")
        st.info("Если столбец ниже нуля — инфляция «съела» весь прирост зарплаты в этом году.")
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.barplot(data=final_df[final_df['Year'] > 2000], x='Year', y='Real_Growth_%', hue='Industry', ax=ax2)
        plt.axhline(0, color='red', linestyle='--')
        plt.xticks(rotation=45)
        st.pyplot(fig2)

        # Вывод таблицы данных
        with st.expander("Посмотреть сырые данные"):
            st.dataframe(final_df)

except Exception as e:
    st.error(f"Ошибка загрузки файлов: {e}")
    st.warning("Убедитесь, что файлы 'tab3-zpl_2025.xlsx' и 'Statistic_Inflatio_Russia.xlsx' лежат в одной папке с кодом.")
