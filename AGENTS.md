# Instructions projet

## Priorite generale

Pour ce projet, privilegier la simplicite.

L'objectif est de produire un test technique clair, lisible et facile a expliquer en entretien, pas une architecture complexe de production.

## Code

- Garder peu de fichiers.
- Eviter les abstractions inutiles.
- Preferer des fonctions simples et explicites.
- Nommer les variables et fonctions de maniere directe.
- Ne pas wrapper toute l'API Enovacom.
- Ne coder que les tools utiles au flux d'appel.
- Garder les regles metier visibles et faciles a relire.
- Ajouter des commentaires seulement quand ils aident vraiment a comprendre.

## Architecture

Structure cible simple :

```txt
app/
  main.py
  enovacom.py
  rules.py
  config.py
docs/
README.md
.env.example
```

Cette structure peut evoluer si necessaire, mais il faut eviter de multiplier les couches, dossiers ou patterns sans besoin clair.

## Documentation

- Expliquer les choix simplement.
- Montrer le raisonnement metier avant la technique.
- Preferer des bullets clairs a une documentation longue.
- Documenter les limites et les cas transferes a un humain.
- Garder les explications defendables en partage d'ecran.

## Restitution

Le projet doit etre facile a presenter dans cet ordre :

1. Le flux d'appel.
2. Le choix du site Enovacom.
3. Les tools disponibles.
4. Les tests locaux avec `curl`.
5. Le deploiement public.
6. Les limites et ameliorations possibles.

## Principe de decision

Quand deux options sont possibles, choisir la plus simple tant qu'elle respecte l'enonce.

Escalader vers une solution plus complexe uniquement si elle resout un vrai probleme du test.
