# Test technique - Integration agent vocal pour un centre de radiologie

## Contexte

Le Dr. Karim Tahar dirige un centre de radiologie independant a Marseille. Il vient de signer avec Rounded pour deployer un agent vocal qui gerera la prise de rendez-vous par telephone.

Le centre :

- 4 radiologues associes
- 6 manipulateurs
- 3 secretaires
- Environ 150 rendez-vous par jour
- Examens proposes : radios, scanner, IRM, echographie, mammographie, osteodensitometrie
- RIS utilise : Enovacom AIR

## Probleme identifie

- Files d'attente telephoniques saturees entre 8h et 10h
- 25 a 30% des appels sont abandonnes
- Les secretaires passent l'essentiel de leur temps au telephone au lieu de gerer le centre

## Attentes pour l'agent vocal Rounded

L'agent doit pouvoir :

- Prendre des rendez-vous par telephone
- Annuler un rendez-vous existant
- Reconnaitre un patient existant a partir de son numero
- Detecter les contre-indications de base et refuser le rendez-vous ou transferer si besoin
- Transferer a un humain pour les urgences, les resultats d'examen, les questions medicales et tout cas hors cadre

Contre-indications a detecter :

- IRM : pace-maker, implants ferromagnetiques
- Scanner avec injection : allergie a l'iode, insuffisance renale
- Radio : grossesse

## Hors perimetre absolu

L'agent ne donne jamais d'information medicale, ne commente jamais un resultat d'examen et ne donne jamais d'avis sur un symptome.

Tout ce qui est medical doit etre transfere a un humain.

## Mission

Le perimetre fonctionnel se limite a :

- Prise de rendez-vous
- Annulation de rendez-vous

Rien d'autre.

L'API Enovacom de recette expose 5 sites differents. Il faut en choisir un seul des le depart, considere comme le centre du Dr. Tahar, puis travailler uniquement avec ses examens, praticiens et creneaux.

Ce choix doit etre documente dans le repo.

## Ordre attendu

### 1. Penser le flux d'appel en amont

Avant d'ecrire du code, il faut reflechir au deroulement d'un appel de prise de rendez-vous :

- Quelles informations collecter
- Dans quel ordre
- Quels embranchements prevoir
- Comment gerer les hesitations
- Comment gerer un changement d'avis
- Comment gerer une contre-indication

Cette reflexion determine ensuite les tools necessaires. Il ne faut pas simplement wrapper toute l'API Enovacom.

La documentation du raisonnement doit etre presente dans le repo.

### 2. Concevoir et coder les tools

A partir du flux, il faut definir les tools necessaires :

- Interface
- Parametres
- Comportement attendu

Les tools doivent etre codables et testables en local, individuellement, sans dependance immediate a la plateforme Rounded.

### 3. Deployer les tools

Les tools doivent etre deployes sur un endpoint publiquement accessible, par exemple :

- Cloud Run
- Lambda
- Autre serverless

Ils doivent ensuite pouvoir etre branches a Rounded.

### Bonus

Si le temps le permet :

- Creer l'agent dans la plateforme Rounded
- Rediger son prompt, sa persona et son comportement
- Brancher les tools deployes
- Demontrer un appel test qui cree un vrai rendez-vous dans Enovacom de bout en bout

Le bonus est valorise, mais le coeur du test reste les etapes 1, 2 et 3.

## API Enovacom RIS

Environnement de recette :

```txt
https://ris-recette-instance3.nd.care/AIR/eris_project/eris_php/WebServices/WS_rdv_externe.php
```

Documentation interactive :

```txt
https://ris-recette-instance3.nd.care/AIR/eris_project/eris_php/WebServices/WS_rdv_externe.php?view=true
```

Toutes les requetes sont des POST avec un body JSON contenant :

- `token`
- `command`

Exemple :

```bash
curl -X POST "$URL" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "$ENOVACOM_TOKEN",
    "command": "get_config"
  }'
```

## Methodes disponibles

Methodes principales utiles pour ce test :

- `get_config` : configuration complete, sites, examens, praticiens, salles, liens
- `get_availabilities` : creneaux disponibles pour un examen donne
- `add_rdv` : creer un rendez-vous
- `delete_rdv` : annuler un rendez-vous
- `list_rdv` : lister les rendez-vous d'une journee
- `get_patient` : rechercher un patient
- `get_rdv` : details d'un rendez-vous

Autres methodes disponibles :

- `confirm_rdv`
- `move_rdv`
- `update_rdv`
- `get_document`
- `add_file`

## Points d'attention API

- Tous les parametres sont des strings, meme les IDs numeriques dans `add_rdv`
- Le format de date varie selon l'endpoint
- `sending_application` est obligatoire pour `add_rdv` et `delete_rdv`
- Utiliser `sending_application: "rounded"`
- `patient_id: "0"` dans `add_rdv` cree automatiquement un nouveau patient
- La documentation HTML interactive detaille les parametres obligatoires et optionnels
- L'environnement est une recette : les rendez-vous peuvent etre crees, modifies et supprimes librement

## Donnees disponibles

- 5 sites
- 508 examens
- 22 praticiens
- 41 salles / equipements
- Disponibilites ouvertes sur les prochaines semaines

## Restitution attendue

Pendant la restitution, il faudra montrer :

1. La reflexion sur le flux d'appel
2. Les tools deployes, leur URL publique, leur signature et leur comportement individuel
3. Bonus : l'agent branche a Rounded avec les tools connectes
4. Bonus ++ : un appel test vocal qui cree un vrai rendez-vous dans Enovacom de bout en bout

Il n'est pas necessaire de preparer des slides. Le repo et l'environnement de code seront regardes directement.

## Livrables

Un repo Git partage avec `@yassinegmrounded`, contenant :

- Le code des tools
- L'eventuelle configuration de deploiement
- La documentation du flux
- Un README expliquant comment lancer et tester les tools en local
- L'URL publique des tools deployes
- Les choix d'architecture
- Les dependances importantes
- Les priorites retenues
- Ce qui aurait ete fait avec plus de temps

Des commits reguliers avec des messages explicites sont apprecies.
