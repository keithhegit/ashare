from langchain_core.messages import HumanMessage

from src.agents.state import AgentState, show_agent_reasoning, show_workflow_status
from src.utils.api_utils import agent_endpoint, log_llm_interaction

import json

##### Fundamental Agent #####


@agent_endpoint("fundamentals", "基本面分析师，分析公司财务指标、盈利能力和增长潜力")
def fundamentals_agent(state: AgentState):
    """Responsible for fundamental analysis"""
    show_workflow_status("Fundamentals Analyst")
    show_reasoning = state["metadata"]["show_reasoning"]
    data = state["data"]
    metrics = data["financial_metrics"][0]

    # Initialize signals list for different fundamental aspects
    signals = []
    reasoning = {}

    # 1. Profitability Analysis
    return_on_equity = metrics.get("return_on_equity", 0)
    net_margin = metrics.get("net_margin", 0)
    operating_margin = metrics.get("operating_margin", 0)

    thresholds = [
        (return_on_equity, 0.15),  # Strong ROE above 15%
        (net_margin, 0.20),  # Healthy profit margins
        (operating_margin, 0.15)  # Strong operating efficiency
    ]
    profitability_score = sum(
        metric is not None and metric > threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if profitability_score >=
                   2 else 'bearish' if profitability_score == 0 else 'neutral')
    reasoning["profitability_signal"] = {
        "signal": signals[0],
        "details": (
            f"ROE: {metrics.get('return_on_equity', 0):.2%}" if metrics.get(
                "return_on_equity") is not None else "ROE: N/A"
        ) + ", " + (
            f"Net Margin: {metrics.get('net_margin', 0):.2%}" if metrics.get(
                "net_margin") is not None else "Net Margin: N/A"
        ) + ", " + (
            f"Op Margin: {metrics.get('operating_margin', 0):.2%}" if metrics.get(
                "operating_margin") is not None else "Op Margin: N/A"
        )
    }

    # 2. Growth Analysis
    revenue_growth = metrics.get("revenue_growth", 0)
    earnings_growth = metrics.get("earnings_growth", 0)
    book_value_growth = metrics.get("book_value_growth", 0)

    thresholds = [
        (revenue_growth, 0.10),  # 10% revenue growth
        (earnings_growth, 0.10),  # 10% earnings growth
        (book_value_growth, 0.10)  # 10% book value growth
    ]
    growth_score = sum(
        metric is not None and metric > threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if growth_score >=
                   2 else 'bearish' if growth_score == 0 else 'neutral')
    reasoning["growth_signal"] = {
        "signal": signals[1],
        "details": (
            f"Revenue Growth: {metrics.get('revenue_growth', 0):.2%}" if metrics.get(
                "revenue_growth") is not None else "Revenue Growth: N/A"
        ) + ", " + (
            f"Earnings Growth: {metrics.get('earnings_growth', 0):.2%}" if metrics.get(
                "earnings_growth") is not None else "Earnings Growth: N/A"
        )
    }

    # 3. Financial Health
    current_ratio = metrics.get("current_ratio", 0)
    debt_to_equity = metrics.get("debt_to_equity", 0)
    free_cash_flow_per_share = metrics.get("free_cash_flow_per_share", 0)
    earnings_per_share = metrics.get("earnings_per_share", 0)

    health_score = 0
    if current_ratio and current_ratio > 1.5:  # Strong liquidity
        health_score += 1
    if debt_to_equity and debt_to_equity < 0.5:  # Conservative debt levels
        health_score += 1
    if (free_cash_flow_per_share and earnings_per_share and
            free_cash_flow_per_share > earnings_per_share * 0.8):  # Strong FCF conversion
        health_score += 1

    signals.append('bullish' if health_score >=
                   2 else 'bearish' if health_score == 0 else 'neutral')
    reasoning["financial_health_signal"] = {
        "signal": signals[2],
        "details": (
            f"Current Ratio: {metrics.get('current_ratio', 0):.2f}" if metrics.get(
                "current_ratio") is not None else "Current Ratio: N/A"
        ) + ", " + (
            f"D/E: {metrics.get('debt_to_equity', 0):.2f}" if metrics.get(
                "debt_to_equity") is not None else "D/E: N/A"
        )
    }

    # 4. Price to X ratios
    pe_ratio = metrics.get("pe_ratio", 0)
    price_to_book = metrics.get("price_to_book", 0)
    price_to_sales = metrics.get("price_to_sales", 0)

    thresholds = [
        (pe_ratio, 25),  # Reasonable P/E ratio
        (price_to_book, 3),  # Reasonable P/B ratio
        (price_to_sales, 5)  # Reasonable P/S ratio
    ]
    price_ratio_score = sum(
        metric is not None and metric < threshold
        for metric, threshold in thresholds
    )

    signals.append('bullish' if price_ratio_score >=
                   2 else 'bearish' if price_ratio_score == 0 else 'neutral')
    reasoning["price_ratios_signal"] = {
        "signal": signals[3],
        "details": (
            f"P/E: {pe_ratio:.2f}" if pe_ratio else "P/E: N/A"
        ) + ", " + (
            f"P/B: {price_to_book:.2f}" if price_to_book else "P/B: N/A"
        ) + ", " + (
            f"P/S: {price_to_sales:.2f}" if price_to_sales else "P/S: N/A"
        )
    }

    # Determine overall signal
    bullish_signals = signals.count('bullish')
    bearish_signals = signals.count('bearish')

    if bullish_signals > bearish_signals:
        overall_signal = 'bullish'
    elif bearish_signals > bullish_signals:
        overall_signal = 'bearish'
    else:
        overall_signal = 'neutral'

    # Calculate confidence level
    total_signals = len(signals)
    confidence = max(bullish_signals, bearish_signals) / total_signals

    # 中文结构化输出
    message_content = {
        "投资信号": "看多" if overall_signal == 'bullish' else "看空" if overall_signal == 'bearish' else "中性",
        "置信度": f"{round(confidence * 100)}%",
        "分析说明": {
            "盈利能力分析": {
                "信号": "看多" if signals[0] == 'bullish' else "看空" if signals[0] == 'bearish' else "中性",
                "详情": f"ROE（净资产收益率）为{metrics.get('return_on_equity', 0):.2%}，净利率为{metrics.get('net_margin', 0):.2%}，营业利润率为{metrics.get('operating_margin', 0):.2%}。数值越高代表公司盈利能力越强。"
            },
            "增长能力分析": {
                "信号": "看多" if signals[1] == 'bullish' else "看空" if signals[1] == 'bearish' else "中性",
                "详情": f"营收增长率为{metrics.get('revenue_growth', 0):.2%}，净利润增长率为{metrics.get('earnings_growth', 0):.2%}。正值且较高代表公司成长性较好。"
            },
            "财务健康分析": {
                "信号": "看多" if signals[2] == 'bullish' else "看空" if signals[2] == 'bearish' else "中性",
                "详情": f"流动比率为{metrics.get('current_ratio', 0):.2f}，资产负债率（D/E）为{metrics.get('debt_to_equity', 0):.2f}。流动比率高且负债率低说明公司财务稳健。"
            },
            "估值分析": {
                "信号": "看多" if signals[3] == 'bullish' else "看空" if signals[3] == 'bearish' else "中性",
                "详情": f"市盈率（P/E）为{pe_ratio:.2f}，市净率（P/B）为{price_to_book:.2f}，市销率（P/S）为{price_to_sales:.2f}。数值越低代表估值越合理。"
            }
        }
    }

    # Create the fundamental analysis message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="fundamentals_agent",
    )

    # Print the reasoning if the flag is set
    if show_reasoning:
        show_agent_reasoning(message_content, "Fundamental Analysis Agent")
        # 保存推理信息到metadata供API使用
        state["metadata"]["agent_reasoning"] = message_content

    show_workflow_status("Fundamentals Analyst", "completed")
    return {
        "messages": [message],
        "data": {
            **data,
            "fundamental_analysis": message_content
        },
        "metadata": state["metadata"],
    }
