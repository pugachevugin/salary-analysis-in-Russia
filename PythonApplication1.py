import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

st.set_page_config(page_title="Анализ зарплат РФ", layout="wide")
st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_and_clean_data():
    try:
        # 1. Загрузка инфляции
        inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
        inf_df.columns = [str(c).strip() for c in inf_df.columns]
        if 'Год' in inf_df.columns: inf_df = inf_df.rename(columns={'Год': 'Year'})
        if 'Всего' in inf_df.columns: inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
        inf_df['Year'] = pd.to_numeric(inf_df['Year'], errors='coerce')
        
        # 2. Загрузка зарплат
        xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
        # Читаем лист без пропуска строк, чтобы найти таблицу программно
        df_raw = pd.read_excel(xls, 'с 2017 г.')
        
        # Ищем строку, где начинаются годы (2017, 2018...)
        header_idx = None
        for i, row in df_raw.iterrows():
            row_str = row.astype(str).values
            if any('2017' in s for s in row_str):
                header_idx = i
                break
        
        if header_idx is None:
            st.error("Не удалось найти строку с годами в Excel-файле.")
            return None, None

        # Перечитываем файл с правильного заголовка
        df = pd.read_excel(xls, 'с 2017 г.', skiprows=header_idx + 1)
        # Названия колонок из строки заголовка
        cols = df_raw.iloc[header_idx].values
        # Очищаем названия колонок (года)
        clean_cols = []
        for c in cols:
            match = re.search(r'20\d{2}', str(c))
            clean_cols.append(match.group() if match else str(c).strip())
        df.columns = clean_cols
        
        # Очистка первой колонки (отрасли)
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        
        return df, inf_df[['Year', 'Inflation_Rate']].dropna()
    except Exception as e:
        st.error(f"Ошибка при обработке файлов: {e}")
        return None, None

df_salary, df_inf = load_and_clean_data()

if df_salary is not None:
    # Фильтруем список отраслей
    all_industries = sorted([
        str(x) for x in df_salary.iloc[:, 0].unique() 
        if pd.notnull(x) and len(str(x)) > 5 and not str(x).startswith(('1)', '2)', '3)'))
    ])
    
    selected = st.multiselect("Выберите отрасли:", options=all_industries, 
                              default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]])

    if selected:
        plot_data = []
        # Определяем доступные колонки-годы
        available_years = [c for c in df_salary.columns if re.match(r'20\d{2}', str(c))]
        
        for ind in selected:
            row = df_salary[df_salary.iloc[:, 0] == ind]
            if not row.empty:
                for yr in available_years:
                    val = row[yr].values[0]
                    # Очистка от спецсимволов (неразрывные пробелы, сноски)
                    if pd.notnull(val):
                        try:
                            s_val = str(val).split('(')[0] # Убираем сноски типа 50000(1)
                            clean_val = float(s_val.replace('\xa0', '').replace(' ', '').replace(',', '.'))
                            plot_data.append({'Year': int(yr), 'Salary': clean_val, 'Industry': ind})
                        except: continue

        if plot_data:
            final_df = pd.DataFrame(plot_data)
            final_df = pd.merge(final_df, df_inf, on='Year', how='left')
            final_df = final_df.sort_values(['Industry', 'Year'])
            
            # Расчеты
            final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
            final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
            final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

            # Визуализация
            st.subheader("Динамика зарплат и реальный рост")
            fig1, ax1 = plt.subplots(figsize=(10, 4))
            sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
            plt.title("Номинальная зарплата (руб.)")
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots(figsize=(10, 4))
            sns.barplot(data=final_df.dropna(subset=['Real_Growth']), x='Year', y='Real_Growth', hue='Industry')
            plt.axhline(0, color='red', linestyle='--')
            plt.title("Реальный рост зарплаты (с учетом инфляции), %")
            st.pyplot(fig2)
            
            with st.expander("Открыть таблицу данных"):
                st.dataframe(final_df)
        else:
            st.error("Числовые данные не найдены. Проверьте структуру Excel-файла.")
