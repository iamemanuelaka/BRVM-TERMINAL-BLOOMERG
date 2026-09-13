/**
 * ═══════════════════════════════════════════════════════════════
 * LEADERBOARD ENGINE — Classe les traders et attribue des badges
 * ═══════════════════════════════════════════════════════════════
 */

class LeaderboardEngine {
  constructor() {
    this.periods = {
      '1M': 30,
      '3M': 90,
      '6M': 180,
      '1Y': 365,
      'ALL': 9999
    };
    this.currentPeriod = 'ALL';
    this.currentSort = 'composite';
  }

  /**
   * Récupère les prédictions scorées pour une période donnée
   */
  getScoredPredictions(period = 'ALL') {
    const days = this.periods[period] || 9999;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    return PREDICTIONS.filter(p => 
      p.status === 'scored' && 
      p.scoredAt && 
      new Date(p.scoredAt) >= cutoff
    );
  }

  /**
   * Agrège les stats par trader
   */
  aggregateByTrader(period = 'ALL') {
    const preds = this.getScoredPredictions(period);
    const traders = {};

    preds.forEach(p => {
      if (!traders[p.author]) {
        traders[p.author] = {
          name: p.author,
          totalPreds: 0,
          hits: 0,
          misses: 0,
          totalPnl: 0,
          wins: [],
          losses: [],
          symbols: new Set(),
          avgConfidence: 0,
          confidences: [],
          bestTrade: null,
          worstTrade: null,
        };
      }

      const t = traders[p.author];
      t.totalPreds++;
      t.symbols.add(p.symbol);
      t.confidences.push(p.conf);
      t.totalPnl += p.pnlPct || 0;

      if (p.hitTarget) {
        t.hits++;
        t.wins.push(p.pnlPct || 0);
      } else {
        t.misses++;
        t.losses.push(p.pnlPct || 0);
      }

      if (!t.bestTrade || (p.pnlPct || 0) > t.bestTrade.pnl) {
        t.bestTrade = { symbol: p.symbol, pnl: p.pnlPct || 0 };
      }
      if (!t.worstTrade || (p.pnlPct || 0) < t.worstTrade.pnl) {
        t.worstTrade = { symbol: p.symbol, pnl: p.pnlPct || 0 };
      }
    });

    // Calcul des métriques finales
    Object.values(traders).forEach(t => {
      t.hitRate = t.totalPreds > 0 ? (t.hits / t.totalPreds) * 100 : 0;
      t.avgPnl = t.totalPreds > 0 ? t.totalPnl / t.totalPreds : 0;
      t.avgConfidence = t.confidences.length > 0 
        ? t.confidences.reduce((a, b) => a + b, 0) / t.confidences.length 
        : 0;
      
      // Profit Factor = Moyenne gains / Moyenne pertes
      const avgWin = t.wins.length > 0 ? t.wins.reduce((a, b) => a + b, 0) / t.wins.length : 0;
      const avgLoss = t.losses.length > 0 ? Math.abs(t.losses.reduce((a, b) => a + b, 0) / t.losses.length) : 0;
      t.profitFactor = avgLoss > 0 ? avgWin / avgLoss : (avgWin > 0 ? 99 : 0);

      // Calibration = corrélation entre confiance et réussite
      t.calibration = t.avgConfidence > 0 ? (t.hitRate / t.avgConfidence) * 100 : 0;

      // ─── SCORE COMPOSITE (0-100) ───
      // 40% Précision + 25% P&L normalisé + 20% Calibration + 15% Profit Factor
      const precisionScore = Math.min(100, t.hitRate);
      const pnlScore = Math.min(100, Math.max(0, (t.avgPnl + 20) * 2.5)); // -20% → 0, +20% → 100
      const calibScore = Math.min(100, t.calibration);
      const pfScore = Math.min(100, t.profitFactor * 33); // PF 3 = 100

      t.compositeScore = Math.round(
        precisionScore * 0.40 +
        pnlScore * 0.25 +
        calibScore * 0.20 +
        pfScore * 0.15
      );

      // ─── BADGES ───
      t.badges = this.computeBadges(t);
    });

    return Object.values(traders);
  }

