# -*- coding: utf-8 -*-
"""
加密货币多资产回测策略（基于 TradingView 数据 + vectorbt）
使用 pandas-ta 计算技术指标，vectorbt 执行回测
"""

# 导入必要库
from tvDatafeed import TvDatafeed, Interval  # 从 TradingView 获取金融数据
import pandas as pd                         # 数据处理
import pandas_ta as ta                     # 技术分析指标
import vectorbt as vbt                     # 高性能向量化回测
import config_api                          # 存放账号密码等敏感信息
import matplotlib.pyplot as plt            # 可视化
from typing import List, Tuple, Dict      # 类型提示，提升代码可读性

# =================== 配置参数 ===================
SYMBOLS = ['BNBUSDT', 'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'ADAUSDT']  # 多资产列表
EXCHANGE = 'BINANCE'
INTERVAL = Interval.in_daily               # 日线级别
BARS = 5000                                # 获取最近 5000 根K线

# 指标参数
RSI_LENGTH = 14
RSI_BUY_THRESHOLD = 50                     # RSI 买入阈值
OBV_FAST = 5
OBV_SLOW = 35
MA_TYPE = 'ema'                            # 移动平均类型
MA_FAST = 5
MA_SLOW = 15

# 登录 TradingView 的凭证（建议放在 config_api.py 中）
TV_USER = config_api.tradingview_user
TV_PASSWORD = config_api.tradingview_password


# =================== 核心函数 ===================

def create_tv_client() -> TvDatafeed:
    """
    创建并返回已登录的 TradingView 数据客户端
    使用后应调用 tv.close() 关闭浏览器
    """
    print("正在登录 TradingView...")
    tv = TvDatafeed(username=TV_USER, password=TV_PASSWORD, chromedriver_path=None)
    return tv


def fetch_data_for_symbols(symbols: List[str]) -> Dict[str, pd.DataFrame]:
    """
    批量获取多个交易对的历史数据
    :param symbols: 交易对列表，如 ['BTCUSDT', 'ETHUSDT']
    :return: 字典，键为 symbol，值为 OHLCV 数据 DataFrame
    """
    tv = create_tv_client()
    data = {}

    try:
        for symbol in symbols:
            print(f"正在获取 {symbol} 数据...")
            df = tv.get_hist(symbol=symbol, exchange=EXCHANGE, interval=INTERVAL, n_bars=BARS)
            if df is not None and not df.empty:
                data[symbol] = df
            else:
                print(f"⚠️ 警告：未能获取 {symbol} 的数据")
    finally:
        tv.close()  # 确保关闭浏览器
    return data


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    为单个资产的 DataFrame 添加技术指标
    :param df: 原始 OHLCV 数据
    :return: 添加指标后的新 DataFrame
    """
    # 使用 pandas_ta 添加指标（不修改原数据）
    df = df.copy()

    # RSI 指标
    df['rsi'] = ta.rsi(df['close'], length=RSI_LENGTH)

    # OBV 交叉信号（类似 MACD 思路）
    obv_signal = ta.ma_obv(fast=OBV_FAST, slow=OBV_SLOW, mamode=MA_TYPE)
    df['obv_signal'] = obv_signal

    # 均线交叉信号（快线上穿慢线为买入）
    ma_fast_line = ta.ma(MA_TYPE, df['close'], length=MA_FAST)
    ma_slow_line = ta.ma(MA_TYPE, df['close'], length=MA_SLOW)
    df['ma_fast'] = ma_fast_line
    df['ma_slow'] = ma_slow_line

    return df


def generate_signals(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    """
    根据指标生成买入/卖出信号
    :param df: 包含指标的 DataFrame
    :return: 元组 (entries: 买入信号, exits: 卖出信号)
    """
    close = df['close']
    rsi = df['rsi']
    obv_signal = df['obv_signal']
    ma_fast = df['ma_fast']
    ma_slow = df['ma_slow']

    # 买入条件：RSI > 阈值 & OBV 快线 > 慢线 & 均线金叉
    entries = (
        (rsi > RSI_BUY_THRESHOLD) &
        (obv_signal > 0) &
        (ma_fast > ma_slow) &
        (ma_fast.shift(1) <= ma_slow.shift(1))  # 上一根是死叉，当前金叉
    )

    # 卖出条件：RSI < 阈值 或 均线死叉
    exits = (
        (rsi < RSI_BUY_THRESHOLD) |
        ((ma_fast < ma_slow) & (ma_fast.shift(1) >= ma_slow.shift(1)))
    )

    return entries, exits


def run_backtest_for_symbol(symbol: str, data: Dict[str, pd.DataFrame]) -> vbt.Portfolio:
    """
    对单个资产运行回测
    :param symbol: 资产名称，如 'BTCUSDT'
    :param data: 所有资产数据字典
    :return: vectorbt 回测结果对象
    """
    if symbol not in data:
        raise ValueError(f"未找到 {symbol} 的数据")

    df = data[symbol]
    df = add_indicators(df)
    entries, exits = generate_signals(df)

    # 使用 vectorbt 运行回测（假设每次交易使用 100% 资金）
    portfolio = vbt.Portfolio.from_signals(
        close=df['close'],
        entries=entries,
        exits=exits,
        init_cash=10000,           # 初始资金 10,000 USDT
        size=1,                    # 每次买入 1 个单位（可改为动态仓位）
        fees=0.001,                # 0.1% 交易手续费
        freq='D'                   # 日频
    )
    return portfolio


def run_multi_asset_backtest(symbols: List[str]) -> Dict[str, vbt.Portfolio]:
    """
    对多个资产并行运行回测
    :param symbols: 资产列表
    :return: 回测结果字典
    """
    print("开始获取多资产数据...")
    data = fetch_data_for_symbols(symbols)

    results = {}
    for symbol in symbols:
        print(f"正在回测 {symbol}...")
        try:
            results[symbol] = run_backtest_for_symbol(symbol, data)
        except Exception as e:
            print(f"❌ 回测 {symbol} 失败: {e}")

    return results


def analyze_results(results: Dict[str, vbt.Portfolio]):
    """
    分析并可视化回测结果
    """
    # 提取各资产的累计收益
    equity = pd.DataFrame({symbol: res.total_return() for symbol, res in results.items()}, index=[0]).T
    equity.columns = ['Total Return']

    print("\n📊 各资产总收益率:")
    print(equity)

    # 绘图
    plt.figure(figsize=(12, 6))
    for symbol, res in results.items():
        res.plot().show()  # 显示单个资产的回测图表
        # 或者只画净值曲线
        # res.cumulative_returns().plot(label=symbol)

    plt.title("Multi-Asset Backtest Cumulative Returns")
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# =================== 主程序入口 ===================
if __name__ == "__main__":
    # 运行多资产回测
    backtest_results = run_multi_asset_backtest(SYMBOLS)

    # 分析结果
    analyze_results(backtest_results)

    # 示例：查看 BTCUSDT 的详细报告
    if 'BTCUSDT' in backtest_results:
        report = backtest_results['BTCUSDT'].stats()
        print("\n📈 BTCUSDT 回测统计:")
        print(report)