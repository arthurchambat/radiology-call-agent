# Bonus - Configuration de l'agent Rounded

## Objectif

Brancher l'agent vocal Rounded aux tools deployes publiquement :

```txt
https://radiology-call-agent.vercel.app
```

L'objectif du bonus est de demontrer qu'un appel peut aller jusqu'a la creation d'un vrai rendez-vous dans Enovacom.

## Role de l'agent

L'agent est un assistant administratif pour le centre de radiologie du Dr Tahar.

Il peut uniquement :

- prendre un rendez-vous ;
- annuler un rendez-vous.

Il ne doit jamais :

- donner une information medicale ;
- commenter un resultat ;
- donner un avis sur un symptome ;
- choisir un examen a la place du patient.

Tout cas medical, urgent, ambigu ou hors perimetre doit etre transfere a un humain.

## Prompt agent

```txt
Tu es l'assistant vocal du centre de radiologie du Dr Tahar.

Ton role est strictement administratif.
Tu peux uniquement aider un patient a prendre ou annuler un rendez-vous.

Tu ne donnes jamais d'information medicale.
Tu ne commentes jamais un resultat d'examen.
Tu ne donnes jamais d'avis sur un symptome.
Tu ne choisis jamais un examen a la place du patient.

Si le patient parle d'urgence, de douleur, de symptome, de resultat, de preparation medicale, ou pose une question medicale, tu transferes a un humain.

Au debut de l'appel :
- recupere le numero appelant si disponible ;
- utilise le tool find_patient pour voir si un patient est associe au numero ;
- ne confirme l'identite qu'apres avoir compris la demande du patient.

Pour une prise de rendez-vous :
1. identifie l'examen demande ;
2. utilise search_exam pour trouver l'examen correspondant ;
3. si plusieurs examens sont possibles, demande une precision simple ;
4. pose les questions de contre-indication adaptees ;
5. si le patient declare une contre-indication ou s'il a un doute, transfere a un humain ;
6. identifie le patient ;
7. utilise get_available_slots pour recuperer des creneaux ;
8. propose 2 ou 3 creneaux ;
9. demande une confirmation explicite ;
10. appelle create_appointment seulement apres confirmation ;
11. recapitule le rendez-vous cree.

Pour une annulation :
1. identifie le patient ;
2. verifie quel rendez-vous doit etre annule ;
3. demande une confirmation explicite ;
4. appelle cancel_appointment seulement apres confirmation ;
5. confirme l'annulation.

Ne cree jamais et n'annule jamais un rendez-vous sans confirmation explicite.
Si tu n'es pas certain, transfere a un humain.
```

## Tools a configurer

Selon la documentation Rounded, un custom tool doit avoir :

- un nom clair ;
- une description ;
- une phrase de patience pendant l'appel API ;
- des parametres de tool ;
- les reglages d'appel API ;
- eventuellement un mapping de reponse.

Les reponses de nos tools contiennent aussi un champ `instructions` a la racine. Rounded peut utiliser ce champ pour donner a l'agent une consigne simple apres l'appel API, sans l'obliger a interpreter tout le JSON brut.

### 1. `search_exam`

URL :

```txt
POST https://radiology-call-agent.vercel.app/tools/search_exam
```

Description :

```txt
Recherche un examen disponible sur le site choisi a partir de la demande du patient.
```

Schema d'entree :

```json
{
  "query": "irm genou"
}
```

Schema de sortie :

```json
{
  "matches": [
    {
      "visit_motive_id": "302",
      "name": "IRM GENOU SANS IV",
      "category": "IRM MEMBRE INF"
    }
  ],
  "instructions": "Examens trouves : IRM GENOU SANS IV (id 302). Si plusieurs options sont possibles, demander une precision au patient."
}
```

### 2. `find_patient`

URL :

```txt
POST https://radiology-call-agent.vercel.app/tools/find_patient
```

Description :

```txt
Recherche un patient existant par numero de telephone et, si disponible, par nom.
```

Schema d'entree :

```json
{
  "phone_number": "0600000000",
  "last_name": "Dupont"
}
```

`last_name` est optionnel.

Schema de sortie :

```json
{
  "found": false,
  "ambiguous": true,
  "patients": [],
  "instructions": "Plusieurs patients possibles : demander une verification supplementaire ou transferer a un humain."
}
```

Regle agent :

```txt
Si found=true, confirmer l'identite.
Si ambiguous=true, transferer a un humain ou demander une verification supplementaire.
Si found=false, collecter les informations patient necessaires.
```

### 3. `get_available_slots`

URL :

```txt
POST https://radiology-call-agent.vercel.app/tools/get_available_slots
```

Description :

```txt
Recupere des creneaux disponibles pour un examen donne.
```

Schema d'entree :

```json
{
  "visit_motive_id": "302",
  "start_date": "2026-05-28",
  "days": 14
}
```

Pour Rounded, la configuration la plus simple est d'utiliser des parametres plats plutot que des objets imbriques. Le endpoint accepte donc aussi :

```json
{
  "visit_motive_id": "302",
  "start": "2026-05-28 09:30:00",
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
  "ferromagnetic_implant": false,
  "pregnant": false,
  "iodine_allergy": false,
  "renal_failure": false
}
```

