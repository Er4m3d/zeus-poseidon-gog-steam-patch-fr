# Patch FR — Le Maître de l'Olympe : Zeus & Poséidon (GOG / Steam)

**Un seul exe, sans rien à installer**, qui transforme la version GOG (*Zeus and Poseidon*) ou Steam (*Zeus + Poseidon*) du jeu :

- **entièrement en français**, à partir de **vos deux CD français** (*Le Maître de l'Olympe - Zeus* et *Le Maître de l'Atlantide - Poséidon*) : textes, messages, voix, vidéos, campagnes, ambiances, polices et accents d'origine ;
- en **1280 × 720** (à la place du mode 1024 × 768), avec la **vidéo d'intro en plein écran** ;
- sans les **figements réguliers de l'image** (toutes les quelques secondes) du jeu d'origine ;
- avec des **animations à la bonne vitesse** : apparition des dieux, hippodrome, poste de commerce, bateaux de pêche.

> **Aucun fichier du jeu n'est distribué.** L'exe ne contient que le code de ce dépôt : les fichiers français sont lus sur vos CD au moment de l'installation, et tout le reste est fabriqué à partir de votre propre jeu.

---

## Installer

**Il faut :**

| | |
|---|---|
| Windows | 10 ou 11 |
| Le jeu | version GOG ou Steam, en anglais d'origine (`Zeus.exe` 2.1.4.0 non modifié) |
| CD 1 | *Le Maître de l'Olympe - Zeus* (jeu de base), version française |
| CD 2 | *Le Maître de l'Atlantide - Poséidon* (extension), version française |

Un seul lecteur suffit : l'installateur lit d'abord le CD 1, puis demande d'insérer le CD 2. Les images ISO montées (double-clic sur le fichier .iso) ou des copies des CD sur le disque conviennent aussi.

