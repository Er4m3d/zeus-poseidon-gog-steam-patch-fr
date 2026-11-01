# Patch FR — Le Maître de l'Olympe : Zeus & Poséidon (GOG / Steam)

**Un seul exe, sans rien à installer**, qui transforme la version GOG (*Zeus and Poseidon*) ou Steam (*Zeus + Poseidon*) du jeu :

- **en français**, à partir de **votre CD français** de *Le Maître de l'Atlantide - Poséidon* : textes, messages, voix, vidéos, campagnes, accents ;
- en **1280 × 720** (à la place du mode 1024 × 768) ;
- avec la **correction de l'apparition des dieux** et des animations au ralenti ;
- sans les **figements réguliers de l'image** (toutes les quelques secondes) du jeu d'origine.

> **Aucun fichier du jeu n'est distribué.** L'exe ne contient que le code de ce dépôt : les fichiers français sont lus sur votre CD au moment de l'installation, et tout le reste est fabriqué à partir de votre propre jeu.

---

## Installer

**Il faut :**

| | |
|---|---|
| Windows | 10 ou 11 |
| Le jeu | version GOG ou Steam, en anglais d'origine (`Zeus.exe` 2.1.4.0 non modifié) |
| Le CD | *Le Maître de l'Atlantide - Poséidon*, version française, dans un lecteur — ou son image ISO montée (double-clic sur le fichier .iso) |

