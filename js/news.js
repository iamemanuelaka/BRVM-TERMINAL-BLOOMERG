/**
 * BRVM TERMINAL - NEWS MODULE
 * Gestion des actualités avec filtres, sentiment et alertes
 */

class NewsManager {
  constructor() {
    this.news = [];
    this.filters = {
      source: null,
      sentiment: null,
      ticker: null,
      search: ''
    };
    this.alerts = [];
    this.stats = null;
  }

  async load() {
    try {
      const [news, stats] = await Promise.all([
        api.request('/news/?limit=100'),
        api.request('/news/stats')
      ]);
      this.news = news;
      this.stats = stats;
      
      // Charger les alertes si connecté
      if (api.isAuthenticated()) {
        try {
          this.alerts = await api.request('/news/alerts');
        } catch (e) {
          this.alerts = [];
        }
      }
      
      return true;
    } catch (error) {
      console.warn('[News] Erreur chargement:', error);
      return false;
    }
  }

  async triggerScrape() {
    try {
      const result = await api.request('/news/scrape', { method: 'POST' });
      await this.load();
      return result;
    } catch (error) {
      console.error('[News] Erreur scraping:', error);
      throw error;
    }
  }

  setFilter(key, value) {
    this.filters[key] = value;
    if (typeof renderNews === 'function') renderNews();
  }

  getFiltered() {
    let filtered = [...this.news];

    if (this.filters.source) {
      filtered = filtered.filter(n => n.source === this.filters.source);
    }
    if (this.filters.sentiment) {
      filtered = filtered.filter(n => n.sentiment === this.filters.sentiment);
    }
    if (this.filters.ticker) {
      filtered = filtered.filter(n => 
        n.tickers && n.tickers.includes(this.filters.ticker)
      );
    }
    if (this.filters.search) {
      const q = this.filters.search.toLowerCase();
      filtered = filtered.filter(n =>
        n.title.toLowerCase().includes(q) ||
        (n.summary && n.summary.toLowerCase().includes(q))
      );
    }

    return filtered;
  }

  getSentimentColor(sentiment) {
    switch (sentiment) {
      case 'positive': return 'var(--up)';
      case 'negative': return 'var(--down)';
      case 'neutral': return 'var(--muted)';
      default: return 'var(--muted)';
    }
  }

  getSentimentIcon(sentiment) {
    switch (sentiment) {
      case 'positive': return '📈';
      case 'negative': return '📉';
      case 'neutral': return '➡️';
      default: return '❓';
    }
  }

  formatTime(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins}min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    return date.toLocaleDateString('fr-FR');
  }

  async createAlert(data) {
    const alert = await api.request('/news/alerts', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    this.alerts.push(alert);
    return alert;
  }

  async deleteAlert(alertId) {
    await api.request(`/news/alerts/${alertId}`, { method: 'DELETE' });
    this.alerts = this.alerts.filter(a => a.id !== alertId);
  }
}

const newsManager = new NewsManager();

/* ═══════════════════════════════════════════════════════
   RENDU UI
   ═══════════════════════════════════════════════════════ */
