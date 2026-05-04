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
        df_raw = pd.read_excel(xls, 'с 2017 г.', header=None)
        
        # Поиск строки-заголовка с годами (2017-2023)
        header_idx = None
        for i, row in df_raw.iterrows():
            if any('2017' in str(val) for val in row.values):
                header_idx = i
                break
        
        if header_idx is None: return None, None

        # Сопоставляем колонки и годы
        raw_headers = df_raw.iloc[header_idx].values
        years_map = {}
        for idx, h in enumerate(raw_headers):
            match = re.search(r'20\d{2}', str(h))
            if match:
                years_map[idx] = int(match.group())

        # Собираем данные построчно
        rows_list = []
        for i in range(header_idx + 1, len(df_raw)):
            current_row = df_raw.iloc[i]
            industry_raw = str(current_row[0]).strip()
            
            # ФИЛЬТР: Пропускаем сноски, пустые строки и слишком короткие названия
            if (len(industry_raw) < 10 or 
                industry_raw.startswith(('1)', '2)', '3)', '4)', '*)')) or 
                'данные' in industry_raw.lower() or 
                'обновлено' in industry_raw.lower()):
                continue

            for col_idx, yr in years_map.items():
                val = current_row[col_idx]
                if pd.notnull(val):
                    # Очистка числа от сносок и мусора
                    clean_str = "".join(re.findall(r'[0-9.,]', str(val).split('(')[0]))
                    if clean_str and clean_str not in ['.', ',']:
                        try:
                            num = float(clean_str.replace(',', '.'))
                            # Зарплата не может быть меньше 1000 рублей в этот период
                            if num > 1000:
                                rows_list.append({
                                    'Industry': industry_raw,
                                    'Year': yr,
                                    'Salary': num
                                })
                        except: continue
        
        if not rows_list: return None, None
            
        return pd.DataFrame(rows_list), inf_df[['Year', 'Inflation_Rate']].dropna()
    except Exception as e:
        st.error(f"Ошибка загрузки: {e}")
        return None, None

df_salary, df_inf = load_and_clean_data()

if df_salary is not None:
    # Очищенный список отраслей
    all_industries = sorted(df_salary['Industry'].unique())
    
    selected = st.multiselect(
        "Выберите отрасли для анализа:", 
        options=all_industries, 
        default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]]
    )

    if selected:
        final_df = df_salary[df_salary['Industry'].isin(selected)].copy()
        
        # Слияние с инфляцией
        final_df['Year'] = final_df['Year'].astype(int)
        df_inf['Year'] = df_inf['Year'].astype(int)
        final_df = pd.merge(final_df, df_inf, on='Year', how='left')
        
        # Расчет динамики
        final_df = final_df.sort_values(['Industry', 'Year'])
        final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
        final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
        final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

        if not final_df.empty:
            st.subheader("Визуализация динамики")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Номинальная зарплата (руб.)**")
                fig1, ax1 = plt.subplots(figsize=(8, 5))
                sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
                plt.grid(True, alpha=0.2)
                st.pyplot(fig1)

            with col2:
                st.markdown("**Реальный рост (за вычетом инфляции), %**")
                fig2, ax2 = plt.subplots(figsize=(8, 5))
                # Рисуем только если есть данные для сравнения (со 2-го года)
                plot_growth = final_df.dropna(subset=['Real_Growth'])
                if not plot_growth.empty:
                    sns.barplot(data=plot_growth, x='Year', y='Real_Growth', hue='Industry')
                    plt.axhline(0, color='red', lw=1.5, ls='--')
                st.pyplot(fig2)
            
            st.divider()
            with st.expander("Открыть таблицу показателей"):
                st.dataframe(final_df)
    else:
        st.info("Пожалуйста, выберите хотя бы одну отрасль в списке выше.")
else:
    st.error("Данные не найдены. Проверьте, что файлы загружены в репозиторий GitHub.")
