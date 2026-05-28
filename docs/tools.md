# Question 2 - Conception des tools

## Objectif

Les tools servent a connecter l'agent vocal au RIS Enovacom.

Le choix est volontairement simple : on expose uniquement les actions utiles au flux d'appel, pas toute l'API Enovacom.

Les 5 tools retenus sont :

- `search_exam`
- `find_patient`
- `get_available_slots`
- `create_appointment`
- `cancel_appointment`

## 1. `search_exam`

### Role

Trouver un examen disponible sur le site choisi a partir de la demande du patient.

Exemple :

- "IRM genou"
- "radio thorax"
- "scanner avec injection"

### Entree

```json
{
  "query": "irm genou"
}
```

Pour faciliter la configuration Rounded, le endpoint accepte aussi une entree plate :

```json
{
  "visit_motive_id": "123",
  "start": "2026-05-28 09:30:00",
  "duration_minutes": "20",
  "practitioner_id": "4",
  "location_id": "8",
  "patient_id": "0",
  "first_name": "Jean",
  "last_name": "Dupont",
  "birth_date": "19800131",
  "gender": "1",
  "phone": "0612345678",
  "exam_category": "IRM",
  "pacemaker": false,
  "ferromagnetic_implant": false
}
```

### Sortie

```json
{
  "matches": [
    {
      "visit_motive_id": "123",
      "name": "IRM genou",
      "category": "IRM"
    }
  ]
}
```

### Appel Enovacom utilise

- `get_config`

Le tool lit les examens disponibles, puis filtre les examens lies au site choisi.

## 2. `find_patient`

### Role

Rechercher un patient existant.

Ce tool sert dans deux cas :

- au debut de l'appel, avec le numero appelant ;
- plus tard dans le flux, avec nom et telephone si le numero n'a pas permis d'identifier un patient.

### Entree

```json
{
  "phone_number": "0612345678",
  "last_name": "Dupont"
}
```

`last_name` est optionnel.

### Sortie

```json
{
  "found": true,
  "patient": {
    "patient_id": "456",
    "first_name": "Jean",
    "last_name": "Dupont",
    "birth_date": "19800131",
    "phone": "0612345678"
  }
}
```

### Appel Enovacom utilise

- `get_patient`

## 3. `get_available_slots`

### Role

Chercher des creneaux disponibles pour un examen donne.

Le tool filtre les resultats pour ne garder que les creneaux du site choisi.

### Entree

```json
{
  "visit_motive_id": "123",
  "start_date": "2026-05-28",
  "days": 14
}
```

`start_date` accepte aussi des formats plus naturels comme `28/05/2026`, `28 mai`, `demain`, `apres-demain`, `lundi prochain` ou `dans 3 jours`.

### Sortie

```json
{
  "slots": [
    {
      "start": "2026-05-28 09:30:00",
      "stop": "2026-05-28 09:50:00",
      "duration_minutes": "20",
      "practitioner_id": "4",
      "location_id": "8",
      "site_id": "1"
    }
  ]
}
```

### Appel Enovacom utilise

- `get_availabilities`

Point technique masque par le tool : Enovacom attend ici `visit_motive_id` sous forme d'entier, alors que d'autres endpoints utilisent des strings. Le tool garde une entree simple en string et convertit avant l'appel.

## 4. `create_appointment`

### Role

Creer un rendez-vous apres confirmation explicite du patient.

Ce tool recoit deja le creneau choisi. Il ne decide pas a la place du patient.

### Entree

```json
{
  "visit_motive_id": "123",
  "slot": {
    "start": "2026-05-28 09:30:00",
    "duration_minutes": "20",
    "practitioner_id": "4",
    "location_id": "8"
  },
  "patient_id": "0",
  "patient": {
    "first_name": "Jean",
    "last_name": "Dupont",
    "birth_date": "19800131",
    "gender": "1",
    "phone": "0612345678"
  },
  "contraindications": {
    "pacemaker": false,
    "ferromagnetic_implant": false,
    "pregnant": false,
    "iodine_allergy": false,
    "renal_failure": false
  }
}
```

### Sortie

```json
{
  "appointment_created": true,
  "appointment_id": "43975"
}
```

### Appel Enovacom utilise

- `add_rdv`

Avant l'appel Enovacom, le code verifie les contre-indications simples. Si une contre-indication est presente, le tool refuse la creation et indique qu'il faut transferer a un humain.

## 5. `cancel_appointment`

### Role

Annuler un rendez-vous apres confirmation explicite du patient.

### Entree

```json
{
  "appointment_id": "43975"
}
```

### Sortie

```json
{
  "cancelled": true
}
```

### Appel Enovacom utilise

- `delete_rdv`

## Gestion des erreurs

Les erreurs sont retournees de facon simple pour que l'agent sache quoi faire.

Exemple :

```json
{
  "error": "no_availability",
  "message": "Aucun creneau disponible sur cette periode",
  "next_action": "transfer"
}
```

Dans le doute, l'agent transfere a un humain.

## 6. `create_appointment_from_text`

### Role

Creer un rendez-vous a partir d'un resume texte complet.

Ce tool est surtout utile pour Rounded, car il evite de configurer beaucoup de parametres plats dans l'interface.

Il utilise Gemini cote backend pour extraire les champs structures, puis appelle la meme logique que `create_appointment`.

### Entree

```json
{
  "request_text": "Le patient confirme un rendez-vous pour IRM GENOU SANS IV, visit_motive_id 302, le 2026-05-28 12:00:00, duree 20 minutes, practitioner_id 3, location_id 26. Patient : Jean Dupont, ne le 1990-01-01, telephone 0600000000, nouveau patient donc patient_id 0. Categorie IRM. Pas de pacemaker, pas d'implant ferromagnetique."
}
```

### Sortie

```json
{
  "appointment_created": true,
  "appointment_id": 44100,
  "instructions": "Le rendez-vous est cree. Recapituler l'examen, la date, l'heure et rappeler que l'agent ne donne pas d'information medicale."
}
```

### Variables d'environnement

```txt
GEMINI_API_KEY
GEMINI_MODEL=gemini-2.5-flash
```
