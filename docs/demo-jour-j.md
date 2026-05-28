# Demo jour J

## Objectif de la restitution

Montrer que le projet couvre les trois attentes principales :

1. le flux d'appel a ete pense avant le code ;
2. les tools sont simples, utiles et testables ;
3. les tools sont deployes sur une URL publique.

Le fil conducteur a garder pendant la presentation :

> L'agent vocal gere uniquement la prise et l'annulation de rendez-vous. Des qu'une demande devient medicale, ambigue ou hors cadre, il transfere a un humain.

## 1. Presenter le flux d'appel

Fichier a ouvrir :

```txt
docs/flux-appel.md
```

Message a expliquer :

- le numero appelant est recupere des le debut ;
- on cherche s'il correspond a un patient existant ;
- on ne confirme l'identite qu'apres avoir compris la demande ;
- l'agent ne collecte les informations personnelles que quand c'est necessaire ;
- l'agent ne fait jamais de medical.

Ordre du flux de prise de RDV :

```txt
demande → examen → contre-indications → patient → creneaux → confirmation → creation
```

Ordre du flux d'annulation :

```txt
demande → patient → RDV futur → confirmation → annulation
```

## 2. Presenter le choix du site

Fichier a ouvrir :

```txt
docs/site-choice.md
```

Message a expliquer :

- Enovacom expose 5 sites ;
- j'en ai choisi un seul comme demande dans l'enonce ;
- le site choisi est `SCM PASTEUR REC1`, `site_id=5` ;
- c'est celui qui a le plus d'examens et de salles dans la configuration de recette ;
- tous les tools filtrent les donnees sur ce site.

## 3. Presenter les tools

Fichier a ouvrir :

```txt
docs/tools.md
```

Tools exposes :

```txt
search_exam
find_patient
get_available_slots
create_appointment
cancel_appointment
```

Message a expliquer :

- je n'ai pas wrappe toute l'API Enovacom ;
- chaque tool correspond a une action utile dans l'appel ;
- les regles de contre-indication restent deterministes ;
- l'agent ne cree ou n'annule jamais sans confirmation explicite.

## 4. Tester l'URL publique

URL de production :

```txt
https://radiology-call-agent.vercel.app
```

Test rapide :

```bash
curl https://radiology-call-agent.vercel.app/health
```

Resultat attendu :

```json
{"status":"ok"}
```

## 5. Lancer le run-through automatique

Le script suivant teste :

- la sante de l'API ;
- la recherche d'examen ;
- les disponibilites ;
- le refus de creation en cas de contre-indication.

```bash
python3 scripts/run_demo_tests.py
```

Ce test ne cree pas de vrai rendez-vous.

## 6. Lancer le test de bout en bout

Ce test cree un vrai rendez-vous en recette Enovacom, puis l'annule immediatement.

```bash
python3 scripts/run_demo_tests.py --e2e
```

A expliquer avant de le lancer :

> Ce test utilise l'environnement de recette. Il cree un patient de test et un rendez-vous de test, puis annule le rendez-vous dans la foulee.

## 7. Commandes curl utiles

Recherche d'examen :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/search_exam \
  -H "Content-Type: application/json" \
  -d '{"query":"irm genou"}'
```

Disponibilites :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/get_available_slots \
  -H "Content-Type: application/json" \
  -d '{"visit_motive_id":"302","start_date":"2026-05-28","days":14}'
```

Le meme tool accepte aussi une date plus naturelle :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/get_available_slots \
  -H "Content-Type: application/json" \
  -d '{"visit_motive_id":"302","start_date":"demain","days":14}'
```

Refus pour contre-indication :

```bash
curl -s -X POST https://radiology-call-agent.vercel.app/tools/create_appointment \
  -H "Content-Type: application/json" \
  -d '{
    "visit_motive_id":"302",
    "slot":{
      "start":"2026-05-28 09:30:00",
      "duration_minutes":"20",
      "practitioner_id":"3",
      "location_id":"26",
      "site_id":"5"
    },
    "patient_id":"0",
    "patient":{
      "first_name":"Test",
      "last_name":"Blocked",
      "birth_date":"19900101",
      "gender":"1",
      "phone":"0600000001"
    },
    "exam_category":"IRM",
    "contraindications":{
      "pacemaker":true,
      "ferromagnetic_implant":false
    }
  }'
```

## 8. Limites a assumer

Points a dire simplement si on te demande :

- le matching d'examen est volontairement simple ;
- Gemini n'est pas utilise dans les tools, car les tools doivent rester deterministes ;
- la partie conversationnelle est portee par Rounded ;
- les tools retournent aussi un champ `instructions` pour guider l'agent apres chaque appel API ;
- en production, on ajouterait authentification, logs structures et monitoring ;
- en production, on renforcerait l'identification patient avant toute action sensible.

## 9. Conclusion

Phrase de conclusion possible :

> J'ai garde une architecture volontairement simple : un flux clair, cinq tools metier, un deploiement public, et des tests curl. L'objectif etait de montrer un agent branche sur Enovacom sans exposer toute l'API au modele vocal.
