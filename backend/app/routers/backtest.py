"""Endpoint pour le backtesting de stratégies quantitatives."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])

class BacktestRequest(BaseModel):
    symbol: str
    strategy: str  # 'sma_cross', 'rsi', 'momentum'
    start_date: str
    end_date: str
    initial_capital: float = 10000000
    fees_pct: float = 0.5

@router.post("/run")
async def run_backtest(req: BacktestRequest):
    try:
        # 1. Récupérer les données (Yahoo Finance pour l'historique riche)
        ticker = yf.Ticker(req.symbol)
        df = ticker.history(start=req.start_date, end=req.end_date)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Aucune donnée trouvée pour ce symbole")
        
        df['Returns'] = df['Close'].pct_change()
        df['Strategy_Returns'] = 0.0
        df['Trades'] = 0
        
        # 2. Logique des stratégies
        if req.strategy == 'sma_cross':
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['Signal'] = 0
            df.loc[df['SMA_20'] > df['SMA_50'], 'Signal'] = 1
            df.loc[df['SMA_20'] < df['SMA_50'], 'Signal'] = -1
            df['Position'] = df['Signal'].shift(1)
            df['Strategy_Returns'] = df['Position'] * df['Returns']
            
        elif req.strategy == 'rsi':
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            df['Signal'] = 0
            df.loc[df['RSI'] < 30, 'Signal'] = 1
            df.loc[df['RSI'] > 70, 'Signal'] = -1
            df['Position'] = df['Signal'].shift(1)
            df['Strategy_Returns'] = df['Position'] * df['Returns']
            
        elif req.strategy == 'momentum':
            df['ROC'] = df['Close'].pct_change(periods=20)
            df['Signal'] = 0
            df.loc[df['ROC'] > 0.05, 'Signal'] = 1   # Momentum positif
            df.loc[df['ROC'] < -0.05, 'Signal'] = -1 # Momentum négatif
            df['Position'] = df['Signal'].shift(1)
            df['Strategy_Returns'] = df['Position'] * df['Returns']

        # 3. Appliquer les frais de transaction
        df['Trades'] = df['Position'].diff().abs().fillna(0)
        df['Strategy_Returns'] = np.where(
            df['Trades'] > 0, 
            df['Strategy_Returns'] - (req.fees_pct / 100), 
            df['Strategy_Returns']
        )

        # Supprimer les NaN générés par les fenêtres glissantes
        df = df.dropna()

        # 4. Calculer les courbes d'équité
        df['Strategy_Equity'] = (1 + df['Strategy_Returns']).cumprod() * req.initial_capital
        df['BuyHold_Equity'] = (1 + df['Returns']).cumprod() * req.initial_capital

        # 5. Calculer les métriques
        total_return = ((df['Strategy_Equity'].iloc[-1] / req.initial_capital) - 1) * 100
        buy_hold_return = ((df['BuyHold_Equity'].iloc[-1] / req.initial_capital) - 1) * 100
        
        daily_rf = 0.03 / 252
        excess_returns = df['Strategy_Returns'] - daily_rf
        sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std()) if excess_returns.std() > 0 else 0
        
        rolling_max = df['Strategy_Equity'].cummax()
        drawdown = (df['Strategy_Equity'] - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100

        winning_trades = df[df['Strategy_Returns'] > 0]['Strategy_Returns']
        losing_trades = df[df['Strategy_Returns'] < 0]['Strategy_Returns']
        
        active_days = len(df[df['Position'] != 0])
        win_rate = (len(winning_trades) / active_days * 100) if active_days > 0 else 0
        profit_factor = abs(winning_trades.sum() / losing_trades.sum()) if len(losing_trades) > 0 and losing_trades.sum() != 0 else 99.9

        # 6. Formater les données pour le graphique frontend
        chart_data = []
        for index, row in df.iterrows():
            chart_data.append({
                'time': index.strftime('%Y-%m-%d'),
                'strategy': round(row['Strategy_Equity'], 2),
                'buyhold': round(row['BuyHold_Equity'], 2)
            })

        return {
            'metrics': {
                'total_return': round(total_return, 2),
                'buy_hold_return': round(buy_hold_return, 2),
                'sharpe_ratio': round(sharpe, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 1),
                'profit_factor': round(profit_factor, 2),
                'total_trades': int(df['Trades'].sum())
            },
            'chart_data': chart_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
