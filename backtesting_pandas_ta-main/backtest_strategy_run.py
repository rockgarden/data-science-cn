# -*- coding: utf-8 -*-
"""
基于 TradingView 数据的多币种加密货币策略回测
使用 pandas-ta 计算指标，vectorbt 执行信号生成与回测
"""

import pandas as pd
import pandas_ta as ta
import vectorbt as vbt
from tvDatafeed import TvDatafeed, Interval
import config_api
import matplotlib.pyplot as plt
import os

# =================== 配置参数 ===================
SYMBOLS = ['BNBUSDT', 'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT']
EXCHANGE = 'BINANCE'
INTERVAL = Interval.in_daily
BARS = 5000

# 指标参数
RSI_LENGTH = 14
RSI_THRESHOLD = 50
OBV_FAST = 5
OBV_SLOW = 35
MA_TYPE = 'ema'
MA_FAST = 5
MA_SLOW = 15

# 回测参数
INIT_CASH = 100
FEES = 0.0025  # 0.25%
SLIPPAGE = 0.0050  # 0.5%

# 文件路径
OUTPUT_DIR = '../trading_signal_backtest/port_plot'
CSV_FILE = 'crypto_tf1d_backtest.csv'

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 登录 TradingView
user = config_api.tradingview_user
password = config_api.tradingview_password
tv = TvDatafeed(user, password, chromedriver_path=None)


# =================== 核心回测函数 ===================
def run_backtest(symbol: str):
    """
    对单个交易对运行策略回测
    :param symbol: 交易对名称，如 'BTCUSDT'
    :return: 回测结果 stats DataFrame 和 Portfolio 对象
    """
    print(f"📊 正在回测 {symbol}...")

    # 获取数据
    df = tv.get_hist(symbol=symbol, exchange=EXCHANGE, interval=INTERVAL, n_bars=BARS)
    if df is None or df.empty:
        raise ValueError(f"{symbol} 数据获取失败")

    # 添加技术指标
    df['rsi'] = df.ta.rsi(length=RSI_LENGTH)
    ma_obv = df.ta.ma_obv(fast=OBV_FAST, slow=OBV_SLOW, mamode=MA_TYPE)
    ma_cross = df.ta.ma_cross(fast=MA_FAST, slow=MA_SLOW, mamode=MA_TYPE)

    # 生成因子信号（1 表示看涨，-1 表示看跌）
    df['strength'] = 1 if df['rsi'].iloc[-1] >= RSI_THRESHOLD else -1
    df['vol_in'] = 1 if ma_obv.iloc[-1] > 0 else -1
    df['ma_cross'] = 1 if ma_cross.iloc[-1] > 0 else -1

    # 综合买入信号：三者同时为 1
    signal = (df['vol_in'] == 1) & (df['strength'] == 1) & (df['ma_cross'] == 1)

    # 构建 vectorbt 所需的信号（布尔型 entries/exits）
    entries = signal.shift(1)  # 今天信号，明天开盘买入
    exits = ~entries  # 简单持有，可替换为其他退出逻辑

    # 下一根K线的开盘价作为成交价
    next_open = df['open'].shift(-1)

    # 创建回测组合
    portfolio = vbt.Portfolio.from_signals(
        close=next_open,
        entries=entries,
        exits=exits,
        freq='1D',
        init_cash=INIT_CASH,
        fees=FEES,
        slippage=SLIPPAGE
    )

    # 策略名称（用于图表和文件命名）
    strat_name = f"{symbol}_OBV{OBV_FAST}_{OBV_SLOW}_RSI{RSI_THRESHOLD}_MACROSS{MA_FAST}_{MA_SLOW}"

    # 可视化并保存图像
    fig = portfolio.plot()
    fig.show()
    fig.write_image(f"{OUTPUT_DIR}/{strat_name}.png", format='png', scale=2.0)

    # 计算统计指标
    stats = portfolio.stats()
    annual_ret = portfolio.annualized_return()
    annual_vol = portfolio.annualized_volatility()
    ret_risk_ratio = annual_ret / annual_vol if annual_vol != 0 else float('inf')

    # 将风险调整收益加入统计
    stats['Annualized Return Adjust Vol'] = ret_risk_ratio

    # 转换为 DataFrame 并设置列名
    stats_df = pd.DataFrame(stats).T  # 转置为一行
    stats_df.index = [strat_name]

    return stats_df, portfolio, strat_name


# =================== 主程序 ===================
if __name__ == "__main__":
    all_stats = []
    portfolio_dict = {}

    for symbol in SYMBOLS:
        try:
            stats_df, portfolio, strat_name = run_backtest(symbol)

            # 保存 portfolio 对象（便于后续分析）
            portfolio.save(f"./portfolios/{strat_name}.p")

            # 缓存结果
            all_stats.append(stats_df)
            portfolio_dict[strat_name] = portfolio

        except Exception as e:
            print(f"❌ 回测 {symbol} 失败: {e}")
            continue

    # 合并所有回测结果
    if all_stats:
        final_stats = pd.concat(all_stats, axis=0)

        # 保存到 CSV
        final_stats.to_csv(CSV_FILE)
        print(f"\n✅ 所有回测完成，结果已保存至: {CSV_FILE}")

        # 显示汇总表格
        print("\n📈 回测结果汇总:")
        print(final_stats[['Start', 'End', 'Total Return [%]', 'Annualized Return [%]',
                           'Max Drawdown [%]', 'Win Rate [%]', 'Annualized Return Adjust Vol']])
    else:
        print("⚠️ 所有回测均失败，请检查网络或 TradingView 登录状态。")

    # 可选：绘制多资产净值曲线对比
    # 如果你想比较多个资产的累计收益
    # 示例：
    # fig = vbt.Portfolio.plot_multiple(
    #     [(p, n) for n, p in portfolio_dict.items()],
    #     fields='cumulative_returns'
    # )
    # fig.show()