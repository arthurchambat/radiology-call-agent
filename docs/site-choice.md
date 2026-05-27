# Choix du site Enovacom

## Site choisi

Le site retenu pour le centre du Dr Tahar est :

```txt
SCM PASTEUR REC1
site_id = 5
```

## Pourquoi ce choix

L'API Enovacom de recette expose 5 sites.

Apres appel a `get_config`, les sites disponibles sont :

| Site | ID | Examens lies | Praticiens lies | Salles liees |
| --- | ---: | ---: | ---: | ---: |
| POLE DE SANTE REC1 | 1 | 365 | 22 | 13 |
| SCM PASTEUR REC1 | 5 | 501 | 22 | 21 |
| KELDOC SITE 1 REC1 | 7 | 16 | 22 | 4 |
| KELDOC SITE 2 REC1 | 8 | 8 | 22 | 1 |
| SELASTEST | 13 | 21 | 17 | 2 |

`SCM PASTEUR REC1` est le choix le plus simple pour le test, car c'est le site avec :

- le plus grand nombre d'examens disponibles ;
- le plus grand nombre de salles ;
- une couverture large pour les types d'examens attendus.

## Consequence dans le projet

Tous les tools filtrent les donnees sur ce site.

La variable d'environnement a utiliser est :

```txt
ENOVACOM_SITE_ID=5
```

L'agent ne doit donc proposer que les examens et les creneaux compatibles avec ce site.
