import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Конфигурация страницы
st.set_page_config(
    page_title="Экономика РФ: Аналитика 2000-2024",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Исправленный блок стилизации (фикс ошибки TypeError)
st.markdown("""
    <style>
    .main { 
        background-color: #f5f7f9; 
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4e73df;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Функция загрузки данных
@st.cache_data
def load_data():
    try:
        # Загрузка инфляции
        inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
        # Загрузка зарплат
        zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
        
        # Трансформация зарплат в длинный формат (melt) для построения графиков
        zpl = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
        zpl['Год'] = zpl['Год'].astype(int)
        
        # Объединение
        merged_df = pd.merge(zpl, inf, on='Год')
        return merged_df, zpl_raw
    except Exception as e:
        st.error(f"Ошибка при загрузке файлов CSV: {e}")
        return None, None

df, df_wide = load_data()

if df is not None:
    # --- БОКОВАЯ ПАНЕЛЬ ---
    st.sidebar.image("https://img.icons8.com/fluency/96/commercial.png")
    st.sidebar.title("Настройки")
    
    all_inds = sorted(df['Отрасль'].unique())
    selected_inds = st.sidebar.multiselect(
        "Выберите отрасли для сравнения (Пункт 3):",
        options=all_inds,
        default=["ИТ и связь", "Средняя по РФ"]
    )

    # Расчеты (Пункт 4)
    res = df[df['Отрасль'].isin(selected_inds)].sort_values(['Отрасль', 'Год'])
    res['Ном_Прирост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
    res['Реал_Прирост'] = res['Ном_Прирост'] - res['Инфляция']

    # --- ОСНОВНОЙ КОНТЕНТ ---
    st.title("📊 Анализ зарплат и инфляции в РФ")
    st.markdown("Визуализация выполнена в рамках учебного проекта специальности **09.03.03**.")

    # Вкладки для различных визуализаций
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Тепловая карта", 
        "📈 Номинальные зарплаты", 
        "📉 Реальный рост", 
        "📋 Исходные данные"
    ])

    with tab1:
        st.subheader("Карта интенсивности зарплат по отраслям и годам")
        heat_data = df_wide.set_index('Отрасль')
        fig_heat = px.imshow(
            heat_data,
            labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
            color_continuous_scale='YlGnBu',
            aspect="auto",
            text_auto=False
        )
        fig_heat.update_xaxes(side="top")
        st.plotly_chart(fig_heat, use_container_width=True)
        st.info("Хитмап позволяет мгновенно увидеть периоды резкого роста доходов в разных секторах.")

    with tab2:
        st.subheader("Динамика изменения зарплаты по годам (Пункт 3)")
        fig_line = px.line(
            res, x='Год', y='Зарплата', color='Отрасль', 
            markers=True, line_shape="spline",
            labels={'Зарплата': 'Сумма (руб.)', 'Год': 'Год'}
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        # Дополнительная круговая диаграмма для 2024 года
        st.divider()
        st.subheader("Распределение уровня зарплат (2024 год)")
        latest_data = df[df['Год'] == 2024]
        fig_pie = px.pie(latest_data, values='Зарплата', names='Отрасль', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        st.subheader("Влияние инфляции на реальные доходы (Пункт 4 и 5)")
        fig_bar = px.bar(
            res.dropna(), x='Год', y='Реал_Прирост', color='Отрасль',
            barmode='group', title="Реальный прирост зарплаты (сверх инфляции), %",
            labels={'Реал_Прирост': 'Прирост (%)', 'Год': 'Год'}
        )
        fig_bar.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.subheader("Контекст: Инфляция vs Ключевая ставка")
        context_df = df.drop_duplicates('Год')
        fig_context = go.Figure()
        fig_context.add_trace(go.Scatter(x=context_df['Год'], y=context_df['Инфляция'], name="Инфляция", line=dict(color='red', width=3)))
        fig_context.add_trace(go.Bar(x=context_df['Год'], y=context_df['Ключевая_ставка'], name="Ключевая ставка", marker_color='rgba(0, 0, 255, 0.2)'))
        st.plotly_chart(fig_context, use_container_width=True)

    with tab4:
        st.subheader("Сводная таблица расчетов")
        st.dataframe(
            res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Прирост', 'Статус_инфляции']]
            .style.format({'Зарплата': '{:,.0f} ₽', 'Реал_Прирост': '{:+.2f}%'})
            .background_gradient(subset=['Реал_Прирост'], cmap='RdYlGn'),
            use_container_width=True
        )
        
        # Выводы (Пункт 5)
        st.divider()
        st.markdown("### 📝 Аналитические выводы:")
        for ind in selected_inds:
            avg_real = res[res['Отрасль'] == ind]['Реал_Прирост'].mean()
            if avg_real > 0:
                st.success(f"**{ind}**: Отрасль стабильно растет быстрее цен (средний рост {avg_real:.2f}%).")
            else:
                st.warning(f"**{ind}**: Темпы роста в этой сфере едва догоняют инфляцию ({avg_real:.2f}%).")

else:
    st.error("Пожалуйста, убедитесь, что CSV-файлы находятся в корневой папке приложения.")
