# Flux d'appel

## Principe

L'agent ne traite que deux intentions : **prendre un rendez-vous** ou **annuler un rendez-vous**.

Tout le reste part vers un humain : urgence, résultat, symptôme, question médicale, doute ou cas ambigu.

## Entrée d'appel

```txt
Début appel
  ↓
Récupérer le numéro appelant
  ↓
Chercher un patient associé au numéro
  ↓
Dire bonjour et qualifier la demande
  ↓
Prise RDV → flux prise RDV
Annulation → flux annulation
Autre → transfert humain
```

Le numéro est recherché dès le début, mais l'identité n'est confirmée qu'après avoir compris la demande.

## Prise de RDV

```txt
Demander l'examen
  ↓
search_exam
  ↓
Vérifier les contre-indications simples
  ↓
Identifier le patient
  ↓
get_available_slots
  ↓
Proposer 2 ou 3 créneaux
  ↓
Confirmation explicite
  ↓
create_appointment
  ↓
Récapitulatif
```

Règle clé : aucun rendez-vous n'est créé sans confirmation claire du patient.

## Annulation

```txt
Identifier le patient
  ↓
Identifier le RDV à annuler
  ↓
Confirmation explicite
  ↓
cancel_appointment
```

L'API sait annuler un RDV si `appointment_id` est connu. Pour une annulation vocale complète, il faudrait ajouter ensuite un tool `list_patient_appointments`.

## Contre-indications

- IRM : pacemaker, implant ferromagnétique.
- Scanner avec injection : allergie à l'iode, insuffisance rénale.
- Radio : grossesse.

Si oui ou doute : transfert humain.

## Transfert humain

Transfert si urgence, résultat, symptôme, question médicale, contre-indication, patient ambigu, examen introuvable ou erreur technique.
