# Démo jour J

## Message d'ouverture

> J'ai gardé une approche simple : un flux clair, cinq tools métier, un déploiement public, et un début d'intégration Rounded en bonus.

## 1. Question 1 - Flux d'appel

Ouvrir :

```txt
docs/flux-appel.md
```

À dire :

- l'agent ne fait que prise et annulation de RDV ;
- tout ce qui est médical est transféré ;
- le numéro appelant est recherché au début ;
- l'identité est confirmée seulement quand elle devient nécessaire ;
- aucun RDV n'est créé sans confirmation explicite.

## 2. Question 2 - Tools

Ouvrir :

```txt
docs/tools.md
```

À dire :

- je n'ai pas wrappé toute l'API Enovacom ;
- chaque tool correspond à une action utile dans l'appel ;
- les contre-indications sont déterministes ;
- les tools retournent `instructions` pour aider Rounded.

Tools principaux :

```txt
search_exam
find_patient
get_available_slots
create_appointment
cancel_appointment
```

## 3. Question 3 - Déploiement

URL publique :

```txt
https://radiology-call-agent.vercel.app
```

Test simple :

```bash
curl https://radiology-call-agent.vercel.app/health
```

Réponse attendue :

```json
{"status":"ok"}
```

## 4. Run-through automatique

Sans création de RDV :

```bash
python3 scripts/run_demo_tests.py
```

Avec création puis annulation immédiate en recette :

```bash
python3 scripts/run_demo_tests.py --e2e
```

À dire avant le `--e2e` :

> Ce test crée un RDV de test dans l'environnement de recette, puis l'annule immédiatement.

## 5. Tests curl utiles

Recherche examen :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/search_exam \
  -H "Content-Type: application/json" \
  -d '{"query":"irm genou"}'
```

Recherche avec faute de transcription :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/search_exam \
  -H "Content-Type: application/json" \
  -d '{"query":"her aime genou"}'
```

Clarification examen :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/search_exam \
  -H "Content-Type: application/json" \
  -d '{"query":"irm genou","clarification_answer":"sans injection"}'
```

Disponibilités :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/get_available_slots \
  -H "Content-Type: application/json" \
  -d '{"visit_motive_id":"302","start_date":"demain","days":14}'
```

Contre-indication :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/create_appointment \
  -H "Content-Type: application/json" \
  -d '{
    "visit_motive_id":"302",
    "start":"2026-05-28 12:00:00",
    "duration_minutes":"20",
    "practitioner_id":"3",
    "location_id":"26",
    "patient_id":"0",
    "first_name":"Test",
    "last_name":"Blocked",
    "birth_date":"19900101",
    "gender":"1",
    "phone":"0600000001",
    "exam_category":"IRM",
    "pacemaker":true,
    "ferromagnetic_implant":false
  }'
```

Résultat attendu :

```json
{
  "appointment_created": false,
  "next_action": "transfer"
}
```

## 6. Bonus Rounded

Ouvrir :

```txt
docs/rounded-agent.md
```

À dire :

- j'ai commencé à brancher les tools dans Rounded ;
- le flow est simple : qualification → prise RDV ou transfert humain ;
- j'ai ajouté un tool bonus `create_appointment_from_text` pour simplifier la configuration Rounded avec Gemini ;
- je n'ai pas finalisé tout le flow vocal, mais la base technique est prête.

## 7. Limites assumées

- Annulation vocale complète : il manque un tool `list_patient_appointments`.
- Matching d'examen : volontairement simple.
- Production réelle : ajouter auth, logs, monitoring et règles RGPD plus strictes.

## Conclusion

> Le cœur du test est fonctionnel : flux documenté, tools codés, endpoints publics, création et annulation testées en recette.
