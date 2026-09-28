# Patch FR — Le Maître de l'Olympe : Zeus & Poséidon (version GOG)

Remet la version GOG de *Zeus: Master of Olympus + Poseidon* (en anglais) **entièrement en français**, à partir des fichiers de la version française d'origine (CD Sierra, v2.1) :

- textes de l'interface, des bâtiments, des dieux et des héros ;
- messages et événements (requêtes, oracles, invasions…) ;
- polices françaises, **avec les accents correctement affichés** ;
- voix françaises des habitants et des campagnes, ambiances sonores ;
- vidéos d'introduction françaises ;
- campagnes et aventures avec leurs titres et textes français.

Le jeu reste celui de GOG (pas de protection CD, compatible Windows 10/11). Seul l'affichage des lettres accentuées est corrigé dans `Zeus.exe` (voir [Fonctionnement](#fonctionnement)).

> **Ce dépôt ne contient aucun fichier du jeu.** Le patch se construit à partir de **votre propre** version CD française et de **votre** version GOG. Ne publiez pas le patch construit (dossier `dist/`) : il contient des fichiers protégés par le droit d'auteur.

---

## Construire le patch

### Prérequis

| Élément | Détail |
|---|---|
| Windows | 10 ou 11, PowerShell 5.1 (inclus) ou 7 |
| Version GOG | *Zeus and Poseidon*, `Zeus.exe` v2.1.4.0, **en anglais d'origine** (patch FR non installé) |
| Version CD française | *Le Maître de l'Olympe : Zeus + Poséidon* v2.1 installée (le dossier d'installation suffit) |
| 7-Zip | pour créer le ZIP (`C:\Program Files\7-Zip\7z.exe` par défaut) |
| Python 3 + capstone | `python -m pip install --user capstone` (génération et vérification du correctif de `Zeus.exe`) |

### Commande

```powershell
git clone https://github.com/Er4m3d/zeus-poseidon-gog-patch-fr.git
cd zeus-poseidon-gog-patch-fr
powershell -ExecutionPolicy Bypass -File .\build_patch.ps1 -SourceFR "C:\Sierra\Le Maître de l' Olympe  Zeus" -SourceGOG "C:\Program Files\GOG Galaxy\Games\Zeus and Poseidon"
```

(`-ExecutionPolicy Bypass` évite le blocage des scripts téléchargés par Windows ; adaptez les deux chemins à vos installations.)

