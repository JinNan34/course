import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 设置页面配置
st.set_page_config(page_title="校园课程表智能提醒工具", page_icon="📚", layout="wide")

# ---------------------- 1. 初始化数据 ----------------------
# 定义课程表的列名
COURSE_COLUMNS = ["课程名称", "星期", "开始时间", "结束时间", "教室", "任课老师"]
# 初始化会话状态，存储课表数据
if "courses" not in st.session_state:
    st.session_state.courses = pd.DataFrame(columns=COURSE_COLUMNS)

# ---------------------- 2. 辅助函数（AI核心逻辑） ----------------------
def check_conflict(new_course, existing_courses):
    """
    AI课程冲突检测：检查新添加的课程是否与已有课程时间冲突
    """
    # 筛选同一星期的课程
    same_weekday = existing_courses[existing_courses["星期"] == new_course["星期"]]
    if same_weekday.empty:
        return False
    
    # 转换时间为datetime格式，便于对比
    def str_to_time(time_str):
        return datetime.strptime(time_str, "%H:%M").time()
    
    new_start = str_to_time(new_course["开始时间"])
    new_end = str_to_time(new_course["结束时间"])
    
    # 遍历同一星期的课程，检测时间重叠
    for _, course in same_weekday.iterrows():
        exist_start = str_to_time(course["开始时间"])
        exist_end = str_to_time(course["结束时间"])
        # 时间重叠判定规则：新课程开始时间 < 已有课程结束时间，且新课程结束时间 > 已有课程开始时间
        if new_start < exist_end and new_end > exist_start:
            return True, course["课程名称"]
    return False, None

def recommend_materials(course_name):
    """
    AI学习资料推荐：基于课程名称关键词匹配推荐资料（模拟AI推荐逻辑）
    """
    # 关键词-资料映射（可扩展）
    material_map = {
        "Python": ["Python官方文档: https://docs.python.org", "菜鸟教程Python: https://www.runoob.com/python"],
        "人工智能": ["李沐《动手学深度学习》: https://zh.d2l.ai", "吴恩达AI课程: https://www.coursera.org/specializations/ai-for-everyone"],
        "数据结构": ["数据结构与算法分析: https://book.douban.com/subject/1139426/", "LeetCode刷题指南: https://leetcode.cn"],
        "高数": ["同济高数教材: https://www.math同济.edu.cn", "高数网课: https://www.bilibili.com/video/BV1YT411g7br"]
    }
    # 遍历关键词，匹配课程名称
    for keyword, materials in material_map.items():
        if keyword in course_name:
            return materials
    return ["暂无匹配的学习资料，可自行添加~"]

def get_upcoming_courses(courses):
    """
    智能课程提醒：获取接下来15分钟内要开始的课程
    """
    if courses.empty:
        return []
    # 设置时区（避免时间偏移）
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz).time()
    # 计算15分钟后的时间
    now_plus_15 = (datetime.combine(datetime.today(), now) + timedelta(minutes=15)).time()
    
    upcoming = []
    # 获取今天的星期（1-7，对应周一到周日）
    weekday_map = {1:"周一", 2:"周二", 3:"周三", 4:"周四", 5:"周五", 6:"周六", 7:"周日"}
    today_weekday = weekday_map[datetime.now(tz).weekday() + 1]
    
    # 筛选今天的课程
    today_courses = courses[courses["星期"] == today_weekday]
    for _, course in today_courses.iterrows():
        course_start = datetime.strptime(course["开始时间"], "%H:%M").time()
        # 判定：课程开始时间在当前时间到15分钟后之间
        if now <= course_start <= now_plus_15:
            upcoming.append(course)
    return upcoming

# ---------------------- 3. 页面布局与交互 ----------------------
st.title("📚 校园课程表智能提醒工具")

# 侧边栏：课表录入
with st.sidebar:
    st.header("添加课程信息")
    course_name = st.text_input("课程名称")
    weekday = st.selectbox("星期", ["周一", "周二", "周三", "周四", "周五", "周六", "周日"])
    start_time = st.text_input("开始时间（格式：HH:MM）", placeholder="如：08:00")
    end_time = st.text_input("结束时间（格式：HH:MM）", placeholder="如：09:40")
    classroom = st.text_input("教室")
    teacher = st.text_input("任课老师")
    
    # 提交课程按钮
    if st.button("添加课程"):
        # 基础校验
        if not all([course_name, weekday, start_time, end_time, classroom, teacher]):
            st.error("请填写所有课程信息！")
        else:
            # 构造新课程数据
            new_course = {
                "课程名称": course_name,
                "星期": weekday,
                "开始时间": start_time,
                "结束时间": end_time,
                "教室": classroom,
                "任课老师": teacher
            }
            # 检测冲突
            conflict, conflict_course = check_conflict(new_course, st.session_state.courses)
            if conflict:
                st.error(f"⚠️ 时间冲突！该时间段已有课程：{conflict_course}")
            else:
                # 添加新课程到会话状态
                new_row = pd.DataFrame([new_course])
                st.session_state.courses = pd.concat([st.session_state.courses, new_row], ignore_index=True)
                st.success("✅ 课程添加成功！")

# 主页面1：智能提醒
st.subheader("🔔 近期课程提醒")
upcoming_courses = get_upcoming_courses(st.session_state.courses)
if upcoming_courses:
    st.warning("接下来15分钟即将开始的课程：")
    for course in upcoming_courses:
        st.write(f"📖 {course['课程名称']} | 时间：{course['开始时间']}-{course['结束时间']} | 教室：{course['教室']}")
else:
    st.info("暂无近期课程，放心摸鱼~")

# 主页面2：课程表展示
st.subheader("📋 我的课程表")
if not st.session_state.courses.empty:
    st.dataframe(st.session_state.courses, use_container_width=True)
    
    # 学习资料推荐（选中课程后显示）
    selected_course = st.selectbox("选择课程查看推荐资料", st.session_state.courses["课程名称"].unique())
    if selected_course:
        st.subheader("📚 学习资料推荐")
        materials = recommend_materials(selected_course)
        for idx, material in enumerate(materials, 1):
            st.write(f"{idx}. {material}")
else:
    st.info("还未添加任何课程，请在侧边栏添加~")

# 清空课程表按钮
if st.button("清空课程表"):
    st.session_state.courses = pd.DataFrame(columns=COURSE_COLUMNS)
    st.success("课程表已清空！")