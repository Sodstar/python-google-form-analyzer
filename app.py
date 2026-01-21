import streamlit as st
import pandas as pd
import re
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Багш үнэлгээний систем", page_icon="📊", layout="wide")

st.title("📊 Багш үнэлгээний судалгааны систем")
st.markdown("---")

# Function to categorize responses
def categorize_response(val):
    if pd.isna(val):
        return None
    val_str = str(val).lower().strip()
    
    if 'мэдэхгүй' in val_str:
        return 'Exclude'
    elif 'маш сайн' in val_str or 'сайн' in val_str:
        return 'Good'
    elif 'дунд' in val_str:
        return 'Medium'
    elif 'муу' in val_str:
        return 'Bad'
    else:
        return None

def process_survey_data(df):
    """Process the survey data and return results DataFrame"""
    teacher_data = {}
    pattern = re.compile(r"(.*?) \[(.*?)\]")
    
    for col in df.columns:
        match = pattern.match(col)
        if match:
            teacher_name = match.group(1).strip()
            criterion = match.group(2).strip()
            
            if teacher_name not in teacher_data:
                teacher_data[teacher_name] = []
                
            mapped_col = df[col].apply(categorize_response)
            valid_responses = mapped_col[mapped_col.isin(['Good', 'Medium', 'Bad'])]
            total_valid = len(valid_responses)
            
            if total_valid > 0:
                counts = valid_responses.value_counts()
                good_pct = (counts.get('Good', 0) / total_valid) * 100
                medium_pct = (counts.get('Medium', 0) / total_valid) * 100
                bad_pct = (counts.get('Bad', 0) / total_valid) * 100
            else:
                good_pct = medium_pct = bad_pct = 0.0
                
            teacher_data[teacher_name].append({
                'criterion': criterion,
                'good': good_pct,
                'medium': medium_pct,
                'bad': bad_pct,
                'count': total_valid
            })
    
    # Flatten into final list with Averages
    final_results = []
    for teacher, criteria_list in teacher_data.items():
        sum_good = 0
        sum_med = 0
        sum_bad = 0
        num_criteria = 0
        
        for item in criteria_list:
            final_results.append({
                'Багшийн нэр': teacher,
                'Үзүүлэлт': item['criterion'],
                'Сайн (%)': round(item['good'], 1),
                'Дунд (%)': round(item['medium'], 1),
                'Муу (%)': round(item['bad'], 1),
                'Үнэлсэн тоо': item['count']
            })
            
            sum_good += item['good']
            sum_med += item['medium']
            sum_bad += item['bad']
            num_criteria += 1
            
        if num_criteria > 0:
            final_results.append({
                'Багшийн нэр': teacher,
                'Үзүүлэлт': '--- ДУНДАЖ ---',
                'Сайн (%)': round(sum_good / num_criteria, 1),
                'Дунд (%)': round(sum_med / num_criteria, 1),
                'Муу (%)': round(sum_bad / num_criteria, 1),
                'Үнэлсэн тоо': '-'
            })
    
    return pd.DataFrame(final_results)

