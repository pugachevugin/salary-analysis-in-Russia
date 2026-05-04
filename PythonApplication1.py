import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Ultimate Analytics 2026", layout="wide", initial_sidebar_state="expanded")

# Стилизация для "красоты"
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_style_error=True)

@st.cache_data
def load_data():
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    # Перевод в длинный формат
    zpl = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl['Год'] = zpl['Год'].astype(int)
    return pd.merge(zpl, inf, on='Год'), zpl_raw

df, df_wide = load_data()

# --- ИНТЕРФЕЙС ---
st.title("🚀 Аналитический дашборд: Экономика РФ 2000-2024")
st.sidebar.image("https://img.icons8.com/fluency/96/analytics.png")
st.sidebar.header("Параметры")

selected_inds = st.sidebar.multiselect(
    "Выберите отрасли:", df['Отрасль'].unique(), default=["ИТ и связь", "Средняя по РФ"]
)

# Фильтрация
res = df[df['Отрасль'].isin(selected_inds)].sort_values(['Отрасль', 'Год'])
res['Ном_Рост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
res['Реал_Рост'] = res['Ном_Рост'] - res['Инфляция']

# --- ВКЛАДКИ ---
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Тепловая карта", "📊 Тренды", "📉 Реальный рост", "📋 Таблицы"])

with tab1:
    st.subheader("Карта интенсивности зарплат по годам")
    # Подготовка данных для хитмапа
    heat_data = df_wide.set_index('Отрасль')
    fig_heat = px.imshow(
        heat_data,
        labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
        color_continuous_scale='Viridis',
        aspect="auto",
        text_auto=".0f" # Показывает цифры внутри ячеек
    )
    fig_heat.update_layout(height=500)
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Хитмап наглядно показывает 'взрывной' рост в ИТ и Финансах после 2015 года.")

with tab2:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Линейные тренды")
        fig_line = px.line(res, x='Год', y='Зарплата', color='Отрасль', markers=True,
                          line_shape="spline", render_mode="svg")
        st.plotly_chart(fig_line, use_container_width=True)
    with col2:
        st.subheader("Доли по отраслям (2024)")
        latest = df[df['Год'] == 2024]
        fig_pie = px.pie(latest, values='Зарплата', names='Отрасль', hole=0.4,
                        color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("Ежегодная гистограмма реального роста (Пункт 5)")
    fig_bar = px.bar(res.dropna(), x='Год', y='Реал_Рост', color='Отрасль',
                    barmode='group', title="Рост выше/ниже инфляции",
                    color_discrete_sequence=px.colors.qualitative.Bold)
    fig_bar.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.subheader("Сравнение инфляции и ключевой ставки")
    inf_data = df.drop_duplicates('Год')
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=inf_data['Год'], y=inf_data['Инфляция'], fill='tozeroy', name='Инфляция'))
    fig_area.add_trace(go.Scatter(x=inf_data['Год'], y=inf_data['Ключевая_ставка'], name='Ставка ЦБ'))
    st.plotly_chart(fig_area, use_container_width=True)

with tab4:
    st.subheader("Детальная аналитика по каждому году")
    st.dataframe(
        res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Рост', 'Статус_инфляции']]
        .style.format({'Зарплата': '{:,.0f} ₽', 'Реал_Рост': '{:+.2f}%'})
        .background_gradient(subset=['Реал_Рост'], cmap='RdYlGn'),
        use_container_width=True
    )
