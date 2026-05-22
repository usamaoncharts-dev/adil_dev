from datetime import datetime
import pandas as pd
from .base_strategy import BaseStrategy, StrategyResult


class OrderBlockMatrixStrategy(BaseStrategy):
    name = 'Order Block Matrix'
    description = 'Simplified order block trade engine based on volume, rejection, and price zone retest.'

    def evaluate(self, df: pd.DataFrame) -> StrategyResult:
        if len(df) < 30:
            return StrategyResult(
                name=self.name,
                symbol='unknown',
                signal='no_data',
                score=0.0,
                details='Not enough candle history for signal generation.',
                timestamp=datetime.utcnow(),
            )

        df = df.copy()
        df['body_size'] = (df['close'] - df['open']).abs()
        df['up_range'] = df['high'] - df['low']
        df['volume_avg'] = df['volume'].rolling(20).mean()

        candidate = df.iloc[-6]
        current = df.iloc[-1]
        last_vol = current['volume']
        avg_vol = df['volume_avg'].iloc[-1]

        bearish_block = (
            candidate['close'] < candidate['open']
            and candidate['body_size'] > candidate['up_range'] * 0.35
            and candidate['volume'] > avg_vol * 1.1
            and current['low'] <= max(candidate['open'], candidate['close'])
            and current['close'] > current['open']
        )

        bullish_block = (
            candidate['close'] > candidate['open']
            and candidate['body_size'] > candidate['up_range'] * 0.35
            and candidate['volume'] > avg_vol * 1.1
            and current['high'] >= min(candidate['open'], candidate['close'])
            and current['close'] < current['open']
        )

        if bearish_block:
            signal = 'buy'
            details = (
                'Bullish order block retest detected: strong bearish block followed by bullish rejection and volume support.'
            )
            score = min(100.0, max(0.0, (last_vol / avg_vol) * 40))
        elif bullish_block:
            signal = 'sell'
            details = (
                'Bearish order block retest detected: strong bullish block followed by bearish rejection and volume support.'
            )
            score = min(100.0, max(0.0, (last_vol / avg_vol) * 40))
        else:
            signal = 'neutral'
            details = (
                'No clean order block retest found in the current window. Waiting for a stronger zone signal.'
            )
            score = 0.0

        return StrategyResult(
            name=self.name,
            symbol='unknown',
            signal=signal,
            score=score,
            details=details,
            timestamp=datetime.utcnow(),
        )
