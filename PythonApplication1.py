import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Advanced Analytics Dashboard", layout="wide")

# Кастомный CSS для стилизации карточек и фона
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df_inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
        df_zpl_wide = pd.read_csv('tab3-zpl_2025_2.csv')
        # Убираем пробелы в названиях колонок
        df_inf.columns = df_inf.columns.str.strip()
        df_zpl_wide.columns = df_zpl_wide.columns.str.strip()
        
        df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
        df_zpl['Year'] = df_zpl['Year'].astype(int)
        return pd.merge(df_zpl, df_inf, on='Year')
    except Exception as e:
        st.error(f"Ошибка данных: {e}")
        return None

df = load_data()

if df is not None:
    # --- СТРУКТУРА SIDEBAR ---
    st.sidebar.header("📊 Фильтры данных")
    industries = sorted(df['Industry'].unique())
    selected = st.sidebar.multiselect("Выберите отрасли:", industries, default=[industries[0]])
    
    # Расчеты
    filtered = df[df['Industry'].isin(selected)].sort_values(['Industry', 'Year'])
    filtered['Nominal_Growth'] = filtered.groupby('Industry')['Salary'].pct_change() * 100
    filtered['Real_Growth'] = filtered['Nominal_Growth'] - filtered['Inflation']

    # --- ЗАГОЛОВОК ---
    st.title("📈 Аналитический хаб: Зарплаты и Макроэкономика")
    st.markdown("Визуализация реальной покупательной способности и экономических трендов.")

    # --- ВЕРХНИЕ МЕТРИКИ ---
    if not filtered.empty:
        last_year = filtered['Year'].max()
        m_cols = st.columns(len(selected))
        for i, ind in enumerate(selected):
            row = filtered[(filtered['Industry'] == ind) & (filtered['Year'] == last_year)]
            if not row.empty:
                m_cols[i].metric(label=ind, value=f"{row['Salary'].values[0]:,.0f} ₽", 
                                 delta=f"{row['Real_Growth'].values[0]:.2f}% (Реально)")

    # --- ТАБЫ С ВИЗУАЛИЗАЦИЯМИ ---
    tab1, tab2, tab3 = st.tabs(["🔥 Тепловая карта", "📊 Сравнение роста", "📉 Линейные тренды"])

    with tab1:
        st.subheader("Тепловая карта интенсивности зарплат")
        # Создаем матрицу для Heatmap
        pivot_df = filtered.pivot(index="Industry", columns="Year", values="Salary")
        fig_heatmap = px.imshow(
            pivot_df,
            labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
            color_continuous_scale='Viridis', # Красивый градиент от фиолетового к желтому
            text_auto='.0f', # Вывод цифр прямо в ячейках
            aspect="auto"
        )
        fig_heatmap.update_layout(title_font_size=20)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        st.info("💡 Чем светлее ячейка, тем выше уровень зарплаты в данном году и отрасли.")

    with tab2:
        st.subheader("Реальный рост vs Инфляция")
        # Группированная гистограмма
        fig_bar = px.bar(
            filtered.dropna(subset=['Real_Growth']), 
            x='Year', y='Real_Growth', color='Industry',
            barmode='group',
            title="Ежегодный реальный прирост доходов (%)",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_bar.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("Динамика номинальных зарплат")
        fig_line = px.line(
            filtered, x='Year', y='Salary', color='Industry',
            markers=True, line_shape="spline", # Сглаженные линии
            render_mode="svg"
        )
        fig_line.update_layout(hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)

    # --- ТАБЛИЦА ---
    with st.expander("📝 Посмотреть исходные данные"):
        st.dataframe(filtered.style.background_gradient(subset=['Real_Growth'], cmap='RdYlGn'), use_container_width=True)
