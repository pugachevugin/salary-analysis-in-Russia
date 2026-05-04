import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# 1. Настройка интерфейса
st.set_page_config(page_title="Анализ зарплат РФ", layout="wide")
st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_and_clean_data():
    try:
        # Загрузка инфляции
        inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
        inf_df.columns = [str(c).strip() for c in inf_df.columns]
        if 'Год' in inf_df.columns: inf_df = inf_df.rename(columns={'Год': 'Year'})
        if 'Всего' in inf_df.columns: inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
        inf_df['Year'] = pd.to_numeric(inf_df['Year'], errors='coerce')
        
        # Загрузка зарплат
        xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
        df_raw = pd.read_excel(xls, 'с 2017 г.')
        
        # Поиск строки-заголовка с годами
        header_idx = None
        for i, row in df_raw.iterrows():
            row_str = [str(val) if pd.notnull(val) else "" for val in row.values]
            if any('2017' in s for s in row_str):
                header_idx = i
                break
        
        if header_idx is None:
            return None, None

        # Читаем данные и настраиваем колонки
        df = pd.read_excel(xls, 'с 2017 г.', skiprows=header_idx + 1)
        raw_headers = df_raw.iloc[header_idx].values
        clean_cols = []
        for c in raw_headers:
            match = re.search(r'20\d{2}', str(c))
            clean_cols.append(match.group() if match else str(c).strip())
        df.columns = clean_cols
        
        # Очистка названий отраслей
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        
        return df, inf_df[['Year', 'Inflation_Rate']].dropna()
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        return None, None

df_salary, df_inf = load_and_clean_data()

if df_salary is not None:
    # Отрасли для выбора
    all_industries = sorted([
        str(x) for x in df_salary.iloc[:, 0].unique() 
        if pd.notnull(x) and len(str(x)) > 5 and not str(x).startswith(('1)', '2)', '3)'))
    ])
    
    selected = st.multiselect("Выберите отрасли:", options=all_industries, 
                              default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]])

    if selected:
        plot_data = []
        available_years = [c for c in df_salary.columns if re.match(r'20\d{2}', str(c))]
        
        for ind in selected:
            row = df_salary[df_salary.iloc[:, 0] == ind]
            if not row.empty:
                for yr in available_years:
                    val = row[yr].values[0]
                    if pd.notnull(val):
                        # УЛЬТРА-ОЧИСТКА: оставляем только цифры, точки и запятые
                        s_val = str(val).split('(')[0] # Отрезаем сноски
                        # Оставляем только то, что похоже на число
                        clean_str = "".join(re.findall(r'[0-9.,]', s_val))
                        if clean_str:
                            try:
                                num_val = float(clean_str.replace(',', '.'))
                                plot_data.append({'Year': int(yr), 'Salary': num_val, 'Industry': ind})
                            except: continue

        if plot_data:
            final_df = pd.DataFrame(plot_data)
            final_df['Year'] = final_df['Year'].astype(int)
            df_inf['Year'] = df_inf['Year'].astype(int)
            
            final_df = pd.merge(final_df, df_inf, on='Year', how='left')
            final_df = final_df.sort_values(['Industry', 'Year'])
            
            # Расчеты роста
            final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
            final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
            final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

            # Графики
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Номинальная зарплата, руб.**")
                fig1, ax1 = plt.subplots()
                sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
                plt.grid(True, alpha=0.2); st.pyplot(fig1)

            with col2:
                st.markdown("**Реальный рост (с учетом инфляции), %**")
                fig2, ax2 = plt.subplots()
                sns.barplot(data=final_df.dropna(subset=['Real_Growth']), x='Year', y='Real_Growth', hue='Industry')
                plt.axhline(0, color='red', lw=1); st.pyplot(fig2)
            
            st.divider()
            st.dataframe(final_df)
        else:
            st.error("Числовые данные не найдены. Попробуйте выбрать 'Всего по экономике'.")
