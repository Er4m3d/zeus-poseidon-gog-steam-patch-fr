"""Génère data/patch_exe.txt : les modifications de Zeus.exe (GOG / Steam 2.1.4.0), par groupe.

    python tools/generer_patch_exe.py --gog "<Zeus.exe GOG d'origine>" --cd D:\\

Lignes « GROUPE|offset fichier|nouveaux octets » (hexadécimal). Aucun octet du jeu n'y figure : l'installateur
 vérifie l'empreinte MD5 de Zeus.exe entier avant toute modification, et la table de caractères française est
 lue sur le CD au moment de l'installation (« CAB:fichier:offset:longueur:MD5 » à la place des octets).

Groupes :

  COMMUN      taille virtuelle de .text étendue pour couvrir les routines ajoutées (espace libre en fin de section).
  ACCENTS     table caractère -> glyphe de l'exe français (lue à l'installation dans le Zeus.exe du CD) et position
              verticale des lettres accentuées (hauteurs de référence de l'exe français, liste de lettres
              polonaises désactivée). Voir README, « Accents ».
  DIEUX       apparition des dieux et animations au ralenti : 70 appels à la fonction d'animation (0x5AF8C0 et
              voisines) reçoivent 0 au lieu de 100, ce qui fait avancer l'image à chaque tic au lieu de suivre la
              vitesse propre de l'animation. Emplacements identifiés par le « Zeus/Poseidon Animation Fix Patch »
              de Pecunia (2018) ; ce fichier ne dépend pas de ce patch.
  SON         figements périodiques de l'image (200 à 400 ms toutes les quelques secondes) : le fil principal attend
              le moteur audio Miles. Les sons d'ambiance 3D sont arrêtés un par un (AIL_end_3D_sample, bloquant), même
              ceux déjà terminés : l'arrêt ne se fait plus que pour un son qui joue encore. Le fondu de la musique
              attend 33 ms à chaque palier de volume : l'attente est supprimée. Voir README, « Figements ».
  RESOLUTION  le mode « 1024 x 768 » devient 1280 x 720 : mode d'affichage, taille d'écran mémorisée, vue de la ville
              en cases, mise en page du panneau latéral « 202 px » (celle du 800 x 600), barre du haut prolongée,
              bande de finition au bord droit. Voir README, « Résolution 1280 x 720 ».
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
    def jcc8(self, op, nom): self.o(op, 0); self.fix.append((len(self.code) - 1, nom))
    def call(self, cible): self.o(0xE8); self.i32(cible - (self.ici() + 4))
    def jmp(self, cible): self.o(0xE9); self.i32(cible - (self.ici() + 4))
    def fin(self):
        for pos, nom in self.fix:
            rel = self.etiq[nom] - (self.va + pos + 1)
            assert -128 <= rel <= 127, nom
            self.code[pos] = rel & 0xFF
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


# ------------------------------------------------------------------------------------------- résolution
W, H = 1280, 720
PANNEAU = W - 202            # bord gauche du panneau latéral (mise en page du 800x600 : panneau 186 + bande 16)
PANNEAU_REPLIE = W - 82      # bord du panneau replié
COLS = (PANNEAU - 31) // 58  # colonnes de la vue : la fenêtre de message (58n+31 px) tient dans la vue
COLS_REPLIE = (W - 31) // 58
LIGNES = H // 15 - 1         # même règle que les modes d'origine (480 -> 31, 600 -> 39, 768 -> 50)
LARGEUR, HAUTEUR = 0xF2A6B4, 0xF2A6B0
DESSIN, ECRAN = 0x5ACF50, 0x12AEBE8          # dessin d'une image et son objet « écran »
CAVE_BARRE, CAVE_BANDE = 0x5D7500, 0x5D7540


def routine_barre():
    """Barre du haut (838 px) : dessinée décalée jusqu'au panneau, puis normalement en (0, 0) par-dessus."""
    a = Asm(CAVE_BARRE)
    a.o(0x05).i32(0x4000).o(0x50)                         # add eax,4000h ; push eax
    a.o(0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0)               # y = 0, 0, 0, 0
    a.o(0x68).i32(PANNEAU - 838).o(0x50)                  # x = panneau - 838 ; id
    a.o(0xB9).i32(ECRAN); a.call(DESSIN)
    a.o(0x58)                                             # pop eax
    a.o(0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0, 0x50)  # (id, 0, 0, 0, 0, 0)
    a.o(0xB9).i32(ECRAN); a.call(DESSIN)
    a.o(0x83, 0xC4, 0x08, 0xC3)                           # add esp,8 ; ret (fin d'origine de la fonction)
    return a.fin()


def routine_bande():
    """Bande de finition de 16 px au bord droit : en 800x600 (d'origine) et en 1280x720, à x = largeur - 16."""
    a = Asm(CAVE_BANDE)
    a.o(0xA1).i32(LARGEUR)                                # mov eax,[largeur]
    a.o(0x3D).i32(800); a.jcc8(0x74, 'oui')               # cmp eax,800 ; je
    a.o(0x3D).i32(W); a.jcc8(0x75, 'fin')                 # cmp eax,W ; jne
    a.etiquette('oui')
    a.o(0x83, 0xE8, 0x10)                                 # sub eax,16
    a.o(0x83, 0x3D).i32(0x12C9464).o(0x62)                # cmp dword [12C9464h],62h
    a.o(0x8B, 0x15).i32(0x12BC830)                        # mov edx,[12BC830h]
    a.jcc8(0x7C, 'grp')                                   # jl
    a.o(0x81, 0xC2).i32(0x310)                            # add edx,310h
    a.etiquette('grp')
    a.o(0x8B, 0x52, 0x04)                                 # mov edx,[edx+4]
    a.o(0x81, 0xC2).i32(0x4000)                           # add edx,4000h
    a.o(0x50, 0x52)                                       # sauvegarde x, id
    a.o(0x6A, 0, 0x6A, 0, 0x6A, 0, 0x6A, 0, 0x50, 0x52)   # (id, x, 0, 0, 0, 0)
    a.o(0xB9).i32(ECRAN); a.call(DESSIN)
    a.o(0x5A, 0x58)                                       # id, x
    a.o(0x6A, 0, 0x6A, 0, 0x6A, 0).o(0x68).i32(max(H - 600, 0)).o(0x50, 0x52)   # seconde copie (bande de 600 px)
    a.o(0xB9).i32(ECRAN); a.call(DESSIN)
    a.etiquette('fin')
    a.jmp(0x517BCB)
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
        (0x517B83, saut(0x517B83, CAVE_BANDE, 12), 'bande de finition -> routine'),
        (CAVE_BARRE, routine_barre(), 'routine barre du haut'),
        (CAVE_BANDE, routine_bande(), 'routine bande de finition'),
    ]
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
    # COMMUN : taille virtuelle de .text = taille brute (couvre les routines ajoutées en fin de section)
    pe = struct.unpack_from('<I', gog, 0x3C)[0]
    sec = pe + 24 + struct.unpack_from('<H', gog, pe + 20)[0]
    assert gog[sec:sec + 5] == b'.text'
    vsize, va_text, taille_brute = struct.unpack_from('<III', gog, sec + 8)
    commun = [(sec + 8 + BASE, d32(taille_brute), 'taille virtuelle de .text')]
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
