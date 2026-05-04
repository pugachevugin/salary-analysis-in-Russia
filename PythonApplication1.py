import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Настройка страницы
st.set_page_config(page_title="Анализ зарплат РФ", layout="wide")
st.title("📊 Анализ зарплат в России (2017-2023)")

@st.cache_data
def load_simple_data():
    # 1. Загрузка данных об инфляции
    try:
        inf_df = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
        inf_df.columns = [str(c).strip() for c in inf_df.columns]
        # Приведение названий колонок к единому стандарту
        if 'Год' in inf_df.columns:
            inf_df = inf_df.rename(columns={'Год': 'Year'})
        if 'Всего' in inf_df.columns:
            inf_df = inf_df.rename(columns={'Всего': 'Inflation_Rate'})
    except Exception as e:
        st.error(f"Ошибка загрузки инфляции: {e}")
        return None, None

    # 2. Загрузка данных о зарплатах
    try:
        xls = pd.ExcelFile('tab3-zpl_2025.xlsx')
        # Работаем с актуальным листом (с 2017 г.)
        df = pd.read_excel(xls, 'с 2017 г.', skiprows=2)
        
        # Очистка заголовков: оставляем только те, где есть 4 цифры года
        new_cols = []
        for col in df.columns:
            year_match = re.search(r'20\d{2}', str(col))
            new_cols.append(year_match.group() if year_match else str(col).strip())
        df.columns = new_cols
        
        # Предварительная очистка названий отраслей
        df.iloc[:, 0] = df.iloc[:, 0].astype(str).str.strip()
        
        return df, inf_df[['Year', 'Inflation_Rate']]
    except Exception as e:
        st.error(f"Ошибка загрузки зарплат: {e}")
        return None, None

try:
    df_salary, df_inf = load_simple_data()

    if df_salary is not None:
        # Формируем чистый список отраслей для выбора
        all_industries = sorted([
            str(x).strip() for x in df_salary.iloc[:, 0].unique() 
            if pd.notnull(x) 
            and len(str(x).strip()) > 5 
            and not str(x).strip().startswith('1)') 
            and 'Unnamed' not in str(x)
        ])
        
        selected = st.multiselect(
            "Выберите отрасли для анализа:",
            options=all_industries,
            default=["Всего по экономике"] if "Всего по экономике" in all_industries else [all_industries[0]]
        )

        if selected:
            plot_data = []
            for ind in selected:
                # Находим строку по выбранной отрасли
                row = df_salary[df_salary.iloc[:, 0].astype(str).str.strip() == ind]
                
                # Ищем колонки-годы (2017-2023)
                years = [col for col in df_salary.columns if re.match(r'20\d{2}', str(col))]
                
                for yr in years:
                    if not row.empty:
                        val = row[yr].values[0]
                        try:
                            # Очистка числа от мусора: неразрывные пробелы, запятые вместо точек
                            clean_val = str(val).replace('\xa0', '').replace(' ', '').replace(',', '.')
                            plot_data.append({
                                'Year': int(yr),
                                'Salary': float(clean_val),
                                'Industry': ind
                            })
                        except (ValueError, TypeError):
                            # Если в ячейке текст (сноска), просто идем дальше
                            continue 
            
            if plot_data:
                final_df = pd.DataFrame(plot_data)
                
                # Объединяем с данными об инфляции
                df_inf['Year'] = df_inf['Year'].astype(int)
                final_df = pd.merge(final_df, df_inf, on='Year', how='left')

                # Сортировка для корректных графиков
                final_df = final_df.sort_values(['Industry', 'Year'])
                
                # Расчет роста (сравнение с предыдущим годом)
                final_df['Prev_Salary'] = final_df.groupby('Industry')['Salary'].shift(1)
                final_df['Nominal_Growth'] = (final_df['Salary'] / final_df['Prev_Salary'] - 1) * 100
                final_df['Real_Growth'] = final_df['Nominal_Growth'] - final_df['Inflation_Rate']

                # Отрисовка
                tab1, tab2 = st.tabs(["📊 Визуализация", "📋 Данные"])
                
                with tab1:
                    st.subheader("Динамика номинальных зарплат (руб.)")
                    fig1, ax1 = plt.subplots(figsize=(10, 5))
                    sns.lineplot(data=final_df, x='Year', y='Salary', hue='Industry', marker='o')
                    plt.grid(True, alpha=0.2)
                    st.pyplot(fig1)

                    st.subheader("Реальный годовой прирост (за вычетом инфляции), %")
                    fig2, ax2 = plt.subplots(figsize=(10, 5))
                    # Убираем NaN для корректного отображения барплота
                    sns.barplot(data=final_df.dropna(subset=['Real_Growth']), x='Year', y='Real_Growth', hue='Industry')
                    plt.axhline(0, color='red', lw=1.5, ls='--')
                    plt.ylabel("Процент роста")
                    st.pyplot(fig2)
                
                with tab2:
                    st.write("Итоговая таблица показателей:")
                    st.dataframe(final_df)
            else:
                st.warning("В выбранных строках не найдено числовых данных. Попробуйте выбрать другие отрасли.")
    else:
        st.error("Не удалось инициализировать данные. Проверьте наличие файлов в репозитории.")

except Exception as e:
    st.error(f"Произошла непредвиденная ошибка: {e}")
