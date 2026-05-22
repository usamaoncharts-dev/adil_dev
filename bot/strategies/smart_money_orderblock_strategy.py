from datetime import datetime
import pandas as pd
from .base_strategy import BaseStrategy, StrategyResult


class SmartMoneyOrderBlockStrategy(BaseStrategy):
    name = 'Smart Money Order Block'
    description = 'Simplified smart money structure with BOS/CHoCH and retest confirmation.'

    def find_swing_points(self, df: pd.DataFrame, left: int = 2, right: int = 2) -> list[tuple[str, int, float]]:
        swings = []
        for i in range(left, len(df) - right):
            window = df.iloc[i - left : i + right + 1]
            center = df.iloc[i]
            is_low = center['low'] == window['low'].min()
            is_high = center['high'] == window['high'].max()
            if is_low:
                swings.append(('low', i, center['low']))
            elif is_high:
                swings.append(('high', i, center['high']))
        return swings

    def evaluate(self, df: pd.DataFrame) -> StrategyResult:
        if len(df) < 40:
            return StrategyResult(
                name=self.name,
                symbol='unknown',
                signal='no_data',
                score=0.0,
                details='Not enough data for smart money structure analysis.',
                timestamp=datetime.utcnow(),
            )

        swings = self.find_swing_points(df)
        current_close = df['close'].iloc[-1]
        current_vol = df['volume'].iloc[-1]
        avg_vol = df['volume'].rolling(20).mean().iloc[-1]

        if len(swings) < 3:
            return StrategyResult(
                name=self.name,
                symbol='unknown',
                signal='neutral',
                score=0.0,
                details='Insufficient swing structure to generate a BOS/CHoCH signal.',
                timestamp=datetime.utcnow(),
            )

        last = swings[-1]
        prev = swings[-2]
        prior = swings[-3]

        signal = 'neutral'
        details = 'No strong smart money breakout was confirmed.'
        score = 0.0

        if last[0] == 'high' and prev[0] == 'low' and prior[0] == 'high':
            bulls_break = last[2] > prior[2] and current_close > last[2]
            if bulls_break and current_vol > avg_vol * 1.05:
                signal = 'buy'
                details = (
                    'Bullish structure breakout with higher swing high and volume confirmation.'
                )
                score = min(100.0, (current_vol / avg_vol) * 35)
        elif last[0] == 'low' and prev[0] == 'high' and prior[0] == 'low':
            bears_break = last[2] < prior[2] and current_close < last[2]
            if bears_break and current_vol > avg_vol * 1.05:
                signal = 'sell'
                details = (
                    'Bearish structure breakout with lower swing low and volume confirmation.'
                )
                score = min(100.0, (current_vol / avg_vol) * 35)

        return StrategyResult(
            name=self.name,
            symbol='unknown',
            signal=signal,
            score=score,
            details=details,
            timestamp=datetime.utcnow(),
        )
