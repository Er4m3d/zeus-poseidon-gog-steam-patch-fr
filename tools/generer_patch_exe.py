"""Génère data/patch_exe.txt : les modifications de Zeus.exe (GOG / Steam 2.1.4.0), par groupe.

    python tools/generer_patch_exe.py --gog "<Zeus.exe GOG d'origine>" --cd D:\\

Lignes « GROUPE|offset fichier|nouveaux octets » (hexadécimal). Aucun octet du jeu n'y figure : l'installateur
 vérifie l'empreinte MD5 de Zeus.exe entier avant toute modification, et la table de caractères française est
 lue sur le CD au moment de l'installation (« CAB:fichier:offset:longueur:MD5 » à la place des octets).

Groupes :

  COMMUN      tailles virtuelles de .text (routines ajoutées, espace libre en fin de section) et de .data (leurs variables).
  ACCENTS     table caractère -> glyphe de l'exe français (lue à l'installation dans le Zeus.exe du CD) et position
              verticale des lettres accentuées (hauteurs de référence de l'exe français, liste de lettres
              polonaises désactivée), positions de 23 textes et 34 rectangles de boutons repris de l'exe français. Voir README, « Accents ».
  DIEUX       apparition des dieux et animations au ralenti : 70 appels à la fonction d'animation (0x5AF8C0 et
              voisines) reçoivent 0 au lieu de 100, ce qui fait avancer l'image à chaque tic au lieu de suivre la
              vitesse propre de l'animation. Emplacements identifiés par le « Zeus/Poseidon Animation Fix Patch »
              de Pecunia (2018) ; ce fichier ne dépend pas de ce patch.
  SON         figements périodiques de l'image (200 à 400 ms toutes les quelques secondes) : le fil principal attend
              le moteur audio Miles. Les sons d'ambiance 3D sont arrêtés un par un (AIL_end_3D_sample, bloquant), même
              ceux déjà terminés : l'arrêt ne se fait plus que pour un son qui joue encore. Le fondu de la musique
              attend 33 ms à chaque palier de volume : l'attente est supprimée. Voir README, « Figements ».
  ANIMATIONS  animations d'ambiance trop rapides : hippodrome (spectateurs, stands de paris, juge de la ligne d'arrivée),
              employé du poste de commerce, bateaux de pêche au filet. Voir README, « Animations trop rapides ».
  RESOLUTION  le mode « 1024 x 768 » devient 1280 x 720 : mode d'affichage, taille d'écran mémorisée, vue de la ville
              en cases (19 colonnes, la vue passe sous le panneau dont le fond est redessiné), panneau latéral de
              186 px collé au bord droit (mise en page du 1024 x 768), largeur des messages bornée, barre du haut,
              vidéo d'intro agrandie en plein écran (le lecteur garde le mode du jeu). Voir README, « Résolution 1280 x 720 ».
"""
import argparse
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iscab import Cab

BASE = 0x400000
MD5_GOG = '7423A12681188325CAB04F72B7DC64F1'


def d32(v): return struct.pack('<I', v & 0xFFFFFFFF)


class Asm:
    """Mini-assembleur : octets x86 écrits à la main, étiquettes pour les sauts courts."""
    def __init__(self, va): self.va, self.code, self.etiq, self.fix = va, bytearray(), {}, []
    def ici(self): return self.va + len(self.code)
    def o(self, *b): self.code += bytes(b); return self
    def i32(self, v): self.code += d32(v); return self
    def etiquette(self, nom): self.etiq[nom] = self.ici()
    def jcc8(self, op, nom): self.o(op, 0); self.fix.append((len(self.code) - 1, nom, 1))
    def jcc32(self, op, nom): self.o(0x0F, op + 0x10).i32(0); self.fix.append((len(self.code) - 4, nom, 4))
    def call(self, cible): self.o(0xE8); self.i32(cible - (self.ici() + 4))
    def jmp(self, cible): self.o(0xE9); self.i32(cible - (self.ici() + 4))
    def fin(self):
        for pos, nom, n in self.fix:
            rel = self.etiq[nom] - (self.va + pos + n)
            if n == 1:
                assert -128 <= rel <= 127, nom
                self.code[pos] = rel & 0xFF
            else:
                self.code[pos:pos + 4] = struct.pack('<i', rel)
        return bytes(self.code)


def saut(src, dst, taille):
    return b'\xE9' + struct.pack('<i', dst - (src + 5)) + b'\x90' * (taille - 5)


# ---------------------------------------------------------------------------------------------- accents
POLICES = 0x12AFBEC         # pointeur vers le tableau des polices (entrées de 8 octets, id à +4)
NB_POLICES = 0x12BC820
HAUTEUR_REF = 0xF13960      # hauteur de référence utilisée par la fonction de dessin 0x508B50
CAVE_ACC_A, CAVE_ACC_B = 0x5D7400, 0x5D7480


def table_caracteres(exe):
    for o in range(len(exe) - 256):
        if all(exe[o + 0x61 + i] == 1 + i and exe[o + 0x41 + i] == 27 + i for i in range(26)):
            return o + 0x20
    raise SystemExit('table de caractères introuvable')


def routine_accents_a():
    """Police « par défaut » : hauteur de référence choisie police par police comme dans l'exe français."""
    a = Asm(CAVE_ACC_A)
    a.o(0xC7, 0x44, 0x24, 0x10).i32(6)                    # mov dword [esp+10h], 6   (largeur espace)
    a.o(0x8B, 0x0D).i32(POLICES)                          # mov ecx, [POLICES]
    a.o(0x8B, 0x15).i32(NB_POLICES)                       # mov edx, [NB_POLICES]
    a.o(0xB8).i32(12)                                     # mov eax, 12   (polices FR 9 et 11)
    for k in (8, 10):
        a.o(0x83, 0xFA, k); a.jcc8(0x7C, f's{k}')          # cmp edx, k ; jl
        a.o(0x3B, 0x71, 8 * k + 4); a.jcc8(0x74, 'ok')     # cmp esi, [ecx+8k+4] ; je ok
        a.etiquette(f's{k}')
    a.o(0xB8).i32(11)                                     # mov eax, 11   (polices FR 12 à 15)
    for k in (11, 12, 13, 14):
        a.o(0x83, 0xFA, k); a.jcc8(0x7C, 'd16')
        a.o(0x3B, 0x71, 8 * k + 4); a.jcc8(0x74, 'ok')
    a.etiquette('d16')
    a.o(0xB8).i32(16)                                     # mov eax, 16   (autres polices)
    a.etiquette('ok')
    a.o(0xA3).i32(HAUTEUR_REF)                            # mov [HAUTEUR_REF], eax
    a.jmp(0x5088CB)
    return a.fin()


