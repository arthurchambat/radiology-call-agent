# Bonus Rounded

## Statut

Bonus commencé, pas présenté comme totalement finalisé.

Objectif : montrer que les tools publics peuvent être branchés dans Rounded.

## Flow recommandé

```txt
qualification
  ├── PriseRDV
  └── TransfertHumain
```

## `qualification`

Rôle : comprendre pourquoi le patient appelle.

Instructions courtes :

```txt
Tu es l'assistant du centre de radiologie du Dr Tahar.
Tu peux aider à prendre ou annuler un rendez-vous.
Si la demande est médicale, urgente, liée à un résultat ou hors périmètre, va vers TransfertHumain.
Si le patient veut prendre rendez-vous, va vers PriseRDV.
```

## `PriseRDV`

Rôle : accompagner la prise de rendez-vous.

Tools utiles :

```txt
search_exam
get_available_slots
create_appointment_from_text
```

`search_exam` utilise Gemini côté backend pour supporter les fautes de transcription, par exemple `her aime genou` → `IRM genou`.

Après `search_exam` :

```txt
status=selected → utiliser selected_exam.visit_motive_id
status=needs_clarification → poser clarification_question au patient, puis rappeler search_exam avec clarification_answer
status=no_match → demander une précision simple ou transférer
```

Pourquoi `create_appointment_from_text` :

- un seul paramètre Rounded : `request_text` ;
- Gemini structure le texte côté backend ;
- c'est plus simple que configurer 15 paramètres dans l'interface.

## Tool bonus `create_appointment_from_text`

URL :

```txt
POST https://radiology-call-agent.vercel.app/tools/create_appointment_from_text
```

Paramètre :

```txt
request_text
Type: string
Required: yes
Description: résumé complet du RDV confirmé par le patient.
```

Exemple de `request_text` :

```txt
Le patient confirme un rendez-vous pour IRM GENOU SANS IV, visit_motive_id 302, le 2026-05-28 12:00:00, durée 20 minutes, practitioner_id 3, location_id 26. Patient Jean Dupont, né le 1990-01-01, téléphone 0600000000, patient_id 0. Catégorie IRM. Pas de pacemaker, pas d'implant ferromagnétique.
```

## `TransfertHumain`

Rôle : transférer tous les cas hors cadre.

Instructions courtes :

```txt
La demande doit être reprise par l'équipe du centre.
Ne donne aucune information médicale.
Transfère l'appel à un humain.
```

## Scénario de test bonus

Patient :

```txt
Bonjour, je voudrais prendre rendez-vous pour une IRM du genou.
```

Réponses attendues :

```txt
Pas de pacemaker.
Pas d'implant métallique.
Patient : Test Rounded.
Né le 1er janvier 1990.
Téléphone : 0600000000.
Oui, je confirme le créneau.
```

## Ce que je dirai en restitution

> J'ai exploré Rounded et commencé le branchement. Pour simplifier l'intégration, j'ai ajouté un tool bonus qui prend un résumé texte et utilise Gemini côté backend pour produire les champs structurés. Je n'ai pas finalisé tout le parcours vocal, mais les endpoints publics et le flow de base sont prêts.
