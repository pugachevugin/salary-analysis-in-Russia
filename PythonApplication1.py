import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Аналитический сервис 09.03.03", layout="wide")

@st.cache_data
def load_and_clean_data():
    try:
        # Читаем инфляцию
        df_inf = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
        # Читаем зарплаты
        df_zpl_raw = pd.read_excel('tab3-zpl_2025.xlsx')
        
        # ОЧИСТКА: Удаляем пустые строки и столбцы, если они есть
        df_inf = df_inf.dropna(how='all').dropna(axis=1, how='all')
        df_zpl_raw = df_zpl_raw.dropna(how='all')
        
        # Убираем пробелы в названиях колонок
        df_inf.columns = df_inf.columns.str.strip()
        df_zpl_raw.columns = df_zpl_raw.columns.str.strip()
        
        # ПРЕОБРАЗОВАНИЕ ЗАРПЛАТ (из широкой в длинную таблицу)
        # Предполагаем, что первая колонка - 'Industry', остальные - годы
        id_col = df_zpl_raw.columns[0] 
        df_zpl = df_zpl_raw.melt(id_vars=[id_col], var_name='Year', value_name='Salary')
        df_zpl.columns = ['Industry', 'Year', 'Salary'] # Унифицируем названия
        
        # Приведение типов (важно для корректных расчетов)
        df_zpl['Year'] = pd.to_numeric(df_zpl['Year'], errors='coerce')
        df_zpl['Salary'] = pd.to_numeric(df_zpl['Salary'], errors='coerce')
        df_inf['Year'] = pd.to_numeric(df_inf['Year'], errors='coerce')
        df_inf['Inflation'] = pd.to_numeric(df_inf['Inflation'], errors='coerce')
        
        # Объединяем по году
        full_data = pd.merge(df_zpl, df_inf, on='Year', how='inner')
        return full_data.dropna(subset=['Salary', 'Inflation']) # Оставляем только полные данные
        
    except Exception as e:
        st.error(f"Ошибка при обработке таблиц: {e}")
        return None

df = load_and_clean_data()

if df is not None:
    # --- SIDEBAR: Выбор отраслей (Пункт 3 задания) ---
    st.sidebar.header("⚙️ Параметры")
    all_inds = sorted(df['Industry'].unique())
    selected_inds = st.sidebar.multiselect(
        "Выберите отрасли для анализа:", 
        all_inds, 
        default=all_inds[:3] if len(all_inds) > 2 else all_inds
    )

    if not selected_inds:
        st.warning("Пожалуйста, выберите хотя бы одну отрасль в меню слева.")
    else:
        # --- ОБРАБОТКА (Пункт 4: Пересчет с учетом инфляции) ---
        analysis_df = df[df['Industry'].isin(selected_inds)].sort_values(['Industry', 'Year'])
        
        # Расчет темпов роста
        analysis_df['Nominal_Pct'] = analysis_df.groupby('Industry')['Salary'].pct_change() * 100
        # Реальный рост = Номинальный рост - Инфляция
        analysis_df['Real_Growth'] = analysis_df['Nominal_Pct'] - analysis_df['Inflation']
        
        # Расчет реальной зарплаты в ценах первого года (базисный индекс)
        # Это позволяет увидеть "покупательную способность" физически
        first_year = analysis_df['Year'].min()
        analysis_df['Real_Salary_Value'] = analysis_df['Salary'] / (1 + analysis_df['Inflation'] / 100)

        # --- ВИЗУАЛИЗАЦИЯ (Пункт 2 и 5) ---
        st.title("🚀 Дашборд социально-экономических показателей")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📊 Динамика реального роста")
            # Группированная гистограмма (Пункт 5)
            fig_bar = px.bar(
                analysis_df.dropna(), 
                x='Year', y='Real_Growth', color='Industry',
                barmode='group',
                title="Превышение роста зарплат над инфляцией (в %)",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bar.add_hline(y=0, line_color="black", line_width=2)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("💡 Выводы")
            for ind in selected_inds:
                ind_data = analysis_df[analysis_df['Industry'] == ind]
                avg_real = ind_data['Real_Growth'].mean()
                state = "выше" if avg_real > 0 else "ниже"
                st.write(f"**{ind}:**")
                st.caption(f"Средний реальный прирост составил {avg_real:.2f}%. Это означает, что доходы росли {state} темпов инфляции.")

        # --- ТАБЛИЦА (Пункт 4: Сравнение) ---
        st.divider()
        st.subheader("📋 Сводная аналитическая таблица")
        st.markdown("Здесь представлен полный пересчет средних зарплат с учетом инфляции:")
        
        # Форматируем таблицу для красоты
        styled_df = analysis_df[['Industry', 'Year', 'Salary', 'Inflation', 'Real_Growth']].copy()
        styled_df.columns = ['Отрасль', 'Год', 'Зарплата (руб)', 'Инфляция (%)', 'Реальный рост (%)']
        
        st.dataframe(
            styled_df.style.format({'Зарплата (руб)': '{:,.0f}', 'Инфляция (%)': '{:.2f}', 'Реальный рост (%)': '{:+.2f}'})
            .background_gradient(subset=['Реальный рост (%)'], cmap='RdYlGn'),
            use_container_width=True
        )

        # Дополнительная визуализация: Тренд номинальных зарплат (Пункт 3)
        with st.expander("Посмотреть графики изменения номинальных зарплат"):
            fig_line = px.line(analysis_df, x='Year', y='Salary', color='Industry', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
