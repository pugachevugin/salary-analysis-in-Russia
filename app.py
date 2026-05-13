import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Конфигурация страницы
st.set_page_config(page_title="Аналитика экономики РФ 2000-2025", layout="wide")

# 2. CSS стили для улучшения интерфейса
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
    # Загрузка данных (имена файлов оставлены согласно вашему запросу)
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    
    # Преобразование широкой таблицы в длинный формат
    zpl_long = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl_long['Год'] = zpl_long['Год'].astype(int)
    
    # Объединение с данными по инфляции
    return pd.merge(zpl_long, inf, on='Год'), zpl_raw

try:
    df, df_wide = load_data()

    # 3. Сайдбар
    st.sidebar.header("📊 Управление")
    selected_industries = st.sidebar.multiselect(
        "Выберите отрасли для сравнения:",
        options=df['Отрасль'].unique(),
        default=["ИТ и связь", "Средняя по РФ"] if "ИТ и связь" in df['Отрасль'].unique() else [df['Отрасль'].unique()[0]]
    )

    # --- ГЛОБАЛЬНАЯ ОБРАБОТКА ДАННЫХ ---
    # Фильтруем данные один раз для всех графиков
    res = df[df['Отрасль'].isin(selected_industries)].sort_values(['Отрасль', 'Год'])
    
    # Расчет процентного изменения (номинальный рост) и реального роста (за вычетом инфляции)
    res['Ном_Рост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
    res['Реал_Рост'] = res['Ном_Рост'] - res['Инфляция']

    # 4. Основной контент
    st.title("📈 Экономический мониторинг (2000-2025)")
    st.markdown("Анализ динамики доходов населения в контексте инфляционных процессов и политики ЦБ.")

    t1, t2, t3 = st.tabs(["📈 Динамика зарплат", "📊 Реальный рост", "📋 Статистика и выводы"])

    with t1:
        st.subheader("Линейный график номинальных зарплат")
        if not res.empty:
            fig_line = px.line(
                res, 
                x='Год', 
                y='Зарплата', 
                color='Отрасль',
                markers=True,
                line_shape='linear',
                labels={'Зарплата': 'Зарплата (₽)', 'Год': 'Год'},
                template="plotly_white"
            )
            fig_line.update_layout(
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig_line.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Пожалуйста, выберите отрасли в меню слева.")

    with t2:
        st.subheader("Реальный прирост зарплат (сверх инфляции)")
        # Убираем NaN, которые образуются в первый год из-за pct_change()
        plot_res = res.dropna(subset=['Реал_Рост'])
        
        if not plot_res.empty:
            fig_bar = px.bar(
                plot_res, 
                x='Год', 
                y='Реал_Рост', 
                color='Отрасль',
                barmode='group',
                labels={'Реал_Рост': 'Реальный рост (%)', 'Год': 'Год'},
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_bar.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
            fig_bar.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.5)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.divider()

        st.subheader("Монетарный контекст: Инфляция vs Ключевая ставка")
        # Данные по инфляции берем уникальные по годам (общие для страны)
        inf_context = df[['Год', 'Инфляция', 'Ключевая_ставка']].drop_duplicates().sort_values('Год')
        
        fig_context = go.Figure()
        fig_context.add_trace(go.Scatter(
            x=inf_context['Год'], y=inf_context['Инфляция'], 
            name="Инфляция (%)", line=dict(color='#e74c3c', width=4)
        ))
        fig_context.add_trace(go.Bar(
            x=inf_context['Год'], y=inf_context['Ключевая_ставка'], 
            name="Ставка ЦБ (%)", marker_color='rgba(52, 152, 219, 0.3)'
        ))
        fig_context.update_layout(
            hovermode="x unified", 
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_context.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
        st.plotly_chart(fig_context, use_container_width=True)

    with t3:
        st.subheader("Детальные данные")
        # Форматирование таблицы для лучшей читаемости
        st.dataframe(
            res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Рост']]
            .sort_values(['Год', 'Отрасль'], ascending=[False, True])
            .style.format({'Зарплата': '{:,.0f} ₽', 'Реал_Рост': '{:+.2f}%', 'Инфляция': '{:.1f}%'})
            .background_gradient(subset=['Реал_Рост'], cmap='RdYlGn', vmin=-10, vmax=10),
            use_container_width=True
        )
        
        st.divider()
        st.subheader("📝 Аналитические выводы")
        
        if selected_industries:
            cols = st.columns(len(selected_industries))
            for i, industry in enumerate(selected_industries):
                ind_data = res[res['Отрасль'] == industry].dropna(subset=['Реал_Рост'])
                if not ind_data.empty:
                    avg_real = ind_data['Реал_Рост'].mean()
                    with cols[i % len(cols)]:
                        if avg_real > 3:
                            st.success(f"**{industry}**\n\nВысокий рост: +{avg_real:.2f}% (в среднем)")
                        elif avg_real > 0:
                            st.info(f"**{industry}**\n\nУмеренный рост: +{avg_real:.2f}% (в среднем)")
                        else:
                            st.warning(f"**{industry}**\n\nСтагнация: {avg_real:.2f}% (в среднем)")
        else:
            st.write("Выберите отрасли для формирования автоматических выводов.")

except Exception as e:
    st.error(f"Ошибка при загрузке или обработке данных: {e}")
    st.info("Проверьте наличие файлов CSV и корректность названий столбцов.")
