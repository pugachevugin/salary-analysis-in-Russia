import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Настройка
st.set_page_config(page_title="Анализ экономики РФ 2000-2024", layout="wide")

# Стили (Фикс ошибки unsafe_allow_html)
st.markdown("""
    <style>
    .main { background-color: #f8f9fc; }
    .stMetric { border: 1px solid #e3e6f0; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    
    # ПЛАВНЫЙ ПЕРЕХОД: Расплавляем таблицу зарплат по годам (каждый год!)
    zpl = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl['Год'] = zpl['Год'].astype(int)
    
    # Соединяем по году
    return pd.merge(zpl, inf, on='Год'), zpl_raw

df, df_wide = load_data()

# Заголовок
st.title("🇷🇺 Мониторинг зарплат и инфляции (2000-2024)")
st.caption("Детальный анализ данных по годам для специальности 09.03.03")

# Настройки в боковой панели
st.sidebar.header("Фильтры")
selected_industries = st.sidebar.multiselect(
    "Выберите отрасли:",
    options=df['Отрасль'].unique(),
    default=["ИТ и связь", "Средняя по РФ"]
)

# Вычисления реального роста (Пункт 4)
res = df[df['Отрасль'].isin(selected_industries)].sort_values(['Отрасль', 'Год'])
res['Ном_Рост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
res['Реал_Рост'] = res['Ном_Рост'] - res['Инфляция']

# ВКЛАДКИ
t1, t2, t3 = st.tabs(["📊 Тренды и Теплокарта", "💸 Реальные доходы", "📋 Данные"])

with t1:
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("Динамика зарплат (по годам)")
        fig_line = px.line(res, x='Год', y='Зарплата', color='Отрасль', markers=True, 
                          line_shape="spline", template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col_b:
        st.subheader("Тепловая карта (Heatmap)")
        # Теперь здесь каждый год от 2000 до 2024
        heat_df = df_wide.set_index('Отрасль')
        fig_heat = px.imshow(heat_df, color_continuous_scale='RdYlGn', aspect="auto")
        st.plotly_chart(fig_heat, use_container_width=True)

with t2:
    st.subheader("Реальный прирост зарплат с учетом инфляции (Пункт 5)")
    # Гистограмма по каждому году
    fig_bar = px.bar(res.dropna(), x='Год', y='Реал_Рост', color='Отрасль', 
                    barmode='group', labels={'Реал_Рост': 'Прирост выше инфляции (%)'})
    fig_bar.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.info("Если столбец выше нуля — зарплата росла быстрее цен. Если ниже — инфляция 'съедала' доход.")

with t3:
    st.subheader("Полная годовая статистика")
    # Красивая таблица с градиентом
    st.dataframe(
        res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Рост']]
        .style.format({'Реал_Рост': '{:+.2f}%', 'Зарплата': '{:,.0f} ₽'})
        .background_gradient(subset=['Реал_Рост'], cmap='RdYlGn'),
        use_container_width=True
    )

    # Выводы (Пункт 5)
    st.markdown("### Выводы по анализу:")
    for ind in selected_industries:
        avg_real = res[res['Отрасль'] == ind]['Реал_Рост'].mean()
        status = "превышает" if avg_real > 0 else "не догоняет"
        st.write(f"- В отрасли **{ind}** средний реальный рост за 24 года {status} темпы инфляции.")