  /**
   * Attribue des badges selon les performances
   */
  computeBadges(trader) {
    const badges = [];

    if (trader.hitRate >= 80 && trader.totalPreds >= 5) {
      badges.push({ icon: '🎯', name: 'SNIPER', desc: 'Précision > 80%' });
    }
    if (trader.totalPnl >= 50) {
      badges.push({ icon: '🐋', name: 'WHALE', desc: 'P&L > 50%' });
    }
    if (trader.totalPreds >= 20) {
      badges.push({ icon: '🏛️', name: 'VÉTÉRAN', desc: '20+ prédictions' });
    }
    if (trader.profitFactor >= 2 && trader.totalPreds >= 5) {
      badges.push({ icon: '💎', name: 'DIAMANT', desc: 'Profit Factor > 2' });
    }
    if (trader.calibration >= 90 && trader.totalPreds >= 5) {
      badges.push({ icon: '🧘', name: 'ZEN', desc: 'Confiance calibrée' });
    }
    if (trader.symbols.size >= 5) {
      badges.push({ icon: '🌍', name: 'DIVERSIFIÉ', desc: '5+ tickers' });
    }
    if (trader.worstTrade && trader.worstTrade.pnl > -10 && trader.totalPreds >= 3) {
      badges.push({ icon: '🛡️', name: 'RISK-MGR', desc: 'Perte max < 10%' });
    }
    if (trader.hitRate >= 90 && trader.totalPreds >= 10) {
      badges.push({ icon: '👑', name: 'LÉGende', desc: 'Précision > 90%' });
    }

    return badges;
  }

  /**
   * Trie les traders selon le critère choisi
   */
  sortTraders(traders, sortBy = 'composite') {
    const sorted = [...traders];
    switch (sortBy) {
      case 'composite':
        sorted.sort((a, b) => b.compositeScore - a.compositeScore);
        break;
      case 'hitRate':
        sorted.sort((a, b) => b.hitRate - a.hitRate);
        break;
      case 'pnl':
        sorted.sort((a, b) => b.totalPnl - a.totalPnl);
        break;
      case 'preds':
        sorted.sort((a, b) => b.totalPreds - a.totalPreds);
        break;
      case 'profitFactor':
        sorted.sort((a, b) => b.profitFactor - a.profitFactor);
        break;
    }
    return sorted;
  }

  /**
   * Change la période et rafraîchit
   */
  setPeriod(period) {
    this.currentPeriod = period;
    if (typeof renderLeaderboard === 'function') renderLeaderboard();
  }

  /**
   * Change le tri et rafraîchit
   */
  setSort(sortBy) {
    this.currentSort = sortBy;
    if (typeof renderLeaderboard === 'function') renderLeaderboard();
  }
}

// Instance globale
const leaderboardEngine = new LeaderboardEngine();

/**
 * Rendu UI du leaderboard
 */
