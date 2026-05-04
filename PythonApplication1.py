import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Аналитика зарплат и инфляции", layout="wide")

# --- ЗАГРУЗКА ДАННЫХ ИЗ CSV ---
@st.cache_data
def load_data():
    try:
        # Считываем файлы
        df_inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
        df_zpl_wide = pd.read_csv('tab3-zpl_2025_2.csv')
        
        # Преобразуем широкую таблицу зарплат в длинный формат (Tidy Data)
        # Это необходимо для удобного построения графиков в Plotly
        df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
        
        # Приводим типы данных к числовым для корректных расчетов
        df_zpl['Year'] = df_zpl['Year'].astype(int)
        df_inf['Year'] = df_inf['Year'].astype(int)
        
        # Объединяем данные по году
        full_df = pd.merge(df_zpl, df_inf, on='Year')
        return full_df
    except Exception as e:
        st.error(f"Ошибка при загрузке файлов: {e}")
        return None

df = load_data()

if df is not None:
    # --- ИНТЕРФЕЙС ---
    st.title("📊 Экономический анализ: Зарплаты vs Инфляция")
    st.markdown("Визуализация данных на основе внешних CSV-отчетов.")

    # SIDEBAR: Динамические фильтры
    st.sidebar.header("🔍 Настройки")
    all_industries = sorted(df['Industry'].unique())
    selected_inds = st.sidebar.multiselect(
        "Выберите отрасли для сравнения:", 
        all_industries, 
        default=all_industries[:2] if len(all_industries) > 1 else all_industries
    )

    # --- РАСЧЕТЫ (Пункт 4 задания) ---
    res = df[df['Industry'].isin(selected_inds)].sort_values(['Industry', 'Year'])
    
    # Считаем номинальный рост (в %)
    res['Nominal_Growth'] = res.groupby('Industry')['Salary'].pct_change() * 100
    
    # Считаем реальный рост (с учетом инфляции)
    res['Real_Growth'] = res['Nominal_Growth'] - res['Inflation']

    # --- ВИЗУАЛИЗАЦИИ ---
    tab1, tab2, tab3 = st.tabs(["🔥 Тепловая карта", "📉 Тренды", "📝 Таблицы и выводы"])

    with tab1:
        st.subheader("Хитмап: Уровень зарплат по отраслям")
        # Для хитмапа используем исходные данные (все отрасли)
        pivot_df = df.pivot(index="Industry", columns="Year", values="Salary")
        fig_heat = px.imshow(
            pivot_df,
            labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
            color_continuous_scale='Viridis',
            aspect="auto"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Реальный рост (%)")
            if not res.empty:
                fig_real = px.bar(
                    res.dropna(), x='Year', y='Real_Growth', color='Industry',
                    barmode='group', title="Прирост сверх инфляции"
                )
                fig_real.add_hline(y=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig_real, use_container_width=True)
        
        with col2:
            st.subheader("Динамика номинальных зарплат")
            fig_line = px.line(res, x='Year', y='Salary', color='Industry', markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

    with tab3:
        st.subheader("Сводные данные")
        # Форматирование для удобства чтения
        st.dataframe(
            res[['Industry', 'Year', 'Salary', 'Inflation', 'Real_Growth']]
            .style.format({'Salary': '{:,.0f}', 'Real_Growth': '{:+.2f}%'})
            .background_gradient(subset=['Real_Growth'], cmap='RdYlGn'),
            use_container_width=True
        )
        
        st.divider()
        st.markdown("### 📌 Аналитический отчет:")
        if not res.empty:
            for ind in selected_inds:
                ind_data = res[res['Industry'] == ind]
                avg_real = ind_data['Real_Growth'].mean()
                
                # Формируем вывод на основе данных
                status = "опережает инфляцию" if avg_real > 0 else "отстает от инфляции"
                st.write(f"- В отрасли **{ind}** средний реальный рост за период составил **{avg_real:.2f}%**. "
                         f"Это указывает на то, что доход в этом секторе в среднем **{status}**.")
