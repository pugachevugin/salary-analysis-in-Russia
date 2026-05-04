import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Настройка страницы
st.set_page_config(page_title="Аналитика РФ 2000-2024", layout="wide")

# Стилизация интерфейса
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stMetric"] { background-color: #ffffff; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    
    # Превращаем широкую таблицу (годы в столбцах) в длинную для графиков
    zpl_long = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl_long['Год'] = zpl_long['Год'].astype(int)
    
    # Объединяем с данными инфляции
    full_df = pd.merge(zpl_long, inf, on='Год')
    return full_df, zpl_raw

df, df_wide = load_data()

# Сайдбар
st.sidebar.header("📊 Управление данными")
selected_industries = st.sidebar.multiselect(
    "Выберите отрасли для анализа:",
    options=df['Отрасль'].unique(),
    default=["ИТ и связь", "Финансы", "Средняя по РФ"]
)

# Расчеты реального роста
res = df[df['Отрасль'].isin(selected_industries)].sort_values(['Отрасль', 'Год'])
res['Ном_Рост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
res['Реал_Рост'] = res['Ном_Рост'] - res['Инфляция']

# --- ОСНОВНОЙ БЛОК ---
st.title("📈 Экономический мониторинг: 2000 – 2024")

t1, t2, t3 = st.tabs(["🔥 Тепловая карта", "📉 Динамика роста", "📋 Таблицы данных"])

with t1:
    st.subheader("Карта интенсивности доходов (Viridis Palette)")
    heat_df = df_wide.set_index('Отрасль')
    
    # Создаем хитмап с палитрой Viridis (Фиолетовый -> Зеленый -> Желтый)
    fig_heat = px.imshow(
        heat_df,
        labels=dict(x="Год", y="Отрасль", color="₽"),
        color_continuous_scale='Viridis', # Та самая палитра
        aspect="auto",
        text_auto=False
    )
    
    # Настройка осей, чтобы видеть КАЖДЫЙ год без сокращений
    fig_heat.update_xaxes(
        tickmode='linear',
        dtick=1,
        tickangle=-45,
        side='bottom'
    )
    
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Цветовая шкала: Темно-фиолетовый (низкие доходы) → Зеленый → Ярко-желтый (максимальные значения).")

with t2:
    st.subheader("Ежегодный реальный прирост зарплат")
    # Указываем nbins или dtick, чтобы столбцы были по каждому году
    fig_bar = px.bar(
        res.dropna(), 
        x='Год', 
        y='Реал_Рост', 
        color='Отрасль',
        barmode='group',
        labels={'Реал_Рост': 'Рост выше инфляции (%)'},
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    
    # Принудительная разметка каждого года на оси X
    fig_bar.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
    fig_bar.add_hline(y=0, line_dash="dash", line_color="black", line_width=2)
    
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Сравнение инфляции и ключевой ставки (По годам)")
    inf_context = df.drop_duplicates('Год').sort_values('Год')
    fig_context = go.Figure()
    fig_context.add_trace(go.Scatter(x=inf_context['Год'], y=inf_context['Инфляция'], 
                                   name="Инфляция", line=dict(color='#e74c3c', width=4)))
    fig_context.add_trace(go.Bar(x=inf_context['Год'], y=inf_context['Ключевая_ставка'], 
                                name="Ставка ЦБ", marker_color='rgba(52, 152, 219, 0.3)'))
    
    fig_context.update_xaxes(tickmode='linear', dtick=1)
    st.plotly_chart(fig_context, use_container_width=True)

with t3:
    st.subheader("Сводная статистика за 25 лет")
    # Форматирование и вывод данных
    st.dataframe(
        res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Рост']]
        .style.format({'Зарплата': '{:,.0f} ₽', 'Реал_Рост': '{:+.2f}%'})
        .background_gradient(subset=['Реал_Рост'], cmap='RdYlGn'),
        use_container_width=True
    )
