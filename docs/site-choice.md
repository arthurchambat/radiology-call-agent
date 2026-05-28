# Choix du site Enovacom

## Site choisi

```txt
SCM PASTEUR REC1
site_id = 5
```

## Pourquoi

Après appel à `get_config`, c'est le site le plus simple pour le test :

| Site | ID | Examens | Salles |
| --- | ---: | ---: | ---: |
| POLE DE SANTE REC1 | 1 | 365 | 13 |
| SCM PASTEUR REC1 | 5 | 501 | 21 |
| KELDOC SITE 1 REC1 | 7 | 16 | 4 |
| KELDOC SITE 2 REC1 | 8 | 8 | 1 |
| SELASTEST | 13 | 21 | 2 |

`SCM PASTEUR REC1` couvre le plus d'examens et de salles.

## Impact

Tous les tools filtrent les examens et créneaux sur :

```txt
ENOVACOM_SITE_ID=5
```
