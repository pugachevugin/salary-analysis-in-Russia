import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Pro Data Science Dashboard", layout="wide", initial_sidebar_state="expanded")

# 2. Кастомный CSS для «дорогого» вида
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #636efa;
    }
    h1 { color: #1e293b; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df_inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
        df_zpl_wide = pd.read_csv('tab3-zpl_2025_2.csv')
        # Очистка имен колонок от пробелов
        df_inf.columns = df_inf.columns.str.strip()
        df_zpl_wide.columns = df_zpl_wide.columns.str.strip()
        
        df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
        df_zpl['Year'] = df_zpl['Year'].astype(int)
        return pd.merge(df_zpl, df_inf, on='Year')
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=100)
    st.sidebar.title("Панель управления")
    
    industries = df['Industry'].unique()
    selected_industries = st.sidebar.multiselect(
        "🎯 Выберите отрасли для сравнения:", 
        industries, 
        default=[industries[0]] if len(industries) > 0 else []
    )
    
    st.sidebar.divider()
    st.sidebar.markdown("### 🛠️ Стек технологий")
    st.sidebar.code("Streamlit\nPlotly Express\nPandas")

    # --- HEADER ---
    st.title("🇷🇺 Аналитика доходов и инфляции")
    st.info("Интерактивный дашборд для визуализации реального благосостояния населения.")

    # Фильтрация
    filtered = df[df['Industry'].isin(selected_industries)].sort_values(['Industry', 'Year'])
    filtered['Nominal_Growth'] = filtered.groupby('Industry')['Salary'].pct_change() * 100
    filtered['Real_Growth'] = filtered['Nominal_Growth'] - filtered['Inflation']

    # --- METRICS SECTION ---
    if not filtered.empty:
        last_year_val = filtered['Year'].max()
        last_data = filtered[filtered['Year'] == last_year_val]
        
        st.subheader(f"📍 Показатели за {last_year_val} год")
        cols = st.columns(len(selected_industries))
        
        for i, ind in enumerate(selected_industries):
            row = last_data[last_data['Industry'] == ind]
            if not row.empty:
                val = row['Salary'].values[0]
                delta = row['Real_Growth'].values[0]
                with cols[i]:
                    st.metric(label=ind, value=f"{val:,.0f} ₽", delta=f"{delta:.2f}% (Реально)")

    # --- MAIN CHARTS ---
    tab1, tab2, tab3 = st.tabs(["📉 Тренд зарплат", "🌡️ Тепловая карта", "📊 Макро-корреляция"])

    with tab1:
        # Линейный график с заливкой (Area chart)
        fig_salary = px.area(
            filtered, x='Year', y='Salary', color='Industry',
            title="Эволюция зарплат по годам",
            line_group='Industry',
            template="plotly_white",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_salary.update_layout(hovermode="x unified")
        st.plotly_chart(fig_salary, use_container_width=True)

    with tab2:
        st.subheader("Плотность зарплат (Heatmap)")
        # Создаем матрицу для тепловой карты
        pivot_df = filtered.pivot(index="Industry", columns="Year", values="Salary")
        fig_heatmap = px.imshow(
            pivot_df, 
            labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
            color_continuous_scale='Viridis',
            aspect="auto"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.write("> **Что это дает:** Чем 'желтее' ячейка, тем выше доход в этой отрасли в конкретный год.")

    with tab3:
        # Комбинированный график (Линии + Столбцы)
        corr_data = filtered.drop_duplicates('Year')
        
        fig_corr = go.Figure()
        # Столбцы для ВВП
        fig_corr.add_trace(go.Bar(
            x=corr_data['Year'], y=corr_data['GDP_Growth'], 
            name="Рост ВВП %", marker_color='rgba(100, 150, 255, 0.6)'
        ))
        # Линия для безработицы
        fig_corr.add_trace(go.Scatter(
            x=corr_data['Year'], y=corr_data['Unemployment'], 
            name="Безработица %", line=dict(color='firebrick', width=4)
        ))
        
        fig_corr.update_layout(
            title="ВВП vs Безработица",
            xaxis_title="Год",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    # --- DATA EXPLORER ---
    st.divider()
    with st.expander("🔍 Исследовать сырые данные"):
        st.write("Вы можете сортировать и фильтровать таблицу прямо здесь:")
        st.dataframe(filtered.style.highlight_max(axis=0, subset=['Salary']), use_container_width=True)
