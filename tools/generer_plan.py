"""Génère data/plan.txt : la liste des fichiers que l'installateur copie, et d'où il les prend.

    python tools/generer_plan.py --fr "<installation française 2.1>" --gog "<jeu GOG/Steam anglais>" --cd D:\\ --cd-zeus E:\\

1. Les fichiers de langue à installer sont ceux de la version française qui diffèrent de la version GOG
   (textes, messages, voix, vidéos, campagnes, polices, ambiances).
2. Pour chacun, on cherche une source sur le CD de Poséidon : fichier en clair, ou fichier de l'archive
   InstallShield ; à défaut, un fichier identique sous un autre nom dans le jeu GOG lui-même ; à défaut,
   un fichier de l'archive du CD du jeu de base Zeus (polices, 17 ambiances parlées).
3. Les aventures et voix de campagne anglaises sans équivalent français sont listées pour être mises de côté.

Le plan ne contient que des chemins et des empreintes MD5 : aucun fichier du jeu.
"""
import argparse
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iscab import Cab

INCLUS = re.compile(r'^(zeus_text\.eng|zeus_mm\.eng|zeus_editor_text\.eng|model\\.+|data\\.+|audio\\.+|binks\\.+|adventures\\.+)$')
EXCLUS = re.compile(r'(^|\\)vssver\.scc$')
A_RETIRER = re.compile(r'^(adventures\\.+|audio\\voice\\campaign\\.+)$')


def md5(chemin):
    h = hashlib.md5()
    with open(chemin, 'rb') as f:
        for bloc in iter(lambda: f.read(1 << 20), b''):
            h.update(bloc)
    return h.hexdigest().upper()


def index(racine):
    res = {}
    for dossier, _, noms in os.walk(racine):
        for n in noms:
            p = os.path.join(dossier, n)
            rel = os.path.relpath(p, racine)
            res[rel.lower()] = (rel, p)
    return res


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--fr', required=True); a.add_argument('--gog', required=True); a.add_argument('--cd', required=True)
    a.add_argument('--cd-zeus', required=True)
    a.add_argument('--sortie', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'plan.txt'))
    args = a.parse_args()

    fr, gog, cab, zeus = index(args.fr), index(args.gog), Cab(args.cd), Cab(args.cd_zeus)
    cab_md5 = {}
    for f in cab.fichiers:
        cab_md5.setdefault(f['md5'], f)
    gog_md5 = {}
    for k, (rel, p) in gog.items():
        if os.path.getsize(p) > 100_000 and k.startswith('adventures\\'):
            gog_md5.setdefault(md5(p), rel)

    lignes, manquants = [], []
    for k in sorted(fr):
        if not INCLUS.match(k) or EXCLUS.search(k):
            continue
        rel, p = fr[k]
        m, taille = md5(p), os.path.getsize(p)
        if k in gog and os.path.getsize(gog[k][1]) == taille and md5(gog[k][1]) == m:
            continue                                   # identique à la version GOG
        en_clair = os.path.join(args.cd, rel)
        if os.path.isfile(en_clair) and os.path.getsize(en_clair) == taille and md5(en_clair) == m:
            lignes.append(f'CD|{rel}|{rel}|{m}|{taille}')
        elif k in cab.par_chemin and cab.par_chemin[k]['md5'] == m:
            lignes.append(f'CAB|{rel}|{cab.par_chemin[k]["chemin"]}|{m}|{taille}')
        elif m in cab_md5:
            lignes.append(f'CAB|{rel}|{cab_md5[m]["chemin"]}|{m}|{taille}')
        elif k == 'zeus_mm.eng' and k in cab.par_chemin:
            # version 2.0 du CD : seule la mention « Version 2.0 » diffère (corrigée par l'installateur)
            c = cab.par_chemin[k]
            lignes.append(f'CAB|{rel}|{c["chemin"]}|{c["md5"]}|{c["taille"]}')
        elif m in gog_md5:
            lignes.append(f'JEU|{rel}|{gog_md5[m]}|{m}|{taille}')
        elif k in zeus.par_chemin and hashlib.md5(zeus.lire(zeus.par_chemin[k])).hexdigest().upper() == m:
            lignes.append(f'ZEUS|{rel}|{zeus.par_chemin[k]["chemin"]}|{m}|{taille}')
        else:
            manquants.append(rel)

    retirer = [gog[k][0] for k in sorted(gog) if A_RETIRER.match(k) and k not in fr]
    os.makedirs(os.path.dirname(os.path.abspath(args.sortie)), exist_ok=True)
    with open(args.sortie, 'w', encoding='utf-8', newline='\r\n') as s:
        s.write('# Plan d\'installation du patch FR (généré par tools/generer_plan.py)\n')
        s.write('# TYPE|cible dans le jeu|source|md5|taille\n')
        s.write('#   CD   = fichier en clair sur le CD de Poséidon ; CAB = fichier de l\'archive InstallShield du CD de Poséidon ;\n')
        s.write('#   ZEUS = fichier de l\'archive InstallShield du CD du jeu de base Zeus ;\n')
        s.write('#   JEU  = fichier identique déjà présent dans le jeu sous un autre nom ; RETIRER = fichier anglais mis de côté\n')
        for r in manquants:
            s.write(f'# absent des deux CD (le fichier anglais est conservé) : {r}\n')
        for l in lignes:
            s.write(l + '\n')
        for r in retirer:
            s.write(f'RETIRER|{r}\n')
    nb = {t: sum(1 for l in lignes if l.startswith(t + '|')) for t in ('CD', 'CAB', 'JEU', 'ZEUS')}
    print(f'{len(lignes)} fichiers ({nb}), {len(retirer)} à mettre de côté, {len(manquants)} absents des CD -> {args.sortie}')


if __name__ == '__main__':
    main()
