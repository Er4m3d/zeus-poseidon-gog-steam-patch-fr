"""Génère le correctif « position verticale des accents » pour Zeus.exe (GOG v2.1.4.0).

L'exe GOG positionne les lettres accentuées avec des hauteurs de référence différentes de
l'exe français d'origine, et remonte de 2 pixels une liste de lettres polonaises (CP1250)
qui tombe sur ê, Ê, œ, æ, ó... en CP1252. Ce script produit les modifications qui
reproduisent le comportement de l'exe français :

  A) fonction 0x508B50 (texte courant) : hauteurs de référence par police de l'exe FR ;
  B) fonction 0x4F59B0 (texte des messages) : référence 16, ou 11 pour la police FR n°14 ;
  C) les deux fonctions : suppression de la liste de lettres polonaises.

Sortie : une ligne « OFFSET ORIGINAL NOUVEAU » (hex) par modification, sur stdout.
Usage : python asm_accents.py <Zeus.exe GOG d'origine>
"""
import struct, sys

BASE = 0x400000          # .text : offset fichier = VA - BASE
FONTS = 0x12AFBEC        # pointeur vers le tableau des polices (entrées de 8 octets, id à +4)
NFONTS = 0x12BC820       # nombre de polices chargées
LINE_H = 0xF13960        # hauteur de référence utilisée par la fonction A
CAVE_A = 0x5D7400
CAVE_B = 0x5D7480
TEXT_VSIZE_FIELD = None  # calculé depuis l'en-tête PE


class Asm:
    def __init__(self, va):
        self.va, self.code, self.labels, self.fix = va, bytearray(), {}, []

    def here(self):
        return self.va + len(self.code)

    def emit(self, *bs):
        self.code += bytes(bs)

    def imm32(self, v):
        self.code += struct.pack('<I', v & 0xFFFFFFFF)

    def label(self, name):
        self.labels[name] = self.here()

    def jcc8(self, op, name):          # saut court conditionnel vers une étiquette
        self.emit(op, 0)
        self.fix.append((len(self.code) - 1, name))

    def jmp32(self, target):
        self.emit(0xE9)
        self.imm32(target - (self.here() + 4))

    def done(self):
        for pos, name in self.fix:
            rel = self.labels[name] - (self.va + pos + 1)
            assert -128 <= rel <= 127, name
            self.code[pos] = rel & 0xFF
        return bytes(self.code)


def cave_a():
    """Remplace « police par défaut : largeur espace 6, référence 11 » par le choix FR par police."""
    a = Asm(CAVE_A)
    a.emit(0xC7, 0x44, 0x24, 0x10); a.imm32(6)          # mov dword [esp+10h], 6
    a.emit(0x8B, 0x0D); a.imm32(FONTS)                  # mov ecx, [FONTS]
    a.emit(0x8B, 0x15); a.imm32(NFONTS)                 # mov edx, [NFONTS]
    a.emit(0xB8); a.imm32(12)                           # mov eax, 12   (polices FR 9 et 11)
    for k in (8, 10):
        a.emit(0x83, 0xFA, k); a.jcc8(0x7C, f's{k}')    # cmp edx, k ; jl
        a.emit(0x3B, 0x71, 8 * k + 4); a.jcc8(0x74, 'done')  # cmp esi, [ecx+8k+4] ; je done
        a.label(f's{k}')
    a.emit(0xB8); a.imm32(11)                           # mov eax, 11   (polices FR 12 à 15)
    for k in (11, 12, 13, 14):
        a.emit(0x83, 0xFA, k); a.jcc8(0x7C, 'd16')
        a.emit(0x3B, 0x71, 8 * k + 4); a.jcc8(0x74, 'done')
    a.label('d16')
    a.emit(0xB8); a.imm32(16)                           # mov eax, 16   (autres polices)
    a.label('done')
    a.emit(0xA3); a.imm32(LINE_H)                       # mov [LINE_H], eax
    a.jmp32(0x5088CB)
    return a.done()


