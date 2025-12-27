import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import base64

# ====================== 全局配置：自定义背景+UI样式 ======================
def set_page_background():
    st.sidebar.header("🎨 自定义背景设置")
    # 背景类型选择
    bg_type = st.sidebar.radio("背景类型", ["纯色背景", "本地图片", "在线图片链接"])
    
    # 1. 纯色背景
    if bg_type == "纯色背景":
        bg_color = st.sidebar.color_picker("选择背景色", "#f0f8ff")  # 浅蓝默认
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-color: {bg_color};
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    
    # 2. 本地图片背景
    elif bg_type == "本地图片":
        uploaded_bg = st.sidebar.file_uploader("上传背景图片", type=["png", "jpg", "jpeg"])
        if uploaded_bg:
            bg_base64 = base64.b64encode(uploaded_bg.read()).decode()
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{bg_base64}");
                    background-size: cover;  /* 拉伸铺满 */
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
                .stApp > div {{
                    background-color: rgba(255,255,255,0.85);  /* 内容区半透明 */
                    padding: 20px;
                    border-radius: 10px;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )
    
    # 3. 在线图片链接
    else:
        bg_url = st.sidebar.text_input("输入背景图片链接", placeholder="https://xxx.jpg")
        if bg_url:
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background-image: url("{bg_url}");
                    background-size: cover;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
                .stApp > div {{
                    background-color: rgba(255,255,255,0.85);
                    padding: 20px;
                    border-radius: 10px;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

# 页面基础配置
st.set_page_config(page_title="课程表工具·简约版", page_icon="📚", layout="wide")
# 设置背景
set_page_background()

# ====================== 核心功能代码（与原功能一致） ======================
# 1. 初始化数据
COURSE_COLUMNS = ["课程名称", "星期", "开始时间", "结束时间", "教室", "任课老师"]
if "courses" not in st.session_state:
    st.session_state.courses = pd.DataFrame(columns=COURSE_COLUMNS)

# 2. 辅助函数（冲突检测/提醒/推荐）
def check_conflict(new_course, existing_courses):
    same_weekday = existing_courses[existing_courses["星期"] == new_course["星期"]]
    if same_weekday.empty:
        return False, None
    def str_to_time(time_str):
        return datetime.strptime(time_str, "%H:%M").time()
    new_start = str_to_time(new_course["开始时间"])
    new_end = str_to_time(new_course["结束时间"])
    for _, course in same_weekday.iterrows():
        exist_start = str_to_time(course["开始时间"])
        exist_end = str_to_time(course["结束时间"])
        if new_start < exist_end and new_end > exist_start:
            return True, course["课程名称"]
    return False, None

def recommend_materials(course_name):
    material_map = {
        "Python": ["Python官方文档: https://docs.python.org", "菜鸟教程Python: https://www.runoob.com/python"],
        "人工智能": ["李沐《动手学深度学习》: https://zh.d2l.ai", "吴恩达AI课程: https://www.coursera.org/specializations/ai-for-everyone"],
        "数据结构": ["数据结构与算法分析: https://book.douban.com/subject/1139426/", "LeetCode刷题指南: https://leetcode.cn"],
        "高数": ["同济高数教材: https://www.tongji.edu.cn", "高数网课: https://www.bilibili.com/video/BV1YT411g7br"]
    }
    for keyword, materials in material_map.items():
        if keyword in course_name:
            return materials
    return ["暂无匹配的学习资料，可自行添加~"]

def get_upcoming_courses(courses):
    if courses.empty:
        return []
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz).time()
    now_plus_15 = (datetime.combine(datetime.today(), now) + timedelta(minutes=15)).time()
    upcoming = []
    weekday_map = {1:"周一", 2:"周二", 3:"周三", 4:"周四", 5:"周五", 6:"周六", 7:"周日"}
    today_weekday = weekday_map[datetime.now(tz).weekday() + 1]
    today_courses = courses[courses["星期"] == today_weekday]
    for _, course in today_courses.iterrows():
        course_start = datetime.strptime(course["开始时间"], "%H:%M").time()
        if now <= course_start <= now_plus_15:
            upcoming.append(course)
    return upcoming

def validate_course_csv(csv_df):
    if list(csv_df.columns) != COURSE_COLUMNS:
        return False, f"CSV列名不匹配！要求：{COURSE_COLUMNS}"
    if csv_df.isnull().any().any():
        empty_cols = [col for col in COURSE_COLUMNS if csv_df[col].isnull().any()]
        return False, f"空值列：{empty_cols}"
    def check_time_format(time_str):
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except:
            return False
    invalid_start = csv_df[~csv_df["开始时间"].apply(check_time_format)]["课程名称"].tolist()
    invalid_end = csv_df[~csv_df["结束时间"].apply(check_time_format)]["课程名称"].tolist()
    if invalid_start or invalid_end:
        return False, f"时间格式错误：{invalid_start + invalid_end}"
    valid_weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    invalid_weekday = csv_df[~csv_df["星期"].isin(valid_weekdays)]["课程名称"].tolist()
    if invalid_weekday:
        return False, f"星期错误：{invalid_weekday}"
    return True, csv_df

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False, encoding="utf-8-sig")

# ====================== UI布局：顶部标签页（简约风核心） ======================
st.title("📚 校园课程表智能提醒工具 · 简约清新版")
# 顶部标签页：导入/手动添加/提醒/课程表
tab1, tab2, tab3, tab4 = st.tabs(["📤 CSV批量导入", "✏️ 手动添加课程", "🔔 近期提醒", "📋 我的课程表"])

# 标签1：CSV导入
with tab1:
    st.subheader("CSV课程表批量导入")
    st.info("📌 标准模板格式（列名：课程名称、星期、开始时间、结束时间、教室、任课老师）")
    template_df = pd.DataFrame([
        ["Python程序设计", "周一", "08:00", "09:40", "教学楼A101", "张老师"],
        ["人工智能导论", "周三", "14:00", "15:40", "实验楼B202", "李老师"]
    ], columns=COURSE_COLUMNS)
    st.dataframe(template_df, use_container_width=True)
    template_csv = convert_df_to_csv(template_df)
    st.download_button("📥 下载CSV模板", data=template_csv, file_name="课程表模板.csv", mime="text/csv")
    
    uploaded_csv = st.file_uploader("选择CSV文件", type=["csv"])
    if uploaded_csv is not None:
        try:
            csv_df = pd.read_csv(uploaded_csv, encoding="utf-8-sig")
            is_valid, result = validate_course_csv(csv_df)
            if not is_valid:
                st.error(f"校验失败：{result}")
            else:
                conflict_courses = []
                valid_courses = []
                for _, row in result.iterrows():
                    new_course = row.to_dict()
                    conflict, conflict_name = check_conflict(new_course, st.session_state.courses)
                    if conflict:
                        conflict_courses.append(f"{new_course['课程名称']}（与{conflict_name}冲突）")
                    else:
                        valid_courses.append(new_course)
                if conflict_courses:
                    st.warning(f"冲突课程未导入：{conflict_courses}")
                if valid_courses:
                    valid_df = pd.DataFrame(valid_courses)
                    st.session_state.courses = pd.concat([st.session_state.courses, valid_df], ignore_index=True)
                    st.success(f"✅ 成功导入{len(valid_df)}门课程！")
                    st.dataframe(valid_df, use_container_width=True)
        except Exception as e:
            st.error(f"读取失败：{str(e)}")

# 标签2：手动添加
with tab2:
    st.subheader("手动添加课程信息")
    # 分栏布局：左右两列
    col1, col2 = st.columns(2)
    with col1:
        course_name = st.text_input("课程名称")
        weekday = st.selectbox("星期", ["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
        start_time = st.text_input("开始时间（HH:MM）", placeholder="08:00")
    with col2:
        end_time = st.text_input("结束时间（HH:MM）", placeholder="09:40")
        classroom = st.text_input("教室")
        teacher = st.text_input("任课老师")
    
    if st.button("✅ 添加课程", type="primary"):
        if not all([course_name, weekday, start_time, end_time, classroom, teacher]):
            st.error("请填写所有信息！")
        else:
            new_course = {
                "课程名称": course_name, "星期": weekday, "开始时间": start_time,
                "结束时间": end_time, "教室": classroom, "任课老师": teacher
            }
            conflict, conflict_course = check_conflict(new_course, st.session_state.courses)
            if conflict:
                st.error(f"⚠️ 时间冲突！已有课程：{conflict_course}")
            else:
                new_row = pd.DataFrame([new_course])
                st.session_state.courses = pd.concat([st.session_state.courses, new_row], ignore_index=True)
                st.success("✅ 课程添加成功！")

# 标签3：近期提醒
with tab3:
    st.subheader("近期课程提醒")
    upcoming_courses = get_upcoming_courses(st.session_state.courses)
    if upcoming_courses:
        st.warning("接下来15分钟即将开始的课程：")
        for course in upcoming_courses:
            # 卡片式展示
            st.markdown(
                f"""
                <div style="background-color: #e8f4f8; padding: 10px; border-radius: 8px; margin: 5px 0;">
                📖 <b>{course['课程名称']}</b> | 时间：{course['开始时间']}-{course['结束时间']} | 教室：{course['教室']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("暂无近期课程，放心学习~")

# 标签4：我的课程表
with tab4:
    st.subheader("我的课程表")
    if not st.session_state.courses.empty:
        st.dataframe(st.session_state.courses, use_container_width=True)
        selected_course = st.selectbox("选择课程查看推荐资料", st.session_state.courses["课程名称"].unique())
        if selected_course:
            st.subheader("📚 学习资料推荐")
            materials = recommend_materials(selected_course)
            for idx, material in enumerate(materials, 1):
                st.write(f"{idx}. {material}")
    else:
        st.info("还未添加任何课程，请通过CSV导入或手动添加~")
    
    if st.button("🗑️ 清空课程表", type="secondary"):
        st.session_state.courses = pd.DataFrame(columns=COURSE_COLUMNS)
        st.success("课程表已清空！")