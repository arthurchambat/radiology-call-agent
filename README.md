# Radiology call agent

Tools publics pour le test technique Rounded : un agent vocal de centre de radiologie capable de prendre un rendez-vous et de transférer les cas hors cadre.

URL de production :

```txt
https://radiology-call-agent.vercel.app
```

## Ce que couvre le projet

1. **Flux d'appel** : le parcours patient est documenté avant le code.
2. **Tools locaux** : les actions utiles sont exposées via une petite API FastAPI.
3. **Déploiement** : les tools sont disponibles publiquement sur Vercel.
4. **Bonus commencé** : une configuration Rounded est préparée, avec un tool simplifié par Gemini.

## Architecture

```txt
app/
  main.py       # endpoints FastAPI
  enovacom.py   # appels au RIS Enovacom
  rules.py      # contre-indications simples
  gemini.py     # extraction texte -> JSON pour le bonus Rounded
  config.py     # variables d'environnement
docs/
  flux-appel.md
  site-choice.md
  tools.md
  demo-jour-j.md
  rounded-agent.md
scripts/
  run_demo_tests.py
```

## Variables d'environnement

```txt
ENOVACOM_BASE_URL=https://ris-recette-instance3.nd.care/AIR/eris_project/eris_php/WebServices/WS_rdv_externe.php
ENOVACOM_TOKEN=...
ENOVACOM_SITE_ID=5
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

`GEMINI_API_KEY` sert uniquement au bonus Rounded.

## Lancer en local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

Health check :

```bash
curl http://localhost:8000/health
```

## Tests de démo

Test public sans créer de rendez-vous :

```bash
python3 scripts/run_demo_tests.py
```

Test public complet avec création puis annulation immédiate d'un RDV de recette :

```bash
python3 scripts/run_demo_tests.py --e2e
```

## Endpoints

```txt
GET  /health
POST /tools/search_exam
POST /tools/find_patient
POST /tools/get_available_slots
POST /tools/create_appointment
POST /tools/create_appointment_from_text
POST /tools/cancel_appointment
```

## Docs utiles

- `docs/flux-appel.md` : raisonnement du flux d'appel.
- `docs/site-choice.md` : choix du site Enovacom.
- `docs/tools.md` : liste courte des tools.
- `docs/demo-jour-j.md` : déroulé de présentation.
- `docs/rounded-agent.md` : bonus Rounded commencé.

## Choix principal

Le projet reste volontairement simple : peu de fichiers, peu de tools, et des actions métier lisibles plutôt qu'un wrapper complet de l'API Enovacom.