# File uploader
st.sidebar.header("📁 Файл оруулах")
uploaded_file = st.sidebar.file_uploader(
    "CSV файл сонгох",
    type=['csv'],
    help="Google Forms-оос татаж авсан CSV файлаа оруулна уу"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Тохиргоо")
show_charts = st.sidebar.checkbox("График харуулах", value=True)
chart_type = st.sidebar.selectbox(
    "График төрөл",
    ["Бүгд", "Багшаар", "Нийтлэг тойм", "Харьцуулалт"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 Заавар")
st.sidebar.info(
    """
    1. CSV файлаа сонгоно уу
    2. Өгөгдөл автоматаар боловсруулагдана
    3. График болон хүснэгт үзнэ үү
    4. Excel файл татаж авна уу
    """
)

# Main content
if uploaded_file is not None:
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        
        st.success(f"✅ Файл амжилттай уншигдлаа! ({len(df)} мөр)")
        
        # Process the data
        with st.spinner('Өгөгдлийг боловсруулж байна...'):
            result_df = process_survey_data(df)
        
        if len(result_df) > 0:
            st.success(f"✅ Боловсруулалт дууслаа! ({len(result_df)} үр дүн)")
            
            # Statistics
            st.markdown("### 📊 Нийт статистик")
            col1, col2, col3, col4 = st.columns(4)
            
            teachers_count = result_df[result_df['Үзүүлэлт'] != '--- ДУНДАЖ ---']['Багшийн нэр'].nunique()
            total_responses = result_df[result_df['Үзүүлэлт'] != '--- ДУНДАЖ ---']['Үнэлсэн тоо'].sum()
            avg_good = result_df[result_df['Үзүүлэлт'] == '--- ДУНДАЖ ---']['Сайн (%)'].mean()
            avg_medium = result_df[result_df['Үзүүлэлт'] == '--- ДУНДАЖ ---']['Дунд (%)'].mean()
            
            with col1:
                st.metric("Нийт багш", teachers_count)
            with col2:
                st.metric("Нийт үнэлгээ", int(total_responses))
            with col3:
                st.metric("Дундаж сайн", f"{avg_good:.1f}%", delta=None)
            with col4:
                st.metric("Дундаж дунд", f"{avg_medium:.1f}%", delta=None)
            
            # Charts section
            if show_charts:
                st.markdown("---")
                st.markdown("### 📈 График дүрслэл")
                
                # Get average data
                avg_data = result_df[result_df['Үзүүлэлт'] == '--- ДУНДАЖ ---'].copy()
                detail_data = result_df[result_df['Үзүүлэлт'] != '--- ДУНДАЖ ---'].copy()
                
                # Chart 1: Overall Average Distribution (Pie Chart)
                if chart_type in ["Бүгд", "Нийтлэг тойм"]:
                    st.markdown("#### 🥧 Нийт үнэлгээний хуваарилалт")
                    
                    overall_avg = {
                        'Төрөл': ['Сайн', 'Дунд', 'Муу'],
                        'Хувь': [avg_good, avg_medium, 100 - avg_good - avg_medium]
                    }
                    
                    fig_pie = px.pie(
                        overall_avg,
                        values='Хувь',
                        names='Төрөл',
                        color='Төрөл',
                        color_discrete_map={'Сайн': '#2ecc71', 'Дунд': '#f39c12', 'Муу': '#e74c3c'}
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # Chart 2: Teacher Comparison (Bar Chart)
                if chart_type in ["Бүгд", "Багшаар", "Харьцуулалт"]:
                    st.markdown("#### 📊 Багш бүрийн дундаж үнэлгээ")
                    
                    fig_bar = go.Figure()
                    fig_bar.add_trace(go.Bar(
                        name='Сайн',
                        x=avg_data['Багшийн нэр'],
                        y=avg_data['Сайн (%)'],
                        marker_color='#2ecc71'
                    ))
                    fig_bar.add_trace(go.Bar(
                        name='Дунд',
                        x=avg_data['Багшийн нэр'],
                        y=avg_data['Дунд (%)'],
                        marker_color='#f39c12'
                    ))
                    fig_bar.add_trace(go.Bar(
                        name='Муу',
                        x=avg_data['Багшийн нэр'],
                        y=avg_data['Муу (%)'],
                        marker_color='#e74c3c'
                    ))
                    
                    fig_bar.update_layout(
                        barmode='stack',
                        xaxis_title="Багш",
                        yaxis_title="Хувь (%)",
                        legend_title="Үнэлгээ",
                        height=500
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                # Chart 3: Top/Bottom Teachers by Good Rating
                if chart_type in ["Бүгд", "Харьцуулалт"]:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🏆 Шилдэг 5 багш (Сайн үнэлгээгээр)")
                        top_teachers = avg_data.nlargest(5, 'Сайн (%)')
                        
                        fig_top = px.bar(
                            top_teachers,
                            x='Сайн (%)',
                            y='Багшийн нэр',
                            orientation='h',
                            color='Сайн (%)',
                            color_continuous_scale='Greens',
                            text='Сайн (%)'
                        )
                        fig_top.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig_top.update_layout(height=400, showlegend=False)
                        st.plotly_chart(fig_top, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### ⚠️ Анхаарал хандуулах 5 багш (Муу үнэлгээгээр)")
                        bottom_teachers = avg_data.nlargest(5, 'Муу (%)')
                        
                        fig_bottom = px.bar(
                            bottom_teachers,
                            x='Муу (%)',
                            y='Багшийн нэр',
                            orientation='h',
                            color='Муу (%)',
                            color_continuous_scale='Reds',
                            text='Муу (%)'
                        )
                        fig_bottom.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig_bottom.update_layout(height=400, showlegend=False)
                        st.plotly_chart(fig_bottom, use_container_width=True)
                
                # Chart 4: Detailed view by teacher (if specific teacher selected)
                if chart_type in ["Бүгд", "Багшаар"]:
                    st.markdown("#### 🔍 Багш бүрийн дэлгэрэнгүй үзүүлэлт")
                    
                    selected_teacher = st.selectbox(
                        "Багш сонгох:",
                        options=avg_data['Багшийн нэр'].tolist()
                    )
                    
                    teacher_detail = detail_data[detail_data['Багшийн нэр'] == selected_teacher]
                    
                    fig_detail = go.Figure()
                    fig_detail.add_trace(go.Bar(
                        name='Сайн',
                        x=teacher_detail['Үзүүлэлт'],
                        y=teacher_detail['Сайн (%)'],
                        marker_color='#2ecc71'
                    ))
                    fig_detail.add_trace(go.Bar(
                        name='Дунд',
                        x=teacher_detail['Үзүүлэлт'],
                        y=teacher_detail['Дунд (%)'],
                        marker_color='#f39c12'
                    ))
                    fig_detail.add_trace(go.Bar(
                        name='Муу',
                        x=teacher_detail['Үзүүлэлт'],
                        y=teacher_detail['Муу (%)'],
                        marker_color='#e74c3c'
                    ))
                    
                    fig_detail.update_layout(
                        barmode='group',
                        xaxis_title="Үзүүлэлт",
                        yaxis_title="Хувь (%)",
                        height=500,
                        xaxis={'tickangle': -45}
                    )
                    st.plotly_chart(fig_detail, use_container_width=True)
            
            # Display results table
            st.markdown("---")
            st.markdown("### 📋 Дэлгэрэнгүй хүснэгт")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                filter_teacher = st.multiselect(
                    "Багш шүүх:",
                    options=result_df['Багшийн нэр'].unique().tolist(),
                    default=result_df['Багшийн нэр'].unique().tolist()
                )
            with col2:
                show_avg_only = st.checkbox("Зөвхөн дундаж харуулах", value=False)
            
            # Apply filters
            filtered_df = result_df[result_df['Багшийн нэр'].isin(filter_teacher)]
            if show_avg_only:
                filtered_df = filtered_df[filtered_df['Үзүүлэлт'] == '--- ДУНДАЖ ---']
            
            # Color coding function
            def highlight_rows(row):
                if row['Үзүүлэлт'] == '--- ДУНДАЖ ---':
                    return ['background-color: #f0f0f0; font-weight: bold'] * len(row)
                return [''] * len(row)
            
            st.dataframe(
                filtered_df.style.apply(highlight_rows, axis=1),
                use_container_width=True,
                height=400
            )
            
            # Download section
            st.markdown("---")
            st.markdown("### 💾 Үр дүн татаж авах")
            
            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                result_df.to_excel(writer, index=False, sheet_name='Бүх үр дүн')
                avg_data.to_excel(writer, index=False, sheet_name='Дундаж үнэлгээ')
            excel_data = output.getvalue()
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Excel файл татах (График агуулсан)",
                    data=excel_data,
                    file_name="Teacher_Evaluation_Results_Full.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
        else:
            st.warning("⚠️ Өгөгдөл олдсонгүй. Файлын формат зөв эсэхийг шалгана уу.")
            
    except Exception as e:
        st.error(f"❌ Алдаа гарлаа: {str(e)}")
        st.info("Файлын encoding-г шалгаарай. UTF-8 байх ёстой.")
else:
    # Welcome message
    st.info("👈 Эхлэхийн тулд зүүн талд байрлах CSV файл оруулна уу")
    
    st.markdown("### 📝 Файлын формат")
    st.markdown("""
    Файл дараах форматтай байх ёстой:
    - Google Forms-оос экспорт хийсэн CSV файл
    - Баганы нэр: `Багшийн нэр [Үзүүлэлт]` форматтай
    - Хариултууд: "Сайн", "Маш сайн", "Дунд", "Муу", "Мэдэхгүй" гэх мэт
    
    ### 📊 График боломжууд:
    - 🥧 Нийт үнэлгээний хуваарилалт
    - 📊 Багш бүрийн харьцуулалт
    - 🏆 Шилдэг багш нар
    - 🔍 Багш бүрийн дэлгэрэнгүй үзүүлэлт
    """)
    
    # Demo/Example
    with st.expander("🎨 График жишээ харах"):
        st.markdown("Файл оруулсны дараа дараах графикууд харагдана:")
        st.markdown("- Интерактив багана график")
        st.markdown("- Дугуй график (Pie chart)")
        st.markdown("- Харьцуулалтын график")
        st.markdown("- Багш бүрийн дэлгэрэнгүй шинжилгээ")