def routine_accents_b():
    """Texte des messages : référence 11 pour la police FR n°14, 16 sinon (exe français)."""
    a = Asm(CAVE_ACC_B)
    a.o(0xBA).i32(11)                                     # mov edx, 11
    a.o(0x83, 0x3D).i32(NB_POLICES).o(13)                 # cmp dword [NB_POLICES], 13
    a.jcc8(0x7C, 'p16')                                   # jl
    a.o(0xA1).i32(POLICES)                                # mov eax, [POLICES]
    a.o(0x8B, 0x40, 8 * 13 + 4)                           # mov eax, [eax+6Ch]
    a.o(0x3B, 0x44, 0x24, 0x14)                           # cmp eax, [esp+14h]  (police dessinée)
    a.jcc8(0x74, 'sub')
    a.etiquette('p16')
    a.o(0xBA).i32(16)                                     # mov edx, 16
    a.etiquette('sub')
    a.o(0x2B, 0xCA)                                       # sub ecx, edx
    a.jcc8(0x79, 'pos')                                   # jns
    a.o(0x33, 0xC9)                                       # xor ecx, ecx
    a.etiquette('pos')
    a.jmp(0x4F5A3A)
    return a.fin()


class DepuisCd:
    """Octets lus à l'installation dans un fichier de l'archive du CD (ils ne figurent pas dans patch_exe.txt)."""
    def __init__(self, chemin, donnees, offset, n):
        self.chemin, self.offset, self.octets = chemin, offset, donnees[offset:offset + n]
    def __len__(self): return len(self.octets)
    def champ(self):
        return f'CAB:{self.chemin}:{self.offset:X}:{len(self.octets)}:{hashlib.md5(self.octets).hexdigest().upper()}'


# Positions de textes de l'exe français : pour des traductions plus longues, l'exe français déplace ou élargit certains
# textes. Relevé par comparaison des appels d'écriture de texte des deux exe (mêmes instructions, seule la valeur
# diffère). (instruction, position et taille de la valeur, valeur GOG, valeur française, texte groupe/chaîne)
TEXTES_FR = [
    (0x4F4266, 3, 4, 220, 230, '12/2 « pour répondre »'),   # lea eax, [edx + ecx + 0xdc]
    (0x52D05C, 2, 4, 218, 318, '13/3 « Clic droit pour continuer »'),   # lea edx, [esi + 0xda]
    (0x5902DF, 2, 4, 145, 130, '13/8 « Nom Grec: »'),   # add edx, 0x91
    (0x590202, 1, 4, 384, 416, '31/0 « Entrez un nom de chef »'),   # push 0x180
    (0x5C1207, 2, 1, 64, 40, '44/5 « Achète »'),   # lea eax, [edx + 0x40]
    (0x5C0F9C, 2, 1, 64, 40, '44/36 « Vend »'),   # add eax, 0x40
    (0x5C1480, 2, 1, 64, 40, '44/72 « Faveur »'),   # lea eax, [ecx + 0x40]
    (0x5C07DA, 2, 1, 80, 8, '44/167 « Routes générales »'),   # lea eax, [edx + 0x50]
    (0x5C07EF, 1, 4, 236, 234, '44/167 « Routes générales »'),   # push 0xec
    (0x5C0DF1, 2, 1, 64, 40, '44/243 « Rec »'),   # lea eax, [edx + 0x40]
    (0x5C0E78, 2, 1, 64, 40, '44/244 « Paie »'),   # lea eax, [edx + 0x40]
    (0x5C0C76, 2, 1, 64, 40, '44/245 « Chef »'),   # lea eax, [edx + 0x40]
    (0x5C0F2C, 2, 1, 64, 40, '44/348 « Numéro cité »'),   # add eax, 0x40
    (0x5C0D1D, 2, 1, 64, 40, '44/349 « Puissance milit »'),   # lea eax, [edx + 0x40]
    (0x5C0CCF, 2, 1, 64, 40, '44/350 « Puissance éco »'),   # lea eax, [edx + 0x40]
    (0x598188, 3, 1, 8, 10, '47/8 « Retour à la cité »'),   # lea edx, [edx + eax + 8]
    (0x59086E, 2, 4, 426, 446, '50/11 « Employés »'),   # add ecx, 0x1aa
    (0x422BBC, 1, 4, 144, 160, '62/4 « Nouv scénario »'),   # push 0x90
    (0x52EC6C, 2, 4, 466, 426, '62/5 « Rejoindre la cité »'),   # lea eax, [edi + 0x1d2]
    (0x522507, 1, 4, 170, 200, '63/3 « Sujet »'),   # add eax, 0xaa
    (0x5181E5, 3, 1, 65, 72, '130/13 « Vente »'),   # lea edx, [edx + ecx + 0x41]
    (0x59B24F, 2, 1, 48, 61, '153/0 « Paramètres de difficulté »'),   # add edx, 0x30
    (0x42480D, 2, 1, 84, 39, '287/6 « Commencer le scénario »'),   # add edx, 0x54
]


