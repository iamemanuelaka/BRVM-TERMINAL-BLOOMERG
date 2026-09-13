/**
 * ═══════════════════════════════════════════════════════════════
 * SCORING ENGINE — Évalue automatiquement les prédictions expirées
 * ═══════════════════════════════════════════════════════════════
 */

class ScoringEngine {
  constructor() {
    this.lastRun = null;
    this.intervalMs = 60 * 1000; // Vérifie toutes les minutes
  }

  /**
   * Démarre le worker de scoring automatique
   */
  start() {
    console.log('[ScoringEngine] Démarrage du worker...');
    this.run();
    setInterval(() => this.run(), this.intervalMs);
  }

  /**
   * Exécute un cycle de scoring
   */
  run() {
    const now = new Date();
    const expired = PREDICTIONS.filter(p => 
      p.status === 'active' && new Date(p.expiresAt) <= now
    );

    if (expired.length === 0) {
      this.lastRun = now;
      return 0;
    }

    console.log(`[ScoringEngine] ${expired.length} prédiction(s) à scorer`);

    expired.forEach(pred => this.scorePrediction(pred));
    this.lastRun = now;

    // Sauvegarder et rafraîchir l'UI
    if (typeof saveState === 'function') saveState();
    if (typeof renderPredictions === 'function') renderPredictions();
    if (typeof renderLeaderboard === 'function') renderLeaderboard();

    return expired.length;
  }

  /**
   * Score une prédiction individuelle
   */
  scorePrediction(pred) {
    const stock = STOCKS.find(s => s.ticker === pred.symbol);
    if (!stock) {
      console.warn(`[ScoringEngine] Ticker ${pred.symbol} introuvable`);
      return;
    }

    const actualPrice = stock.price;
    const entryPrice = pred.entryPrice || stock.price;
    const targetPrice = pred.target;
    const direction = pred.dir;

    // ─── Calculs de base ───
    const pctError = Math.abs((targetPrice - actualPrice) / actualPrice) * 100;
    
    let pnlPct = 0;
    if (direction === 'LONG') {
      pnlPct = ((actualPrice - entryPrice) / entryPrice) * 100;
    } else if (direction === 'SHORT') {
      pnlPct = ((entryPrice - actualPrice) / entryPrice) * 100;
    }

    // ─── Hit / Miss ───
    let hitTarget = false;
    if (direction === 'LONG') {
      hitTarget = actualPrice >= targetPrice;
    } else if (direction === 'SHORT') {
      hitTarget = actualPrice <= targetPrice;
    }

    // ─── Max Drawdown (simulé avec volatilité) ───
    const volatility = Math.abs(stock.change) / 100 + 0.02;
    const maxDrawdown = -(volatility * Math.sqrt(pred.horizon) * 100);

    // ─── Distance à la cible ───
    const distanceToTarget = ((actualPrice - targetPrice) / targetPrice) * 100;

    // ─── Mise à jour de la prédiction ───
    pred.status = 'scored';
    pred.actualPrice = actualPrice;
    pred.entryPrice = entryPrice;
    pred.pnlPct = +pnlPct.toFixed(2);
    pred.pctError = +pctError.toFixed(2);
    pred.hitTarget = hitTarget;
    pred.maxDrawdown = +maxDrawdown.toFixed(2);
    pred.distanceToTarget = +distanceToTarget.toFixed(2);
    pred.scoredAt = new Date().toISOString();

    console.log(`[ScoringEngine] ✓ ${pred.author} · ${pred.symbol} · ${hitTarget ? 'HIT' : 'MISS'} · P&L: ${pnlPct.toFixed(2)}%`);
  }

  /**
   * Score manuel (pour tester)
   */
  forceScore() {
    const count = this.run();
    if (typeof toast === 'function') {
      toast(count > 0 ? `✓ ${count} prédiction(s) scorée(s)` : 'ℹ Aucune prédiction expirée');
    }
    return count;
  }
}

// Instance globale
const scoringEngine = new ScoringEngine();
