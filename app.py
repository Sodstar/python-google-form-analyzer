import streamlit as st
import pandas as pd
import re
from io import BytesIO

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
st.sidebar.markdown("### Заавар")
st.sidebar.info(
    """
    1. CSV файлаа сонгоно уу
    2. Өгөгдөл автоматаар боловсруулагдана
    3. Үр дүнг харна уу
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
            
            # Display results
            st.markdown("### 📈 Үр дүн")
            st.dataframe(result_df, use_container_width=True, height=400)
            
            # Download button
            st.markdown("### 💾 Үр дүн татаж авах")
            
            # Convert to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                result_df.to_excel(writer, index=False, sheet_name='Үр дүн')
            excel_data = output.getvalue()
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 Excel файл татах",
                    data=excel_data,
                    file_name="Teacher_Evaluation_Results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # Statistics
            st.markdown("---")
            st.markdown("### 📊 Статистик")
            col1, col2, col3 = st.columns(3)
            
            teachers_count = result_df[result_df['Үзүүлэлт'] != '--- ДУНДАЖ ---']['Багшийн нэр'].nunique()
            total_responses = result_df[result_df['Үзүүлэлт'] != '--- ДУНДАЖ ---']['Үнэлсэн тоо'].sum()
            
            with col1:
                st.metric("Нийт багш", teachers_count)
            with col2:
                st.metric("Нийт үнэлгээ", int(total_responses))
            with col3:
                avg_good = result_df[result_df['Үзүүлэлт'] == '--- ДУНДАЖ ---']['Сайн (%)'].mean()
                st.metric("Дундаж сайн үнэлгээ", f"{avg_good:.1f}%")
                
        else:
            st.warning("⚠️ Өгөгдөл олдсонгүй. Файлын формат зөв эсэхийг шалгана уу.")
            
    except Exception as e:
        st.error(f"❌ Алдаа гарлаа: {str(e)}")
        st.info("Файлын encoding-г шалгаарай. UTF-8 байх ёстой.")
else:
    # Welcome message
    st.info("👈 Эхлэхийн тулд зүүн талд байрлах CSV файл оруулна уу")
    
    st.markdown("### Файлын формат")
    st.markdown("""
    Файл дараах форматтай байх ёстой:
    - Google Forms-оос экспорт хийсэн CSV файл
    - Баганы нэр: `Багшийн нэр [Үзүүлэлт]` форматтай
    - Хариултууд: "Сайн", "Маш сайн", "Дунд", "Муу", "Мэдэхгүй" гэх мэт
    """);