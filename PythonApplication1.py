import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Настройка стиля
st.set_page_config(page_title="Data Science Dashboard", layout="wide")

# Кастомный CSS для красоты
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    df_inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    df_zpl_wide = pd.read_csv('tab3-zpl_2025_2.csv')
    df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
    df_zpl['Year'] = df_zpl['Year'].astype(int)
    return pd.merge(df_zpl, df_inf, on='Year')

try:
    df = load_data()
    
    # --- SIDEBAR ---
    st.sidebar.header("⚙️ Настройки анализа")
    industries = df['Industry'].unique()
    selected_industries = st.sidebar.multiselect("Выберите отрасли:", industries, default=[industries[0], industries[1]])
    
    st.sidebar.divider()
    st.sidebar.write("👤 **Автор:** Студент 09.03.03")
    st.sidebar.info("Данные: Росстат и открытые источники")

    # --- HEADER ---
    st.title("📈 Анализ экономики и зарплат в РФ")
    st.markdown("Сравнение номинальных доходов, инфляции и макроэкономических показателей.")

    # --- METRICS ---
    filtered = df[df['Industry'].isin(selected_industries)].sort_values(['Industry', 'Year'])
    filtered['Nominal_Growth'] = filtered.groupby('Industry')['Salary'].pct_change() * 100
    filtered['Real_Growth'] = filtered['Nominal_Growth'] - filtered['Inflation']

    last_year = filtered[filtered['Year'] == filtered['Year'].max()]
    
    cols = st.columns(len(selected_industries))
    for i, ind in enumerate(selected_industries):
        val = last_year[last_year['Industry'] == ind]['Salary'].values[0]
        growth = last_year[last_year['Industry'] == ind]['Real_Growth'].values[0]
        cols[i].metric(label=f"ЗП: {ind}", value=f"{val:,.0f} ₽", delta=f"{growth:.1f}% (реальный рост)")

    # --- CHARTS ---
    tab1, tab2, tab3 = st.tabs(["📊 Динамика зарплат", "🧬 Инфляция и Реальный рост", "🔍 Корреляция"])

    with tab1:
        fig_salary = px.line(filtered, x='Year', y='Salary', color='Industry', 
                             markers=True, title="Динамика номинальной зарплаты (2017-2023)",
                             template="plotly_white")
        st.plotly_chart(fig_salary, use_container_width=True)

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_inf = px.area(filtered.drop_duplicates('Year'), x='Year', y='Inflation', 
                              title="Уровень инфляции в РФ (%)", color_discrete_sequence=['#ff4b4b'])
            st.plotly_chart(fig_inf, use_container_width=True)
        with col_b:
            fig_real = px.bar(filtered.dropna(), x='Year', y='Real_Growth', color='Industry', barmode='group',
                              title="Реальное изменение доходов (за вычетом инфляции)")
            st.plotly_chart(fig_real, use_container_width=True)

    with tab3:
        st.subheader("Взаимосвязь с ВВП и Безработицей")
        corr_data = filtered.drop_duplicates('Year')
        
        fig_corr = go.Figure()
        fig_corr.add_trace(go.Scatter(x=corr_data['Year'], y=corr_data['GDP_Growth'], name="Рост ВВП %", line=dict(dash='dash')))
        fig_corr.add_trace(go.Scatter(x=corr_data['Year'], y=corr_data['Unemployment'], name="Безработица %"))
        fig_corr.update_layout(title="Макроэкономические тренды", template="plotly_white")
        st.plotly_chart(fig_corr, use_container_width=True)
        
        st.write("**Вывод:** На графике видно, как падение ВВП в 2020-2022 годах коррелирует с замедлением реального роста зарплат.")

    # --- DATA VIEW ---
    with st.expander("📂 Посмотреть детальную таблицу"):
        st.dataframe(filtered, use_container_width=True)

except Exception as e:
    st.error(f"Ошибка: {e}")
