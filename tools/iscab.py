"""Lecture des archives InstallShield 6 (data1.hdr / dataN.cab) du CD de Poséidon.

Même algorithme que src/InstallShieldCab.cs (installateur) : en-tête commun, table des fichiers,
données compressées en blocs « longueur 16 bits + deflate brut », fichiers à cheval sur deux volumes.
"""
import os
import struct
import zlib

FILE_SPLIT, FILE_OBFUSCATED, FILE_COMPRESSED, FILE_INVALID = 1, 2, 4, 8


class Cab:
    def __init__(self, dossier, base='data'):
        self.dossier, self.base = dossier, base
        self.hdr = open(os.path.join(dossier, base + '1.hdr'), 'rb').read()
        sig, self.version, _, self.desc, _ = struct.unpack_from('<IIIII', self.hdr, 0)
        if sig != 0x28635349:
            raise ValueError('pas une archive InstallShield')
        d = self.desc
        self.table = d + struct.unpack_from('<I', self.hdr, d + 0x0C)[0]
        self.nb_dossiers = struct.unpack_from('<I', self.hdr, d + 0x1C)[0]
        self.nb_fichiers, table2 = struct.unpack_from('<II', self.hdr, d + 0x28)
        noms_dossiers = [self._chaine(self.table + struct.unpack_from('<I', self.hdr, self.table + 4 * i)[0])
                         for i in range(self.nb_dossiers)]
        self.fichiers = []
        for i in range(self.nb_fichiers):
            p = self.table + table2 + i * 0x57
            flags, = struct.unpack_from('<H', self.hdr, p)
            taille, taille_c, offset = struct.unpack_from('<QQQ', self.hdr, p + 2)
            md5 = self.hdr[p + 0x1A:p + 0x2A].hex().upper()
            nom_off, dossier = struct.unpack_from('<IH', self.hdr, p + 0x3A)
            volume, = struct.unpack_from('<H', self.hdr, p + 0x55)
            if flags & FILE_INVALID or not nom_off:
                continue
            nom = self._chaine(self.table + nom_off)
            chemin = (noms_dossiers[dossier] + '\\' + nom).lstrip('\\') if dossier < len(noms_dossiers) else nom
            self.fichiers.append(dict(index=i, flags=flags, taille=taille, taille_c=taille_c, offset=offset,
                                      md5=md5, chemin=chemin, volume=volume))
        self.par_chemin = {f['chemin'].lower(): f for f in self.fichiers}

    def _chaine(self, off):
        return self.hdr[off:self.hdr.index(b'\0', off)].decode('cp1252')

    def _volume(self, n):
        b = open(os.path.join(self.dossier, f'{self.base}{n}.cab'), 'rb').read(20 + 0x40)
        v = struct.unpack_from('<16I', b, 20)
        return dict(dernier=v[3], premier_offset=v[4], dernier_offset=v[7], dernier_taille_c=v[9])

    def lire(self, f):
        if f['flags'] & FILE_OBFUSCATED:
            raise ValueError('fichier obscurci non géré : ' + f['chemin'])
        besoin = f['taille_c'] if f['flags'] & FILE_COMPRESSED else f['taille']
        vol = f['volume']; vh = self._volume(vol)
        if f['flags'] & FILE_SPLIT and f['index'] == vh['dernier'] and vh['dernier_taille_c'] != besoin:
            with open(os.path.join(self.dossier, f'{self.base}{vol}.cab'), 'rb') as h:
                h.seek(vh['dernier_offset']); brut = h.read(vh['dernier_taille_c'])
            vh2 = self._volume(vol + 1)
            with open(os.path.join(self.dossier, f'{self.base}{vol + 1}.cab'), 'rb') as h:
                h.seek(vh2['premier_offset']); brut += h.read(besoin - len(brut))
        else:
            with open(os.path.join(self.dossier, f'{self.base}{vol}.cab'), 'rb') as h:
                h.seek(f['offset']); brut = h.read(besoin)
        if not f['flags'] & FILE_COMPRESSED:
            return brut
        sortie, p = bytearray(), 0
        while p < len(brut):
            n, = struct.unpack_from('<H', brut, p); p += 2
            sortie += zlib.decompressobj(-15).decompress(brut[p:p + n]); p += n
        return bytes(sortie)
