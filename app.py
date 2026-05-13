import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Конфигурация страницы
st.set_page_config(page_title="Аналитика экономики РФ 2000-2025", layout="wide")

# 2. CSS стили
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
    inf = pd.read_csv('Statistic_Inflatio_Russia_2.csv')
    zpl_raw = pd.read_csv('tab3-zpl_2025_2.csv')
    
    zpl_long = zpl_raw.melt(id_vars=['Отрасль'], var_name='Год', value_name='Зарплата')
    zpl_long['Год'] = zpl_long['Год'].astype(int)
    
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

    # --- ОБРАБОТКА ДАННЫХ ---
    res = df[df['Отрасль'].isin(selected_industries)].sort_values(['Отрасль', 'Год'])
    res['Ном_Рост'] = res.groupby('Отрасль')['Зарплата'].pct_change() * 100
    res['Реал_Рост'] = res['Ном_Рост'] - res['Инфляция']

    df_wide_filtered = df_wide[df_wide['Отрасль'].isin(selected_industries)]

    # 4. Основной контент
    st.title("Экономический мониторинг (2000-2025)")
    
    t1, t2, t3 = st.tabs(["🔥 Тепловая карта", "📈 Графики роста", "📋 Данные и Выводы"])

    with t1:
        st.subheader("Интенсивность роста зарплат (Heatmap)")
        if not df_wide_filtered.empty:
            heat_df = df_wide_filtered.set_index('Отрасль')
            fig_heat = px.imshow(
                heat_df,
                color_continuous_scale='Viridis', # Возвращаем исходную палитру
                labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
                aspect="auto"
            )
            fig_heat.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.warning("Выберите отрасли в меню слева.")

    with t2:
        st.subheader("Динамика реального прироста зарплат (%)")
        st.caption("Реальный рост = Номинальный рост зарплаты минус годовая инфляция")
        
        plot_data = res.dropna(subset=['Реал_Рост'])
        if not plot_data.empty:
            # Заменяем bar на line по твоему запросу
            fig_real = px.line(
                plot_data, 
                x='Год', 
                y='Реал_Рост', 
                color='Отрасль',
                markers=True,
                labels={'Реал_Рост': 'Реальный прирост (%)'},
                template="plotly_white"
            )
            fig_real.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Порог инфляции")
            fig_real.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
            fig_real.update_layout(hovermode="x unified")
            st.plotly_chart(fig_real, use_container_width=True)
        
        st.divider()

        st.subheader("Контекст: Инфляция и Ключевая ставка")
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
        fig_context.update_xaxes(tickmode='linear', dtick=1, tickangle=-45)
        fig_context.update_layout(template="plotly_white", hovermode="x")
        st.plotly_chart(fig_context, use_container_width=True)

    with t3:
        st.subheader("Детальная статистика")
        st.dataframe(
            res[['Отрасль', 'Год', 'Зарплата', 'Инфляция', 'Реал_Рост']]
            .style.format({'Зарплата': '{:,.0f} ₽', 'Реал_Рост': '{:+.2f}%'})
            .background_gradient(subset=['Реал_Рост'], cmap='RdYlGn'),
            use_container_width=True
        )
        
        st.divider()
        st.subheader("📝 Аналитические выводы")
        if selected_industries:
            for industry in selected_industries:
                ind_data = res[res['Отрасль'] == industry].dropna(subset=['Реал_Рост'])
                if not ind_data.empty:
                    avg_real = ind_data['Реал_Рост'].mean()
                    if avg_real > 3:
                        st.success(f"**{industry}**: Средний реальный рост +{avg_real:.2f}% — доходы уверенно обгоняют инфляцию.")
                    elif avg_real > 0:
                        st.info(f"**{industry}**: Средний реальный рост +{avg_real:.2f}% — покупательная способность сохраняется.")
                    else:
                        st.warning(f"**{industry}**: Средний показатель {avg_real:.2f}% — риск обесценивания доходов.")

except Exception as e:
    st.error(f"Ошибка: {e}")