def cave_b():
    """ecx = hauteur du glyphe ; décalage = max(0, ecx - réf), réf = 11 pour la police FR 14, sinon 16."""
    a = Asm(CAVE_B)
    a.emit(0xBA); a.imm32(11)                           # mov edx, 11
    a.emit(0x83, 0x3D); a.imm32(NFONTS); a.emit(13)     # cmp dword [NFONTS], 13
    a.jcc8(0x7C, 'p16')                                 # jl
    a.emit(0xA1); a.imm32(FONTS)                        # mov eax, [FONTS]
    a.emit(0x8B, 0x40, 8 * 13 + 4)                      # mov eax, [eax+6Ch]
    a.emit(0x3B, 0x44, 0x24, 0x14)                      # cmp eax, [esp+14h]  (police dessinée)
    a.jcc8(0x74, 'sub')
    a.label('p16')
    a.emit(0xBA); a.imm32(16)                           # mov edx, 16
    a.label('sub')
    a.emit(0x2B, 0xCA)                                  # sub ecx, edx
    a.jcc8(0x79, 'ok')                                  # jns ok
    a.emit(0x33, 0xC9)                                  # xor ecx, ecx
    a.label('ok')
    a.jmp32(0x4F5A3A)
    return a.done()


def jmp_bytes(src, dst, total):
    rel = dst - (src + 5)
    return b'\xE9' + struct.pack('<i', rel) + b'\x90' * (total - 5)


def main():
    exe = open(sys.argv[1], 'rb').read()
    pe = struct.unpack_from('<I', exe, 0x3C)[0]
    opt = struct.unpack_from('<H', exe, pe + 20)[0]
    sec = pe + 24 + opt                                  # 1re section = .text
    assert exe[sec:sec + 5] == b'.text'
    vsize_off = sec + 8
    vsize, va, rawsize = struct.unpack_from('<III', exe, sec + 8)

    patches = []

    def patch(va_or_off, new, is_file_offset=False):
        off = va_or_off if is_file_offset else va_or_off - BASE
        patches.append((off, exe[off:off + len(new)], bytes(new)))

    # A : hauteurs de référence des polices spéciales (imm32 des « mov [LINE_H], x »)
    for va_imm, val in ((0x50884E, 0x1D), (0x508871, 0x1D), (0x50888A, 0x0A), (0x5088B3, 0x0A)):
        patch(va_imm, struct.pack('<I', val))
    # A : police par défaut -> routine A
    patch(0x5088B9, jmp_bytes(0x5088B9, CAVE_A, 18))
    # A et B : sauter la liste de lettres polonaises
    patch(0x508BFA, jmp_bytes(0x508BFA, 0x508C84, 5))
    patch(0x4F5A4E, jmp_bytes(0x4F5A4E, 0x4F5AD4, 5))
    # B : référence -> routine B
    patch(0x4F5A33, jmp_bytes(0x4F5A33, CAVE_B, 7))
    # Routines dans l'espace libre en fin de .text, et taille virtuelle de .text étendue
    patch(CAVE_A, cave_a())
    patch(CAVE_B, cave_b())
    patch(vsize_off, struct.pack('<I', rawsize), is_file_offset=True)

    # Vérifications : octets d'origine attendus, zone libre vide, routines dans la section
    expect = {
        0x50884E - BASE: '17000000', 0x508871 - BASE: '18000000', 0x50888A - BASE: '09000000',
        0x5088B3 - BASE: '07000000', 0x5088B9 - BASE: 'c744241006000000c7056039f1000b000000',
        0x508BFA - BASE: '8b44241083', 0x4F5A4E - BASE: '8d43203db9', 0x4F5A33 - BASE: '83e90b790233c9',
    }
    for off, orig, new in patches:
        if off in expect:
            assert orig.hex() == expect[off], f'octets inattendus à 0x{off:X}: {orig.hex()}'
        elif off in (CAVE_A - BASE, CAVE_B - BASE):
            assert orig == b'\0' * len(orig), f'zone libre non vide à 0x{off:X}'
            assert off + len(new) <= va + rawsize and off >= va + vsize
    assert CAVE_A + len(cave_a()) <= CAVE_B

    for off, orig, new in patches:
        print(f'{off:X} {orig.hex().upper()} {new.hex().upper()}')


if __name__ == '__main__':
    main()