function renderNews() {
  const filtered = newsManager.getFiltered();
  const stats = newsManager.stats;

  // Sidebar (version courte)
  const sidebar = document.getElementById('news-sb');
  if (sidebar) {
    sidebar.innerHTML = filtered.slice(0, 4).map(n => renderNewsCard(n, true)).join('')
      || '<p style="color:var(--muted);text-align:center;padding:10px;font-size:10px">Aucune news</p>';
  }

  // Vue complète (F2)
  const full = document.getElementById('news-full');
  if (!full) return;

  full.innerHTML = `
    <!-- STATS -->
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-bottom:12px">
      <div class="pcard">
        <div class="lb">TOTAL</div>
        <div class="vl" style="font-size:18px">${stats?.total || 0}</div>
      </div>
      <div class="pcard">
        <div class="lb">📈 POSITIF</div>
        <div class="vl" style="font-size:18px;color:var(--up)">${stats?.positive || 0}</div>
        <div class="sb">${stats?.sentiment_ratio?.positive || 0}%</div>
      </div>
      <div class="pcard">
        <div class="lb">📉 NÉGATIF</div>
        <div class="vl" style="font-size:18px;color:var(--down)">${stats?.negative || 0}</div>
        <div class="sb">${stats?.sentiment_ratio?.negative || 0}%</div>
      </div>
      <div class="pcard">
        <div class="lb">➡️ NEUTRE</div>
        <div class="vl" style="font-size:18px">${stats?.neutral || 0}</div>
        <div class="sb">${stats?.sentiment_ratio?.neutral || 0}%</div>
      </div>
      <div class="pcard">
        <div class="lb">24H</div>
        <div class="vl" style="font-size:18px">${stats?.last_24h || 0}</div>
      </div>
    </div>

    <!-- FILTRES -->
    <div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:end">
      <div style="flex:1;min-width:200px">
        <label style="display:block;color:var(--dim);font-size:9px;margin-bottom:2px;text-transform:uppercase">🔍 RECHERCHE</label>
        <input type="text" id="news-search" placeholder="Rechercher..." 
          value="${newsManager.filters.search || ''}"
          oninput="newsManager.setFilter('search', this.value)"
          style="width:100%;background:var(--bg);color:var(--text);border:1px solid var(--border-2);padding:4px 6px;font-family:inherit;font-size:11px;outline:none">
      </div>
      <div>
        <label style="display:block;color:var(--dim);font-size:9px;margin-bottom:2px;text-transform:uppercase">SOURCE</label>
        <select onchange="newsManager.setFilter('source', this.value || null)"
          style="background:var(--bg);color:var(--text);border:1px solid var(--border-2);padding:4px 6px;font-family:inherit;font-size:11px;outline:none">
          <option value="">Toutes</option>
          <option value="brvm_mock" ${newsManager.filters.source === 'brvm_mock' ? 'selected' : ''}>BRVM</option>
          <option value="bceao_mock" ${newsManager.filters.source === 'bceao_mock' ? 'selected' : ''}>BCEAO</option>
          <option value="business_mock" ${newsManager.filters.source === 'business_mock' ? 'selected' : ''}>Business</option>
          <option value="market_mock" ${newsManager.filters.source === 'market_mock' ? 'selected' : ''}>Market</option>
        </select>
      </div>
      <div>
        <label style="display:block;color:var(--dim);font-size:9px;margin-bottom:2px;text-transform:uppercase">SENTIMENT</label>
        <select onchange="newsManager.setFilter('sentiment', this.value || null)"
          style="background:var(--bg);color:var(--text);border:1px solid var(--border-2);padding:4px 6px;font-family:inherit;font-size:11px;outline:none">
          <option value="">Tous</option>
          <option value="positive" ${newsManager.filters.sentiment === 'positive' ? 'selected' : ''}>📈 Positif</option>
          <option value="negative" ${newsManager.filters.sentiment === 'negative' ? 'selected' : ''}>📉 Négatif</option>
          <option value="neutral" ${newsManager.filters.sentiment === 'neutral' ? 'selected' : ''}>➡️ Neutre</option>
        </select>
      </div>
      <div>
        <label style="display:block;color:var(--dim);font-size:9px;margin-bottom:2px;text-transform:uppercase">TICKER</label>
        <select onchange="newsManager.setFilter('ticker', this.value || null)"
          style="background:var(--bg);color:var(--text);border:1px solid var(--border-2);padding:4px 6px;font-family:inherit;font-size:11px;outline:none">
          <option value="">Tous</option>
          ${(market.stocks || []).map(s => 
            `<option value="${s.ticker}" ${newsManager.filters.ticker === s.ticker ? 'selected' : ''}>${s.ticker}</option>`
          ).join('')}
        </select>
      </div>
      <button class="btn btn-sm" onclick="triggerScrape()" style="width:auto;padding:6px 12px;background:var(--cyan);height:26px">
        🕷️ SCRAPER
      </button>
    </div>

    <!-- TIMELINE -->
    <div style="color:var(--muted);font-size:10px;margin-bottom:8px">
      ${filtered.length} article${filtered.length > 1 ? 's' : ''} trouvé${filtered.length > 1 ? 's' : ''}
    </div>
    <div id="news-timeline">
      ${filtered.length > 0 
        ? filtered.map(n => renderNewsCard(n, false)).join('')
        : '<div style="text-align:center;padding:40px;color:var(--muted)">Aucune news ne correspond aux filtres</div>'
      }
    </div>
  `;
}

