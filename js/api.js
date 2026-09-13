/**
 * ═══════════════════════════════════════════════════════════════
 * BRVM TERMINAL - API CLIENT
 * Client centralisé pour tous les appels au backend FastAPI
 * ═══════════════════════════════════════════════════════════════
 */

const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000/api/v1'
  : '/api/v1';  // En production, même domaine

class BRVMClient {
  constructor() {
    this.baseURL = API_BASE;
    this.token = localStorage.getItem('brvm_token');
    this.isConnected = false;
  }

  /**
   * Effectue une requête HTTP avec gestion d'erreurs
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    // Ajouter le token JWT si présent
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Erreur serveur' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      this.isConnected = true;
      return await response.json();
    } catch (error) {
      this.isConnected = false;
      console.error(`[API] ${endpoint}:`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════
  // MARKET ENDPOINTS
  // ═══════════════════════════════════════════════════════════

  /**
   * Récupère toutes les valeurs BRVM avec leurs cotations
   */
  async getTickers() {
    return this.request('/market/tickers');
  }

  /**
   * Récupère les données OHLCV pour un ticker (pour les graphiques)
   */
  async getOHLCV(symbol, limit = 365) {
    return this.request(`/market/${symbol}/ohlcv?limit=${limit}`);
  }

  /**
   * Recherche des tickers par nom ou symbole
   */
  async searchTickers(query) {
    return this.request(`/market/search?q=${encodeURIComponent(query)}`);
  }

  // ═══════════════════════════════════════════════════════════
  // PREDICTIONS ENDPOINTS
  // ═══════════════════════════════════════════════════════════

  /**
   * Récupère toutes les prédictions (avec filtres optionnels)
   */
  async getPredictions(filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.symbol) params.append('symbol', filters.symbol);
    if (filters.limit) params.append('limit', filters.limit);
    
    const queryString = params.toString();
    return this.request(`/predictions/${queryString ? '?' + queryString : ''}`);
  }

  /**
   * Crée une nouvelle prédiction
   */
  async createPrediction(data) {
    return this.request('/predictions/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  /**
   * Récupère les statistiques globales des prédictions
   */
  async getPredictionStats() {
    return this.request('/predictions/stats');
  }

  // ═══════════════════════════════════════════════════════════
  // AUTH ENDPOINTS (pour plus tard)
  // ═══════════════════════════════════════════════════════════

  async register(username, email, password) {
    const result = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password })
    });
    this.token = result.access_token;
    localStorage.setItem('brvm_token', this.token);
    return result;
  }

  async login(username, password) {
    const result = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.token = result.access_token;
    localStorage.setItem('brvm_token', this.token);
    return result;
  }

  logout() {
    this.token = null;
    localStorage.removeItem('brvm_token');
  }

  // ═══════════════════════════════════════════════════════════
  // HEALTH CHECK
  // ═══════════════════════════════════════════════════════════

  async healthCheck() {
    try {
      const response = await fetch(`${this.baseURL.replace('/api/v1', '')}/health`);
      this.isConnected = response.ok;
      return this.isConnected;
    } catch {
      this.isConnected = false;
      return false;
    }
  }
}

// Instance globale
const api = new BRVMClient();
