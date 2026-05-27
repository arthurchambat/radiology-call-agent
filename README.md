# Rounded radiology agent tools

Petit service FastAPI pour le test technique Rounded.

L'objectif est de garder une implementation simple et explicable :

- 5 tools metier ;
- pas de wrapper complet de l'API Enovacom ;
- configuration par variables d'environnement ;
- tests possibles avec `curl`.

## Flux d'appel

Le flux est documente ici :

- `docs/flux-appel.md`
- `docs/site-choice.md`

## Tools

Les tools sont documentes ici :

- `docs/tools.md`

Endpoints exposes :

- `POST /tools/search_exam`
- `POST /tools/find_patient`
- `POST /tools/get_available_slots`
- `POST /tools/create_appointment`
- `POST /tools/cancel_appointment`

## Configuration

Copier `.env.example` vers `.env`, puis renseigner :

```txt
ENOVACOM_TOKEN=...
ENOVACOM_SITE_ID=...
```

Le token ne doit pas etre commit.

## Lancer en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Le service est ensuite disponible sur :

```txt
http://localhost:8000
```

## Tester rapidement

```bash
curl http://localhost:8000/health
```

```bash
curl -X POST http://localhost:8000/tools/search_exam \
  -H "Content-Type: application/json" \
  -d '{"query": "irm genou"}'
```

```bash
curl -X POST http://localhost:8000/tools/find_patient \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "0612345678", "last_name": "Dupont"}'
```

```bash
curl -X POST http://localhost:8000/tools/get_available_slots \
  -H "Content-Type: application/json" \
  -d '{"visit_motive_id": "302", "start_date": "2026-05-28", "days": 14}'
```

## Deploiement

Le projet est pret pour un deploiement Vercel via :

```bash
vercel --prod
```

Variables d'environnement a configurer sur Vercel :

```txt
ENOVACOM_BASE_URL=https://ris-recette-instance3.nd.care/AIR/eris_project/eris_php/WebServices/WS_rdv_externe.php
ENOVACOM_TOKEN=...
ENOVACOM_SITE_ID=5
```

Une fois deploye, les memes endpoints sont disponibles sur l'URL publique :

```txt
https://<project>.vercel.app/tools/search_exam
https://<project>.vercel.app/tools/get_available_slots
https://<project>.vercel.app/tools/create_appointment
https://<project>.vercel.app/tools/cancel_appointment
```

Le projet contient aussi un `Dockerfile` si on choisit finalement une plateforme Docker-compatible comme Cloud Run, Render ou Railway.

## Choix d'architecture

Structure volontairement courte :

```txt
app/
  main.py       # endpoints FastAPI
  enovacom.py   # appels HTTP vers Enovacom
  rules.py      # contre-indications simples
  config.py     # variables d'environnement
docs/
README.md
```

Cette structure suffit pour montrer le raisonnement, tester les tools et les deployer.
