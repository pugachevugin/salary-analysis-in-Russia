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
        # 1. Инфляция
        inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
        inf_df.columns = [str(c).strip() for c in inf_df.columns]
        if 'Год' in inf_df.columns: inf_df = inf_df.rename(columns={'Год': 'Year'})
        if 'Всего' in inf_df.columns: inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
        inf_df['Year'] = pd.to_numeric(inf_df['Year'], errors='coerce')
        
        # 2. Зарплаты
        xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
        df_raw = pd.read_excel(xls, 'с 2017 г.', header=None)
        
        # Поиск строки-заголовка
        header_idx = None
        for i, row in df_raw.iterrows():
            if any('2017' in str(val) for val in row.values):
                header_idx = i
                break
        
        if header_idx is None: return None, None

        # Собираем заголовки (годы)
        raw_headers = df_raw.iloc[header_idx].values
        years_map = {}
        for idx, h in enumerate(raw_headers):
            match = re.search(r'20\d{2}', str(h))
            if match:
                years_map[idx] = match.group()

        # Собираем данные, пропуская пустые строки ПОСЛЕ заголовка
        rows_list = []
        for i in range(header_idx + 1, len(df_raw)):
            current_row = df_raw.iloc[i]
            industry_name = str(current_row[0]).strip()
            
            # Если в строке есть хоть одно числовое значение в колонках лет
            has_data = False
            for col_idx, yr in years_map.items():
                val = current_row[col_idx]
                # Очистка и проверка на число
                clean_str = "".join(re.findall(r'[0-9.,]', str(val).split('(')[0]))
                if clean_str and clean_str not in ['.', ',']:
                    try:
                        num = float(clean_str.replace(',', '.'))
                        rows_list.append({
                            'Industry': industry_name,
                            'Year': int(yr),
                            'Salary': num
                        })
                        has_data = True
                    except: continue
        
        if not rows_list: return None, None
            
        return pd.DataFrame(rows_list), inf_df[['Year', 'Inflation_Rate']].dropna()
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        return None, None

df_salary, df_inf = load_and_clean_data()

if df_salary is not None:
    # Чистим список отраслей от пустых и технических
    all_industries = sorted([
        x for x in df_salary['Industry'].unique() 
        if len(x) > 5 and not x.startswith(('1)', '2)', 'nan', 'Unnamed'))
    ])
    
    selected = st.multiselect("Выберите отрасли:", options=all_industries, 
                              default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]])

    if selected:
        # Фильтруем данные по выбранным отраслям
        final_df = df_salary[df_salary['Industry'].isin(selected)].copy()
        
        # Объединяем с инфляцией
        final_df['Year'] = final_df['Year'].astype(int)
        df_inf['Year'] = df_inf['Year'].astype(int)
        final_df = pd.merge(final_df, df_inf, on='Year', how='left')
        
        # Расчеты
        final_df = final_df.sort_values(['Industry', 'Year'])
        final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
        final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
        final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

        if not final_df.dropna(subset=['Salary']).empty:
            st.subheader("Визуализация динамики")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Зарплата (руб.)**")
                fig1, ax1 = plt.subplots()
                sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
                plt.grid(True, alpha=0.2); st.pyplot(fig1)

            with col2:
                st.markdown("**Реальный рост, %**")
                fig2, ax2 = plt.subplots()
                sns.barplot(data=final_df.dropna(subset=['Real_Growth']), x='Year', y='Real_Growth', hue='Industry')
                plt.axhline(0, color='red', lw=1); st.pyplot(fig2)
            
            st.divider()
            with st.expander("Таблица показателей"):
                st.dataframe(final_df)
        else:
            st.warning("Нет числовых данных для отображения графиков.")
else:
    st.error("Файлы не найдены или имеют неверную структуру.")