1. Téléchargez **`ZeusPatchFR.exe`** dans la page [**Releases**](https://github.com/Er4m3d/zeus-poseidon-gog-steam-patch-fr/releases).
2. Lancez-le et acceptez la demande d'autorisation de Windows (le jeu est souvent dans *Program Files*).
   Si Windows affiche « Windows a protégé votre ordinateur » : *Informations complémentaires* › *Exécuter quand même*.
3. Choisissez le jeu (les versions GOG et Steam sont détectées), le lecteur du CD, puis cliquez sur **Installer**.

**Désinstaller** : relancez `ZeusPatchFR.exe` et cliquez sur **Désinstaller** — le jeu redevient identique à l'original.

### Bon à savoir

- **GOG Galaxy** (*Vérifier / Réparer*) et **Steam** (*Vérifier l'intégrité des fichiers du jeu*) remettent les fichiers anglais : relancez alors le patch. De même après une mise à jour du jeu par Steam.
- **1280 × 720** : l'option « Résolution 1280 x 720 » du menu *Options* remplace l'ancienne « 1024 x 768 » et est choisie à l'installation. Le jeu s'en sert si l'écran fait au moins 1280 pixels de large **après mise à l'échelle de Windows** (un écran 1920 × 1080 convient jusqu'à 150 %) ; sinon il se met en 800 × 600.
- **Sauvegardes** : les campagnes portent des noms français ; une campagne commencée en anglais ne peut pas être continuée en français (et inversement).
- **Ambiances sonores** : 17 ambiances du jeu de base (agora, philosophes, théâtre) ne sont pas sur le CD de Poséidon et restent en anglais.
- **Ligne de commande** (sans fenêtre) :
  `ZeusPatchFR.exe --installer --jeu "<dossier du jeu>" --cd D:\ [--sans-resolution] [--sans-dieux] [--sans-son] [--journal <fichier>]`
  `ZeusPatchFR.exe --desinstaller --jeu "<dossier du jeu>"`

---

## Ce que fait le patch

| Élément | Source | Détail |
|---|---|---|
| 902 fichiers (voix, vidéos…) | CD, fichiers en clair | copiés tels quels |
| 71 fichiers (textes, messages, aventures…) | CD, archive InstallShield `data1.hdr` / `data*.cab` | extraits par l'installateur |
| 5 campagnes de Zeus | le jeu lui-même | identiques à la version anglaise, recopiées sous leur nom français |
| Polices | le jeu lui-même | adaptées au français (voir plus bas) |
| `Zeus.exe` | le jeu lui-même | accents, 1280 × 720, dieux, figements (voir plus bas) |
| 25 images de fond | le jeu lui-même | menus et cartes du monde au format 1280 × 720 |

Chaque fichier lu sur le CD est contrôlé par son empreinte MD5 (`data/plan.txt`) ; `Zeus.exe` est contrôlé par son empreinte MD5 avant toute modification. `data/patch_exe.txt` ne contient que des adresses et les octets ajoutés par le patch, aucun octet du jeu : la table de caractères française, seule donnée reprise de l'exe français, est lue sur le CD à l'installation et contrôlée par son empreinte. Tout fichier remplacé est d'abord sauvegardé dans `Sauvegarde_VO_Patch_FR`, dans le dossier du jeu.

---

## Fonctionnement

### Fichiers français

La version française d'origine et les versions GOG / Steam ont le même exécutable (2.1.4.0) et le même format de données : tout le texte est externe (`Zeus_Text.eng`, `Zeus_MM.eng`, `Model\Zeus eventmsg.txt`, textes des aventures). Le CD de Poséidon (version 2.0) contient presque tous les fichiers de la version française 2.1 : seul `Zeus_MM.eng` diffère, par la mention « Version 2.0 » de l'aide, corrigée à l'installation.

Les fichiers absents du CD de Poséidon viennent du CD du jeu de base Zeus : cinq campagnes (identiques à la version anglaise, il suffit de les renommer), dix-sept ambiances sonores (laissées en anglais) et les polices (voir ci-dessous). Les aventures anglaises, qui n'ont pas le même nom de fichier, sont mises de côté pour ne pas apparaître en double.

L'archive du CD est au format InstallShield 6 : `src/InstallShieldCab.cs` lit la table des fichiers de `data1.hdr` et décompresse les données (blocs « longueur 16 bits + deflate brut », fichiers à cheval sur deux volumes).

### Polices

Les polices françaises ne sont pas sur le CD de Poséidon. Celles de GOG / Steam contiennent les mêmes dessins de lettres, avec deux différences corrigées par `src/Polices.cs` :

1. dans 4 des 18 polices, GOG a interverti cinq paires de glyphes (à/â, è/ê, ì/î, ò/ô, ù/û) : les données sont remises dans l'ordre français, en gardant les positions croissantes et contiguës dans le `.555` (le moteur l'exige) ;
2. le « ç » est 1 à 3 pixels trop bas : il est remonté pour aligner son corps sur celui du « c », et réencodé à sa place (même longueur).

### Accents dans `Zeus.exe`

- **Table caractère → glyphe** : celle de l'exe français (lue dans le `Zeus.exe` du CD) remplace celle de l'exe GOG, qui diffère sur 39 valeurs.
- **Position verticale** : le moteur remonte chaque lettre accentuée de `hauteur du glyphe − hauteur de référence de la police`. L'exe GOG utilise d'autres hauteurs de référence, et remonte en plus de 2 pixels une liste de lettres polonaises (CP1250) qui correspond à ê, Ê, œ, æ, ó, ñ… en CP1252. Le patch reprend les valeurs de l'exe français :

| Police (n° FR) | Exe FR | Exe GOG / Steam |
|---|---|---|
| 7, 8 | 29 | 23, 24 |
| 1 | 10 | 9 |
| 17 | 10 | 7 |
| 9, 11 | 12 | 11 |
| 12 à 15 | 11 | 11 |
| autres (menus…) | 16 | 11 |
| texte des messages | 16 (11 pour la police 14) | 11 |

### Apparition des dieux

La fonction d'animation des personnages (`0x5AF8C0` et voisines) reçoit une vitesse : avec 100, l'image n'avance qu'aux tics prévus par la vitesse propre de l'animation, d'où des dieux qui apparaissent et agissent au ralenti ; avec 0, elle avance à chaque tic. Le patch passe cette valeur à 0 pour 70 appels (dieux, ramasseurs d'oursins, quelques autres animations). Ces emplacements ont été identifiés par le *Zeus/Poseidon Animation Fix Patch* de Pecunia (2018) ; le patch n'a pas besoin de ce dernier.

### Figements de l'image

Le jeu d'origine (versions GOG et Steam) se fige 200 à 400 ms toutes les quelques secondes : le fil principal attend le moteur audio Miles (`mss32.dll`). Deux causes, mesurées en échantillonnant le fil principal pendant les figements :

- **sons d'ambiance** : le jeu arrête régulièrement un par un tous les sons d'ambiance 3D, même ceux déjà terminés, et chaque `AIL_end_3D_sample` bloque un moment. Une petite routine ajoutée (`0x5D7600`) ne fait plus l'arrêt que pour un son qui joue encore (`AIL_3D_sample_status` = 4) ;
- **musique** : au changement de morceau, le fondu baisse le volume par paliers avec un `Sleep(33)` à chaque palier ; l'attente passe à 0 (le morceau change sans fondu).

Sur une partie de 60 s : 6 figements avant, 0 lié au son après. Il reste un figement d'environ 300 ms à chaque **sauvegarde automatique** (`Historique_autosave.sav`, compressé par le jeu) ; on peut l'éviter avec *Options* › *Enreg auto - Non*.

### 1280 × 720

Le mode « 1024 × 768 » devient 1280 × 720. Les emplacements du code qui dépendent de la résolution ont été repérés en comparant avec le mod grand écran *ZEUS_WIDE1*, puis complétés et revus (le patch n'a pas besoin de ce mod) ; les valeurs sont recalculées à partir des règles des modes d'origine et vérifiées en jeu :

| Élément | 1024 × 768 | 1280 × 720 |
|---|---|---|
| Mode d'affichage, taille d'écran mémorisée, tests « largeur = 1024 » | 1024 × 768 | 1280 × 720 |
| Vue de la ville : lignes de cases (`hauteur / 15 − 1`) | 50 | 47 |
| Vue de la ville : colonnes (la fenêtre de message, `58 n + 31` px, tient dans la vue) | 14 / 17 | 18 / 21 |
| Bord du panneau latéral, ouvert / replié | 838 / 958 | 1078 / 1198 |

- **Panneau latéral** : mise en page « 202 px » du mode 800 × 600 (panneau de 186 px + bande de finition de 16 px au bord droit), qui laisse la place à 18 colonnes de cases sans que les messages débordent. La bande de finition est dessinée par une petite routine ajoutée (deux fois, car elle fait 600 px de haut).
- **Barre du haut** (une image de 838 px) : une routine la dessine une première fois décalée jusqu'au panneau, puis normalement par-dessus.
- **Écrans plein écran** (menus, fenêtres) : le moteur les centre déjà (`(1024 − largeur) / 2`, `(768 − hauteur) / 2`) ; leurs images de fond sont générées en 1280 × 720 : l'original au centre, côtés remplis par l'image agrandie, floutée et assombrie (`src/Images.cs`).
- **Cartes du monde** : l'original reste à gauche (positions des villes inchangées) et la carte est prolongée vers l'est jusqu'au panneau par une texture de mer prise dans la carte elle-même.
- Le bas du panneau latéral (portrait des dieux, purement décoratif) est coupé de 48 px.

Les routines ajoutées sont placées dans l'espace libre en fin de section `.text` (dont la taille virtuelle est étendue) ; `tools/generer_patch_exe.py` les assemble et contrôle l'absence de chevauchement.

---

## Construire depuis les sources

**Compiler l'exe** — rien à installer, le compilateur C# fait partie de Windows (.NET Framework 4) :

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1        # -> dist\ZeusPatchFR.exe
```

**Régénérer les données** (`data/plan.txt`, `data/patch_exe.txt`) — Python 3, une installation française 2.1 de référence, le jeu GOG / Steam d'origine et le CD :

```powershell
python tools\generer_plan.py --fr "<installation française 2.1>" --gog "<jeu GOG / Steam>" --cd D:\
python tools\generer_patch_exe.py --gog "<jeu GOG / Steam>\Zeus.exe" --cd D:\
```

Ces fichiers ne contiennent que des chemins, des empreintes et des octets de code : aucun fichier du jeu.

```
build.ps1                  compilation de l'exe
src/
  Programme.cs             point d'entrée (fenêtre ou ligne de commande)
  Fenetre.cs               interface
  Jeu.cs                   détection des versions GOG et Steam
  SourceCd.cs              détection et contrôle du CD
  InstallShieldCab.cs      lecture de l'archive InstallShield du CD
  Installateur.cs          installation, sauvegarde, désinstallation
  Polices.cs               adaptation des polices
  Images.cs                images de fond 1280 x 720
  Donnees.cs               plan et correctif de Zeus.exe intégrés à l'exe
  app.manifest             droits administrateur, compatibilité
data/
  plan.txt                 fichiers à installer, avec leur source et leur MD5
  patch_exe.txt            modifications de Zeus.exe, par groupe (aucun octet du jeu)
tools/
  iscab.py                 lecture de l'archive du CD (Python)
  generer_plan.py          génération de data/plan.txt
  generer_patch_exe.py     génération de data/patch_exe.txt (accents, dieux, son, 1280 x 720)
```

---

## Crédits

- Traduction française : version officielle (Sierra / Impressions Games), lue sur le CD de l'utilisateur.
- Emplacements de la correction des animations : *Zeus/Poseidon Animation Fix Patch* de Pecunia (2018).
- Repérage des emplacements dépendant de la résolution : comparaison avec le mod grand écran *ZEUS_WIDE1*.

## Licence

Code source sous licence [MIT](LICENSE). La licence ne couvre pas les fichiers du jeu.

## Avertissement

Projet non officiel, sans lien avec Sierra, Impressions Games, Activision, GOG ou Valve (Steam). *Le Maître de l'Olympe : Zeus* et *Poséidon* sont des marques de leurs propriétaires respectifs. Le patch s'utilise avec des copies du jeu et un CD que vous possédez.
