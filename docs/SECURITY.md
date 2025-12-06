# Analyse de Sécurité - Self-Healing V3

## Modèle de Menaces

### Vecteurs d'attaque identifiés

| Vecteur | Risque V2 | Risque V3 | Mitigation V3 |
|---------|-----------|-----------|---------------|
| Prompt Injection via logs | Élevé | Faible | Intent Engine |
| Hallucination de commande | Élevé | Nul | Whitelist stricte |
| Chaînage de commandes | Moyen | Nul | Pattern blocker |
| Boucle de redémarrage | Moyen | Faible | Rate limiting |
| DoS via alertes spam | Moyen | Faible | Rate limiting |
| Escalade de privilèges | Faible | Faible | SSH user limité |

### Score de sécurité

**V2 : 5/10** - Sécurité dépendante du LLM
**V3 : 7.5/10** - Sécurité dépendante du code

## Défenses en profondeur

### Couche 1 : Rate Limiting

```
Max 3 actions / service / heure
Max 10 actions globales / heure
```

Protège contre :
- Boucles infinies
- Attaques par volume
- Épuisement des ressources

### Couche 2 : Intent Engine

```
LLM ne peut générer QUE des intents prédéfinis
Tout intent inconnu → REJET
```

Protège contre :
- Hallucination de commande
- Prompt injection
- Commandes arbitraires

### Couche 3 : Target Validation

```
Chaque intent a sa liste de targets valides
Target inconnu → REJET
```

Protège contre :
- Modification de cible
- Injection dans le target

### Couche 4 : Pattern Blocker

```javascript
const BLOCKED = [';', '|', '&&', '||', '`', '$(', '${', '>', '<'];
```

Protège contre :
- Chaînage de commandes
- Substitution de commandes
- Redirection de sortie

### Couche 5 : Audit Trail

```
Log AVANT exécution (intention)
Log APRÈS exécution (résultat)
```

Permet :
- Forensics
- Non-répudiation
- Amélioration continue

## Limites connues

### Ce que V3 ne protège PAS

1. **Compromission du serveur N8N** : Si l'attaquant a accès à N8N, il peut modifier les workflows.

2. **Clé SSH compromise** : L'accès SSH permet l'exécution de commandes.

3. **Vulnérabilité dans les services eux-mêmes** : Un restart ne corrige pas une faille applicative.

### Recommandations additionnelles

1. **SSH** : Utiliser un user dédié sans sudo, avec sudoers restrictif
2. **Réseau** : Isoler le serveur N8N du reste de l'infra
3. **Monitoring** : Alerter sur les security_alerts du workflow
4. **Rotation** : Changer régulièrement les credentials

## Comparaison avec Dual-LLM (V2.2)

| Aspect | Dual-LLM V2.2 | Intent Engine V3 |
|--------|---------------|-------------------|
| Sécurité réelle | 5/10 | 7.5/10 |
| Temps d'exécution | ~150s | ~90s (N1), ~5s (N0) |
| Coût CPU | Élevé (2 inférences) | Faible à moyen |
| Protection injection | Faible | Forte |
| Maintenabilité | Complexe | Simple |

### Pourquoi Dual-LLM n'apporte pas de sécurité

1. **Biais corrélés** : Qwen et Phi ont les mêmes données d'entraînement
2. **Même contexte** : Les deux reçoivent les mêmes logs
3. **Security theater** : Consensus ≠ Correction
4. **La vraie sécurité** : Vient du code déterministe, pas de l'IA

## Conclusion

La V3 déplace la responsabilité de sécurité du LLM vers le code. Le LLM devient un **classificateur** dont la sortie est **validée et contrainte** par des règles déterministes.

> "L'IA propose, le Code dispose."
