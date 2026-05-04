import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os

# 1. Настройка страницы
st.set_page_config(page_title="Анализ зарплат РФ", layout="wide")
st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_and_clean_data():
    try:
        # Диагностика: проверяем, что файлы вообще есть в папке
        files_in_dir = os.listdir('.')
        salary_file = 'tab3-zpl_2025.xlsx'
        inflation_file = 'Statistic_Inflatio_Russia.xlsx'

        if salary_file not in files_in_dir or inflation_file not in files_in_dir:
            st.error(f"Критическая ошибка: Файлы не найдены в корневой папке!")
            st.info(f"Доступные файлы в репозитории: {files_in_dir}")
            return None, None

        # --- ЗАГРУЗКА ИНФЛЯЦИИ ---
        inf_df = pd.read_excel(inflation_file)
        inf_df.columns = [str(c).strip() for c in inf_df.columns]
        # Приводим названия колонок к стандарту
        if 'Год' in inf_df.columns: inf_df = inf_df.rename(columns={'Год': 'Year'})
        if 'Всего' in inf_df.columns: inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
        inf_df['Year'] = pd.to_numeric(inf_df['Year'], errors='coerce')
        
        # --- ЗАГРУЗКА ЗАРПЛАТ ---
        xls = pd.ExcelFile(salary_file)
        # Работаем с листом 'с 2017 г.' (проверьте название в Excel!)
        sheet_name = 'с 2017 г.' if 'с 2017 г.' in xls.sheet_names else xls.sheet_names[0]
        df_raw = pd.read_excel(xls, sheet_name, header=None)
        
        # Ищем строку, где начинаются годы (2017)
        header_idx = None
        for i, row in df_raw.iterrows():
            if any('2017' in str(val) for val in row.values):
                header_idx = i
                break
        
        if header_idx is None:
            st.error("Не удалось найти строку с заголовками (2017) в файле зарплат.")
            return None, None

        # Сопоставляем индексы колонок с годами
        raw_headers = df_raw.iloc[header_idx].values
        years_map = {}
        for idx, h in enumerate(raw_headers):
            match = re.search(r'20\d{2}', str(h))
            if match:
                years_map[idx] = int(match.group())

        # Собираем данные построчно, фильтруя мусор
        rows_list = []
        for i in range(header_idx + 1, len(df_raw)):
            current_row = df_raw.iloc[i]
            industry_raw = str(current_row[0]).strip()
            
            # Фильтр технических строк и сносок
            if (len(industry_raw) < 10 or 
                industry_raw.startswith(('1)', '2)', '3)', '4)', '*)')) or 
                'данные' in industry_raw.lower() or 
                'обновлено' in industry_raw.lower()):
                continue

            for col_idx, yr in years_map.items():
                val = current_row[col_idx]
                if pd.notnull(val):
                    # Чистим строку от сносок в скобках и лишних символов
                    clean_str = "".join(re.findall(r'[0-9.,]', str(val).split('(')[0]))
                    if clean_str and clean_str not in ['.', ',']:
                        try:
                            num = float(clean_str.replace(',', '.'))
                            # Отсекаем аномально низкие значения (индексы сносок)
                            if num > 1000:
                                rows_list.append({
                                    'Industry': industry_raw,
                                    'Year': yr,
                                    'Salary': num
                                })
                        except: continue
        
        if not rows_list:
            st.warning("Числовые данные не извлечены. Проверьте формат ячеек.")
            return None, None
            
        return pd.DataFrame(rows_list), inf_df[['Year', 'Inflation_Rate']].dropna()

    except Exception as e:
        st.error(f"Ошибка при обработке данных: {e}")
        return None, None

# 2. Выполнение загрузки
df_salary, df_inf = load_and_clean_data()

# 3. Интерфейс и логика приложения
if df_salary is not None:
    all_industries = sorted(df_salary['Industry'].unique())
    
    # Селектор отраслей
    selected = st.multiselect(
        "Выберите отрасли для анализа:", 
        options=all_industries, 
        default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]]
    )

    if selected:
        final_df = df_salary[df_salary['Industry'].isin(selected)].copy()
        
        # Объединение с инфляцией
        final_df['Year'] = final_df['Year'].astype(int)
        df_inf['Year'] = df_inf['Year'].astype(int)
        final_df = pd.merge(final_df, df_inf, on='Year', how='left')
        
        # Расчет показателей роста
        final_df = final_df.sort_values(['Industry', 'Year'])
        final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
        final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
        final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

        # Визуализация
        st.subheader("Визуализация динамики")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Номинальная зарплата (руб.)**")
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o', linewidth=2.5)
            plt.grid(True, alpha=0.3)
            st.pyplot(fig1)

        with col2:
            st.markdown("**Реальный рост (за вычетами инфляции), %**")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            plot_growth = final_df.dropna(subset=['Real_Growth'])
            if not plot_growth.empty:
                sns.barplot(data=plot_growth, x='Year', y='Real_Growth', hue='Industry')
                plt.axhline(0, color='red', linestyle='--', linewidth=1)
            st.pyplot(fig2)
        
        st.divider()
        with st.expander("📊 Посмотреть итоговую таблицу данных"):
            st.dataframe(final_df.style.format(precision=2), use_container_width=True)
    else:
        st.info("Выберите хотя бы одну отрасль для отображения графиков.")