# Rectangles de boutons et de zones de l'exe français (fiches de 28 octets en .data : x1, y1, x2, y2 en 16 bits, puis
# deux adresses de fonctions) : l'exe français remet en page certaines fenêtres pour ses textes (liste des chefs, etc.).
# Relevé en alignant les 1215 fiches des deux exe ; deux faux positifs (fiches chevauchant la suivante) écartés.
# (adresse, rectangle GOG, rectangle français)
BOUTONS_FR = [
    (0x005E86E8, (20, 40, 140, 120), (18, 40, 172, 120)),
    (0x005E8704, (170, 40, 290, 120), (184, 40, 340, 120)),
    (0x005E8720, (320, 40, 440, 120), (352, 40, 510, 120)),
    (0x005E873C, (20, 150, 140, 230), (18, 150, 172, 230)),
    (0x005E8758, (170, 150, 290, 230), (184, 150, 340, 230)),
    (0x005E8774, (320, 150, 440, 230), (352, 150, 510, 230)),
    (0x005EE740, (437, 30, 529, 55), (502, 30, 594, 55)),
    (0x005EE75C, (437, 60, 529, 85), (502, 60, 594, 85)),
    (0x005EE778, (437, 90, 529, 115), (502, 90, 594, 115)),
    (0x005EE794, (437, 120, 529, 145), (502, 120, 594, 145)),
    (0x005EE7B0, (437, 150, 529, 175), (502, 150, 594, 175)),
    (0x005EE7CC, (437, 180, 529, 205), (502, 180, 594, 205)),
    (0x005EE7E8, (437, 210, 529, 235), (502, 210, 594, 235)),
    (0x005EE804, (437, 240, 529, 265), (502, 240, 594, 265)),
    (0x005EE820, (437, 270, 529, 295), (502, 270, 594, 295)),
    (0x005EE83C, (437, 300, 529, 325), (502, 300, 594, 325)),
    (0x005FB900, (20, 40, 330, 64), (20, 40, 360, 64)),
    (0x005FB91C, (20, 68, 330, 92), (20, 68, 360, 92)),
    (0x005FB938, (20, 96, 330, 120), (20, 96, 360, 120)),
    (0x00632BEC, (280, 358, 450, 378), (260, 358, 410, 378)),
    (0x00632C08, (113, 55, 311, 80), (133, 55, 311, 80)),
    (0x00632C78, (113, 151, 343, 176), (113, 151, 243, 176)),
    (0x00632D74, (140, 440, 200, 465), (202, 440, 242, 465)),
    (0x00632D90, (401, 57, 588, 82), (401, 57, 561, 82)),
    (0x00632E38, (113, 88, 311, 113), (133, 88, 311, 113)),
    (0x00632E54, (201, 343, 351, 368), (201, 343, 321, 368)),
    (0x00632E70, (220, 440, 380, 465), (252, 440, 312, 465)),
    (0x006431C8, (142, 332, 267, 357), (142, 332, 262, 357)),
    (0x006431E4, (276, 332, 406, 357), (268, 332, 396, 357)),
    (0x00643200, (418, 332, 498, 357), (403, 332, 498, 357)),
    (0x0065BE90, (5, 480, 125, 500), (35, 480, 145, 500)),
    (0x0065BEAC, (153, 480, 273, 500), (158, 480, 298, 500)),
    (0x0065BEC8, (290, 480, 410, 500), (310, 480, 410, 500)),
    (0x0065BEE4, (409, 480, 529, 500), (439, 480, 549, 500)),
]


def accents(gog, exe_fr):
    mods = []
    pos_gog, pos_fr = table_caracteres(gog), table_caracteres(exe_fr)
    mods.append((pos_gog + BASE, DepuisCd('Zeus.exe', exe_fr, pos_fr, 224), 'table caractère -> glyphe (exe français, lue sur le CD)'))
    for va, val in ((0x50884E, 0x1D), (0x508871, 0x1D), (0x50888A, 0x0A), (0x5088B3, 0x0A)):
        mods.append((va, d32(val), 'hauteur de référence d\'une police'))
    mods.append((0x5088B9, saut(0x5088B9, CAVE_ACC_A, 18), 'police par défaut -> routine A'))
    mods.append((0x508BFA, saut(0x508BFA, 0x508C84, 5), 'liste de lettres polonaises ignorée (texte courant)'))
    mods.append((0x4F5A4E, saut(0x4F5A4E, 0x4F5AD4, 5), 'liste de lettres polonaises ignorée (messages)'))
    mods.append((0x4F5A33, saut(0x4F5A33, CAVE_ACC_B, 7), 'référence des messages -> routine B'))
    for va, pos, taille, v_gog, v_fr, quoi in TEXTES_FR:
        o = va + pos - BASE
        assert int.from_bytes(gog[o:o + taille], 'little') == v_gog, hex(va)
        mods.append((va + pos, v_fr.to_bytes(taille, 'little'), f'position de texte : {quoi}'))
    for va, r_gog, r_fr in BOUTONS_FR:
        assert struct.unpack_from('<4h', gog, va - BASE) == r_gog, hex(va)
        mods.append((va, struct.pack('<4h', *r_fr), f'rectangle de bouton {r_gog} -> {r_fr} (exe français)'))
    mods.append((CAVE_ACC_A, routine_accents_a(), 'routine A'))
    mods.append((CAVE_ACC_B, routine_accents_b(), 'routine B'))
    return mods


# ------------------------------------------------------------------------------------------------ dieux
DIEUX = [0x430407, 0x4B395D, 0x4B3992, 0x4B5642, 0x4B5AED, 0x4B5DE5, 0x4B65FF, 0x4B69B7, 0x4B91D6, 0x4B9AB2,
         0x4B9AFB, 0x4B9B7C, 0x4B9DB1, 0x4BA007, 0x4BAC20, 0x4BAC31, 0x4BAC42, 0x4BAC53, 0x4BB1F4, 0x4BB381,
         0x4BB3E5, 0x4BB40B, 0x4BB431, 0x4BB457, 0x4BB47D, 0x4BB4A3, 0x4BB4C9, 0x4BB4EC, 0x4BB50F, 0x4BB532,
         0x4BB593, 0x4BB5AD, 0x4BB5C7, 0x4BB5E4, 0x4BB656, 0x4BD331, 0x4BD349, 0x4BD3B2, 0x4BDC62, 0x4BDC7F,
         0x4BDC9C, 0x4BDCB9, 0x4BDD2F, 0x4BDDD7, 0x4BDE5A, 0x4BDE9F, 0x4BDEE4, 0x4BDF29, 0x4BDF6E, 0x4BDFB3,
         0x4BDFF8, 0x4BE03D, 0x4BE082, 0x4BE0C7, 0x4BFC43, 0x4BFDF8, 0x4BFF47, 0x4C26D1, 0x4C2740, 0x4C28E3,
         0x4C2904, 0x4C2BD8, 0x4C3A78, 0x4C8415, 0x4C84FC, 0x4C9DEC, 0x4C9E80, 0x4CB1D7, 0x4CB1F0, 0x4CB23F]


