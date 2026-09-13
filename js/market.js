/**
 * ═══════════════════════════════════════════════════════════════
 * BRVM TERMINAL - MARKET MODULE (v3.2 - Unifié BRVM + Global)
 * ═══════════════════════════════════════════════════════════════
 */

class MarketManager {
  constructor() {
    this.stocks = [];
    this.selectedTicker = 'SNTS';
  }

  /**
   * Charge les tickers depuis l'API unifiée (BRVM + Fallback Yahoo)
   */
  async loadTickers() {
    try {
      const tickers = await api.getTickers();
      if (tickers && tickers.length > 0) {
        this.stocks = tickers.map(t => ({
          ticker: t.symbol,
          name: t.name,
          price: t.price || 0,
          change: t.change_pct || 0,
          volume: t.volume || 0,
          sector: t.sector || 'N/A',
          country: t.country || 'N/A',
          cap: t.market_cap ? (t.market_cap / 1e9).toFixed(1) : (t.cap_mrds || 0),
          per: t.trailing_pe ? t.trailing_pe.toFixed(1) + 'x' : 'N/A',
          beta: t.beta || 1.0,
          source: t.source || 'yahoo' // 'brvm' ou 'yahoo'
        }));
        console.log(`[Market] ✓ ${this.stocks.length} tickers chargés`);
        return true;
      }
    } catch (error) {
      console.warn('[Market] API indisponible, utilisation des données locales de secours');
    }
    
    // Fallback ultime si tout échoue
    this.stocks = [
      { ticker: 'SNTS', name: 'SONATEL SENEGAL', price: 17500, change: 1.45, volume: 14250, sector: 'Télécom', country: 'SN', cap: 2845, per: '14.2x', beta: 0.87, source: 'local' },
      { ticker: 'ETIT', name: 'ECOBANK TRANS.', price: 19, change: -5.00, volume: 850000, sector: 'Banque', country: 'TG', cap: 1250, per: '5.1x', beta: 1.15, source: 'local' },
      { ticker: 'AAPL', name: 'APPLE INC.', price: 175, change: 0.50, volume: 50000000, sector: 'Technologie', country: 'US', cap: 2700, per: '28.5x', beta: 1.2, source: 'yahoo' }
    ];
    return false;
  }

  /**
   * Récupère les données OHLCV (gère automatiquement BRVM ou Yahoo via le backend)
   */
  async loadOHLCV(symbol, limit = 365) {
    try {
      return await api.getOHLCV(symbol, limit);
    } catch (error) {
      console.warn(`[Market] OHLCV ${symbol} indisponible`);
      return [];
    }
  }

  /**
   * Sélectionne un ticker (fonctionne aussi pour les tickers globaux)
   */
  selectTicker(symbol) {
    this.selectedTicker = symbol.toUpperCase();
    
    // Si le ticker n'est pas dans la liste, on l'ajoute dynamiquement avec des données par défaut
    if (!this.stocks.find(s => s.ticker === this.selectedTicker)) {
      this.stocks.unshift({
        ticker: this.selectedTicker,
        name: this.selectedTicker,
        price: 0, change: 0, volume: 0,
        sector: 'Global', country: 'INT', cap: 0, per: 'N/A', beta: 1.0,
        source: 'yahoo'
      });
    }
    
    if (typeof renderWatchlist === 'function') renderWatchlist();
    if (typeof renderTickerDetail === 'function') renderTickerDetail();
    if (typeof rebuildCharts === 'function') rebuildCharts();
  }

  getSelected() {
    return this.stocks.find(s => s.ticker === this.selectedTicker) || this.stocks[0];
  }

  refreshPrices() {
    // Simulation locale uniquement pour les données 'local'
    this.stocks.forEach(s => {
      if (s.source === 'local') {
        const delta = (Math.random() - 0.5) * 0.4;
        s.change = +(s.change + delta).toFixed(2);
        s.price = Math.round(s.price * (1 + delta / 100));
      }
    });
  }
}

const market = new MarketManager();
