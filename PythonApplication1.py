import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Аналитика экономики РФ", layout="wide")

# 2. CSS стили
st.markdown("""
    <style>
    .main { background-color: #f8f9fc; }
    .stMetric { background-color: #ffffff; border: 1px solid #dee2e6; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Загрузка данных
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    
    # Преобразование в длинный формат для графиков
    zpl_long = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl_long['Год'] = zpl_long['Год'].astype(int)
    
    # Слияние таблиц
    return pd.merge(zpl_long, inf, on='Год'), zpl_raw

df, df_wide = load_data()

# 3. Боковая панель
st.sidebar.header("⚙️ Параметры анализа")
selected_industries = st.sidebar.multiselect(
    "Выберите отрасли:",
    options=df['Отрасль'].unique(),
    default=["ИТ и связь", "Средняя по РФ"]
)

# Расчет показателей (Пункт 4)
res = df[df['Отрасль'].isin(selected_industries)].sort_values(['Отрасль', 'Год'])
res['Ном_Рост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
res['Реал_Рост'] = res['Ном_Рост'] - res['Инфляция']

# 4. Основной интерфейс
st.title("📈 Динамика доходов и инфляции (2000-2024)")

t1, t2, t3 = st.tabs(["🔥 Тепловая карта", "📊 Графики роста", "📋 Данные и Выводы"])

with t1:
    st.subheader("Карта интенсивности зарплат (Viridis)")
    heat_df = df_wide.set_index('Отрасль')
    
    # Визуализация с переходом от фиолетового к желтому
    fig_heat = px.imshow(
        heat_df,
        color_continuous_scale='Viridis',
        labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
        aspect="auto"
    )
    # Настройка шага в 1 год
    fig_heat.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
    st.plotly_chart(fig_heat, use_container_width=True)

with t2:
    st.subheader("Реальный прирост зарплат по годам")
    # Гистограмма с шагом в 1 год
    fig_bar = px.bar(
        res.dropna(), x='Год', y='Реал_Рост', color='Отрасль',
        barmode='group', template="plotly_white"
    )
    fig_bar.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
    fig_bar.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_bar, use_container_width=True)

with t3:
    st.subheader("Детальная статистика и аналитика")
    
    # Отображение таблицы с градиентом
    st.dataframe(
        res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Рост']]
        .style.format({'Зарплата': '{:,.0f} ₽', 'Реал_Рост': '{:+.2f}%'})
        .background_gradient(subset=['Реал_Рост'], cmap='RdYlGn'),
        use_container_width=True
    )
    
    st.divider()
    
    # СЕКЦИЯ ВЫВОДОВ (Пункт 5)
    st.subheader("📝 Аналитические выводы по выбранным отраслям")
    
    for industry in selected_industries:
        ind_data = res[res['Отрасль'] == industry].dropna()
        avg_real = ind_data['Реал_Рост'].mean()
        max_year = ind_data.loc[ind_data['Зарплата'].idxmax(), 'Год']
        
        # Логика для текста выводов
        status = "✅ Опережает инфляцию" if avg_real > 0 else "❌ Обесценивается инфляцией"
        
        with st.expander(f"Анализ отрасли: {industry}"):
            st.write(f"**Текущий статус:** {status}")
            st.write(f"**Средний реальный прирост:** {avg_real:.2f}% в год.")
            st.write(f"**Пик номинальной зарплаты:** зафиксирован в {max_year} году.")
            
            # Динамический комментарий
            if avg_real > 5:
                st.info(f"Отрасль '{industry}' демонстрирует агрессивный рост, значительно перекрывающий рост цен.")
            elif avg_real > 0:
                st.success(f"Доходы в сфере '{industry}' стабильны и сохраняют покупательную способность.")
            else:
                st.error(f"Внимание: рост зарплат в сфере '{industry}' не компенсирует инфляционные риски.")
