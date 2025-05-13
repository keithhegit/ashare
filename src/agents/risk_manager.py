import math

from langchain_core.messages import HumanMessage

from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.tools.api import prices_to_df
from src.utils.api_utils import agent_endpoint, log_llm_interaction

import json
import ast

# 兼容中英文key的访问函数
def get_value(d, *keys):
    for key in keys:
        if key in d:
            return d[key]
    return None

##### Risk Management Agent #####


@agent_endpoint("risk_management", "风险管理专家，评估投资风险并给出风险调整后的交易建议")
def risk_management_agent(state: AgentState):
    """Responsible for risk management"""
    show_workflow_status("Risk Manager")
    show_reasoning = state["metadata"]["show_reasoning"]
    portfolio = state["data"]["portfolio"]
    data = state["data"]

    prices_df = prices_to_df(data["prices"])

    # Fetch debate room message instead of individual analyst messages
    debate_message = next(
        msg for msg in state["messages"] if msg.name == "debate_room_agent")

    try:
        debate_results = json.loads(debate_message.content)
    except Exception as e:
        debate_results = ast.literal_eval(debate_message.content)

    # 1. Calculate Risk Metrics
    returns = prices_df['close'].pct_change().dropna()
    daily_vol = returns.std()
    # Annualized volatility approximation
    volatility = daily_vol * (252 ** 0.5)

    # 计算波动率的历史分布
    rolling_std = returns.rolling(window=120).std() * (252 ** 0.5)
    volatility_mean = rolling_std.mean()
    volatility_std = rolling_std.std()
    volatility_percentile = (volatility - volatility_mean) / volatility_std

    # Simple historical VaR at 95% confidence
    var_95 = returns.quantile(0.05)
    # 使用60天窗口计算最大回撤
    max_drawdown = (
        prices_df['close'] / prices_df['close'].rolling(window=60).max() - 1).min()

    # 2. Market Risk Assessment
    market_risk_score = 0

    # Volatility scoring based on percentile
    if volatility_percentile > 1.5:     # 高于1.5个标准差
        market_risk_score += 2
    elif volatility_percentile > 1.0:   # 高于1个标准差
        market_risk_score += 1

    # VaR scoring
    # Note: var_95 is typically negative. The more negative, the worse.
    if var_95 < -0.03:
        market_risk_score += 2
    elif var_95 < -0.02:
        market_risk_score += 1

    # Max Drawdown scoring
    if max_drawdown < -0.20:  # Severe drawdown
        market_risk_score += 2
    elif max_drawdown < -0.10:
        market_risk_score += 1

    # 3. Position Size Limits
    # Consider total portfolio value, not just cash
    current_stock_value = portfolio['stock'] * prices_df['close'].iloc[-1]
    total_portfolio_value = portfolio['cash'] + current_stock_value

    # Start with 25% max position of total portfolio
    base_position_size = total_portfolio_value * 0.25

    if market_risk_score >= 4:
        # Reduce position for high risk
        max_position_size = base_position_size * 0.5
    elif market_risk_score >= 2:
        # Slightly reduce for moderate risk
        max_position_size = base_position_size * 0.75
    else:
        # Keep base size for low risk
        max_position_size = base_position_size

    # 4. Stress Testing
    stress_test_scenarios = {
        "market_crash": -0.20,
        "moderate_decline": -0.10,
        "slight_decline": -0.05
    }

    stress_test_results = {}
    current_position_value = current_stock_value

    for scenario, decline in stress_test_scenarios.items():
        potential_loss = current_position_value * decline
        portfolio_impact = potential_loss / (portfolio['cash'] + current_position_value) if (
            portfolio['cash'] + current_position_value) != 0 else math.nan
        stress_test_results[scenario] = {
            "potential_loss": potential_loss,
            "portfolio_impact": portfolio_impact
        }

    # 5. Risk-Adjusted Signal Analysis
    # 兼容中英文key
    bull_confidence = get_value(debate_results, "bull_confidence", "多头置信度", "多方置信度")
    bear_confidence = get_value(debate_results, "bear_confidence", "空头置信度", "空方置信度")
    debate_confidence = get_value(debate_results, "confidence", "置信度", "辩论置信度")
    debate_signal = get_value(debate_results, "signal", "信号", "辩论信号", "多空信号")

    # 缺失时降级处理
    if bull_confidence is None or bear_confidence is None or debate_confidence is None or debate_signal is None:
        message_content = {
            "最大持仓规模": float('nan'),
            "风险评分": "暂无分析",
            "交易建议": "暂无分析",
            "风险指标": "暂无分析",
            "辩论分析": "暂无分析",
            "分析说明": "未能获取到完整的辩论分析数据，无法进行风险评估。"
        }
        message = HumanMessage(
            content=json.dumps(message_content),
            name="risk_management_agent",
        )
        if show_reasoning:
            show_agent_reasoning(message_content, "Risk Management Agent")
            state["metadata"]["agent_reasoning"] = message_content
        show_workflow_status("Risk Manager", "completed")
        return {
            "messages": state["messages"] + [message],
            "data": {
                **data,
                "risk_analysis": message_content
            },
            "metadata": state["metadata"],
        }

    # Add to risk score if confidence is low or debate was close
    confidence_diff = abs(bull_confidence - bear_confidence)
    if confidence_diff < 0.1:  # Close debate
        market_risk_score += 1
    if debate_confidence < 0.3:  # Low overall confidence
        market_risk_score += 1

    # Cap risk score at 10
    risk_score = min(round(market_risk_score), 10)

    # 6. Generate Trading Action
    # Consider debate room signal along with risk assessment
    if risk_score >= 9:
        trading_action = "hold"
    elif risk_score >= 7:
        trading_action = "reduce"
    else:
        if debate_signal == "bullish" and debate_confidence > 0.5:
            trading_action = "buy"
        elif debate_signal == "bearish" and debate_confidence > 0.5:
            trading_action = "sell"
        else:
            trading_action = "hold"

    # 中文结构化输出
    message_content = {
        "最大持仓规模": float(max_position_size),
        "风险评分": risk_score,
        "交易建议": (
            "买入" if trading_action == "buy" else
            "卖出" if trading_action == "sell" else
            "减仓" if trading_action == "reduce" else
            "持有"
        ),
        "风险指标": {
            "波动率": float(volatility),
            "95%风险价值": float(var_95),
            "最大回撤": float(max_drawdown),
            "市场风险评分": market_risk_score,
            "压力测试结果": stress_test_results
        },
        "辩论分析": {
            "多方置信度": bull_confidence,
            "空方置信度": bear_confidence,
            "辩论置信度": debate_confidence,
            "辩论信号": debate_signal
        },
        "分析说明": f"风险评分{risk_score}/10：市场风险={market_risk_score}，波动率={volatility:.2%}，VaR={var_95:.2%}，最大回撤={max_drawdown:.2%}，辩论信号={debate_signal}"
    }

    # Create the risk management message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="risk_management_agent",
    )

    if show_reasoning:
        show_agent_reasoning(message_content, "Risk Management Agent")
        # 保存推理信息到metadata供API使用
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Risk Manager", "completed")
    return {
        "messages": state["messages"] + [message],
        "data": {
            **data,
            "risk_analysis": message_content
        },
        "metadata": state["metadata"],
    }
