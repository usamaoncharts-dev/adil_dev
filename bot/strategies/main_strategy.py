import math
from datetime import datetime
import pandas as pd
from .base_strategy import BaseStrategy, StrategyResult


class MainEMAStrategy(BaseStrategy):
    name = 'Main Strategy'
    description = '5-minute EMA crossover with momentum and sideways market filter.'

    def evaluate(self, df: pd.DataFrame) -> StrategyResult:
        if len(df) < 20:
            return StrategyResult(
                name=self.name,
                symbol='unknown',
                signal='no_data',
                score=0.0,
                details='Not enough candle history for signal generation.',
                timestamp=datetime.utcnow(),
            )

        df = df.copy()
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema15'] = df['close'].ewm(span=15, adjust=False).mean()
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].abs().rolling(20).mean()

        last = df.iloc[-1]
        prior = df.iloc[-2]

        crossover_bull = prior['ema9'] <= prior['ema15'] and last['ema9'] > last['ema15']
        crossover_bear = prior['ema15'] <= prior['ema9'] and last['ema15'] > last['ema9']

        slope_pct = 0.0
        if prior['ema9'] > 0:
            slope_pct = (last['ema9'] - prior['ema9']) / prior['ema9']
        angle = abs(math.degrees(math.atan(slope_pct * 100)))

        sideways = last['volatility'] < 0.0015
        score = min(100.0, max(0.0, angle * 2.0))

        if crossover_bull and angle >= 30 and not sideways:
            signal = 'buy'
            details = (
                f'EMA 9/15 bullish crossover with angle ≈ {angle:.1f}° and volatility filter passed.'
            )
        elif crossover_bear and angle >= 30 and not sideways:
            signal = 'sell'
            details = (
                f'EMA 9/15 bearish crossover with angle ≈ {angle:.1f}° and volatility filter passed.'
            )
        else:
            signal = 'neutral'
            details = (
                'No clear EMA crossover signal, momentum is insufficient, or market is sideways.'
                f' angle={angle:.1f}°, sideways={sideways}.'
            )

        return StrategyResult(
            name=self.name,
            symbol='unknown',
            signal=signal,
            score=score,
            details=details,
            timestamp=datetime.utcnow(),
        )