Parametres recommandes dans Rounded :

```txt
visit_motive_id      string   id de l'examen choisi
start                string   horaire du creneau choisi, ex: 2026-05-28 09:30:00
duration_minutes     string   duree du creneau, ex: 20
practitioner_id      string   id du praticien retourne par get_available_slots
location_id          string   id de salle retourne par get_available_slots
patient_id           string   utiliser "0" si nouveau patient
first_name           string   prenom patient
last_name            string   nom patient
birth_date           string   date de naissance, idealement YYYYMMDD
gender               string   "1" par defaut si non precise
phone                string   numero de telephone
exam_category        string   categorie examen, ex: IRM
pacemaker            boolean  true si le patient declare un pacemaker
ferromagnetic_implant boolean true si implant ferromagnetique
pregnant             boolean  true si grossesse
iodine_allergy       boolean  true si allergie iode
renal_failure        boolean  true si insuffisance renale
```

Le parametre `start_date` accepte plusieurs formats pour faciliter l'appel depuis Rounded :

```txt
2026-05-28
28/05/2026
28-05-2026
28 mai 2026
28 mai
aujourd'hui
demain
apres-demain
lundi
lundi prochain
dans 3 jours
```

Si possible, demander quand meme a l'agent de convertir la date au format `YYYY-MM-DD`, mais le tool reste tolerant.

Schema de sortie :

```json
{
  "slots": [
    {
      "start": "2026-05-28 09:30:00",
      "stop": "2026-05-28 09:50:00",
      "duration_minutes": "20",
      "practitioner_id": "3",
      "location_id": "26",
      "site_id": "5"
    }
  ],
  "instructions": "Proposer ces creneaux au patient. Ne creer le rendez-vous qu'apres confirmation explicite."
}
```

### 4. `create_appointment`

URL :

```txt
POST https://radiology-call-agent.vercel.app/tools/create_appointment
```

Description :

```txt
Cree un rendez-vous apres confirmation explicite du patient.
Refuse la creation si une contre-indication simple est declaree.
```

Schema d'entree :

```json
{
  "visit_motive_id": "302",
  "slot": {
    "start": "2026-05-28 09:30:00",
    "duration_minutes": "20",
    "practitioner_id": "3",
    "location_id": "26",
    "site_id": "5"
  },
  "patient_id": "0",
  "patient": {
    "first_name": "Jean",
    "last_name": "Dupont",
    "birth_date": "19900101",
    "gender": "1",
    "phone": "0600000000"
  },
  "exam_category": "IRM",
  "contraindications": {
    "pacemaker": false,
    "ferromagnetic_implant": false,
    "pregnant": false,
    "iodine_allergy": false,
    "renal_failure": false
  }
}
```

Schema de sortie :

```json
{
  "appointment_created": true,
  "appointment_id": 44097,
  "instructions": "Le rendez-vous est cree. Recapituler l'examen, la date et l'heure."
}
```

### 5. `cancel_appointment`

URL :

```txt
POST https://radiology-call-agent.vercel.app/tools/cancel_appointment
```

Description :

```txt
Annule un rendez-vous apres confirmation explicite du patient.
```

Schema d'entree :

```json
{
  "appointment_id": "44097"
}
```

Schema de sortie :

```json
{
  "cancelled": true,
  "instructions": "Si cancelled=true, confirmer au patient que le rendez-vous est annule."
}
```

## Scenario de test vocal - prise de RDV

Objectif : creer un vrai rendez-vous de test.

Deroule :

1. Patient : "Bonjour, je voudrais prendre rendez-vous pour une IRM du genou."
2. Agent : recherche l'examen avec `search_exam`.
3. Agent : demande les contre-indications IRM.
4. Patient : "Non, pas de pacemaker, pas d'implant metallique."
5. Agent : demande l'identite patient.
6. Agent : cherche les creneaux avec `get_available_slots`.
7. Agent : propose 2 ou 3 creneaux.
8. Patient : choisit un creneau.
9. Agent : recapitule et demande confirmation.
10. Patient : confirme.
11. Agent : appelle `create_appointment`.
12. Agent : confirme le rendez-vous cree.

## Scenario de test vocal - contre-indication

Objectif : montrer que l'agent transfere au lieu de creer.

Deroule :

1. Patient : "Je veux prendre rendez-vous pour une IRM du genou."
2. Agent : demande les contre-indications IRM.
3. Patient : "J'ai un pacemaker."
4. Agent : n'appelle pas la creation de RDV.
5. Agent : transfere a un humain.

## Limite actuelle pour l'annulation

Le tool `cancel_appointment` annule bien un rendez-vous quand l'identifiant `appointment_id` est connu.

Pour une experience vocale complete d'annulation, il faudrait idealement ajouter un tool supplementaire :

```txt
list_patient_appointments
```

Ce tool permettrait de retrouver les rendez-vous futurs d'un patient avant d'appeler `cancel_appointment`.

Pour le bonus, la demonstration prioritaire est donc la creation de rendez-vous de bout en bout.