function renderLeaderboard() {
  const container = document.getElementById('leaderboard-content');
  if (!container) return;

  const period = leaderboardEngine.currentPeriod;
  const sortBy = leaderboardEngine.currentSort;
  const traders = leaderboardEngine.sortTraders(
    leaderboardEngine.aggregateByTrader(period),
    sortBy
  );

  // Mise à jour des boutons actifs
  document.querySelectorAll('.lb-period-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.period === period);
  });
  document.querySelectorAll('.lb-sort-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.sort === sortBy);
  });

  if (traders.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:40px;color:var(--muted)">
        <div style="font-size:40px;margin-bottom:12px">🏆</div>
        <div style="font-size:12px;margin-bottom:8px">Aucun trader classé pour cette période</div>
        <div style="font-size:10px">Les prédictions sont scorées automatiquement à leur expiration.</div>
        <div style="font-size:10px;margin-top:4px">Créez des prédictions avec un horizon court pour tester !</div>
      </div>
    `;
    return;
  }

  // Top 3 podium
  const podium = traders.slice(0, 3);
  const rest = traders.slice(3);

  container.innerHTML = `
    <!-- PODIUM -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px">
      ${podium.map((t, i) => {
        const medals = ['🥇', '🥈', '🥉'];
        const colors = ['#ffd700', '#c0c0c0', '#cd7f32'];
        return `
          <div style="background:var(--panel-2);border:2px solid ${colors[i]};padding:12px;text-align:center;position:relative">
            <div style="position:absolute;top:-10px;left:50%;transform:translateX(-50%);background:${colors[i]};color:#000;padding:2px 8px;font-size:16px;border-radius:50%">
              ${medals[i]}
            </div>
            <div style="color:var(--cyan);font-weight:bold;font-size:12px;margin-top:8px">${t.name}</div>
            <div style="color:${colors[i]};font-size:24px;font-weight:bold;margin:8px 0">${t.compositeScore}</div>
            <div style="color:var(--muted);font-size:9px">SCORE COMPOSITE</div>
            <div style="display:flex;justify-content:space-around;margin-top:8px;font-size:10px">
              <div><div style="color:var(--up)">${t.hitRate.toFixed(0)}%</div><div style="color:var(--dim);font-size:8px">PRÉCISION</div></div>
              <div><div style="color:${t.totalPnl >= 0 ? 'var(--up)' : 'var(--down)'}">${t.totalPnl >= 0 ? '+' : ''}${t.totalPnl.toFixed(1)}%</div><div style="color:var(--dim);font-size:8px">P&L</div></div>
              <div><div style="color:var(--text)">${t.totalPreds}</div><div style="color:var(--dim);font-size:8px">PRÉDS</div></div>
            </div>
            ${t.badges.length > 0 ? `
              <div style="margin-top:8px;display:flex;gap:4px;justify-content:center;flex-wrap:wrap">
                ${t.badges.slice(0, 3).map(b => `<span title="${b.name}: ${b.desc}" style="font-size:14px;cursor:help">${b.icon}</span>`).join('')}
              </div>
            ` : ''}
          </div>
        `;
      }).join('')}
    </div>

    <!-- CLASSEMENT COMPLET -->
    <table class="trade-tbl">
      <thead>
        <tr>
          <th>#</th>
          <th>TRADER</th>
          <th>SCORE</th>
          <th>PRÉCISION</th>
          <th>P&L</th>
          <th>PRÉDS</th>
          <th>PF</th>
          <th>BADGES</th>
        </tr>
      </thead>
      <tbody>
        ${traders.map((t, i) => `
          <tr>
            <td style="color:var(--accent);font-weight:bold">${i + 1}</td>
            <td style="color:var(--cyan);font-weight:bold">${t.name}</td>
            <td style="color:var(--accent);font-weight:bold;font-size:14px">${t.compositeScore}</td>
            <td class="${t.hitRate >= 60 ? 'pnl-pos' : t.hitRate < 40 ? 'pnl-neg' : ''}">${t.hitRate.toFixed(1)}%</td>
            <td class="${t.totalPnl >= 0 ? 'pnl-pos' : 'pnl-neg'}">${t.totalPnl >= 0 ? '+' : ''}${t.totalPnl.toFixed(1)}%</td>
            <td>${t.totalPreds}</td>
            <td>${t.profitFactor.toFixed(2)}</td>
            <td style="font-size:14px">${t.badges.map(b => `<span title="${b.name}: ${b.desc}" style="cursor:help">${b.icon}</span>`).join(' ')}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>

    <!-- STATS GLOBALES -->
    <div style="margin-top:16px;display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
      <div class="pcard">
        <div class="lb">TRADERS ACTIFS</div>
        <div class="vl" style="font-size:18px">${traders.length}</div>
      </div>
      <div class="pcard">
        <div class="lb">PRÉDICTIONS SCORÉES</div>
        <div class="vl" style="font-size:18px">${traders.reduce((s, t) => s + t.totalPreds, 0)}</div>
      </div>
      <div class="pcard">
        <div class="lb">HIT RATE MOYEN</div>
        <div class="vl" style="font-size:18px">${(traders.reduce((s, t) => s + t.hitRate, 0) / traders.length).toFixed(1)}%</div>
      </div>
      <div class="pcard">
        <div class="lb">P&L MOYEN</div>
        <div class="vl" style="font-size:18px">${(traders.reduce((s, t) => s + t.avgPnl, 0) / traders.length).toFixed(1)}%</div>
      </div>
    </div>
  `;
}
