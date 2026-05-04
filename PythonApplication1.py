import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# 1. Настройка страницы
st.set_page_config(page_title="Аналитика 2000-2024", layout="wide")

# --- ГЕНЕРАЦИЯ ПОЛНОЦЕННОЙ БАЗЫ ДАННЫХ (с 2000 года) ---
@st.cache_data
def get_historical_data():
    years = list(range(2000, 2025))
    # Историческая инфляция РФ (усредненные значения для модели)
    inf_rates = [
        20.2, 18.6, 15.1, 12.0, 11.7, 10.9, 9.0, 11.9, 13.3, 8.8,
        8.8, 6.1, 6.6, 6.5, 11.4, 12.9, 5.4, 2.5, 4.3, 3.0,
        4.9, 8.4, 11.9, 7.4, 7.7
    ]
    df_inf = pd.DataFrame({'Year': years, 'Inflation': inf_rates})

    # Отрасли и их стартовые зарплаты в 2000 году
    industries = {
        "ИТ и связь": 3500, 
        "Добыча ископаемых": 6000, 
        "Образование": 1500, 
        "Здравоохранение": 1800, 
        "Финансы": 5500
    }
    
    data = []
    for ind, base_sal in industries.items():
        curr_sal = base_sal
        for i, year in enumerate(years):
            # Моделируем рост: инфляция + структурный рост отрасли
            growth_mod = 1.05 if ind == "ИТ и связь" else 1.02
            curr_sal *= (1 + (inf_rates[i]/100)) * growth_mod
            data.append({"Industry": ind, "Year": year, "Salary": round(curr_sal)})
            
    df_zpl = pd.DataFrame(data)
    return pd.merge(df_zpl, df_inf, on='Year')

df = get_historical_data()

# --- ИНТЕРФЕЙС ---
st.title("📊 Экономическая ретроспектива: 2000 — 2024")
st.markdown("Анализ динамики зарплат и инфляции за последние 25 лет.")

# SIDEBAR
st.sidebar.header("🔍 Фильтры")
selected_inds = st.sidebar.multiselect(
    "Выберите отрасли:", df['Industry'].unique(), default=["ИТ и связь", "Образование"]
)

# --- РАСЧЕТЫ (Пункт 4) ---
# Считаем показатели для выбранных отраслей
res = df[df['Industry'].isin(selected_inds)].sort_values(['Industry', 'Year'])
res['Nominal_Growth'] = res.groupby('Industry')['Salary'].pct_change() * 100
res['Real_Growth'] = res['Nominal_Growth'] - res['Inflation']

# --- ВИЗУАЛИЗАЦИИ ---
tab1, tab2, tab3 = st.tabs(["🔥 Тепловая карта", "📉 Тренды", "📝 Таблицы и выводы"])

with tab1:
    st.subheader("Хитмап: Распределение зарплат по десятилетиям")
    # Матрица для хитмапа
    pivot_df = df.pivot(index="Industry", columns="Year", values="Salary")
    fig_heat = px.imshow(
        pivot_df,
        labels=dict(x="Год", y="Отрасль", color="Зарплата (₽)"),
        color_continuous_scale='Viridis',
        aspect="auto"
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Визуализация позволяет увидеть резкий переход уровней дохода после 2010-х и 2020-х годов.")

with tab2:
    st.subheader("Динамика реального прироста (Пункт 5)")
    if not res.empty:
        # График реального роста (Зарплата vs Инфляция)
        fig_real = px.bar(
            res.dropna(), x='Year', y='Real_Growth', color='Industry',
            barmode='group', title="Реальный рост доходов за вычетом инфляции (%)"
        )
        fig_real.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_real, use_container_width=True)
    
    st.subheader("Изменение номинальных зарплат (Пункт 3)")
    fig_line = px.line(res, x='Year', y='Salary', color='Industry', markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

with tab3:
    st.subheader("Детальные данные и расчеты")
    # Очищенная таблица для пользователя
    st.dataframe(
        res[['Industry', 'Year', 'Salary', 'Inflation', 'Real_Growth']]
        .style.format({'Salary': '{:,.0f}', 'Real_Growth': '{:+.2f}%'})
        .background_gradient(subset=['Real_Growth'], cmap='RdYlGn'),
        use_container_width=True
    )
    
    st.divider()
    st.markdown("### 📌 Итоговые выводы по заданию:")
    if not res.empty:
        for ind in selected_inds:
            avg_real = res[res['Industry'] == ind]['Real_Growth'].mean()
            st.write(f"- **{ind}**: Среднегодовой реальный рост составил **{avg_real:.2f}%**. "
                     f"{'Отрасль успешно обгоняет инфляцию.' if avg_real > 0 else 'Инфляция поглощает большую часть роста.'}")
