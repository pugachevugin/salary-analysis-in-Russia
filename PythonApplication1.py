import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os

st.set_page_config(page_title="Анализ зарплат РФ", layout="wide")
st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_and_clean_data():
    try:
        files_in_dir = os.listdir('.')
        salary_file = 'tab3-zpl_2025.xlsx'
        inflation_file = 'Statistic_Inflatio_Russia.xlsx'

        if salary_file not in files_in_dir or inflation_file not in files_in_dir:
            st.error(f"Файлы не найдены: {files_in_dir}")
            return None, None

        # 1. Инфляция
        inf_df = pd.read_excel(inflation_file)
        inf_df.columns = [str(c).strip() for c in inf_df.columns]
        inf_df = inf_df.rename(columns={'Год': 'Year', 'Всего': 'Inflation_Rate'})
        inf_df['Year'] = pd.to_numeric(inf_df['Year'], errors='coerce')
        
        # 2. Зарплаты
        xls = pd.ExcelFile(salary_file)
        sheet_name = 'с 2017 г.' if 'с 2017 г.' in xls.sheet_names else xls.sheet_names[0]
        # Читаем всё как строки, чтобы не потерять данные из-за неверного авто-определения типов
        df_raw = pd.read_excel(xls, sheet_name, header=None, dtype=str)
        
        header_idx = None
        for i, row in df_raw.iterrows():
            if any('2017' in str(val) for val in row.values):
                header_idx = i
                break
        
        if header_idx is None: return None, None

        raw_headers = df_raw.iloc[header_idx].values
        years_map = {idx: int(re.search(r'20\d{2}', str(h)).group()) 
                     for idx, h in enumerate(raw_headers) if re.search(r'20\d{2}', str(h))}

        rows_list = []
        for i in range(header_idx + 1, len(df_raw)):
            current_row = df_raw.iloc[i]
            industry_raw = str(current_row[0]).strip()
            
            # Фильтр технических строк
            if len(industry_raw) < 5 or industry_raw.startswith(('1)', '2)', '3)', '4)', '*)')):
                continue

            for col_idx, yr in years_map.items():
                val = str(current_row[col_idx])
                
                # Удаляем ВСЕ нецифровые символы, кроме точки и запятой
                # Включая неразрывные пробелы (\xa0) и обычные пробелы
                clean_val = re.sub(r'[^\d.,]', '', val.split('(')[0].replace('\xa0', ''))
                
                if clean_val:
                    try:
                        # Заменяем запятую на точку для float
                        num = float(clean_val.replace(',', '.'))
                        # Если число похоже на зарплату (больше 100), сохраняем
                        if num > 100: 
                            rows_list.append({'Industry': industry_raw, 'Year': yr, 'Salary': num})
                    except ValueError:
                        continue
        
        if not rows_list:
            # Если данных нет, выведем кусочек таблицы для диагностики
            st.warning("Диагностика: Данные в первой строке после заголовка:")
            st.code(df_raw.iloc[header_idx + 1].to_dict())
            return None, None
            
        return pd.DataFrame(rows_list), inf_df[['Year', 'Inflation_Rate']].dropna()

    except Exception as e:
        st.error(f"Ошибка: {e}")
        return None, None

# Запуск
df_salary, df_inf = load_and_clean_data()

if df_salary is not None:
    all_industries = sorted(df_salary['Industry'].unique())
    selected = st.multiselect("Отрасли:", options=all_industries, 
                              default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]])

    if selected:
        final_df = df_salary[df_salary['Industry'].isin(selected)].copy()
        final_df['Year'] = final_df['Year'].astype(int)
        df_inf['Year'] = df_inf['Year'].astype(int)
        
        res = pd.merge(final_df, df_inf, on='Year', how='left').sort_values(['Industry', 'Year'])
        res['Nominal_Growth'] = (res.groupby('Industry')['Salary'].pct_change()) * 100
        res['Real_Growth'] = res['Nominal_Growth'] - res['Inflation_Rate']

        st.subheader("Анализ")
        col1, col2 = st.columns(2)
        with col1:
            fig1, ax1 = plt.subplots()
            sns.lineplot(data=res, x='Year', y='Salary', hue='Industry', marker='o')
            st.pyplot(fig1)
        with col2:
            fig2, ax2 = plt.subplots()
            sns.barplot(data=res.dropna(), x='Year', y='Real_Growth', hue='Industry')
            plt.axhline(0, color='black', lw=1)
            st.pyplot(fig2)
        st.dataframe(res)
