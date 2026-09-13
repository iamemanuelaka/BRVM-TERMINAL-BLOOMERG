# BRVM-TERMINAL-BLOOMERG
Application web d'analyse technique (style MetaTrader/TradingView), d'évaluation de risque (VaR, Sharpe) et de backtesting algorithmique pour le marché de la BRVM.

# 📈 BRVM Terminal — Plateforme d'Analyse Financière & Trading Quantitatif

**BRVM Terminal** est une application web haute performance conçue pour l'analyse technique, l'évaluation fondamentale, la gestion de portefeuille et le trading quantitatif sur la Bourse Régionale des Valeurs Mobilières (BRVM) et les marchés financiers.

Inspiré des terminaux financiers professionnels (type Bloomberg / MetaTrader), cet outil centralise le suivi de marché, l'analyse graphique interactive et le backtesting algorithmique au sein d'une interface ultra-réactive et entièrement personnalisable.

---

## 🚀 Fonctionnalités Principales

### 🎨 1. Personnalisation & Thèmes
- **Thèmes visuels** : Basculez en un clic entre les modes **Sombre**, **Clair** et **Bleu Nuit**.
- **Types de graphiques** : Affichage au choix en **Bougies japonaises** (Candlesticks), **Lignes** ou vue combinée.

### 📊 2. Multi-Vues & Analyse Technique
- **F1 (EQUITY)** : Dashboard d'observation rapide (cours en direct, variations OHLCV, métriques clés).
- **F5 (CHARTS)** : Analyse multi-timeframe avec indicateurs techniques dynamiques (SMA, EMA, Bandes de Bollinger, RSI).
- **F6 (ANALYST)** : Espace d'analyse plein écran avec intégration du widget TradingView (trendlines, retracements de Fibonacci, pinceau libre, annotations).

### 📓 3. Carnet d'Ordres & Historique de Trading (MetaTrader Style)
- **Gestion des positions** : Suivi des positions ouvertes et fermées (Prix d'entrée, Take Profit / Stop Loss, P&L Latent, P&L Réalisé).
- **Statistiques de performance** : Calcul automatique du **Win Rate**, du **Profit Factor** et du PnL cumulé.

### 💼 4. Analytics de Portefeuille & Risque (PORT)
- Attribution de performance du portefeuille.
- Calculateur de facteurs de risque : **Beta pondéré**, **Ratio de Sharpe**, **Value at Risk (VaR 95%)**, **Max Drawdown**.

### 🐍 5. Environnement Quantitatif & Backtesting (QUANT / PRED)
- **Éditeur Python In-Browser (Pyodide)** : Écrivez, exécutez et validez vos algorithmes directement dans le navigateur en WebAssembly.
- **Backtesting & Stratégies** : Modélisation et simulation de stratégies (Moyennes mobiles, RSI, Momentum, Mean Reversion).
- **Gestionnaire de Prédictions** : Enregistrement, suivi et évaluation des signaux générés par vos modèles.

---

## 🛠️ Technologies Utilisées

- **Frontend** : HTML5, CSS3 (Variables CSS dynamiques), JavaScript (ES6+).
- **Graphiques** :
  - [TradingView Advanced Charting Library](https://s3.tradingview.com/tv.js)
  - Monaco Editor (Moteur d'édition VS Code)
- **Moteur Python** : [Pyodide](https://pyodide.org/) (Python exécuté en WebAssembly dans le navigateur)

---

## ⚡ Prise en main rapide

### Installation
Aucun serveur ni installation complexe n'est requis.

1. **Cloner le dépôt** :
   ```bash
   git clone [https://github.com/votre-utilisateur/brvm-terminal.git](https://github.com/votre-utilisateur/brvm-terminal.git)
   cd brvm-terminal
   
2.voir l'apercu 
   [🚀 VOIR L'APERÇU DU TERMINAL EN DIRECT](https://iamemanuelaka.github.io/BRVM-TERMINAL-BLOOMERG/apercu%20du%20terminal.html)
