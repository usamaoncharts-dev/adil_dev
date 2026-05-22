from dataclasses import dataclass
from datetime import datetime
import pandas as pd


@dataclass
class StrategyResult:
    name: str
    symbol: str
    signal: str
    score: float
    details: str
    timestamp: datetime


class BaseStrategy:
    name = 'Base Strategy'
    description = 'Abstract strategy base class'

    def __init__(self, config):
        self.config = config

    def evaluate(self, df: pd.DataFrame) -> StrategyResult:
        raise NotImplementedError('Strategy must implement evaluate()')
