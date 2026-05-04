import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Аналитика экономики РФ", layout="wide")

@st.cache_data
def load_data():
    # Загрузка инфляции (используем новые русские заголовки)
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    # Загрузка зарплат
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    
    # Трансформация зарплат в длинный формат
    zpl = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl['Год'] = zpl['Год'].astype(int)
    
    # Объединение таблиц по колонке 'Год'
    return pd.merge(zpl, inf, on='Год')

df = load_data()

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ---
st.title("📊 Экономический мониторинг (2000 – 2024)")
st.markdown("Приложение для анализа взаимосвязи доходов населения и инфляционных процессов.")

# SIDEBAR
st.sidebar.header("⚙️ Настройки")
selected_industries = st.sidebar.multiselect(
    "Выберите отрасли для сравнения:",
    options=df['Отрасль'].unique(),
    default=["ИТ и связь", "Средняя по РФ"]
)

# Фильтрация
plot_df = df[df['Отрасль'].isin(selected_industries)].sort_values(['Отрасль', 'Год'])

# РАСЧЕТЫ (Пункт 4 задания)
# Номинальный рост в %
plot_df['Ном_Прирост'] = plot_df.groupby('Отрасль')['Зарплата'].pct_change() * 100
# Реальный рост (за вычетом инфляции)
plot_df['Реальный_Прирост'] = plot_df['Ном_Прирост'] - plot_df['Инфляция']

# --- ВИЗУАЛИЗАЦИИ ---
tab1, tab2, tab3 = st.tabs(["📈 Динамика зарплат", "🌡️ Инфляция и Ставка", "📄 Отчет и Данные"])

with tab1:
    st.subheader("Изменение номинальных зарплат (в рублях)")
    fig_nom = px.line(plot_df, x='Год', y='Зарплата', color='Отрасль', 
                     markers=True, labels={'Зарплата': 'Сумма (₽)', 'Год': 'Год'})
    st.plotly_chart(fig_nom, use_container_width=True)
    
    st.subheader("Реальный прирост доходов (Пункт 5)")
    fig_real = px.bar(plot_df.dropna(), x='Год', y='Реальный_Прирост', color='Отрасль', 
                     barmode='group', title="Рост покупательной способности (%)",
                     labels={'Реальный_Прирост': 'Прирост (%)', 'Год': 'Год'})
    fig_real.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig_real, use_container_width=True)

with tab2:
    st.subheader("Монетарный контекст: Инфляция vs Ключевая ставка")
    # Группируем данные, чтобы не дублировать линии инфляции для каждой отрасли
    context_df = df.drop_duplicates('Год').sort_values('Год')
    
    fig_context = go.Figure()
    fig_context.add_trace(go.Scatter(x=context_df['Год'], y=context_df['Инфляция'], 
                                   name="Инфляция (%)", line=dict(color='red', width=3)))
    fig_context.add_trace(go.Bar(x=context_df['Год'], y=context_df['Ключевая_ставка'], 
                                name="Ключевая ставка (%)", marker_color='rgba(100, 150, 250, 0.4)'))
    
    fig_context.update_layout(xaxis_title="Год", yaxis_title="Процент (%)", hovermode="x unified")
    st.plotly_chart(fig_context, use_container_width=True)
    st.info("График показывает, как Центральный Банк реагировал изменением ставки на всплески инфляции.")

with tab3:
    st.subheader("Детальная таблица расчетов")
    # Отображаем только важные колонки
    display_cols = ['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Ключевая_ставка', 'Реальный_Прирост', 'Статус_инфляции']
    st.dataframe(
        plot_df[display_cols].style.format({
            'Зарплата': '{:,.0f} ₽', 
            'Инфляция': '{:.2f}%', 
            'Реальный_Прирост': '{:+.2f}%'
        }).background_gradient(subset=['Реальный_Прирост'], cmap='RdYlGn'),
        use_container_width=True
    )
    
    st.divider()
    st.markdown("### 📝 Аналитические выводы:")
    if not plot_df.empty:
        for ind in selected_industries:
            ind_avg = plot_df[plot_df['Отрасль'] == ind]['Реальный_Прирост'].mean()
            verdict = "опережает инфляцию" if ind_avg > 0 else "обесценивается инфляцией"
            st.write(f"- В секторе **{ind}** средний реальный рост составляет **{ind_avg:.2f}%**. Это означает, что доход в данной сфере **{verdict}**.")
