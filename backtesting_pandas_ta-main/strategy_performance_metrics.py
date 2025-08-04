import pandas as pd
import vectorbt as vbt

##### import stats csv
port_csv = pd.read_csv('./crypto_tf1d_backtest.csv', index_col= 0)
port_csv


##### setup dataframe 
def setup_dataframe(symbol: str, data: pd.DataFrame) -> pd.DataFrame:
    """
    设置单个资产的 DataFrame
    :param symbol: 资产名称，如 'BTCUSDT'
    :param data: 包含所有资产数据的 DataFrame
    :return: 单个资产的 DataFrame
    """
    df = data[symbol].copy()
    df['symbol'] = symbol
    return df

#####  calculate any metrics
def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
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
##### plot
def plot_portfolio(portfolio: vbt.Portfolio) -> None:
    """
    绘制回测组合的性能图表
    :param portfolio: vectorbt 回测组合对象
    """
    # 绘制净值曲线
    portfolio.total_return().vbt.plot(title='Portfolio Total Return')
    
    # 绘制每个交易对的表现
    portfolio.value().vbt.plot(title='Portfolio Value Over Time')
    
    # 绘制交易信号
    portfolio.trades.vbt.plot(title='Trades')