# Tools

Les tools restent proches du métier. Ils ne wrappent pas toute l'API Enovacom.

## `search_exam`

Trouve un examen à partir d'une demande patient, même avec des fautes de transcription.

```txt
POST /tools/search_exam
```

Entrée :

```json
{"query": "irm genou"}
```

Exemples acceptés :

```txt
irm genou
irme jnou
her aime genou
scanner abdomnial
```

Si l'examen est ambigu, le tool retourne une question à poser au patient.

Deuxième appel possible :

```json
{"query": "irm genou", "clarification_answer": "sans injection"}
```

Sortie principale :

```json
{
  "status": "selected",
  "selected_exam": {
    "visit_motive_id": "302",
    "name": "IRM GENOU SANS IV",
    "category": "IRM MEMBRE INF"
  },
  "matches": []
}
```

Autres statuts :

```txt
needs_clarification
no_match
```

Le matching se fait avec Gemini sur les examens du site choisi uniquement.

## `find_patient`

Recherche un patient par téléphone et éventuellement nom.

```txt
POST /tools/find_patient
```

Entrée :

```json
{"phone_number": "0600000000", "last_name": "Dupont"}
```

Sortie : `found`, `ambiguous`, `patients`.

## `get_available_slots`

Retourne les créneaux disponibles pour un examen.

```txt
POST /tools/get_available_slots
```

Entrée :

```json
{"visit_motive_id": "302", "start_date": "demain", "days": 14}
```

`start_date` accepte aussi `2026-05-28`, `28/05/2026`, `28 mai`, `lundi prochain`, `dans 3 jours`.

## `create_appointment`

Crée un RDV après confirmation explicite du patient.

```txt
POST /tools/create_appointment
```

Le endpoint accepte un format plat, plus simple pour Rounded :

```json
{
  "visit_motive_id": "302",
  "start": "2026-05-28 12:00:00",
  "duration_minutes": "20",
  "practitioner_id": "3",
  "location_id": "26",
  "patient_id": "0",
  "first_name": "Jean",
  "last_name": "Dupont",
  "birth_date": "19900101",
  "gender": "1",
  "phone": "0600000000",
  "exam_category": "IRM",
  "pacemaker": false,
  "ferromagnetic_implant": false
}
```

## `create_appointment_from_text`

Bonus Rounded : crée un RDV à partir d'un résumé texte.

```txt
POST /tools/create_appointment_from_text
```

Entrée :

```json
{
  "request_text": "Le patient confirme un RDV pour IRM GENOU SANS IV, visit_motive_id 302, le 2026-05-28 12:00:00, durée 20 minutes, practitioner_id 3, location_id 26. Patient Jean Dupont, né le 1990-01-01, téléphone 0600000000. Pas de pacemaker."
}
```

Ce tool utilise Gemini pour transformer le texte en champs structurés.

`GEMINI_THINKING_BUDGET=0` désactive le raisonnement interne Gemini pour réduire la latence des calls API.

## `cancel_appointment`

Annule un RDV si son identifiant est connu.

```txt
POST /tools/cancel_appointment
```

Entrée :

```json
{"appointment_id": "44100"}
```

## Réponse `instructions`

Les tools retournent aussi un champ `instructions` pour guider l'agent Rounded après l'appel API.