Résultat : `dist\Patch_FR_Zeus_Poseidon_GOG_v1.3\` et le ZIP correspondant.

Options :

- `-SansAccents` : variante de secours, textes et noms de fichiers convertis en ASCII (é → e, œ → oe…), polices et `Zeus.exe` d'origine intacts ;
- `-Sortie <dossier>` : dossier de sortie (par défaut `dist`) ;
- `-SevenZip <chemin>` : emplacement de `7z.exe`.

Le script compare les deux installations, ne garde que les fichiers de langue qui diffèrent (≈ 1 000 fichiers, ≈ 260 Mo) et prépare la liste des fichiers anglais à mettre de côté.

---

## Installer le patch

1. Fermez le jeu.
2. Extrayez le ZIP (clic droit › *Extraire tout…*).
3. Double-cliquez sur **`INSTALLER.bat`**.
4. Le jeu GOG est détecté automatiquement (registre GOG, emplacements usuels) ; sinon une fenêtre permet de choisir son dossier.
5. Acceptez la demande d'autorisation Windows si le jeu est dans `C:\Program Files`.

Pendant l'installation, tous les fichiers anglais remplacés (dont `Zeus.exe`) sont sauvegardés dans le dossier du jeu, sous-dossier `Sauvegarde_VO_Patch_FR`.

**Désinstaller** : double-cliquez sur **`DESINSTALLER.bat`** — le jeu redevient identique à l'original.

**Mettre à jour** : lancez l'`INSTALLER.bat` de la nouvelle version, par-dessus l'ancienne.

Options avancées de `scripts\patch.ps1` : `-DossierJeu "<chemin>"`, `-Desinstaller`, `-Oui` (aucune question).

### Remarques

- N'utilisez pas *Vérifier / Réparer* dans GOG Galaxy : cela remet les fichiers anglais. Il suffit alors de relancer `INSTALLER.bat`.
- Les campagnes portent des noms français : une campagne commencée en anglais ne peut pas être continuée après le patch (et inversement).

---

## Fonctionnement

### Fichiers de langue

Les deux versions ont le même exécutable (v2.1.4.0) et le même format de données : le texte est entièrement externe (`Zeus_Text.eng`, `Zeus_MM.eng`, `Zeus_Editor_Text.eng`, `Model\Zeus eventmsg.txt`, textes des aventures). Le patch copie donc les fichiers français à la place des anglais. Les aventures anglaises, qui n'ont pas le même nom de fichier, sont mises de côté pour ne pas apparaître en double.

L'exe du CD français, protégé par SecuROM, n'est pas utilisé.

### Correctif des accents dans `Zeus.exe`

Les polices françaises sont dessinées pour l'exe français. Avec l'exe GOG, deux problèmes apparaissent :

1. **Mauvais glyphes** : la table « caractère → glyphe de police » (224 octets, caractères 0x20 à 0xFF) diffère sur 39 valeurs (à, è/ê, ì/î, ò/ô, ù/û, œ, æ…). Elle est remplacée par celle de l'exe français.
2. **Accents décalés vers le haut** : le moteur remonte chaque lettre accentuée de `hauteur du glyphe − hauteur de référence de la police`. L'exe GOG utilise d'autres hauteurs de référence, et remonte en plus de 2 pixels une liste de lettres polonaises (CP1250) qui correspond à ê, Ê, œ, æ, ó, ñ… en CP1252. Le correctif reprend les valeurs de l'exe français :

| Police (n° FR) | Exe FR | Exe GOG |
|---|---|---|
| 7, 8 | 29 | 23, 24 |
| 1 | 10 | 9 |
| 17 | 10 | 7 |
| 9, 11 | 12 | 11 |
| 12 à 15 | 11 | 11 |
| autres (menus…) | 16 | 11 |
| texte des messages | 16 (11 pour la police 14) | 11 |

Deux petites routines sont ajoutées dans l'espace libre en fin de section `.text`. `tools/asm_accents.py` les assemble et vérifie les octets d'origine. Le correctif est décrit dans `scripts\zeus_exe_patch.txt` (lignes `offset octets_d'origine nouveaux_octets`) : l'installateur vérifie chaque zone avant d'écrire et refuse tout exe non reconnu.

### Formats (pour la variante sans accents)

- `Zeus_Text.eng` : en-tête de 28 octets, 1000 entrées d'index `(offset, nombre)`, puis chaînes terminées par `\0` à partir de 0x1F5C.
- `Zeus_MM.eng` : en-tête de 24 octets, 1000 entrées de 80 octets (offsets de texte aux positions 56, 68, 72, 76), puis chaînes.

`tools/SansAccents.ps1` convertit les chaînes et recalcule les offsets.

---

## Structure du dépôt

```
build_patch.ps1            construction du patch
src/
  INSTALLER.bat            lanceur d'installation
  DESINSTALLER.bat         lanceur de désinstallation
  LISEZMOI.txt             notice incluse dans le ZIP
  scripts/patch.ps1        installation / désinstallation / mise à jour
tools/
  asm_accents.py           correctif du positionnement des accents dans Zeus.exe
  TableCaracteres.ps1      recherche de la table caractère → glyphe
  SansAccents.ps1          conversion ASCII des fichiers de texte (variante -SansAccents)
```

## Licence

Code source sous licence [MIT](LICENSE). La licence ne couvre pas les fichiers du jeu ni les patchs construits.

## Avertissement

Projet non officiel, sans lien avec Sierra, Impressions Games, Activision ou GOG. *Le Maître de l'Olympe : Zeus* et *Poséidon* sont des marques de leurs propriétaires respectifs. Utilisez ce patch uniquement avec des copies du jeu que vous possédez.
