from langchain_core.messages import HumanMessage
from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction
import json
import ast


@agent_endpoint("researcher_bull", "多方研究员，从看多角度分析市场数据并提出投资论点")
def researcher_bull_agent(state: AgentState):
    """Analyzes signals from a bullish perspective and generates optimistic investment thesis."""
    show_workflow_status("Bullish Researcher")
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
        return obj.get("thesis_points") or obj.get("多方论点") or []

    # Analyze from bullish perspective
    bullish_points = []
    confidence_scores = []

    # Technical Analysis
    if get_signal(technical_signals) == "bullish" or get_signal(technical_signals) == "看多":
        bullish_points.append(
            f"技术指标显示看多动能，置信度{get_confidence(technical_signals):.0%}")
        confidence_scores.append(get_confidence(technical_signals))
    else:
        bullish_points.append("技术指标偏保守，或存在买入机会")
        confidence_scores.append(0.3)

    # Fundamental Analysis
    if get_signal(fundamental_signals) == "bullish" or get_signal(fundamental_signals) == "看多":
        bullish_points.append(
            f"基本面强劲，置信度{get_confidence(fundamental_signals):.0%}")
        confidence_scores.append(get_confidence(fundamental_signals))
    else:
        bullish_points.append("公司基本面有改善潜力")
        confidence_scores.append(0.3)

    # Sentiment Analysis
    if get_signal(sentiment_signals) == "bullish" or get_signal(sentiment_signals) == "看多":
        bullish_points.append(
            f"市场情绪积极，置信度{get_confidence(sentiment_signals):.0%}")
        confidence_scores.append(get_confidence(sentiment_signals))
    else:
        bullish_points.append("市场情绪偏悲观，或存在价值机会")
        confidence_scores.append(0.3)

    # Valuation Analysis
    if get_signal(valuation_signals) == "bullish" or get_signal(valuation_signals) == "看多":
        bullish_points.append(
            f"估值偏低，置信度{get_confidence(valuation_signals):.0%}")
        confidence_scores.append(get_confidence(valuation_signals))
    else:
        bullish_points.append("当前估值未充分反映成长潜力")
        confidence_scores.append(0.3)

    # Calculate overall bullish confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores)

    # 中文结构化输出
    message_content = {
        "研究视角": "多方",
        "置信度": f"{avg_confidence:.0%}",
        "多方论点": bullish_points,
        "分析说明": "基于技术面、基本面、情感面和估值等多维度综合分析，提出多方投资理由。"
    }

    message = HumanMessage(
        content=json.dumps(message_content),
        name="researcher_bull_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "Bullish Researcher")
        # 保存推理信息到metadata供API使用
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Bullish Researcher", "completed")
    return {
        "messages": state["messages"] + [message],
        "data": state["data"],
        "metadata": state["metadata"],
    }
