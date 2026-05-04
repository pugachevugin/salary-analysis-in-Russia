import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Конфигурация страницы
st.set_page_config(page_title="Аналитика экономики РФ 2000-2024", layout="wide")

# 2. CSS стили для красоты и читаемости
st.markdown("""
    <style>
    .main { background-color: #f8f9fc; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; border: 1px solid #dee2e6; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #4e73df; color: white; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Загрузка данных из файлов
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    
    # Трансформация зарплат в длинный формат для Plotly
    zpl_long = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl_long['Год'] = zpl_long['Год'].astype(int)
    
    # Слияние в единый DataFrame
    return pd.merge(zpl_long, inf, on='Год'), zpl_raw

df, df_wide = load_data()

# 3. Сайдбар
st.sidebar.header("📊 Управление")
selected_industries = st.sidebar.multiselect(
    "Выберите отрасли для сравнения:",
    options=df['Отрасль'].unique(),
    default=["ИТ и связь", "Средняя по РФ"]
)

# Расчет показателей (Пункт 4: Номинальный и Реальный рост)
res = df[df['Отрасль'].isin(selected_industries)].sort_values(['Отрасль', 'Год'])
res['Ном_Рост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
res['Реал_Рост'] = res['Ном_Рост'] - res['Инфляция']

# 4. Основной контент
st.title("🇷🇺 Экономический мониторинг (2000-2024)")
st.markdown("Анализ взаимосвязи уровня доходов, инфляции и монетарной политики ЦБ РФ.")

t1, t2, t3 = st.tabs(["🔥 Тепловая карта", "📊 Графики роста", "📋 Данные и Выводы"])

with t1:
    st.subheader("Интенсивность роста зарплат по отраслям")
    heat_df = df_wide.set_index('Отрасль')
    
    # Хитмап в палитре Viridis (от фиолетового к желтому)
    fig_heat = px.imshow(
        heat_df,
        color_continuous_scale='Viridis',
        labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
        aspect="auto"
    )
    # Принудительный шаг в 1 год
    fig_heat.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
    st.plotly_chart(fig_heat, use_container_width=True)

with t2:
    # ГРАФИК 1: Реальный прирост зарплат
    st.subheader("Реальный прирост зарплат (сверх инфляции)")
    fig_bar = px.bar(
        res.dropna(), x='Год', y='Реал_Рост', color='Отрасль',
        barmode='group', labels={'Реал_Рост': 'Прирост (%)'}
    )
    fig_bar.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
    fig_bar.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()

    # ГРАФИК 2: Инфляция и Ставка ЦБ (который я вернул)
    st.subheader("Монетарный контекст: Инфляция vs Ключевая ставка")
    inf_context = df.drop_duplicates('Год').sort_values('Год')
    
    fig_context = go.Figure()
    # Линия инфляции
    fig_context.add_trace(go.Scatter(
        x=inf_context['Год'], y=inf_context['Инфляция'], 
        name="Инфляция (%)", line=dict(color='#e74c3c', width=4)
    ))
    # Столбцы ставки ЦБ
    fig_context.add_trace(go.Bar(
        x=inf_context['Год'], y=inf_context['Ключевая_ставка'], 
        name="Ставка ЦБ (%)", marker_color='rgba(52, 152, 219, 0.3)'
    ))
    
    fig_context.update_layout(hovermode="x unified", template="plotly_white")
    fig_context.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
    st.plotly_chart(fig_context, use_container_width=True)

with t3:
    st.subheader("Детальная статистика и аналитика")
    
    # Таблица с градиентом
    st.dataframe(
        res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Рост']]
        .style.format({'Зарплата': '{:,.0f} ₽', 'Реал_Рост': '{:+.2f}%'})
        .background_gradient(subset=['Реал_Рост'], cmap='RdYlGn'),
        use_container_width=True
    )
    
    st.divider()
    
    # СЕКЦИЯ ВЫВОДОВ
    st.subheader("📝 Аналитические выводы")
    
    for industry in selected_industries:
        ind_data = res[res['Отрасль'] == industry].dropna()
        avg_real = ind_data['Реал_Рост'].mean()
        
        # Автоматический вердикт
        if avg_real > 3:
            st.success(f"**{industry}**: Высокая устойчивость. Средний реальный рост (+{avg_real:.2f}%) значительно опережает инфляцию.")
        elif avg_real > 0:
            st.info(f"**{industry}**: Умеренный рост. Доходы в среднем растут на {avg_real:.2f}% быстрее цен.")
        else:
            st.warning(f"**{industry}**: Рискованная зона. Рост зарплат ({avg_real:.2f}%) не всегда покрывает инфляцию.")
