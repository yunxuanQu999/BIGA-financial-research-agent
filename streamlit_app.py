import streamlit as st

from workflow.router import classify_intent, run_agent_request


st.set_page_config(page_title="多智能体投研系统", layout="wide")

st.title("多智能体投研系统")
st.caption("LangGraph + RAG + Memory + Tool Calling")

with st.sidebar:
    user_id = st.text_input("用户 ID", value="default_user")
    company_name = st.text_input("公司名称（可选）", value="贵州茅台")
    st.markdown("示例：")
    st.code("分析 600519.SH\n今日哪些板块强？\n记住我持有半导体ETF，风险偏好中等")

query = st.text_area("输入任务", value="分析 600519.SH", height=120)

decision = classify_intent(query)
st.info(f"Planner Router: {decision.route} | {decision.reason}")

if st.button("运行分析", type="primary"):
    with st.spinner("Agent 工作流运行中..."):
        result = run_agent_request(query, user_id=user_id, company_name=company_name)
    st.subheader("输出结果")
    st.markdown(result)