1. Téléchargez **`ZeusPatchFR.exe`** dans la page [**Releases**](https://github.com/Er4m3d/zeus-poseidon-gog-steam-patch-fr/releases).
2. Lancez-le et acceptez la demande d'autorisation de Windows (le jeu est souvent dans *Program Files*).
   Si Windows affiche « Windows a protégé votre ordinateur » : *Informations complémentaires* › *Exécuter quand même*.
3. Choisissez le jeu (les versions GOG et Steam sont détectées) et le lecteur de chaque CD (le même s'il n'y en a qu'un), puis cliquez sur **Installer**.
4. Insérez les CD quand l'installateur les demande : d'abord **Zeus**, puis **Poséidon**. Rien n'est modifié dans le jeu avant que les deux CD aient été lus et contrôlés.

**Désinstaller** : relancez `ZeusPatchFR.exe` et cliquez sur **Désinstaller** — le jeu redevient identique à l'original.

### Bon à savoir

- **GOG Galaxy** (*Vérifier / Réparer*) et **Steam** (*Vérifier l'intégrité des fichiers du jeu*) remettent les fichiers anglais : relancez alors le patch. De même après une mise à jour du jeu par Steam.
- **1280 × 720** : l'option « Résolution 1280 x 720 » du menu *Options* remplace l'ancienne « 1024 x 768 » et est choisie à l'installation. Le jeu s'en sert si l'écran fait au moins 1280 pixels de large **après mise à l'échelle de Windows** (un écran 1920 × 1080 convient jusqu'à 150 %) ; sinon il se met en 800 × 600.
- **Sauvegardes** : les campagnes portent des noms français ; une campagne commencée en anglais ne peut pas être continuée en français (et inversement).
- **Ligne de commande** (sans fenêtre) :
  `ZeusPatchFR.exe --installer --jeu "<dossier du jeu>" --cd-zeus D:\ --cd-poseidon E:\ [--sans-resolution] [--sans-son] [--sans-animations] [--journal <fichier>]`
  (en ligne de commande, les deux CD doivent être accessibles en même temps : deux lecteurs, images ISO ou copies)
  `ZeusPatchFR.exe --desinstaller --jeu "<dossier du jeu>"`

---

## Ce que fait le patch

| Élément | Source | Détail |
|---|---|---|
| 902 fichiers (voix, vidéos…) | CD 2 Poséidon, fichiers en clair | copiés tels quels |
| 71 fichiers (textes, messages, aventures…) | CD 2 Poséidon, archive InstallShield `data1.hdr` / `data*.cab` | extraits par l'installateur |
| Polices et 17 ambiances parlées (philosophes, agora, théâtre) | CD 1 Zeus, archive InstallShield `data1.cab` | extraites par l'installateur |
| 5 campagnes de Zeus | le jeu lui-même | identiques à la version anglaise, recopiées sous leur nom français |
| `Zeus.exe` | le jeu lui-même | accents, 1280 × 720, dieux, figements, animations (voir plus bas) |
| 37 images de fond | le jeu lui-même | menus, écrans de chargement et cartes du monde au format 1280 × 720 |

Chaque fichier lu sur les CD est contrôlé par son empreinte MD5 (`data/plan.txt`) ; `Zeus.exe` est contrôlé par son empreinte MD5 avant toute modification. `data/patch_exe.txt` ne contient que des adresses et les octets ajoutés par le patch, aucun octet du jeu : la table de caractères française, seule donnée reprise de l'exe français, est lue sur le CD à l'installation et contrôlée par son empreinte. Tout fichier remplacé est d'abord sauvegardé dans `Sauvegarde_VO_Patch_FR`, dans le dossier du jeu.

---

## Fonctionnement

### Fichiers français

La version française d'origine et les versions GOG / Steam ont le même exécutable (2.1.4.0) et le même format de données : tout le texte est externe (`Zeus_Text.eng`, `Zeus_MM.eng`, `Model\Zeus eventmsg.txt`, textes des aventures). Le CD de Poséidon (version 2.0) contient presque tous les fichiers de la version française 2.1 : seul `Zeus_MM.eng` diffère, par la mention « Version 2.0 » de l'aide, corrigée à l'installation.

Les fichiers absents du CD de Poséidon sont pris sur le CD du jeu de base Zeus : les **polices** françaises (`DATA\Zeus_Fonts.sg3` / `.555`) et **17 ambiances parlées** (citations des philosophes, marchands de l'agora, acteurs et public du théâtre). Ils sont identiques à ceux d'une installation française 2.1. Les cinq campagnes de Zeus sont identiques à la version anglaise : il suffit de les renommer. Les aventures anglaises, qui n'ont pas le même nom de fichier, sont mises de côté pour ne pas apparaître en double.

Le CD 1 est lu en premier : ses 19 fichiers (environ 8 Mo) sont contrôlés puis gardés en mémoire, ce qui permet de changer de disque avec un seul lecteur. Le CD 2 est lu ensuite, et une version précédente du patch n'est retirée qu'une fois les deux CD contrôlés.

`src/InstallShieldCab.cs` lit les deux formats d'archive : InstallShield 6 pour le CD de Poséidon (table des fichiers dans `data1.hdr`, fichiers à cheval sur deux volumes) et InstallShield 5 pour le CD de Zeus (table au début de `data1.cab`). Les données sont compressées en blocs « longueur 16 bits + deflate brut ».

### Accents dans `Zeus.exe`

- **Table caractère → glyphe** : celle de l'exe français (lue dans le `Zeus.exe` du CD) remplace celle de l'exe GOG, qui diffère sur 39 valeurs.
- **Positions des textes** : l'exe français déplace ou élargit 23 textes pour que des traductions plus longues tiennent (« Commencer le scénario », « Rejoindre la cité », « Entrez un nom de chef », « Paramètres de difficulté »…). Il élargit aussi 34 boutons ou zones de fenêtres (liste des chefs : « Continuer »…). Ces valeurs, relevées en comparant les deux exe, sont reprises dans l'exe GOG (`TEXTES_FR`, `BOUTONS_FR`).
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

### Animations trop rapides

Quelques animations d'ambiance tournent bien trop vite. Les vitesses retenues ont été réglées à l'œil, en jeu :

- **Hippodrome** (jeu d'origine) : les spectateurs des tribunes, les stands de paris et le juge de la ligne d'arrivée sont dessinés avec `image = compteur ÷ diviseur`, le compteur avançant à chaque tic. Les diviseurs passent de 3 (ou 2) à 60 (ou 40).
- **Poste de commerce** (jeu d'origine) : l'employé sur le toit avance d'une image à chaque affichage, sans suivre le rythme du jeu. Il n'avance plus que lorsque la table de rythme du jeu l'autorise (`0x6668EC`, toutes les 60 ms), comme les autres animations.
- **Bateaux de pêche au filet** : trop lents dans le jeu d'origine, beaucoup trop rapides avec la correction des dieux (une image par tic). Une petite routine les fait avancer un tic sur trois en moyenne (5 sur 15), au même rythme pour tous les bateaux. Seule l'action de pêcher est concernée, pas le déplacement des bateaux ni la pêche elle-même.

### 1280 × 720

Le mode « 1024 × 768 » devient 1280 × 720. Les emplacements du code qui dépendent de la résolution ont été repérés en comparant avec le mod grand écran *ZEUS_WIDE1*, puis complétés et revus (le patch n'a pas besoin de ce mod) ; les valeurs sont recalculées à partir des règles des modes d'origine et vérifiées en jeu :

| Élément | 1024 × 768 | 1280 × 720 |
|---|---|---|
| Mode d'affichage, taille d'écran mémorisée, tests « largeur = 1024 » | 1024 × 768 | 1280 × 720 |
| Vue de la ville : lignes de cases (`hauteur / 15 − 1`) | 50 | 47 |
| Vue de la ville : colonnes (largeur `60 n − 2` px) | 14 / 17 | 19 / 21 |
| Bord du panneau latéral, ouvert / replié | 838 / 958 | 1094 / 1214 |

- **Panneau latéral** : collé au bord droit de l'écran, comme en 1024 × 768 (panneau de 186 px, à x = 1094). Le moteur ne dessine que des cases entières (la vue fait `60 n − 2` px) : 18 colonnes s'arrêteraient 16 px avant le panneau, et le mode 800 × 600 d'origine comble cet écart par une bande décorative. Le patch donne 19 colonnes à la vue (1138 px), qui passe sous le panneau comme la vue du panneau replié dans les modes d'origine ; à chaque image, une petite routine redessine la partie recouverte du fond du panneau (1094 à 1138 px, par découpe) avant ses éléments, et la largeur des fenêtres de message est limitée au bord du panneau.
- **Barre du haut** (une image de 838 px) : une routine la dessine une première fois décalée jusqu'au panneau, puis normalement par-dessus. Même traitement pour les écrans plein écran, comme la carte de choix d'une colonie.
- **Écrans plein écran** (menus, fenêtres) : le moteur les centre déjà (`(1024 − largeur) / 2`, `(768 − hauteur) / 2`) ; leurs images de fond sont générées en 1280 × 720 : l'original au centre, côtés remplis par l'image agrandie, floutée et assombrie (`src/Images.cs`). Les 12 écrans de chargement (800 × 600) sont agrandis à la hauteur de l'écran (960 × 720), sans bandes noires en haut et en bas, avec les mêmes côtés.
- **Cartes du monde** : l'original reste à gauche (positions des villes inchangées) et la carte est prolongée vers l'est jusqu'au panneau par une texture de mer prise dans la carte elle-même.
- Le bas du panneau latéral (portrait des dieux, purement décoratif) est coupé de 48 px.
- **Fenêtres et menus** : quand une fenêtre (information sur un bâtiment, une personne, un bateau, un animal ; conseillers) ou un menu déroulant (Fichier, Options) est ouvert, le jeu redessine la ville sans redessiner le panneau, et les 19 colonnes de la vue recouvraient le début du panneau. Les 12 appels concernés passent par la même routine, qui redessine alors le fond et les éléments du panneau.
- **Vidéo d'intro** (`Zeus_Intro_HiQ.bik`, 640 × 480, dont 68 lignes noires intégrées en haut et 69 en bas) : le lecteur vidéo passait l'écran en 640 × 480, d'où une image en 4:3 entourée de noir. Il garde maintenant le mode du jeu ; en 1280 × 720, chaque image est copiée dans un tampon puis agrandie (× 2 en largeur, les 343 lignes utiles étirées sur 720, soit 5 %), sans aucune bande noire.

Les routines ajoutées sont placées dans l'espace libre en fin de section `.text` (dont la taille virtuelle est étendue) ; `tools/generer_patch_exe.py` les assemble et contrôle l'absence de chevauchement.

---

## Construire depuis les sources

**Compiler l'exe** — rien à installer, le compilateur C# fait partie de Windows (.NET Framework 4) :

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1        # -> dist\ZeusPatchFR.exe
```

**Régénérer les données** (`data/plan.txt`, `data/patch_exe.txt`) — Python 3, une installation française 2.1 de référence, le jeu GOG / Steam d'origine et les deux CD :

```powershell
python tools\generer_plan.py --fr "<installation française 2.1>" --gog "<jeu GOG / Steam>" --cd D:\ --cd-zeus E:\
python tools\generer_patch_exe.py --gog "<jeu GOG / Steam>\Zeus.exe" --cd D:\
```

Ces fichiers ne contiennent que des chemins, des empreintes et des octets de code : aucun fichier du jeu.

```
build.ps1                  compilation de l'exe
src/
  Programme.cs             point d'entrée (fenêtre ou ligne de commande)
  Fenetre.cs               interface
  Jeu.cs                   détection des versions GOG et Steam
  SourceCd.cs              détection et contrôle des deux CD
  InstallShieldCab.cs      lecture des archives InstallShield 5 et 6 des CD
  Installateur.cs          installation, sauvegarde, désinstallation
  Images.cs                images de fond 1280 x 720
  Donnees.cs               plan et correctif de Zeus.exe intégrés à l'exe
  app.manifest             droits administrateur, compatibilité
data/
  plan.txt                 fichiers à installer, avec leur source et leur MD5
  patch_exe.txt            modifications de Zeus.exe, par groupe (aucun octet du jeu)
tools/
  iscab.py                 lecture des archives des CD (Python)
  generer_plan.py          génération de data/plan.txt
  generer_patch_exe.py     génération de data/patch_exe.txt (accents, dieux, son, animations, 1280 x 720)
```

---

## Crédits

- Traduction française : version officielle (Sierra / Impressions Games), lue sur les CD de l'utilisateur.
- Emplacements de la correction des animations : *Zeus/Poseidon Animation Fix Patch* de Pecunia (2018).
- Repérage des emplacements dépendant de la résolution : comparaison avec le mod grand écran *ZEUS_WIDE1*.

## Licence

Code source sous licence [MIT](LICENSE). La licence ne couvre pas les fichiers du jeu.

## Avertissement

Projet non officiel, sans lien avec Sierra, Impressions Games, Activision, GOG ou Valve (Steam). *Le Maître de l'Olympe : Zeus* et *Poséidon* sont des marques de leurs propriétaires respectifs. Le patch s'utilise avec des copies du jeu et des CD que vous possédez.