def dieux(gog):
    mods = []
    for va in DIEUX:
        o = va - BASE
        # « push 100 » (6A 64) ou « and ebx, 100 » (83 E3 64)
        assert gog[o] == 0x64 and (gog[o - 1] == 0x6A or gog[o - 2:o] == b'\x83\xE3'), hex(va)
        mods.append((va, b'\x00', 'vitesse d\'animation 100 -> 0'))
    return mods


# --------------------------------------------------------------------------------------------------- son
AIL_3D_SAMPLE_STATUS, AIL_END_3D_SAMPLE = 0x5D82B8, 0x5D82DC     # imports mss32.dll
CAVE_SON = 0x5D7600


def routine_son():
    """Arrêt d'un son d'ambiance 3D : AIL_end_3D_sample seulement si le son joue encore (état 4 = SMP_PLAYING)."""
    a = Asm(CAVE_SON)
    a.o(0x50, 0x50)                                       # push eax (sauvegarde) ; push eax (argument)
    a.o(0xFF, 0x15).i32(AIL_3D_SAMPLE_STATUS)             # call [AIL_3D_sample_status]
    a.o(0x83, 0xF8, 0x04, 0x58)                           # cmp eax,4 ; pop eax
    a.jcc8(0x75, 'fin')                                   # jne
    a.o(0x50, 0xFF, 0x15).i32(AIL_END_3D_SAMPLE)          # push eax ; call [AIL_end_3D_sample]
    a.etiquette('fin')
    a.jmp(0x5C7DB0)
    return a.fin()


def son(gog):
    assert gog[0x5C86DF - BASE:0x5C86E1 - BASE] == b'\x6A\x21'
    assert gog[0x5C7DA9 - BASE:0x5C7DB0 - BASE] == bytes.fromhex('50FF15DC825D00')
    return [
        (0x5C86E0, b'\x00', 'fondu de la musique : Sleep(33) -> Sleep(0) à chaque palier'),
        (0x5C7DA9, saut(0x5C7DA9, CAVE_SON, 7), 'arrêt des sons d\'ambiance -> routine'),
        (CAVE_SON, routine_son(), 'routine arrêt des sons d\'ambiance'),
    ]


# ------------------------------------------------------------------------------------------- animations
# Quelques animations d'ambiance tournent bien trop vite (jeu d'origine, ou effet de la correction DIEUX pour la pêche).
# Les vitesses retenues ont été réglées à l'œil, en jeu.
#   - Hippodrome : spectateurs, stands de paris et juge de la ligne d'arrivée sont dessinés image = compteur / diviseur,
#     le compteur avançant à chaque tic ; les diviseurs passent de 3 (ou 2) à 60 (ou 40).
#   - Poste de commerce : l'employé du toit (0x44C2F0) avance d'une image à chaque affichage ; il n'avance plus que
#     lorsque la case 3 de la table de rythme du jeu (0x6668EC, case k = 1 toutes les 20·k ms) est levée.
#   - Pêche (bateau au filet, animation 0x66DC) : vitesse 0 avec DIEUX (une image par tic, trop rapide), 100 d'origine
#     (trop lent) ; la routine force la vitesse 0 et retient l'image un tic sur trois en moyenne (5 tics sur 15),
#     un seul compteur par tic de l'horloge du jeu (0xF9C0F4), partagé par tous les bateaux.
TABLE_RYTHME, HORLOGE = 0x6668EC, 0xF9C0F4
CAVE_COMMERCE, CAVE_PECHE = 0x5D7740, 0x5D7780
ETAT_PECHE = 0x160DF00       # 12 octets en fin de la dernière page de .data (taille virtuelle étendue, COMMUN)
PECHE_TICS, PECHE_SUR = 5, 15
DIVISEURS = [   # (instruction, octets d'origine, position et taille de la valeur, nouveau diviseur, description)
    (0x44E56A, '6A03', 1, 1, 60, 'hippodrome, spectateurs 0x840A / 0x840B'),
    (0x44E6D6, '6A03', 1, 1, 60, 'hippodrome, spectateurs 0x8409 / 0x840C'),
    (0x44E77D, 'BD03000000', 1, 4, 60, 'hippodrome, stands de paris (cas général)'),
    (0x44E784, 'BD02000000', 1, 4, 40, 'hippodrome, stands de paris (cas particulier)'),
    (0x44E225, 'C744241803000000', 4, 4, 60, 'hippodrome, juge de la ligne d\'arrivée au repos'),
]


def routine_commerce():
    """Fin de 0x44C2F0 : le compteur de l'employé n'est enregistré que si la case 3 de la table de rythme est levée."""
    a = Asm(CAVE_COMMERCE)
    a.o(0xFE, 0xC3, 0x5F, 0x5E)                           # inc bl ; pop edi ; pop esi (code d'origine)
    a.o(0x80, 0x3D).i32(TABLE_RYTHME + 3).o(0)            # cmp byte [table+3],0
    a.jcc8(0x74, 'fin')                                   # je : pas encore l'heure
    a.o(0x88, 0x99).i32(0xCB4B08)                         # mov [ecx+0CB4B08h],bl
    a.etiquette('fin')
    a.jmp(0x44C498)
    return a.fin()


