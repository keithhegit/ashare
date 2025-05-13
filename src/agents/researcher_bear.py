from langchain_core.messages import HumanMessage
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction
import json
import ast


@agent_endpoint("researcher_bear", "空方研究员，从看空角度分析市场数据并提出风险警示")
def researcher_bear_agent(state: AgentState):
    """Analyzes signals from a bearish perspective and generates cautionary investment thesis."""
    show_workflow_status("Bearish Researcher")
    show_reasoning = state["metadata"]["show_reasoning"]

    # Fetch messages from analysts
    technical_message = next(
        msg for msg in state["messages"] if msg.name == "technical_analyst_agent")
    fundamentals_message = next(
        msg for msg in state["messages"] if msg.name == "fundamentals_agent")
    sentiment_message = next(
        msg for msg in state["messages"] if msg.name == "sentiment_agent")
    valuation_message = next(
        msg for msg in state["messages"] if msg.name == "valuation_agent")

    try:
        fundamental_signals = json.loads(fundamentals_message.content)
        technical_signals = json.loads(technical_message.content)
        sentiment_signals = json.loads(sentiment_message.content)
        valuation_signals = json.loads(valuation_message.content)
    except Exception as e:
        fundamental_signals = ast.literal_eval(fundamentals_message.content)
        technical_signals = ast.literal_eval(technical_message.content)
        sentiment_signals = ast.literal_eval(sentiment_message.content)
        valuation_signals = ast.literal_eval(valuation_message.content)

    # 兼容中英文key
    def get_signal(obj):
        return obj.get("signal") or obj.get("技术信号")
    def get_confidence(obj):
        v = obj.get("confidence") or obj.get("置信度")
        if isinstance(v, str) and v.endswith('%'):
            return float(v.replace('%',''))/100
        try:
            return float(v)
        except:
            return 0.0
    def get_thesis_points(obj):
        return obj.get("thesis_points") or obj.get("空方论点") or []

    # Analyze from bearish perspective
    bearish_points = []
    confidence_scores = []

    # Technical Analysis
    if get_signal(technical_signals) == "bearish" or get_signal(technical_signals) == "看空":
        bearish_points.append(
            f"技术指标显示看空动能，置信度{get_confidence(technical_signals):.0%}")
        confidence_scores.append(get_confidence(technical_signals))
    else:
        bearish_points.append("技术反弹或为暂时，存在回调风险")
        confidence_scores.append(0.3)

    # Fundamental Analysis
    if get_signal(fundamental_signals) == "bearish" or get_signal(fundamental_signals) == "看空":
        bearish_points.append(
            f"基本面存在隐忧，置信度{get_confidence(fundamental_signals):.0%}")
        confidence_scores.append(get_confidence(fundamental_signals))
    else:
        bearish_points.append("当前基本面强劲或难以持续")
        confidence_scores.append(0.3)

    # Sentiment Analysis
    if get_signal(sentiment_signals) == "bearish" or get_signal(sentiment_signals) == "看空":
        bearish_points.append(
            f"市场情绪消极，置信度{get_confidence(sentiment_signals):.0%}")
        confidence_scores.append(get_confidence(sentiment_signals))
    else:
        bearish_points.append("市场情绪过于乐观，存在风险")
        confidence_scores.append(0.3)

    # Valuation Analysis
    if get_signal(valuation_signals) == "bearish" or get_signal(valuation_signals) == "看空":
        bearish_points.append(
            f"估值偏高，置信度{get_confidence(valuation_signals):.0%}")
        confidence_scores.append(get_confidence(valuation_signals))
    else:
        bearish_points.append("当前估值未充分反映下行风险")
        confidence_scores.append(0.3)

    # Calculate overall bearish confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores)

    # 中文结构化输出
    message_content = {
        "研究视角": "空方",
        "置信度": f"{avg_confidence:.0%}",
        "空方论点": bearish_points,
        "分析说明": "基于技术面、基本面、情感面和估值等多维度综合分析，提出空方风险警示。"
    }

    message = HumanMessage(
        content=json.dumps(message_content),
        name="researcher_bear_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "Bearish Researcher")
        # 保存推理信息到metadata供API使用
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Bearish Researcher", "completed")
    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
        "metadata": state["metadata"],
    }
