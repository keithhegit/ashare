import streamlit as st
import requests
import time

st.set_page_config(page_title="A股智能投研助手", page_icon=":chart_with_upwards_trend:")

st.title("A股智能投研助手")
st.markdown("请输入A股股票代码（如 301312），点击开始分析。")

# 用户输入
stock_code = st.text_input("股票代码", max_chars=10, help="请输入6位A股代码，如301312")
show_reasoning = st.checkbox("显示详细推理过程", value=False)

if 'run_id' not in st.session_state:
    st.session_state['run_id'] = None
if 'analysis_result' not in st.session_state:
    st.session_state['analysis_result'] = None
if 'show_reasoning' not in st.session_state:
    st.session_state['show_reasoning'] = False
if 'debug_logs' not in st.session_state:
    st.session_state['debug_logs'] = []

def log_debug(msg):
    timestamp = time.strftime('%H:%M:%S')
    st.session_state['debug_logs'].append(f"[{timestamp}] {msg}")

if st.button("开始分析") and stock_code:
    # 启动分析任务
    with st.spinner("正在提交分析任务..."):
        try:
            log_debug(f"请求: POST /api/analysis/start, 参数: ticker={stock_code}, show_reasoning={show_reasoning}")
            resp = requests.post(
                "http://localhost:8000/api/analysis/start",
                json={"ticker": stock_code, "show_reasoning": show_reasoning}
            )
            log_debug(f"响应: {resp.status_code}, 内容: {resp.text}")
        except Exception as e:
            log_debug(f"异常: 启动分析任务时无法连接后端服务: {e}")
            st.error(f"无法连接后端服务: {e}")
            st.stop()
    if resp.status_code == 200 and resp.json().get("success"):
        run_id = resp.json()["data"]["run_id"]
        st.session_state['run_id'] = run_id
        st.session_state['analysis_result'] = None
        log_debug(f"分析任务已启动，任务ID: {run_id}")
        st.success(f"分析任务已启动，任务ID: {run_id}")
    else:
        log_debug(f"分析任务启动失败，响应: {resp.status_code}, 内容: {resp.text}")
        st.error("分析任务启动失败，请检查股票代码或后端服务。")
        st.stop()

# 轮询进度
if st.session_state.get('run_id') and not st.session_state.get('analysis_result'):
    run_id = st.session_state['run_id']
    progress_bar = st.progress(0, text="分析进行中，请稍候...")
    status = "running"
    for i in range(100):
        time.sleep(1.5)
        try:
            log_debug(f"请求: GET /api/analysis/{run_id}/status")
            status_resp = requests.get(f"http://localhost:8000/api/analysis/{run_id}/status")
            log_debug(f"响应: {status_resp.status_code}, 内容: {status_resp.text}")
        except Exception as e:
            log_debug(f"异常: 获取任务状态时出错: {e}")
            st.warning(f"无法获取任务状态: {e}")
            continue
        if status_resp.status_code == 200:
            status_data = status_resp.json().get("data", {})
            status = status_data.get("status", "running")
            log_debug(f"轮询状态: {status}")
            if status == "completed":
                progress_bar.progress(100, text="分析完成！")
                break
            elif status == "failed":
                log_debug("分析失败，任务状态为failed")
                st.error("分析失败，请重试。")
                st.session_state['run_id'] = None
                st.stop()
            else:
                progress_bar.progress(min(i+1, 99), text=f"分析进行中...（状态：{status}）")
        else:
            log_debug(f"获取任务状态失败，响应: {status_resp.status_code}, 内容: {status_resp.text}")
            st.warning("无法获取任务状态，正在重试...")
    # 获取结果
    try:
        log_debug(f"请求: GET /api/analysis/{run_id}/result")
        result_resp = requests.get(f"http://localhost:8000/api/analysis/{run_id}/result")
        log_debug(f"响应: {result_resp.status_code}, 内容: {result_resp.text}")
    except Exception as e:
        log_debug(f"异常: 获取分析结果时出错: {e}")
        st.error(f"未能获取分析结果: {e}")
        st.session_state['run_id'] = None
        st.stop()
    if result_resp.status_code == 200 and result_resp.json().get("data"):
        st.session_state['analysis_result'] = result_resp.json()["data"]
        log_debug("成功获取分析结果")
    else:
        log_debug(f"未能获取分析结果，响应: {result_resp.status_code}, 内容: {result_resp.text}")
        st.error("未能获取分析结果，请稍后重试。")
        st.session_state['run_id'] = None
        st.stop()

# 展示结果
if st.session_state.get('analysis_result'):
    result = st.session_state['analysis_result']
    st.header("投资决策")
    st.json(result.get("final_decision", {}))

    st.header("多智能体分析结果")
    for agent, agent_result in result.get("agent_results", {}).items():
        with st.expander(f"{agent} 分析结果", expanded=False):
            st.json(agent_result)

    # 详细推理（可选项，默认折叠）
    if st.session_state.get('show_reasoning') or show_reasoning:
        with st.expander("详细推理过程", expanded=True):
            for agent, agent_result in result.get("agent_results", {}).items():
                st.subheader(f"{agent} 推理")
                st.write(agent_result.get("reasoning", "无详细推理信息"))
    else:
        if st.button("查看详细推理过程"):
            st.session_state['show_reasoning'] = True
            st.rerun()

# 调试日志区域
with st.expander("调试日志", expanded=False):
    for log in st.session_state['debug_logs']:
        st.write(log) 