def routine_peche():
    """Bateau au filet : vitesse 0, image retenue PECHE_SUR - PECHE_TICS tics sur PECHE_SUR."""
    a = Asm(CAVE_PECHE)
    a.o(0xC7, 0x44, 0x24, 0x08).i32(0)                    # vitesse (déjà empilée) = 0
    a.o(0xA1).i32(HORLOGE)                                # mov eax,[horloge]
    a.o(0x3B, 0x05).i32(ETAT_PECHE); a.jcc8(0x74, 'meme') # même tic : même décision
    a.o(0xA3).i32(ETAT_PECHE)
    a.o(0xA1).i32(ETAT_PECHE + 4).o(0x83, 0xC0, PECHE_TICS)    # accumulateur += PECHE_TICS
    a.o(0x83, 0xF8, PECHE_SUR); a.jcc8(0x7C, 'non')
    a.o(0x83, 0xE8, PECHE_SUR).o(0xC6, 0x05).i32(ETAT_PECHE + 8).o(1); a.jcc8(0xEB, 'st')
    a.etiquette('non'); a.o(0xC6, 0x05).i32(ETAT_PECHE + 8).o(0)
    a.etiquette('st'); a.o(0xA3).i32(ETAT_PECHE + 4)
    a.etiquette('meme')
    a.o(0x80, 0x3D).i32(ETAT_PECHE + 8).o(0); a.jcc8(0x75, 'go')   # ce tic avance : rien à compenser
    a.o(0x80, 0x39, 0x00); a.jcc8(0x74, 'go')             # cmp byte [ecx],0 (n° d'image)
    a.o(0xFE, 0x09)                                       # dec byte [ecx] : compense l'avance de 0x5AF8C0
    a.etiquette('go')
    a.o(0x68).i32(0x66DC); a.call(0x5AF8C0)               # code d'origine
    a.jmp(0x4B6612)
    return a.fin()


