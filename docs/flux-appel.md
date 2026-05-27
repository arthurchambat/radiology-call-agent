# Flux d'appel de l'agent vocal

## Objectif

L'agent vocal traite uniquement deux demandes :

- prendre un rendez-vous ;
- annuler un rendez-vous.

Tout le reste est transfere a un humain : urgence, resultat d'examen, question medicale, symptome, demande hors perimetre ou cas ambigu.

Le flux reste volontairement simple. L'agent commence par comprendre la demande du patient, puis collecte les informations personnelles uniquement quand elles sont necessaires.

## Principe important

Le numero appelant est recupere des le debut de l'appel pour rechercher un patient existant.

En revanche, l'agent ne valide pas l'identite tout de suite. Il qualifie d'abord la demande du patient.

Ensuite seulement :

- si un patient est associe au numero appelant, l'agent confirme son identite ;
- si aucun patient n'est associe au numero, l'agent demande les informations necessaires au bon moment.

Cette approche evite de demander trop d'informations personnelles avant de savoir si la demande peut etre traitee par l'agent.

## Workflow 1 - Entree d'appel et qualification

```txt
Debut appel
  ↓
Recuperer le numero appelant
  ↓
Chercher si un patient est associe a ce numero
  ↓
Memoriser le resultat
  ├── Patient potentiellement identifie
  └── Aucun patient trouve
  ↓
Agent :
"Bonjour, ici le centre de radiologie du Dr Tahar.
Je peux vous aider a prendre ou annuler un rendez-vous."
  ↓
Identifier la demande du patient
  ↓
Demande claire ?
  ├── Non → demander une precision simple
  └── Oui
        ↓
Demande du patient
  ├── Prendre un RDV → Workflow prise de RDV
  ├── Annuler un RDV → Workflow annulation
  └── Autre demande → Transfert humain
```

## Workflow 2 - Prise de rendez-vous

```txt
Patient veut prendre un RDV
  ↓
Demander l'examen souhaite
  ↓
Examen clair ?
  ├── Non → demander une precision simple
  └── Oui
        ↓
Chercher l'examen dans les examens du site choisi
  ↓
Examen trouve ?
  ├── Non → Transfert humain
  └── Oui
        ↓
Verifier les contre-indications selon l'examen
  ↓
Contre-indication ou doute ?
  ├── Oui → Transfert humain
  └── Non
        ↓
Patient trouve grace au numero appelant ?
  ├── Oui
  │     ↓
  │   Confirmer l'identite :
  │   "Je vois un dossier associe a ce numero.
  │    Est-ce que je suis bien en ligne avec [Nom patient] ?"
  │     ↓
  │   Identite confirmee ?
  │     ├── Oui → utiliser le patient existant
  │     └── Non / doute → demander les informations patient
  │
  └── Non
        ↓
      Demander les informations patient :
      nom, prenom, date de naissance, telephone
        ↓
      Rechercher patient existant
        ↓
      Patient trouve ?
        ├── Oui → utiliser le patient existant
        ├── Non → preparer creation nouveau patient
        └── Plusieurs resultats / doute → Transfert humain
  ↓
Chercher les creneaux disponibles
  ↓
Proposer 2 ou 3 creneaux
  ↓
Patient choisit un creneau
  ↓
Recapitulatif :
examen + date + heure + site + patient
  ↓
Confirmation explicite ?
  ├── Non → ne pas creer le RDV
  └── Oui
        ↓
Creer le RDV
  ↓
Creation reussie ?
  ├── Oui → confirmer le rendez-vous
  └── Non → Transfert humain
```

## Workflow 3 - Annulation de rendez-vous

```txt
Patient veut annuler un RDV
  ↓
Patient trouve grace au numero appelant ?
  ├── Oui
  │     ↓
  │   Confirmer l'identite :
  │   "Je vois un dossier associe a ce numero.
  │    Est-ce que je suis bien en ligne avec [Nom patient] ?"
  │     ↓
  │   Identite confirmee ?
  │     ├── Oui → utiliser le patient existant
  │     └── Non / doute → demander les informations patient
  │
  └── Non
        ↓
      Demander les informations patient :
      nom, telephone, date de naissance si besoin
        ↓
      Rechercher patient existant
        ↓
      Patient trouve ?
        ├── Oui → continuer
        └── Non / doute / plusieurs resultats → Transfert humain
  ↓
Retrouver les RDV futurs du patient
  ↓
RDV trouve ?
  ├── Non → Transfert humain
  ├── Plusieurs RDV → demander lequel annuler
  └── Oui
        ↓
Recapitulatif :
examen + date + heure + site
  ↓
Confirmation explicite d'annulation ?
  ├── Non → ne rien annuler
  └── Oui
        ↓
Annuler le RDV
  ↓
Annulation reussie ?
  ├── Oui → confirmer l'annulation
  └── Non → Transfert humain
```

## Cas de transfert humain

L'agent transfere l'appel a un humain dans les cas suivants :

- urgence ;
- resultat d'examen ;
- question medicale ;
- symptome ou douleur ;
- demande hors prise ou annulation de rendez-vous ;
- examen introuvable ;
- patient ne sait pas quel examen prendre ;
- contre-indication ;
- doute sur une contre-indication ;
- patient introuvable ;
- identite ambiguë ;
- rendez-vous introuvable ;
- erreur technique ou erreur API.

## Tools deduits du flux

Ce flux fait apparaitre 5 tools simples :

- `search_exam` : trouver un examen du site choisi ;
- `find_patient` : rechercher un patient par telephone, nom ou date de naissance ;
- `get_available_slots` : recuperer des creneaux disponibles ;
- `create_appointment` : creer le rendez-vous apres confirmation ;
- `cancel_appointment` : annuler le rendez-vous apres confirmation.
