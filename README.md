# Patch FR — Le Maître de l'Olympe : Zeus & Poséidon (versions GOG et Steam)

Remet la version GOG (*Zeus and Poseidon*) ou Steam (*Zeus + Poseidon*) de *Zeus: Master of Olympus* (en anglais) **entièrement en français** :

- textes de l'interface, des bâtiments, des dieux et des héros ;
- messages et événements (requêtes, oracles, invasions…) ;
- polices françaises, **avec les accents correctement affichés** ;
- voix françaises des habitants et des campagnes, ambiances sonores ;
- vidéos d'introduction françaises ;
- campagnes et aventures avec leurs titres et textes français.
- Répare les animations. (facultatif)
- Change la résolution pour du 16/9. (facultatif)

Le jeu reste celui de GOG / Steam (les deux versions ont le même `Zeus.exe`, compatible Windows 10/11).

---

## 📥 Télécharger le patch (Exécutable complet)

Cet exécutable "clé en main" contient **l'ensemble des modifications et traductions citées ci-dessus**. Il est prêt à l'emploi : vous n'avez qu'à le télécharger et le lancer pour traduire votre jeu.

- [**Télécharger via MediaFire (.exe)**](https://www.mediafire.com/file/zwk7siar3avdlqd/Patch_FR_Zeus_Poseidon_v1.6_complet.exe)
- [**Télécharger via Mega (.exe)**](https://mega.nz/file/Ov5HXBDQ#HeSG8zP24V2f-Ki4d40FhFgDWAqf2ZAjYqwiXnJbx-s)

> 💡 **Note :** Si vous préférez vérifier le code, ou si vous avez besoin de générer cet exécutable vous-même de A à Z, vous pouvez le faire en suivant les explications de la section [Construire le patch](#construire-le-patch) juste en dessous.

---

## Construire le patch

### Prérequis

| Élément | Détail |
|---|---|
| Windows | 10 ou 11, PowerShell 5.1 (inclus) ou 7 |
| Version GOG ou Steam | *Zeus and Poseidon* (GOG) ou *Zeus + Poseidon* (Steam), `Zeus.exe` v2.1.4.0, **en anglais d'origine** (patch FR non installé) |
| Version CD française | *Le Maître de l'Olympe : Zeus + Poséidon* v2.1 installée (le dossier d'installation suffit) |
| 7-Zip | pour créer le ZIP (`C:\Program Files\7-Zip\7z.exe` par défaut) |
| Python 3 + capstone | `python -m pip install --user capstone` (génération et vérification du correctif de `Zeus.exe`) |

### Commande

```powershell
git clone https://github.com/Er4m3d/zeus-poseidon-gog-steam-patch-fr.git
cd zeus-poseidon-gog-steam-patch-fr
powershell -ExecutionPolicy Bypass -File .\build_patch.ps1 -SourceFR "C:\Sierra\Le Maître de l' Olympe  Zeus" -SourceGOG "C:\Program Files\GOG Galaxy\Games\Zeus and Poseidon"
```

(`-ExecutionPolicy Bypass` évite le blocage des scripts téléchargés par Windows ; adaptez les deux chemins à vos installations. `-SourceGOG` accepte aussi la version Steam, par exemple `C:\Program Files (x86)\Steam\steamapps\common\Zeus + Poseidon` : le patch obtenu est le même.)

Résultat : `dist\Patch_FR_Zeus_Poseidon_v1.6\` et le ZIP correspondant.

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
4. Les versions installées sont détectées (GOG : registre et emplacements usuels ; Steam : dossier Steam et bibliothèques secondaires). Tapez le numéro de celle à patcher, ou **A** pour choisir un autre dossier. Pour patcher les deux versions, lancez `INSTALLER.bat` deux fois.
5. Acceptez la demande d'autorisation Windows si le jeu est dans `C:\Program Files`.

Pendant l'installation, tous les fichiers anglais remplacés (dont `Zeus.exe`) sont sauvegardés dans le dossier du jeu, sous-dossier `Sauvegarde_VO_Patch_FR`.

**Désinstaller** : double-cliquez sur **`DESINSTALLER.bat`** et choisissez la version à restaurer — le jeu redevient identique à l'original.

**Mettre à jour** : lancez l'`INSTALLER.bat` de la nouvelle version, par-dessus l'ancienne.

Options avancées de `scripts\patch.ps1` : `-Plateforme GOG|Steam`, `-DossierJeu "<chemin>"`, `-SansAnimations`, `-Resolution <LxH|aucune>`, `-Desinstaller`, `-Oui` (aucune question).

### Correctif d'animations (facultatif)

Le **Zeus/Poseidon Animation Fix Patch** de Pecunia (avril 2018) corrige les dieux trop lents, les ramasseurs d'oursins et d'autres animations. Ce n'est pas notre travail : il **n'est pas inclus** dans ce dépôt ni dans le patch.

Si vous l'avez, posez son fichier `zeus_poseidon_animation_patch.zip` à côté de `INSTALLER.bat`. L'installateur :

1. vérifie que l'exe du jeu est bien la version GOG / Steam d'origine et que le ZIP contient le `Zeus.exe` attendu (empreinte MD5) ;
2. propose d'appliquer le correctif d'animations ;
3. part de ce `Zeus.exe` et y ajoute le correctif des accents : les 70 octets modifiés par Pecunia ne touchent aucune des zones du correctif des accents.

`DESINSTALLER.bat` remet le `Zeus.exe` d'origine. Option `-SansAnimations` pour ignorer le ZIP.

### Mod grand écran (facultatif)

Le mod grand écran **ZEUS_WIDE1** (archive `Zeus.7z`, 12 résolutions de 1280×720 à 2560×1600) fournit pour chaque résolution un `Zeus.exe` modifié et 38 images de fond redimensionnées. Il n'est **pas inclus** dans ce dépôt ni dans le patch.

Si vous l'avez, posez `Zeus.7z` (7-Zip requis) ou le dossier `ZEUS_WIDE1` extrait à côté de `INSTALLER.bat`. L'installateur :

1. vérifie l'empreinte MD5 de l'exe de chaque résolution ;
2. propose la liste des résolutions, celle de l'écran étant présélectionnée (`0` = résolution d'origine 1024×768) ;
3. part de l'exe grand écran choisi, y ajoute le correctif d'animations s'il est présent, puis le correctif des accents : les trois correctifs ne modifient aucun octet en commun ;
4. installe les 38 images de la résolution choisie (les originales sont sauvegardées).

`DESINSTALLER.bat` remet tout d'origine. Option `-Resolution 1920x1080` (ou `aucune`) pour choisir sans question.

> **Mise à l'échelle Windows (125 %, 150 %…)** : le jeu utilise la résolution *affichée* par Windows, pas celle de l'écran. Divisez la résolution de l'écran par le facteur d'échelle et choisissez la variante la plus proche en dessous. Exemple testé : écran **1920×1080 à 125 %** (soit 1536×864) → choisir **1280x720**. Le facteur d'échelle se trouve dans *Paramètres › Système › Écran › Échelle*.

> Ces exe portent dans leur en-tête DOS une signature d'un tiers (« MACIOZO ») ; le code ajouté (routine de mise à l'échelle et constantes de résolution) a été vérifié, il ne fait rien d'autre. Leur base est bien l'exe GOG / Steam 2.1.4.0.

Les correctifs facultatifs appliqués sont ceux dont les fichiers sont à côté de `INSTALLER.bat` au moment de l'installation : gardez-les dans le même dossier si vous réinstallez.

### Remarques

- N'utilisez pas *Vérifier / Réparer* (GOG Galaxy) ni *Vérifier l'intégrité des fichiers du jeu* (Steam) : cela remet les fichiers anglais. Il suffit alors de relancer `INSTALLER.bat` (de même après une mise à jour Steam du jeu).
- Les campagnes portent des noms français : une campagne commencée en anglais ne peut pas être continuée après le patch (et inversement).

---

## Fonctionnement

### Fichiers de langue

La version CD française et les versions GOG / Steam ont le même exécutable (v2.1.4.0 ; GOG et Steam sont identiques octet pour octet) et le même format de données : le texte est entièrement externe (`Zeus_Text.eng`, `Zeus_MM.eng`, `Zeus_Editor_Text.eng`, `Model\Zeus eventmsg.txt`, textes des aventures). Le patch copie donc les fichiers français à la place des anglais. Les aventures anglaises, qui n'ont pas le même nom de fichier, sont mises de côté pour ne pas apparaître en double.

L'exe du CD français, protégé par SecuROM, n'est pas utilisé.

### Correctif des accents dans `Zeus.exe`

Les polices françaises sont dessinées pour l'exe français. Avec l'exe GOG / Steam, deux problèmes apparaissent :

1. **Mauvais glyphes** : la table « caractère → glyphe de police » (224 octets, caractères 0x20 à 0xFF) diffère sur 39 valeurs (à, è/ê, ì/î, ò/ô, ù/û, œ, æ…). Elle est remplacée par celle de l'exe français.
2. **Accents décalés vers le haut** : le moteur remonte chaque lettre accentuée de `hauteur du glyphe − hauteur de référence de la police`. L'exe GOG / Steam utilise d'autres hauteurs de référence, et remonte en plus de 2 pixels une liste de lettres polonaises (CP1250) qui correspond à ê, Ê, œ, æ, ó, ñ… en CP1252. Le correctif reprend les valeurs de l'exe français :

| Police (n° FR) | Exe FR | Exe GOG / Steam |
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

## Historique des versions

| Version | Changements |
|---|---|
| 1.6 | Installation facultative du mod grand écran ZEUS_WIDE1 (`Zeus.7z` fourni par l'utilisateur) : choix de la résolution, combinaison avec les correctifs d'animations et des accents. |
| 1.5 | Application facultative du correctif d'animations de Pecunia (ZIP fourni par l'utilisateur), combiné au correctif des accents. |
| 1.4 | Prise en charge de la version Steam (*Zeus + Poseidon*) : détection des versions GOG et Steam, menu de choix, option `-Plateforme GOG\|Steam`. |
| 1.3 | Position verticale des accents corrigée dans `Zeus.exe` (hauteurs de référence de l'exe FR, suppression de la liste de lettres polonaises). |
| 1.2 | Accents conservés : table caractère → glyphe de l'exe FR recopiée dans `Zeus.exe`. |
| 1.1 | Variante sans accents (textes convertis en ASCII). |
| 1.0 | Première version : textes, voix, vidéos et campagnes françaises. |

## Licence

Code source sous licence [MIT](LICENSE). La licence ne couvre pas les fichiers du jeu ni les patchs construits.

## Crédits

- Traduction française : version CD officielle (Sierra / Impressions Games), non incluse.
- Correctif d'animations : Pecunia (*Zeus/Poseidon Animation Fix Patch*, 2018), non inclus.
- Mod grand écran : ZEUS_WIDE1 (auteurs tiers, 2012), non inclus.

## Avertissement

Projet non officiel, sans lien avec Sierra, Impressions Games, Activision, GOG ou Valve (Steam). *Le Maître de l'Olympe : Zeus* et *Poséidon* sont des marques de leurs propriétaires respectifs. Utilisez ce patch uniquement avec des copies du jeu que vous possédez.
