"""Analyse de sentiment simple basée sur lexique (pas de ML lourd)."""
import re
from typing import Tuple

# Lexique positif (contexte financier BRVM)
POSITIVE_WORDS = {
    # Français
    'hausse', 'croissance', 'profit', 'bénéfice', 'gain', 'succès', 'record',
    'amélioration', 'progression', 'rebond', 'optimisme', 'positif', 'favorable',
    'solide', 'robuste', 'excellent', 'bon', 'meilleur', 'hauteur', 'montée',
    'dividende', 'distribution', 'rente', 'performance', 'résultats', 'expansion',
    'acquisition', 'partenariat', 'lancement', 'innovation', 'succès',
    # Anglais
    'growth', 'profit', 'gain', 'success', 'record', 'improvement', 'rise',
    'bullish', 'positive', 'strong', 'excellent', 'good', 'best', 'up',
    'dividend', 'performance', 'results', 'partnership', 'launch', 'innovation'
}

# Lexique négatif
NEGATIVE_WORDS = {
    # Français
    'baisse', 'chute', 'perte', 'déficit', 'crise', 'échec', 'récession',
    'détérioration', 'régression', 'chute', 'pessimisme', 'négatif', 'défavorable',
    'faible', 'fragile', 'mauvais', 'pire', 'moins', 'descente', 'effondrement',
    'faillite', 'dettes', 'problème', 'difficulté', 'risque', 'menace', 'scandale',
    'fraude', 'amende', 'sanction', 'licenciement', 'grève', 'contestation',
    # Anglais
    'decline', 'fall', 'loss', 'deficit', 'crisis', 'failure', 'recession',
    'bearish', 'negative', 'weak', 'poor', 'worst', 'down', 'crash',
    'debt', 'problem', 'risk', 'threat', 'scandal', 'fraud', 'fine', 'strike'
}

# Amplificateurs
AMPLIFIERS = {
    'très': 1.5, 'fortement': 1.5, 'fort': 1.3, 'énorme': 1.8,
    'significatif': 1.4, 'important': 1.3, 'massif': 1.6,
    'very': 1.5, 'strongly': 1.5, 'highly': 1.4, 'significantly': 1.4
}

# Négateurs
NEGATORS = {'ne', 'pas', 'non', 'aucun', 'sans', 'not', 'no', 'never'}


def analyze_sentiment(text: str) -> Tuple[str, float, list]:
    """
    Analyse le sentiment d'un texte.
    
    Returns:
        (sentiment_label, score, keywords)
        - sentiment_label: 'positive', 'negative', 'neutral'
        - score: float entre -1.0 et 1.0
        - keywords: liste de mots-clés extraits
    """
    if not text:
        return 'neutral', 0.0, []
    
    # Nettoyage
    text_clean = text.lower()
    text_clean = re.sub(r'[^\w\s]', ' ', text_clean)
    words = text_clean.split()
    
    # Extraction des mots-clés (mots de plus de 4 lettres)
    keywords = list(set([w for w in words if len(w) > 4 and w not in NEGATORS]))
    keywords = keywords[:10]  # Top 10
    
    # Calcul du score
    score = 0.0
    pos_count = 0
    neg_count = 0
    
    for i, word in enumerate(words):
        # Vérifier si précédé d'un négateur
        is_negated = i > 0 and words[i-1] in NEGATORS
        
        # Vérifier amplificateur
        multiplier = 1.0
        if i > 0 and words[i-1] in AMPLIFIERS:
            multiplier = AMPLIFIERS[words[i-1]]
        
        if word in POSITIVE_WORDS:
            if is_negated:
                score -= 1.0 * multiplier
                neg_count += 1
            else:
                score += 1.0 * multiplier
                pos_count += 1
        elif word in NEGATIVE_WORDS:
            if is_negated:
                score += 1.0 * multiplier
                pos_count += 1
            else:
                score -= 1.0 * multiplier
                neg_count += 1
    
    # Normalisation entre -1 et 1
    total = pos_count + neg_count
    if total > 0:
        normalized_score = max(-1.0, min(1.0, score / total))
    else:
        normalized_score = 0.0
    
    # Label
    if normalized_score > 0.15:
        label = 'positive'
    elif normalized_score < -0.15:
        label = 'negative'
    else:
        label = 'neutral'
    
    return label, round(normalized_score, 3), keywords


def extract_tickers(text: str, known_tickers: list) -> list:
    """Extrait les tickers mentionnés dans le texte."""
    if not text:
        return []
    
    text_upper = text.upper()
    found = []
    
    for ticker in known_tickers:
        # Recherche du ticker dans le texte
        if ticker in text_upper:
            found.append(ticker)
    
    return found