function renderNewsCard(news, compact = false) {
  const sentimentColor = newsManager.getSentimentColor(news.sentiment);
  const sentimentIcon = newsManager.getSentimentIcon(news.sentiment);
  const time = newsManager.formatTime(news.published_at);

  if (compact) {
    return `
      <div class="news-item ${news.sentiment === 'positive' ? 'hot' : ''}" style="border-left-color:${sentimentColor}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">
          <span style="color:${sentimentColor};font-size:9px">${sentimentIcon} ${time}</span>
          <span style="color:var(--dim);font-size:9px">${news.source}</span>
        </div>
        <div style="color:var(--text);font-weight:600;font-size:10px;line-height:1.3">${news.title}</div>
        ${news.tickers && news.tickers.length > 0 ? `
          <div style="margin-top:3px;display:flex;gap:3px;flex-wrap:wrap">
            ${news.tickers.map(t => `<span style="background:var(--panel-3);color:var(--cyan);padding:1px 4px;font-size:8px;border-radius:2px">${t}</span>`).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }

  return `
    <div style="background:var(--panel-2);border:1px solid var(--border);border-left:3px solid ${sentimentColor};padding:12px;margin-bottom:8px;transition:all 0.15s" 
      onmouseover="this.style.borderColor='${sentimentColor}'" 
      onmouseout="this.style.borderColor='var(--border)';this.style.borderLeftColor='${sentimentColor}'">
      <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:6px">
        <div style="flex:1">
          <div style="display:flex;gap:6px;align-items:center;margin-bottom:4px">
            <span style="color:${sentimentColor};font-size:11px;font-weight:bold">${sentimentIcon} ${news.sentiment.toUpperCase()}</span>
            <span style="color:var(--dim);font-size:9px">·</span>
            <span style="color:var(--dim);font-size:9px">${time}</span>
            <span style="color:var(--dim);font-size:9px">·</span>
            <span style="color:var(--accent);font-size:9px;font-weight:bold">${news.source}</span>
            ${news.sentiment_score !== 0 ? `
              <span style="color:var(--dim);font-size:9px">· Score: ${news.sentiment_score.toFixed(2)}</span>
            ` : ''}
          </div>
          <h4 style="color:var(--text);font-size:12px;font-weight:bold;line-height:1.4;margin:0">${news.title}</h4>
        </div>
      </div>
      <p style="color:var(--muted);font-size:11px;line-height:1.5;margin:6px 0">${news.summary || news.content || ''}</p>
      ${news.tickers && news.tickers.length > 0 ? `
        <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:8px">
          ${news.tickers.map(t => `
            <span onclick="newsManager.setFilter('ticker','${t}');document.querySelector('[data-view=equity]').click();market.selectTicker('${t}')"
              style="background:var(--panel-3);color:var(--cyan);padding:2px 8px;font-size:10px;border-radius:3px;cursor:pointer;border:1px solid var(--border-2);transition:all 0.1s"
              onmouseover="this.style.borderColor='var(--accent)'"
              onmouseout="this.style.borderColor='var(--border-2)'">
              ${t}
            </span>
          `).join('')}
        </div>
      ` : ''}
      ${news.keywords && news.keywords.length > 0 ? `
        <div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap">
          ${news.keywords.slice(0, 5).map(k => `
            <span style="color:var(--dim);font-size:9px;font-style:italic">#${k}</span>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

async function triggerScrape() {
  try {
    toast('🕷️ Scraping en cours...');
    const result = await newsManager.triggerScrape();
    renderNews();
    toast('✓ ' + result.message);
  } catch (error) {
    toast('✗ Erreur scraping: ' + error.message);
  }
}
