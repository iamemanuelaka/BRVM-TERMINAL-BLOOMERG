/**
 * BRVM TERMINAL - API CLIENT (avec authentification)
 */

const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8000/api/v1'
  : '/api/v1';

class BRVMClient {
  constructor() {
    this.baseURL = API_BASE;
    this.token = localStorage.getItem('brvm_token');
    this.user = JSON.parse(localStorage.getItem('brvm_user') || 'null');
    this.isConnected = false;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, { ...options, headers });

      if (response.status === 401) {
        // Token expiré ou invalide
        this.logout();
        throw new Error('Session expirée, veuillez vous reconnecter');
      }

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

  // ═══════════════════════════════════════════════════
  // AUTH
  // ═══════════════════════════════════════════════════
  async register(username, email, password) {
    const result = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password })
    });
    this.setAuth(result);
    return result;
  }

  async login(username, password) {
    const result = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.setAuth(result);
    return result;
  }

  setAuth(result) {
    this.token = result.access_token;
    this.user = result.user;
    localStorage.setItem('brvm_token', this.token);
    localStorage.setItem('brvm_user', JSON.stringify(this.user));
  }

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('brvm_token');
    localStorage.removeItem('brvm_user');
    if (typeof onAuthChange === 'function') onAuthChange();
  }

  isAuthenticated() {
    return !!this.token && !!this.user;
  }

  async getMe() {
    return this.request('/auth/me');
  }

  async getMyProfile() {
    return this.request('/auth/me/profile');
  }

  async updateProfile(data) {
    return this.request('/auth/me/profile', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  // ═══════════════════════════════════════════════════
  // API KEYS
  // ═══════════════════════════════════════════════════
  async createAPIKey(name) {
    return this.request('/auth/api-keys', {
      method: 'POST',
      body: JSON.stringify({ name })
    });
  }

  async listAPIKeys() {
    return this.request('/auth/api-keys');
  }

  async deleteAPIKey(keyId) {
    return this.request(`/auth/api-keys/${keyId}`, { method: 'DELETE' });
  }

  // ═══════════════════════════════════════════════════
  // MARKET
  // ═══════════════════════════════════════════════════
  async getTickers() {
    return this.request('/market/tickers');
  }

  async getOHLCV(symbol, limit = 365) {
    return this.request(`/market/${symbol}/ohlcv?limit=${limit}`);
  }

  async searchTickers(query) {
    return this.request(`/market/search?q=${encodeURIComponent(query)}`);
  }

  // ═══════════════════════════════════════════════════
  // PREDICTIONS
  // ═══════════════════════════════════════════════════
  async getPredictions(filters = {}) {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.symbol) params.append('symbol', filters.symbol);
    if (filters.author) params.append('author', filters.author);
    if (filters.limit) params.append('limit', filters.limit);
    const qs = params.toString();
    return this.request(`/predictions/${qs ? '?' + qs : ''}`);
  }

  async createPrediction(data) {
    return this.request('/predictions/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getPredictionStats() {
    return this.request('/predictions/stats');
  }

  // ═══════════════════════════════════════════════════
  // LEADERBOARD
  // ═══════════════════════════════════════════════════
  async getLeaderboard(period = 'ALL', limit = 50) {
    return this.request(`/auth/leaderboard?period=${period}&limit=${limit}`);
  }

  async getPublicProfile(username) {
    return this.request(`/auth/profiles/${username}`);
  }

  // ═══════════════════════════════════════════════════
  // HEALTH
  // ═══════════════════════════════════════════════════
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

const api = new BRVMClient();
