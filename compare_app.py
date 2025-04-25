
import streamlit as st
import pandas as pd
from datetime import date

# 登录验证
st.set_page_config(page_title="原材料比价系统", layout="wide")
st.title("🔐 原材料比价系统")
password = st.text_input("请输入访问密码", type="password")
if password != "abc123":
    st.warning("密码错误，或尚未输入密码")
    st.stop()

st.success("✅ 登录成功！欢迎使用原材料比价系统")

# 数据读取
try:
    projects = pd.read_csv("projects.csv")
    products = pd.read_csv("products.csv")
    quotes = pd.read_csv("quotes.csv")
except Exception as e:
    st.error(f"❌ 数据读取失败：{e}")
    st.stop()

# 页面分区
tab1, tab2, tab3, tab4 = st.tabs(["📁 项目管理", "📦 商品管理", "🧾 商品报价", "📊 比价分析"])

# 项目管理
with tab1:
    st.subheader("📁 所有项目")
    st.dataframe(projects, use_container_width=True)

    st.markdown("### ➕ 添加项目")
    with st.form("add_project"):
        name = st.text_input("项目名称")
        qdate = st.date_input("询价日期", value=date.today())
        submit = st.form_submit_button("✅ 添加")
        if submit and name:
            new_id = projects["项目ID"].max() + 1 if not projects.empty else 1
            new_row = pd.DataFrame([[new_id, name, qdate, str(date.today())]], columns=projects.columns)
            projects = pd.concat([projects, new_row], ignore_index=True)
            projects.to_csv("projects.csv", index=False)
            st.experimental_rerun()

# 商品管理
with tab2:
    st.subheader("📦 商品库")
    st.dataframe(products, use_container_width=True)

    st.markdown("### ➕ 添加商品")
    with st.form("add_product"):
        name = st.text_input("品名")
        spec = st.text_input("规格")
        unit = st.text_input("单位")
        limit = st.number_input("限价", min_value=0.01)
        cat = st.selectbox("类别", ["蔬菜", "水果", "肉制品", "水产", "副食", "调料"])
        go = st.form_submit_button("✅ 添加")
        if go:
            if name in products["品名"].values:
                st.error("该品名已存在，请勿重复添加")
            else:
                new_id = products["商品ID"].max() + 1 if not products.empty else 1
                new_row = pd.DataFrame([[new_id, name, spec, unit, limit, cat]], columns=products.columns)
                products = pd.concat([products, new_row], ignore_index=True)
                products.to_csv("products.csv", index=False)
                st.experimental_rerun()

# 商品报价
with tab3:
    st.subheader("🧾 项目商品报价")
    if projects.empty or products.empty:
        st.info("请先录入项目和商品")
    else:
        pid = st.selectbox("选择项目", projects["项目名称"])
        proj_id = projects[projects["项目名称"] == pid]["项目ID"].values[0]

        st.markdown("### 📄 当前项目商品报价：")
        q_this = quotes[quotes["项目ID"] == proj_id].merge(products, on="商品ID", how="left")
        st.dataframe(q_this[["品名", "规格", "单位", "价格"]], use_container_width=True)

        with st.form("add_quote"):
            pname = st.selectbox("选择商品", products["品名"])
            prod_id = products[products["品名"] == pname]["商品ID"].values[0]
            price = st.number_input("本次报价", min_value=0.01)
            ok = st.form_submit_button("✅ 添加报价")
            if ok:
                new_row = pd.DataFrame([[proj_id, prod_id, price]], columns=quotes.columns)
                quotes = pd.concat([quotes, new_row], ignore_index=True)
                quotes.to_csv("quotes.csv", index=False)
                st.experimental_rerun()

# 项目比价
with tab4:
    st.subheader("📊 项目间比价分析")
    if len(projects) < 2:
        st.info("至少需要两个项目进行比价")
    else:
        col1, col2 = st.columns(2)
        p1 = col1.selectbox("项目 A", projects["项目名称"], index=0)
        p2 = col2.selectbox("项目 B", projects["项目名称"], index=1)
        id1 = projects[projects["项目名称"] == p1]["项目ID"].values[0]
        id2 = projects[projects["项目名称"] == p2]["项目ID"].values[0]
        q1 = quotes[quotes["项目ID"] == id1].set_index("商品ID")["价格"]
        q2 = quotes[quotes["项目ID"] == id2].set_index("商品ID")["价格"]
        all_ids = sorted(set(q1.index) | set(q2.index))

        rows = []
        for sid in all_ids:
            name = products[products["商品ID"] == sid]["品名"].values[0]
            p_old = q1.get(sid, None)
            p_new = q2.get(sid, None)
            if pd.isna(p_old): status = "新增"
            elif pd.isna(p_new): status = "未报价"
            else:
                status = "↑" if p_new > p_old else "↓" if p_new < p_old else "→"
            diff = (p_new - p_old) if p_old and p_new else None
            pct = (diff / p_old * 100) if diff and p_old else None
            rows.append([name, p_old, p_new, diff, pct, status])
        df = pd.DataFrame(rows, columns=["品名", "项目A", "项目B", "涨跌额", "涨跌幅%", "状态"])
        st.dataframe(df, use_container_width=True)
