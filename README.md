# Patch FR — Le Maître de l'Olympe : Zeus & Poséidon (versions GOG et Steam)

Remet la version GOG (*Zeus and Poseidon*) ou Steam (*Zeus + Poseidon*) de *Zeus: Master of Olympus* (en anglais) **entièrement en français**, à partir des fichiers de la version française d'origine (CD Sierra, v2.1) :

- textes de l'interface, des bâtiments, des dieux et des héros ;
- messages et événements (requêtes, oracles, invasions…) ;
- polices françaises, **avec les accents correctement affichés** ;
- voix françaises des habitants et des campagnes, ambiances sonores ;
- vidéos d'introduction françaises ;
- campagnes et aventures avec leurs titres et textes français.

Le jeu reste celui de GOG / Steam (les deux versions ont le même `Zeus.exe`, sans protection CD, compatible Windows 10/11). Seul l'affichage des lettres accentuées est corrigé dans `Zeus.exe` (voir [Fonctionnement](#fonctionnement)).

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
git clone [https://github.com/Er4m3d/zeus-poseidon-gog-steam-patch-fr.git](https://github.com/Er4m3d/zeus-poseidon-gog-steam-patch-fr.git)
cd zeus-poseidon-gog-steam-patch-fr
powershell -ExecutionPolicy Bypass -File .\build_patch.ps1 -SourceFR "C:\Sierra\Le Maître de l' Olympe  Zeus" -SourceGOG "C:\Program Files\GOG Galaxy\Games\Zeus and Poseidon"
