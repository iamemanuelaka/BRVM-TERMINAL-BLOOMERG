/**
 * ═══════════════════════════════════════════════════════════════
 * BRVM TERMINAL - MARKET MODULE
 * Gestion de la watchlist et des données marché
 * ═══════════════════════════════════════════════════════════════
 */

class MarketManager {
  constructor() {
    this.stocks = [];
    this.selectedTicker = 'SNTS';
    this.fallbackStocks = [
      { symbol: 'SNTS', name: 'SONATEL SENEGAL', price: 17500, change_pct: 1.45, volume: 14250, sector: 'Télécom', country: 'SN', cap_mrds: 2845, beta: 0.87 },
      { symbol: 'ETIT', name: 'ECOBANK TRANS. INC.', price: 19, change_pct: -5.00, volume: 850000, sector: 'Banque', country: 'TG', cap_mrds: 1250, beta: 1.15 },
      { symbol: 'SIBC', name: 'SOCIETE IVOIRIENNE DE BANQUE', price: 5400, change_pct: 0.00, volume: 3200, sector: 'Banque', country: 'CI', cap_mrds: 320, beta: 0.95 },
      { symbol: 'BOAB', name: 'BANK OF AFRICA BF', price: 7100, change_pct: 2.16, volume: 11200, sector: 'Banque', country: 'BF', cap_mrds: 410, beta: 0.92 },
      { symbol: 'PALC', name: 'PALM CI', price: 6800, change_pct: -0.73, volume: 4500, sector: 'Agro-industrie', country: 'CI', cap_mrds: 520, beta: 0.78 },
      { symbol: 'SAFC', name: 'SAFCA CI', price: 215, change_pct: 0.94, volume: 8900, sector: 'Finance', country: 'CI', cap_mrds: 180, beta: 1.05 },
      { symbol: 'SGBC', name: 'SG CI', price: 18500, change_pct: 0.54, volume: 2100, sector: 'Banque', country: 'CI', cap_mrds: 680, beta: 0.88 },
      { symbol: 'ORAC', name: 'ORANGE CI', price: 2500, change_pct: 1.21, volume: 15600, sector: 'Télécom', country: 'CI', cap_mrds: 1450, beta: 0.82 },
      { symbol: 'TTLC', name: 'TOTAL CI', price: 2400, change_pct: -0.42, volume: 3400, sector: 'Distribution', country: 'CI', cap_mrds: 290, beta: 0.95 },
      { symbol: 'SLBC', name: 'SOLEIL CI', price: 850, change_pct: 2.41, volume: 12000, sector: 'Agro-industrie', country: 'CI', cap_mrds: 125, beta: 0.72 },
      { symbol: 'NSBC', name: 'NESTLE CI', price: 4200, change_pct: 0.24, volume: 1800, sector: 'Agro-industrie', country: 'CI', cap_mrds: 210, beta: 0.65 },
      { symbol: 'CIEC', name: 'CIE CI', price: 225, change_pct: -1.32, volume: 25000, sector: 'Utilities', country: 'CI', cap_mrds: 340, beta: 0.55 },
    ];
  }

  /**
   * Charge les tickers depuis l'API (avec fallback sur données locales)
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
          cap: t.cap_mrds || 0,
          // Données par défaut si pas dans l'API
          high: t.price ? t.price * 1.01 : 0,
          low: t.price ? t.price * 0.99 : 0,
          per: '10.0x',
          beta: 1.0
        }));
        console.log(`[Market] ✓ ${this.stocks.length} tickers chargés depuis l'API`);
        return true;
      }
    } catch (error) {
      console.warn('[Market] API indisponible, utilisation des données locales');
    }
    
    // Fallback : données locales
    this.stocks = this.fallbackStocks.map(s => ({
      ticker: s.symbol,
      name: s.name,
      price: s.price,
      change: s.change_pct,
      volume: s.volume,
      sector: s.sector,
      country: s.country,
      cap: s.cap_mrds,
      high: s.price * 1.01,
      low: s.price * 0.99,
      per: '10.0x',
      beta: s.beta
    }));
    return false;
  }

  /**
   * Récupère les données OHLCV pour un ticker
   */
  async loadOHLCV(symbol, limit = 365) {
    try {
      return await api.getOHLCV(symbol, limit);
    } catch (error) {
      console.warn(`[Market] OHLCV ${symbol} indisponible, génération locale`);
      const stock = this.stocks.find(s => s.ticker === symbol);
      if (stock && typeof generateOHLCV === 'function') {
        return generateOHLCV(stock.price, limit);
      }
      return [];
    }
  }

  /**
   * Sélectionne un ticker
   */
  selectTicker(symbol) {
    this.selectedTicker = symbol;
    if (typeof renderWatchlist === 'function') renderWatchlist();
    if (typeof renderTickerDetail === 'function') renderTickerDetail();
    if (typeof rebuildCharts === 'function') rebuildCharts();
  }

  /**
   * Récupère le ticker sélectionné
   */
  getSelected() {
    return this.stocks.find(s => s.ticker === this.selectedTicker) || this.stocks[0];
  }

  /**
   * Rafraîchit les prix (simulation locale pour l'instant)
   */
  refreshPrices() {
    this.stocks.forEach(s => {
      const delta = (Math.random() - 0.5) * 0.4;
      s.change = +(s.change + delta).toFixed(2);
      s.price = Math.round(s.price * (1 + delta / 100));
    });
  }
}

// Instance globale
const market = new MarketManager();
