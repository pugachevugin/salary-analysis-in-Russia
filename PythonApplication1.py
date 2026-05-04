import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

# 1. Настройка страницы
st.set_page_config(page_title="Аналитика зарплат и инфляции", layout="wide")

# --- ПОДГОТОВКА ДАННЫХ (CSV формат внутри кода) ---
@st.cache_data
def get_data():
    # Данные по инфляции (2018-2024)
    inf_csv = """Year,Inflation
2018,4.27
2019,3.05
2020,4.91
2021,8.39
2022,11.94
2023,7.42
2024,7.70"""
    
    # Данные по зарплатам (расширенный список отраслей)
    zpl_csv = """Industry,2018,2019,2020,2021,2022,2023,2024
ИТ и связь,66590,75450,88200,105300,121720,145210,162400
Финансы,78510,84900,95350,112400,132100,156400,175200
Добыча ископаемых,83120,89340,95300,103400,118300,135200,148600
Образование,34300,37000,39500,43400,48400,54200,59800
Здравоохранение,40020,43100,49500,53200,57100,63400,69200"""
    
    df_inf = pd.read_csv(io.StringIO(inf_csv))
    df_zpl_wide = pd.read_csv(io.StringIO(zpl_csv))
    
    # Превращаем в длинный формат
    df_zpl = df_zpl_wide.melt(id_vars=['Industry'], var_name='Year', value_name='Salary')
    df_zpl['Year'] = df_zpl['Year'].astype(int)
    
    # Объединяем
    return pd.merge(df_zpl, df_inf, on='Year')

df = get_data()

# --- ИНТЕРФЕЙС ---
st.title("📈 Анализ реальных доходов населения")
st.markdown("""
Данный сервис позволяет оценить, как инфляция влияет на номинальные зарплаты в РФ. 
Работа выполнена в рамках учебного задания (Специальность 09.03.03).
""")

# --- SIDEBAR (Кнопки и фильтры) ---
st.sidebar.header("⚙️ Настройки")
selected_industries = st.sidebar.multiselect(
    "Выберите 2-3 отрасли:", 
    df['Industry'].unique(), 
    default=["ИТ и связь", "Здравоохранение"]
)

# Кнопка сброса (демонстрация элементов интерфейса)
if st.sidebar.button("Очистить выбор"):
    st.rerun()

st.sidebar.divider()
st.sidebar.info("Инфляция учитывается по данным Росстата (итоговые значения за год).")

if len(selected_industries) > 0:
    # --- РАСЧЕТЫ (Пункт 4 задания) ---
    working_df = df[df['Industry'].isin(selected_industries)].sort_values(['Industry', 'Year'])
    
    # 1. Номинальный рост к предыдущему году
    working_df['Nominal_Growth_Pct'] = working_df.groupby('Industry')['Salary'].pct_change() * 100
    
    # 2. Реальный рост (Зарплата_рост % - Инфляция %)
    working_df['Real_Growth_Pct'] = working_df['Nominal_Growth_Pct'] - working_df['Inflation']
    
    # 3. Реальная зарплата (приведенная к ценам 2018 года для наглядности)
    # Формула: Номинал / (1 + Инфляция/100)
    working_df['Real_Salary'] = working_df['Salary'] / (1 + working_df['Inflation'] / 100)

    # --- ВИЗУАЛИЗАЦИЯ 1: Номинальные зарплаты (Пункт 3) ---
    st.subheader("1. Динамика номинальных зарплат")
    fig1 = px.line(
        working_df, x='Year', y='Salary', color='Industry', 
        markers=True, line_shape='spline',
        title="Рост зарплат без учета инфляции (руб.)"
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    with st.expander("Вывод по номинальным зарплатам"):
        st.write("Во всех выбранных отраслях наблюдается положительный номинальный тренд. "
                 "Наибольший темп роста в абсолютных цифрах показывает ИТ-сектор.")

    # --- ВИЗУАЛИЗАЦИЯ 2: Реальный рост (Пункт 5) ---
    st.subheader("2. Динамика реальных зарплат (с учетом инфляции)")
    
    # Создаем столбчатую диаграмму реального прироста
    fig2 = px.bar(
        working_df.dropna(), 
        x='Year', y='Real_Growth_Pct', color='Industry',
        barmode='group', 
        title="Реальный прирост покупательной способности (%)",
        color_discrete_sequence=px.colors.qualitative.T10
    )
    # Добавляем линию инфляции для сравнения
    fig2.add_hline(y=0, line_dash="dash", line_color="black", annotation_text="Порог инфляции")
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("Вывод по реальным зарплатам"):
        st.write("Реальный рост зарплат показывает, насколько увеличилось благосостояние "
                 "за вычетом инфляции. Если столбец выше нуля — доходы обогнали рост цен.")

    # --- ТАБЛИЦА С РЕЗУЛЬТАТАМИ (Пункт 4) ---
    st.subheader("🔍 Детальный пересчет и сравнение")
    
    # Форматирование для красоты
    display_df = working_df[['Industry', 'Year', 'Salary', 'Inflation', 'Real_Growth_Pct']].copy()
    display_df.columns = ['Отрасль', 'Год', 'Зарплата (руб)', 'Инфляция (%)', 'Реальный рост (%)']
    
    st.dataframe(
        display_df.style.format({
            'Зарплата (руб)': '{:,.0f}',
            'Инфляция (%)': '{:.2f}',
            'Реальный рост (%)': '{:+.2f}'
        }).background_gradient(subset=['Реальный рост (%)'], cmap='RdYlGn'),
        use_container_width=True
    )

else:
    st.warning("Выберите хотя бы одну отрасль в боковой панели для отображения графиков.")
