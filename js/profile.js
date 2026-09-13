/**
 * BRVM TERMINAL - PROFILE MODULE
 * Gestion de l'affichage des profils traders publics
 */

class ProfileManager {
    constructor() {
        this.currentUsername = null;
    }

    async loadProfile(username) {
        this.currentUsername = username;
        try {
            const [profile, predictions] = await Promise.all([
                api.request(`/users/${username}/profile`),
                api.request(`/users/${username}/predictions?limit=20`)
            ]);
            this.render(profile, predictions);
        } catch (error) {
            console.error('[Profile] Erreur chargement:', error);
            document.getElementById('profile-content').innerHTML = `
                <div style="text-align:center;padding:40px;color:var(--down)">
                    <div style="font-size:24px;margin-bottom:8px">⚠️</div>
                    <div>Profil introuvable ou privé</div>
                </div>
            `;
        }
    }

    render(profile, predictions) {
        const container = document.getElementById('profile-content');
        if (!container) return;

        // Calcul des badges (même logique que leaderboard)
        const badges = this.computeBadges(profile);

        container.innerHTML = `
            <!-- EN-TÊTE DU PROFIL -->
            <div style="display:flex;gap:16px;align-items:center;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--border-2)">
                <div style="width:60px;height:60px;border-radius:50%;background:var(--accent);color:#000;display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold">
                    ${profile.username.charAt(0).toUpperCase()}
                </div>
                <div style="flex:1">
                    <h2 style="color:var(--text);font-size:18px;margin:0">${profile.display_name || profile.username}</h2>
                    <div style="color:var(--muted);font-size:11px;margin-top:4px">@${profile.username} · ${profile.role || 'TRADER'}</div>
                    ${profile.bio ? `<div style="color:var(--text);font-size:12px;margin-top:8px;font-style:italic">"${profile.bio}"</div>` : ''}
                </div>
                <div style="text-align:right">
                    <div style="color:var(--accent);font-size:24px;font-weight:bold">${profile.composite_score || 0}</div>
                    <div style="color:var(--muted);font-size:10px">SCORE COMPOSITE</div>
                </div>
            </div>

            <!-- STATS CLÉS -->
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:20px">
                <div class="pcard">
                    <div class="lb">PRÉCISION</div>
                    <div class="vl" style="color:${(profile.hit_rate || 0) >= 60 ? 'var(--up)' : 'var(--text)'}">${(profile.hit_rate || 0).toFixed(1)}%</div>
                </div>
                <div class="pcard">
                    <div class="lb">PRÉDICTIONS</div>
                    <div class="vl">${profile.total_predictions || 0}</div>
                </div>
                <div class="pcard">
                    <div class="lb">BADGES</div>
                    <div class="vl" style="font-size:20px">${badges.map(b => b.icon).join(' ') || 'Aucun'}</div>
                </div>
                <div class="pcard">
                    <div class="lb">MEMBRE DEPUIS</div>
                    <div class="vl" style="font-size:14px">${new Date(profile.created_at).toLocaleDateString('fr-FR')}</div>
                </div>
            </div>

            <!-- BADGES DÉTAILLÉS -->
            ${badges.length > 0 ? `
                <div style="margin-bottom:20px">
                    <h4 style="color:var(--cyan);font-size:11px;margin-bottom:8px">🏅 BADGES OBTENUS</h4>
                    <div style="display:flex;gap:8px;flex-wrap:wrap">
                        ${badges.map(b => `
                            <div style="background:var(--panel-2);border:1px solid var(--border-2);padding:6px 10px;border-radius:4px;display:flex;align-items:center;gap:6px" title="${b.desc}">
                                <span style="font-size:16px">${b.icon}</span>
                                <div>
                                    <div style="color:var(--accent);font-size:10px;font-weight:bold">${b.name}</div>
                                    <div style="color:var(--muted);font-size:9px">${b.desc}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <!-- HISTORIQUE DES PRÉDICTIONS -->
            <div>
                <h4 style="color:var(--cyan);font-size:11px;margin-bottom:8px">📜 DERNIÈRES PRÉDICTIONS</h4>
                <div style="max-height:300px;overflow-y:auto">
                    ${predictions.length > 0 ? predictions.map(p => this.renderPredictionCard(p)).join('') : '<p style="color:var(--muted);font-size:11px">Aucune prédiction enregistrée.</p>'}
                </div>
            </div>
        `;
    }

    renderPredictionCard(p) {
        const statusColor = p.status === 'scored' ? (p.hit_target ? 'var(--up)' : 'var(--down)') : 'var(--accent)';
        const statusText = p.status === 'scored' ? (p.hit_target ? '✅ HIT' : '❌ MISS') : '⏳ ACTIVE';
        
        return `
            <div style="background:var(--panel-2);border:1px solid var(--border);padding:8px;margin-bottom:6px;border-left:3px solid ${statusColor}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                    <span style="font-weight:bold;color:var(--text)">${p.symbol}</span>
                    <span style="color:${statusColor};font-size:10px;font-weight:bold">${statusText}</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:10px;color:var(--muted)">
                    <span class="${p.direction === 'LONG' ? 'up' : 'down'}" style="font-weight:bold">${p.direction}</span>
                    <span>Cible: <b style="color:var(--text)">${p.target_price.toLocaleString('fr-FR')}</b></span>
                    <span>Conf: ${p.confidence}%</span>
                </div>
                ${p.status === 'scored' ? `
                    <div style="margin-top:4px;padding-top:4px;border-top:1px solid var(--border-2);font-size:10px;display:flex;justify-content:space-between">
                        <span style="color:var(--dim)">P&L: <b class="${(p.pnl_pct || 0) >= 0 ? 'pnl-pos' : 'pnl-neg'}">${(p.pnl_pct || 0) >= 0 ? '+' : ''}${(p.pnl_pct || 0).toFixed(2)}%</b></span>
                        <span style="color:var(--dim)">Le ${new Date(p.scored_at).toLocaleDateString('fr-FR')}</span>
                    </div>
                ` : `
                    <div style="margin-top:4px;font-size:10px;color:var(--dim)">Expire dans ${p.horizon_days}j</div>
                `}
            </div>
        `;
    }

    computeBadges(profile) {
        const badges = [];
        const hr = profile.hit_rate || 0;
        const tp = profile.total_predictions || 0;
        
        if (hr >= 80 && tp >= 5) badges.push({ icon: '🎯', name: 'SNIPER', desc: 'Précision > 80%' });
        if (tp >= 20) badges.push({ icon: '🏛️', name: 'VÉTÉRAN', desc: '20+ prédictions' });
        if (hr >= 90 && tp >= 10) badges.push({ icon: '👑', name: 'LÉGENDE', desc: 'Précision > 90%' });
        if (tp === 0) badges.push({ icon: '🌱', name: 'DÉBUTANT', desc: 'Premiers pas' });
        
        return badges;
    }
}

const profileManager = new ProfileManager();

// Fonction globale pour ouvrir le profil depuis le leaderboard
function openUserProfile(username) {
    // Basculer vers une vue profil si elle existe, ou ouvrir un modal
    // Pour simplifier, on va injecter ça dans la vue QUANT -> Leaderboard ou créer une vue dédiée
    switchView('profile'); // On va ajouter cette vue
    profileManager.loadProfile(username);
}
