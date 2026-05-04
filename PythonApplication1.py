import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Настройка страницы
st.set_page_config(page_title="Аналитика зарплат РФ", layout="wide")

# Кастомный стиль для выводов
st.markdown("""
    <style>
    .conclusion-box {
        background-color: #e8f4f8;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2980b9;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        # Чтение файлов Excel
        df_inf = pd.read_excel('Statistic_Inflatio_Russia.xlsx')
        df_zpl_wide = pd.read_excel('tab3-zpl_2025.xlsx')
        
        # Очистка названий столбцов
        df_inf.columns = df_inf.columns.str.strip()
        df_zpl_wide.columns = df_zpl_wide.columns.str.strip()
        
        # Преобразование зарплат в длинный формат (Tidy Data)
        df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
        df_zpl['Year'] = df_zpl['Year'].astype(int)
        
        # Объединение данных
        df = pd.merge(df_zpl, df_inf, on='Year')
        return df
    except Exception as e:
        st.error(f"Ошибка при чтении файлов: {e}")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR (Выбор видов деятельности) ---
    st.sidebar.header("🎯 Выбор данных")
    all_industries = sorted(df['Industry'].unique())
    selected = st.sidebar.multiselect(
        "Выберите 2-3 вида деятельности:", 
        all_industries, 
        default=all_industries[:2] # По умолчанию первые два
    )

    # --- РАСЧЕТЫ (Пункт 4 задания) ---
    # Фильтруем данные
    res = df[df['Industry'].isin(selected)].sort_values(['Industry', 'Year'])
    
    # Считаем номинальный рост (%)
    res['Nominal_Growth'] = res.groupby('Industry')['Salary'].pct_change() * 100
    
    # Считаем реальный рост (Зарплата - Инфляция)
    res['Real_Growth'] = res['Nominal_Growth'] - res['Inflation']
    
    # Расчет индекса реальной зарплаты (для графика)
    res['Real_Salary_Index'] = res['Salary'] / (1 + res['Inflation'] / 100)

    # --- ИНТЕРФЕЙС ---
    st.title("📊 Анализ влияния инфляции на доходы населения")
    st.write(f"Выбранные отрасли: **{', '.join(selected)}**")

    # ТАБЫ ДЛЯ ОРГАНИЗАЦИИ ВИЗУАЛИЗАЦИЙ (Пункт 2 задания)
    tab1, tab2, tab3 = st.tabs(["📈 Динамика (Пункт 3)", "⚖️ Реальные зарплаты (Пункт 5)", "📑 Сводная таблица"])

    with tab1:
        st.subheader("Изменение номинальной зарплаты по годам")
        fig_nom = px.line(res, x='Year', y='Salary', color='Industry', markers=True,
                          line_shape='spline', template='plotly_white',
                          labels={'Salary': 'Зарплата (руб)', 'Year': 'Год'})
        st.plotly_chart(fig_nom, use_container_width=True)
        
        st.markdown('<div class="conclusion-box"><b>Вывод:</b> На графике наблюдается устойчивый рост номинальных зарплат во всех выбранных отраслях. Однако для оценки благосостояния необходимо учитывать индекс потребительских цен.</div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("Влияние инфляции на доходы")
        # Создаем комбинированный график: Столбцы (Реальный рост) + Линия (Инфляция)
        fig_real = go.Figure()
        
        for ind in selected:
            ind_data = res[res['Industry'] == ind].dropna()
            fig_real.add_trace(go.Bar(x=ind_data['Year'], y=ind_data['Real_Growth'], name=f"Реал. рост: {ind}"))
        
        # Добавляем линию инфляции для справки
        inf_line = res.drop_duplicates('Year')
        fig_real.add_trace(go.Scatter(x=inf_line['Year'], y=inf_line['Inflation'], 
                                      name="Уровень инфляции %", line=dict(color='red', width=3, dash='dot')))

        fig_real.update_layout(title="Сравнение реального роста зарплат с уровнем инфляции",
                              xaxis_title="Год", yaxis_title="Проценты (%)", barmode='group')
        st.plotly_chart(fig_real, use_container_width=True)
        
        st.markdown('<div class="conclusion-box"><b>Вывод:</b> Если столбец реального роста находится выше нуля, значит зарплата росла быстрее инфляции. В годы с высокой инфляцией (например, 2022) наблюдается значительное сокращение реальных темпов роста доходов.</div>', unsafe_allow_html=True)

    with tab3:
        st.subheader("Детальный пересчет данных")
        # Красивое отображение таблицы с подсветкой
        st.write("Таблица содержит расчет номинального и реального прироста:")
        st.dataframe(res.style.background_gradient(subset=['Real_Growth'], cmap='RdYlGn'), use_container_width=True)

    # Кнопка для скачивания отчета (дополнительный элемент интерфейса)
    csv = res.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button("📥 Скачать результаты (CSV)", csv, "salary_analysis.csv", "text/csv")
