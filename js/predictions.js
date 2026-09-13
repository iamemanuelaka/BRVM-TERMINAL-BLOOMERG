/**
 * ═══════════════════════════════════════════════════════════════
 * BRVM TERMINAL - PREDICTIONS MODULE
 * Gestion des prédictions via l'API backend
 * ═══════════════════════════════════════════════════════════════
 */

class PredictionsManager {
  constructor() {
    this.predictions = [];
    this.useAPI = true; // true = backend, false = localStorage
  }

  /**
   * Charge les prédictions depuis l'API (avec fallback localStorage)
   */
  async load() {
    try {
      const preds = await api.getPredictions({ limit: 200 });
      this.predictions = preds.map(p => this.normalizePrediction(p));
      this.useAPI = true;
      console.log(`[Predictions] ✓ ${this.predictions.length} prédictions chargées depuis l'API`);
      return true;
    } catch (error) {
      console.warn('[Predictions] API indisponible, utilisation du localStorage');
      this.useAPI = false;
      const stored = localStorage.getItem('brvm_preds');
      if (stored) {
        this.predictions = JSON.parse(stored).map(p => this.normalizePrediction(p));
      }
      return false;
    }
  }

  /**
   * Normalise une prédiction (format API ↔ format local)
   */
  normalizePrediction(p) {
    return {
      id: p.id,
      author: p.author_name || p.author || 'Anonyme',
      symbol: p.symbol,
      dir: p.direction,
      entryPrice: p.current_price || p.entryPrice,
      target: p.target_price || p.target,
      horizon: p.horizon_days || p.horizon,
      conf: p.confidence || p.conf,
      thesis: p.thesis || '',
      type: (p.direction || p.dir) === 'LONG' ? 'BULLISH' : 'BEARISH',
      status: p.status || 'active',
      createdAt: p.created_at || p.createdAt || new Date().toISOString(),
      expiresAt: p.expires_at || p.expiresAt,
      // Champs de scoring
      actualPrice: p.actual_price || p.actualPrice,
      pnlPct: p.pnl_pct || p.pnlPct,
      pctError: p.pct_error || p.pctError,
      hitTarget: p.hit_target || p.hitTarget,
      scoredAt: p.scored_at || p.scoredAt
    };
  }

  /**
   * Crée une nouvelle prédiction
   */
  async create(data) {
    const payload = {
      author_name: data.author,
      symbol: data.symbol,
      direction: data.dir,
      current_price: data.entryPrice,
      target_price: data.target,
      stop_loss: data.stopLoss || null,
      confidence: data.conf,
      horizon_days: data.horizon,
      thesis: data.thesis || '',
      tags: data.tags || []
    };

    if (this.useAPI) {
      try {
        const created = await api.createPrediction(payload);
        const normalized = this.normalizePrediction(created);
        this.predictions.unshift(normalized);
        console.log('[Predictions] ✓ Prédiction créée via API');
        return normalized;
      } catch (error) {
        console.error('[Predictions] Erreur API:', error);
        throw error;
      }
    } else {
      // Fallback localStorage
      const newPred = this.normalizePrediction({
        ...payload,
        id: Date.now(),
        status: 'active',
        created_at: new Date().toISOString(),
        expires_at: new Date(Date.now() + data.horizon * 24 * 60 * 60 * 1000).toISOString()
      });
      this.predictions.unshift(newPred);
      this.saveLocal();
      return newPred;
    }
  }

  /**
   * Sauvegarde en localStorage (fallback)
   */
  saveLocal() {
    try {
      localStorage.setItem('brvm_preds', JSON.stringify(this.predictions));
    } catch (e) {
      console.warn('[Predictions] Erreur sauvegarde localStorage:', e);
    }
  }

  /**
   * Récupère les statistiques
   */
  async getStats() {
    if (this.useAPI) {
      try {
        return await api.getPredictionStats();
      } catch (error) {
        console.warn('[Predictions] Stats API indisponibles');
      }
    }
    // Calcul local
    const active = this.predictions.filter(p => p.status === 'active').length;
    const scored = this.predictions.filter(p => p.status === 'scored');
    const hits = scored.filter(p => p.hitTarget).length;
    return {
      total: this.predictions.length,
      active,
      scored: scored.length,
      hit_rate_pct: scored.length > 0 ? (hits / scored.length * 100) : 0
    };
  }

  /**
   * Récupère toutes les prédictions (pour le scoring et le leaderboard)
   */
  getAll() {
    return this.predictions;
  }

  /**
   * Met à jour une prédiction (après scoring)
   */
  update(id, updates) {
    const idx = this.predictions.findIndex(p => p.id === id);
    if (idx !== -1) {
      this.predictions[idx] = { ...this.predictions[idx], ...updates };
      if (!this.useAPI) this.saveLocal();
    }
  }
}

// Instance globale
const predictionsManager = new PredictionsManager();