def animations(gog):
    mods = []
    for va, orig, pos, taille, val, quoi in DIVISEURS:
        assert gog[va - BASE:va - BASE + len(orig) // 2] == bytes.fromhex(orig), hex(va)
        mods.append((va + pos, d32(val)[:taille], f'diviseur {quoi}'))
    assert gog[0x44C48E - BASE:0x44C498 - BASE] == bytes.fromhex('FEC35F5E8899084BCB00')
    assert gog[0x4B6600 - BASE:0x4B6612 - BASE] == bytes.fromhex('8D8989D7DB005651' '68DC660000E8') + \
        struct.pack('<i', 0x5AF8C0 - 0x4B6612)
    mods += [
        (0x44C48E, saut(0x44C48E, CAVE_COMMERCE, 10), 'poste de commerce, compteur de l\'employé -> routine'),
        (CAVE_COMMERCE, routine_commerce(), 'routine poste de commerce'),
        (0x4B6608, saut(0x4B6608, CAVE_PECHE, 10), 'bateau de pêche au filet -> routine'),
        (CAVE_PECHE, routine_peche(), 'routine bateau de pêche'),
    ]
    return mods


# ------------------------------------------------------------------------------------------- résolution
W, H = 1280, 720
PANNEAU = W - 186            # bord gauche du panneau latéral (mise en page du 1024x768 : panneau de 186 px)
PANNEAU_REPLIE = W - 66      # bord du panneau replié (66 px)
COLS = -(-(PANNEAU + 2) // 60)   # colonnes de la vue (60n - 2 px) : des cases jusque sous le panneau (voir plus bas)
COLS_REPLIE = (W - 31) // 58
LIGNES = H // 15 - 1         # même règle que les modes d'origine (480 -> 31, 600 -> 39, 768 -> 50)
LARGEUR, HAUTEUR = 0xF2A6B4, 0xF2A6B0
DESSIN, ECRAN = 0x5ACF50, 0x12AEBE8          # dessin d'une image et son objet « écran »
CAVE_BARRE, CAVE_BARRE_PLEIN = 0x5D7500, 0x5D7A40


def routine_barre(cave=CAVE_BARRE, retour=None):
    """Barre du haut (838 px) : dessinée décalée jusqu'au panneau, puis normalement en (0, 0) par-dessus.

    Deux points d'entrée : la barre de la ville (0x59EC1C, fin de fonction) et celle des écrans plein écran comme la
    carte de choix d'une colonie (0x422D72, retour en 0x422DBF)."""
    a = Asm(cave)
    a.o(0x05).i32(0x4000).o(0x50)                         # add eax,4000h ; push eax
    a.o(0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0)               # y = 0, 0, 0, 0
    a.o(0x68).i32(PANNEAU - 838).o(0x50)                  # x = panneau - 838 ; id
    a.o(0xB9).i32(ECRAN); a.call(DESSIN)
    a.o(0x58)                                             # pop eax
    a.o(0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0, 0x50)  # (id, 0, 0, 0, 0, 0)
    a.o(0xB9).i32(ECRAN); a.call(DESSIN)
    if retour:
        a.jmp(retour)
    else:
        a.o(0x83, 0xC4, 0x08, 0xC3)                       # add esp,8 ; ret (fin d'origine de la fonction)
    return a.fin()


# Vue de la ville en 1280 x 720 : le moteur ne dessine que des cases entières (largeur de vue 60 x colonnes - 2), et
# 18 colonnes s'arrêtent 16 px avant le panneau. La vue a donc 19 colonnes (1138 px) et passe sous le panneau, comme la
# vue du panneau replié dans les modes d'origine. Après le dessin de la vue, à chaque image, une routine redessine la
# partie du fond du panneau recouverte (1094 à 1138 px, découpe 0xF139BC / 0xF139B8), avant les éléments du panneau ;
# la largeur des messages, prise sur celle de la vue, est limitée au bord du panneau.
VUE_OUVERTE = 60 * COLS - 2
CAVE_BORNE_MESSAGES, CAVE_FOND, CAVE_FOND_INFO = 0x5D7540, 0x5D7650, 0x5D7940
# autres appels de la vue (0x51CAB0) : fenêtre ou menu dessiné par-dessus la ville, sans redessiner le panneau
APPELS_VUE = [
    (0x5720E9, 'fenêtre d\'information : bâtiment, terrain'), (0x5730FF, 'fenêtre d\'information : bateau, animal'),
    (0x51412E, 'menu déroulant : Fichier, Options'), (0x5904F0, 'fenêtre de conseiller'), (0x4F2EFF, 'fenêtre de conseiller'),
    (0x4F44C6, 'autre'), (0x514182, 'autre'), (0x5141C1, 'autre'), (0x5146EB, 'autre'), (0x51E6F1, 'autre'),
    (0x51EAF3, 'autre'), (0x5223B4, 'autre'),
]
DECOUPE_G, DECOUPE_D = 0xF139BC, 0xF139B8


def routine_borne_messages():
    """mov ecx,[largeur de la vue] (largeur des messages) ; en 1280 x 720 panneau ouvert, bornée au panneau."""
    a = Asm(CAVE_BORNE_MESSAGES)
    a.o(0x8B, 0x0D).i32(0x7D3B90)                          # mov ecx,[0x7D3B90] (code d'origine)
    a.o(0x81, 0xF9).i32(VUE_OUVERTE); a.jcc8(0x75, 'fin')  # cmp ecx,1138 ; jne
    a.o(0x81, 0x3D).i32(LARGEUR).i32(W); a.jcc8(0x75, 'fin')    # cmp dword [largeur],W ; jne
    a.o(0xB9).i32(PANNEAU)                                 # mov ecx,PANNEAU
    a.etiquette('fin')
    a.jmp(0x4F2FE3)
    return a.fin()


def routine_fond(cave=None, info=False):
    """Après la vue (0x51CAB0) : redessine le fond du panneau entre 1094 et 1138 px, puis les éléments du panneau.

    Choix de l'image repris de 0x517B19 (dessin complet du panneau, d'origine). Deux points d'entrée : l'affichage normal
    (0x514095, à la place de l'appel des éléments du panneau) et l'affichage avec une fenêtre d'information ouverte
    (info=True, appels de APPELS_VUE : fenêtres, menus, à la place de l'appel de la vue : la vue est dessinée, puis le panneau seulement si besoin)."""
    a = Asm(cave or CAVE_FOND)
    if info:
        a.call(0x51CAB0)                                                 # vue de la ville (appel remplacé)
    a.o(0x81, 0x3D).i32(LARGEUR).i32(W); a.jcc32(0x75, 'fin')           # 1280 x 720
    a.o(0x81, 0x3D).i32(0x7D3B90).i32(VUE_OUVERTE); a.jcc32(0x75, 'fin') # vue de 19 colonnes (panneau ouvert)
    a.o(0x83, 0x3D).i32(0x10DFF60).o(0); a.jcc32(0x75, 'fin')           # panneau dessiné
    a.o(0xFF, 0x35).i32(DECOUPE_G).o(0xFF, 0x35).i32(DECOUPE_D)          # sauvegarde de la découpe
    a.o(0xC7, 0x05).i32(DECOUPE_G).i32(PANNEAU)                          # découpe : PANNEAU .. 1138
    a.o(0xC7, 0x05).i32(DECOUPE_D).i32(VUE_OUVERTE)
    a.o(0x6A, 0x01); a.call(0x4200F0); a.o(0x83, 0xC4, 0x04)              # image du fond (code d'origine)
    a.o(0x84, 0xC0); a.jcc8(0x74, 'zeus')
    a.o(0xA1).i32(0x15545F0).o(0x83, 0xF8, 0x45)
    a.o(0xA1).i32(0x15479BC); a.jcc8(0x7C, 'p1')
    a.o(0x05).i32(0x228)
    a.etiquette('p1')
    a.o(0x8B, 0x40, 0x04).o(0x05).i32(0xD0000); a.jcc8(0xEB, 'dessin')
    a.etiquette('zeus')
    a.o(0x83, 0x3D).i32(0x12C9464).o(0x39); a.jcc8(0x7C, 'p2')
    a.o(0x8B, 0x15).i32(0x12BC830).o(0x8D, 0x82).i32(0x1C8); a.jcc8(0xEB, 'p3')
    a.etiquette('p2')
    a.o(0xA1).i32(0x12BC830)
    a.etiquette('p3')
    a.o(0x8B, 0x40, 0x04).o(0x05).i32(0x4000)
    a.etiquette('dessin')
    a.o(0x8B, 0x0D).i32(0x10DFF34)                                       # x du panneau
    a.o(0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0, 0x51, 0x50)                  # (id, x, 0, 0, 0, 0)
    a.o(0xB9).i32(ECRAN); a.call(DESSIN)
    a.o(0x8F, 0x05).i32(DECOUPE_D).o(0x8F, 0x05).i32(DECOUPE_G)          # découpe d'origine
    if info:
        a.call(0x58EA20)                                                 # éléments du panneau, par-dessus
        a.etiquette('fin')
        a.o(0xC3)                                                        # ret
    else:
        a.etiquette('fin')
        a.call(0x58EA20)                                                 # éléments du panneau (appel remplacé)
        a.jmp(0x51409A)
    return a.fin()

# Vidéo d'intro (640 x 480, avec 68 / 69 lignes noires intégrées en haut / en bas) : le lecteur passait l'écran en
# 640 x 480 (mode 1) ; il garde maintenant le mode du jeu, et en 1280 x 720 chaque image est copiée dans un tampon
# puis agrandie : x 2 en largeur, les 343 lignes utiles étirées sur 720 (5 %), sans bandes noires.
CAVE_INTRO, CAVE_MODE_VIDEO = 0x5D7800, 0x5D7920
TAMPON_INTRO = 0x160DF10     # pointeur du tampon (VirtualAlloc), en fin de .data
BINK_COPIE, VIRTUAL_ALLOC = 0x5D8238, 0x5D804C     # imports binkw32.dll / kernel32.dll
PAS_SURFACE, SURFACE = 0x699900, 0x699914          # surface DirectDraw verrouillée : pas et adresse des pixels
INTRO_HAUT, INTRO_UTILE = 68, 343


def routine_intro():
    a = Asm(CAVE_INTRO)
    a.o(0x81, 0x3B).i32(640); a.jcc32(0x75, 'orig')                 # vidéo 640 x 480
    a.o(0x81, 0x7B, 0x04).i32(480); a.jcc32(0x75, 'orig')
    a.o(0x81, 0x3D).i32(LARGEUR).i32(W); a.jcc32(0x75, 'orig')      # écran 1280 x 720
    a.o(0x81, 0x3D).i32(HAUTEUR).i32(H); a.jcc32(0x75, 'orig')
    a.o(0xA1).i32(TAMPON_INTRO).o(0x85, 0xC0); a.jcc8(0x75, 'tampon')
    a.o(0x6A, 0x04).o(0x68).i32(0x3000).o(0x68).i32(640 * 480 * 4).o(0x6A, 0x00)
    a.o(0xFF, 0x15).i32(VIRTUAL_ALLOC).o(0xA3).i32(TAMPON_INTRO)   # VirtualAlloc(0, 640x480x4, MEM_COMMIT|RESERVE, RW)
    a.o(0x85, 0xC0); a.jcc32(0x74, 'orig')
    a.etiquette('tampon')
    a.o(0x8B, 0xC5).o(0x69, 0xC0).i32(640).o(0x89, 0x04, 0x24)      # pas du tampon = 640 x octets par pixel (ebp)
    a.o(0xFF, 0x35).i32(TAMPON_INTRO).o(0x53).o(0xFF, 0x15).i32(BINK_COPIE)   # BinkCopyToBuffer(bink, tampon, ...)
    a.o(0x60).o(0x31, 0xD2)                                         # pushad ; Y = 0
    a.etiquette('ligne')
    a.o(0x8B, 0xC2).o(0x69, 0xC0).i32(INTRO_UTILE).o(0x52, 0x31, 0xD2).o(0xB9).i32(H).o(0xF7, 0xF1).o(0x5A)
    a.o(0x83, 0xC0, INTRO_HAUT).o(0x0F, 0xAF, 0xC5).o(0x69, 0xC0).i32(640)      # ligne source x octets
    a.o(0x8B, 0x35).i32(TAMPON_INTRO).o(0x03, 0xF0)                             # esi = source
    a.o(0x8B, 0xFA).o(0x0F, 0xAF, 0x3D).i32(PAS_SURFACE).o(0x03, 0x3D).i32(SURFACE)   # edi = destination
    a.o(0xB9).i32(640).o(0x83, 0xFD, 0x04); a.jcc8(0x74, 'p4')
    a.etiquette('p2')                                               # 16 bits : chaque pixel doublé
    a.o(0x66, 0x8B, 0x06, 0x66, 0x89, 0x07, 0x66, 0x89, 0x47, 0x02, 0x83, 0xC6, 0x02, 0x83, 0xC7, 0x04, 0x49)
    a.jcc8(0x75, 'p2'); a.jcc8(0xEB, 'suite')
    a.etiquette('p4')                                               # 32 bits
    a.o(0x8B, 0x06, 0x89, 0x07, 0x89, 0x47, 0x04, 0x83, 0xC6, 0x04, 0x83, 0xC7, 0x08, 0x49); a.jcc8(0x75, 'p4')
    a.etiquette('suite')
    a.o(0x42, 0x81, 0xFA).i32(H); a.jcc8(0x7C, 'ligne')
    a.o(0x61); a.jmp(0x417ADC)                                      # popad
    a.etiquette('orig')
    a.o(0x56, 0x53).o(0xFF, 0x15).i32(BINK_COPIE); a.jmp(0x417ADC)  # copie d'origine
    return a.fin()


def routine_mode_video():
    """Lecteur vidéo : changement vers le mode du jeu ([0xF2A770]) au lieu du mode 1 (640 x 480)."""
    a = Asm(CAVE_MODE_VIDEO)
    a.o(0xFF, 0x35).i32(0xF2A770); a.call(0x50BD20); a.jmp(0x418768)
    return a.fin()


def resolution():
    m = [
        (0x5051FA, d32(W), 'modes d\'affichage acceptés : largeur'), (0x505212, d32(H), '... hauteur'),
        (0x50BA29, d32(W), 'changement de mode : largeur'), (0x50BA2E, d32(H), '... hauteur'),
        (0x50BD03, d32(W), 'taille d\'écran mémorisée : largeur'), (0x50BD0D, d32(H), '... hauteur'),
        (0x51CBC8, d32(W), 'vue de la ville (panneau replié) : test de largeur'),
        (0x51CBD3, bytes([LIGNES]), '... lignes'), (0x51CBD5, bytes([COLS_REPLIE]), '... colonnes'),
        (0x51CC1E, d32(W), 'vue de la ville (panneau ouvert) : test de largeur'),
        (0x51CC29, bytes([LIGNES]), '... lignes'), (0x51CC2B, bytes([COLS]), '... colonnes'),
        (0x58E2BE, d32(W), 'position du panneau : test de largeur'),
        (0x58E2CA, d32(PANNEAU), '... panneau ouvert'), (0x58E2D4, d32(PANNEAU_REPLIE), '... panneau replié'),
        (0x58E2F7, d32(W), 'bordure du bas : test de largeur'), (0x58E30A, d32(W), '... largeur'),
        (0x58E3FD, d32(W), 'bordure du bas (2) : test de largeur'), (0x58E41C, d32(W), '...'), (0x58E42F, d32(W), '... largeur'),
        (0x58EF7C, d32(W), 'panneaux d\'information : test de largeur'),
        (0x59EBFB, d32(W), 'barre du haut : test de largeur'),
        (0x422D55, d32(W), 'cadre plein écran : test de largeur'),
        (0x5C459E, d32(W), 'démarrage : écran assez large pour ce mode'),
        # liste des noms grecs (création d'un profil) : le cadre a une position fixe par mode (640 : 110,30 ;
        # 800 : 190,90 ; 1024 : 302,174), soit la position 1024 + le décalage de centrage du mode ; le texte, lui,
        # suit le décalage. Pour la nouvelle résolution : 302 + (W-1024)/2, 174 + (H-768)/2 (dessin et clics).
        (0x59038C, d32(302 + (W - 1024) // 2), 'liste des noms grecs, dessin : x du cadre'),
        (0x590391, d32(174 + (H - 768) // 2), '... y du cadre'),
        (0x514634, d32(302 + (W - 1024) // 2), 'liste des noms grecs, clics : x du cadre'),
        (0x514639, d32(174 + (H - 768) // 2), '... y du cadre'),
        (0x59EC1C, saut(0x59EC1C, CAVE_BARRE, 6), 'barre du haut -> routine'),
        (CAVE_BARRE, routine_barre(), 'routine barre du haut'),
        (0x422D72, saut(0x422D72, CAVE_BARRE_PLEIN, 17), 'barre du haut des écrans plein écran -> routine'),
        (CAVE_BARRE_PLEIN, routine_barre(CAVE_BARRE_PLEIN, 0x422DBF), 'routine barre du haut (écrans plein écran)'),
    ]
    m += [
        (0x417AD4, saut(0x417AD4, CAVE_INTRO, 8), 'vidéo : copie de l\'image -> routine d\'agrandissement'),
        (CAVE_INTRO, routine_intro(), 'routine agrandissement de l\'intro'),
        (0x418761, saut(0x418761, CAVE_MODE_VIDEO, 7), 'vidéo : mode du jeu au lieu de 640 x 480 -> routine'),
        (CAVE_MODE_VIDEO, routine_mode_video(), 'routine mode d\'affichage des vidéos'),
        (0x4F2FDD, saut(0x4F2FDD, CAVE_BORNE_MESSAGES, 6), 'largeur des messages -> routine'),
        (CAVE_BORNE_MESSAGES, routine_borne_messages(), 'routine largeur des messages bornée au panneau'),
        (0x514095, saut(0x514095, CAVE_FOND, 5), 'après la vue de la ville -> routine fond du panneau'),
        (CAVE_FOND, routine_fond(), 'routine fond du panneau sous la vue'),
        (CAVE_FOND_INFO, routine_fond(CAVE_FOND_INFO, info=True), 'routine fond du panneau sous la vue (fenêtres, menus)'),
    ]
    for va, quoi in APPELS_VUE:
        m.append((va, b'\xE8' + struct.pack('<i', CAVE_FOND_INFO - (va + 5)), f'vue de la ville ({quoi}) -> routine'))
    return m


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--gog', required=True); p.add_argument('--cd', required=True)
    p.add_argument('--sortie', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'patch_exe.txt'))
    args = p.parse_args()
    gog = open(args.gog, 'rb').read()
    if hashlib.md5(gog).hexdigest().upper() != MD5_GOG:
        raise SystemExit('Zeus.exe GOG / Steam 2.1.4.0 d\'origine attendu')
    cab = Cab(args.cd)
    exe_fr = cab.lire(cab.par_chemin['zeus.exe'])

    groupes = {
        'ACCENTS': accents(gog, exe_fr),
        'DIEUX': dieux(gog),
        'SON': son(gog),
        'RESOLUTION': resolution(),
    }
    pe = struct.unpack_from('<I', gog, 0x3C)[0]
    sections = pe + 24 + struct.unpack_from('<H', gog, pe + 20)[0]
    sec_data = next(sections + 40 * i for i in range(struct.unpack_from('<H', gog, pe + 6)[0])
                    if gog[sections + 40 * i:sections + 40 * i + 5] == b'.data')
    groupes['ANIMATIONS'] = animations(gog)
    # COMMUN : taille virtuelle de .text = taille brute (couvre les routines ajoutées en fin de section)
    pe = struct.unpack_from('<I', gog, 0x3C)[0]
    sec = pe + 24 + struct.unpack_from('<H', gog, pe + 20)[0]
    assert gog[sec:sec + 5] == b'.text'
    vsize, va_text, taille_brute = struct.unpack_from('<III', gog, sec + 8)
    commun = [(sec + 8 + BASE, d32(taille_brute), 'taille virtuelle de .text')]
    # .data : taille virtuelle étendue à la fin de sa dernière page (état des routines : pêche, tampon de l'intro)
    vsize_d, va_data = struct.unpack_from('<II', gog, sec_data + 8)
    fin_page = (vsize_d + 0xFFF) & ~0xFFF
    assert va_data + BASE + vsize_d <= ETAT_PECHE and TAMPON_INTRO + 4 <= va_data + BASE + fin_page
    commun.append((sec_data + 8 + BASE, d32(fin_page), 'taille virtuelle de .data (variables des routines ajoutées)'))
    groupes = {'COMMUN': commun, **groupes}

    utilises = []
    with open(args.sortie, 'w', encoding='utf-8', newline='\r\n') as s:
        s.write('# Modifications de Zeus.exe GOG / Steam 2.1.4.0 (générées par tools/generer_patch_exe.py)\n')
        s.write('# GROUPE|offset fichier|nouveaux octets (hexadécimal) ou CAB:fichier du CD:offset:longueur:MD5\n')
        for g, mods in groupes.items():
            for va, nouv, quoi in mods:
                off = va - BASE
                orig = gog[off:off + len(nouv)]
                if quoi.startswith('routine'):
                    assert orig == b'\0' * len(orig), f'espace libre attendu en 0x{va:X}'
                    assert off >= va_text + vsize and off + len(nouv) <= va_text + taille_brute
                for a, b in utilises:
                    assert off + len(nouv) <= a or off >= b, f'chevauchement en 0x{va:X}'
                utilises.append((off, off + len(nouv)))
                champ = nouv.champ() if isinstance(nouv, DepuisCd) else nouv.hex().upper()
                s.write(f'# {quoi}\n{g}|{off:X}|{champ}\n')
    print({g: len(m) for g, m in groupes.items()}, '->', args.sortie)


if __name__ == '__main__':
    main()
