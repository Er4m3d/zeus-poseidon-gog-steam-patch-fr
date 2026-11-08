"""Génère l'icône du patch, dans l'esprit des écrans du jeu : l'éclair de Zeus (à gauche) et le trident de Poséidon
(à droite) en or sur un drapeau français, dans un cadre doré en frise grecque.

Usage : python tools/make_icon.py
Produit src/app.ico (16 à 256 px, icône de l'exe), docs/icon-256.png (README) et tools/icon-preview.png.
Dessin original : aucune image du jeu n'est utilisée. En 16 et 32 px, la frise est remplacée par un cadre uni, pour rester lisible.
"""
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
S = 1024  # dessin en haute résolution, puis réduction

CIEL_HAUT, CIEL_BAS = (20, 44, 104), (58, 140, 214)
OR_CLAIR, OR, OR_FONCE = (255, 236, 140), (240, 178, 36), (150, 86, 10)
LAURIER, LAURIER_CLAIR = (186, 150, 40), (246, 214, 96)
CADRE_ROUGE = (176, 66, 58)
BLEU_FR, BLANC_FR, ROUGE_FR = (0, 85, 164), (250, 250, 250), (226, 44, 50)


def masque_forme(marge=28, rayon=200):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((marge, marge, S - marge, S - marge), radius=rayon, fill=255)
    return m


def degrade(haut, bas, masque=None):
    g = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(g)
    for y in range(S):
        t = y / (S - 1)
        d.line([(0, y), (S, y)], fill=tuple(round(haut[i] + (bas[i] - haut[i]) * t) for i in range(3)) + (255,))
    if masque is not None:
        g.putalpha(masque)
    return g


def remplir(icone, masque, couleur_ou_image):
    calque = couleur_ou_image if isinstance(couleur_ou_image, Image.Image) else Image.new("RGBA", (S, S), couleur_ou_image + (255,))
    calque = calque.copy()
    calque.putalpha(ImageChops.multiply(masque, calque.split()[3]))
    return Image.alpha_composite(icone, calque)


def lueur(icone, masque, couleur, rayon, force=255):
    flou = masque.filter(ImageFilter.GaussianBlur(rayon)).point(lambda v: min(255, v * force // 255))
    return remplir(icone, flou, couleur)


def drapeau(forme):
    """Fond en drapeau français (bandes verticales bleu, blanc, rouge), légèrement ondulé comme un tissu."""
    icone = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    fond = Image.new("RGBA", (S, S))
    px = fond.load()
    for y in range(S):
        for x in range(S):
            # ondulation : la frontière des bandes et l'éclairage suivent une sinusoïde
            onde = math.sin((x + y * 0.35) / 120)
            xb = x + 14 * math.sin(y / 150)
            couleur = BLEU_FR if xb < S / 3 else BLANC_FR if xb < 2 * S / 3 else ROUGE_FR
            k = 1 + 0.10 * onde - 0.16 * (y / S)
            px[x, y] = tuple(max(0, min(255, round(c * k))) for c in couleur) + (255,)
    return remplir(icone, forme, fond)

def cadre(icone, forme):
    """Liseré rouge comme les fenêtres du jeu, puis bande dorée en frise grecque."""
    exterieur = forme
    interieur = masque_forme(marge=44, rayon=184)
    icone = remplir(icone, ImageChops.subtract(exterieur, interieur), CADRE_ROUGE)
    bande_ext, bande_int = interieur, masque_forme(marge=104, rayon=128)
    bande = ImageChops.subtract(bande_ext, bande_int)
    icone = remplir(icone, bande, degrade(OR_CLAIR, OR))
    # frise grecque (méandre) en brun sur tout le tour, coins arrondis compris : chaque motif suit la ligne médiane
    # de la bande, tourné selon sa direction, le haut du motif vers l'extérieur
    u, e = 42, 7          # taille du motif, épaisseur du trait
    tuile = Image.new("L", (u + 2 * e, u + 2 * e), 0)
    x, y = e, e
    ImageDraw.Draw(tuile).line([(x, y + u), (x, y), (x + u, y), (x + u, y + u * 0.72), (x + u * 0.3, y + u * 0.72),
                                (x + u * 0.3, y + u * 0.32), (x + u * 0.68, y + u * 0.32)], fill=255, width=e,
                               joint="curve")
    marge, rayon = 74, 156                               # ligne médiane de la bande
    a, b = marge + rayon, S - marge - rayon
    chemin = []                                          # sens horaire, en partant du haut
    for x0, y0, x1, y1, centre, depart in ((a, marge, b, marge, (b, a), -90), (S - marge, a, S - marge, b, (b, b), 0),
                                           (b, S - marge, a, S - marge, (a, b), 90), (marge, b, marge, a, (a, a), 180)):
        chemin += [(x0 + (x1 - x0) * t / 60, y0 + (y1 - y0) * t / 60) for t in range(60)]
        chemin += [(centre[0] + rayon * math.cos(math.radians(depart + k)),
                    centre[1] + rayon * math.sin(math.radians(depart + k))) for k in range(90)]
    longueurs = [0.0]
    for p, q in zip(chemin, chemin[1:] + chemin[:1]):
        longueurs.append(longueurs[-1] + math.dist(p, q))
    total = longueurs[-1]
    n = round(total / (u + 12))
    frise = Image.new("L", (S, S), 0)
    j = 0
    for k in range(n):
        s = (k + 0.5) * total / n
        while longueurs[j + 1] < s:
            j += 1
        p, q = chemin[j], chemin[(j + 1) % len(chemin)]
        t = (s - longueurs[j]) / max(1e-9, longueurs[j + 1] - longueurs[j])
        px, py = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        angle = math.degrees(math.atan2(-(q[1] - p[1]), q[0] - p[0]))
        r = tuile.rotate(angle, resample=Image.BICUBIC, expand=True)
        frise.paste(255, (round(px - r.width / 2), round(py - r.height / 2)), r)
    icone = remplir(icone, ImageChops.multiply(frise, bande), OR_FONCE)
    # filets intérieurs
    filet = ImageChops.subtract(bande_int, masque_forme(marge=112, rayon=120))
    icone = remplir(icone, filet, OR_FONCE)
    return icone


def feuille(longueur, largeur, direction):
    """Feuille pointant dans la direction (dx, dy) de l'écran."""
    f = Image.new("L", (longueur, longueur), 0)
    ImageDraw.Draw(f).ellipse(((longueur - largeur) / 2, 0, (longueur + largeur) / 2, longueur), fill=255)
    alpha = math.degrees(math.atan2(-direction[0], -direction[1]))
    return f.rotate(alpha, resample=Image.BICUBIC, expand=True)


def laurier(icone):
    """Deux branches de laurier le long d'un cercle, de bas en haut, feuilles par paires."""
    m = Image.new("L", (S, S), 0)
    cx, cy, r = 512, 520, 300
    d = ImageDraw.Draw(m)
    for cote in (-1, 1):
        angles = [100 + 12 * k for k in range(11)] if cote < 0 else [80 - 12 * k for k in range(11)]
        pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in angles]
        d.line(pts, fill=255, width=12, joint="curve")
        for k, (a, (x, y)) in enumerate(zip(angles, pts)):
            th = math.radians(a)
            tx, ty = (-math.sin(th), math.cos(th)) if cote < 0 else (math.sin(th), -math.cos(th))
            lg, lr = 104 - 4 * k, 46 - 2 * k
            for ecart in (-38, 38):
                e = math.radians(ecart)
                dx, dy = tx * math.cos(e) - ty * math.sin(e), tx * math.sin(e) + ty * math.cos(e)
                f = feuille(lg, lr, (dx, dy))
                px, py = x + dx * lg * 0.42, y + dy * lg * 0.42
                m.paste(255, (int(px - f.width / 2), int(py - f.height / 2)), f)
        # feuille terminale
        x, y = pts[-1]; th = math.radians(angles[-1])
        tx, ty = (-math.sin(th), math.cos(th)) if cote < 0 else (math.sin(th), -math.cos(th))
        f = feuille(70, 32, (tx, ty)); m.paste(255, (int(x + tx * 30 - f.width / 2), int(y + ty * 30 - f.height / 2)), f)
    icone = lueur(icone, m, (30, 20, 0), 9, 190)
    icone = remplir(icone, m, degrade(LAURIER_CLAIR, LAURIER))
    return icone

def eclair(icone, echelle=1.0, dy=0):
    pts = [(580, 150), (400, 520), (505, 520), (420, 860), (650, 440), (540, 440), (650, 150)]
    pts = [(512 + (x - 512) * echelle, 500 + (y - 500) * echelle + dy) for x, y in pts]
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    icone = lueur(icone, m, (40, 24, 0), 22, 200)
    icone = remplir(icone, m, degrade(OR_CLAIR, OR))
    # biseau : la moitié droite plus sombre
    droite = Image.new("L", (S, S), 0)
    ImageDraw.Draw(droite).polygon([(512 + 30 * echelle, 0), (S, 0), (S, S), (512 - 40 * echelle, S)], fill=80)
    icone = remplir(icone, ImageChops.multiply(m, droite), OR_FONCE)
    contour = Image.new("L", (S, S), 0)
    ImageDraw.Draw(contour).line(pts + [pts[0]], fill=255, width=max(3, round(12 * echelle)), joint="curve")
    return remplir(icone, contour, OR_FONCE)


def ruban(icone):
    """Ruban tricolore noué sous la couronne : deux pans à rayures bleu, blanc, rouge, nœud au centre."""
    def lerp(p, q, t): return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
    pans = [((452, 832), (506, 846), (372, 990), (318, 968)),       # haut gauche, haut droit, bas droit, bas gauche
            ((518, 846), (572, 832), (706, 968), (652, 990))]
    calques = {c: Image.new("L", (S, S), 0) for c in (BLEU_FR, BLANC_FR, ROUGE_FR)}
    tout = Image.new("L", (S, S), 0)
    for a, b, c, dd in pans:
        for k, couleur in enumerate((BLEU_FR, BLANC_FR, ROUGE_FR)):
            poly = [lerp(a, b, k / 3), lerp(a, b, (k + 1) / 3), lerp(dd, c, (k + 1) / 3), lerp(dd, c, k / 3)]
            ImageDraw.Draw(calques[couleur]).polygon(poly, fill=255)
        encoche = [lerp(dd, c, 0.5), lerp(dd, c, 0.5)]
        ImageDraw.Draw(tout).polygon([a, b, c, dd], fill=255)
        # encoche en V au bout du pan
        v = Image.new("L", (S, S), 0)
        mil = lerp(dd, c, 0.5); haut_v = lerp(lerp(a, b, 0.5), mil, 0.86)
        ImageDraw.Draw(v).polygon([dd, mil, c, (c[0], c[1] + 40), (dd[0], dd[1] + 40)], fill=0)
        ImageDraw.Draw(v).polygon([lerp(dd, c, 0.08), haut_v, lerp(dd, c, 0.92), (c[0], c[1] + 60), (dd[0], dd[1] + 60)], fill=255)
        for couleur in calques:
            calques[couleur] = ImageChops.subtract(calques[couleur], v)
        tout = ImageChops.subtract(tout, v)
    noeud = Image.new("L", (S, S), 0)
    ImageDraw.Draw(noeud).rounded_rectangle((468, 806, 556, 870), radius=18, fill=255)
    icone = lueur(icone, ImageChops.lighter(tout, noeud), (8, 18, 48), 10, 180)
    for couleur, masque in calques.items():
        icone = remplir(icone, masque, couleur)
    for k, couleur in enumerate((BLEU_FR, BLANC_FR, ROUGE_FR)):
        bande = Image.new("L", (S, S), 0)
        ImageDraw.Draw(bande).rectangle((468 + k * 88 / 3, 800, 468 + (k + 1) * 88 / 3, 876), fill=255)
        icone = remplir(icone, ImageChops.multiply(noeud, bande), couleur)
    ImageDraw.Draw(icone).rounded_rectangle((468, 806, 556, 870), radius=18, outline=OR_FONCE + (255,), width=6)
    return icone

def objet_dore(icone, masque, contour_pts=None, lignes=()):
    """Remplit un masque en or (dégradé, ombre portée, contour brun)."""
    ombre = masque.transform(masque.size, Image.AFFINE, (1, 0, -10, 0, 1, -16)).filter(ImageFilter.GaussianBlur(8))
    icone = remplir(icone, ombre.point(lambda v: v * 150 // 255), (30, 20, 0))
    icone = remplir(icone, masque, degrade(OR_CLAIR, OR))
    bord = ImageChops.subtract(masque, masque.filter(ImageFilter.MinFilter(15)))
    return remplir(icone, bord, OR_FONCE)


def trident(icone, cx, haut, bas, largeur, angle=0):
    """Trident de Poséidon : hampe, traverse courbe, trois dents à pointes barbelées."""
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    e = largeur * 0.16                                   # épaisseur
    y_trav = haut + (bas - haut) * 0.30
    d.rounded_rectangle((cx - e / 2, y_trav - e, cx + e / 2, bas), radius=e / 2, fill=255)           # hampe
    d.arc((cx - largeur / 2, y_trav - largeur * 0.55, cx + largeur / 2, y_trav + largeur * 0.12),
          start=20, end=160, fill=255, width=round(e))                                            # traverse
    for k, dx in enumerate((-largeur / 2 + e / 2, 0, largeur / 2 - e / 2)):
        x = cx + dx
        y0 = haut + (0 if k == 1 else largeur * 0.12)
        y1 = y_trav - (largeur * 0.05 if k == 1 else largeur * 0.08)
        d.rectangle((x - e / 2, y0 + e * 1.2, x + e / 2, y1), fill=255)                             # dent
        d.polygon([(x - e * 1.25, y0 + e * 2.0), (x, y0 - e * 0.6), (x + e * 1.25, y0 + e * 2.0),
                   (x + e / 2, y0 + e * 1.4), (x - e / 2, y0 + e * 1.4)], fill=255)                 # pointe barbelée
    d.ellipse((cx - e * 0.9, y_trav + e * 0.6, cx + e * 0.9, y_trav + e * 2.2), fill=255)             # bague
    if angle:
        m = m.rotate(angle, resample=Image.BICUBIC, center=(cx, (haut + bas) / 2))
    return objet_dore(icone, m)


def eclair_zeus(icone, cx, cy, h, angle=0):
    """Éclair de Zeus (même dessin que eclair(), placé et orienté librement)."""
    pts = [(580, 150), (400, 520), (505, 520), (420, 860), (650, 440), (540, 440), (650, 150)]
    k = h / 710
    pts = [(cx + (x - 525) * k, cy + (y - 505) * k) for x, y in pts]
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    if angle:
        m = m.rotate(angle, resample=Image.BICUBIC, center=(cx, cy))
    return objet_dore(icone, m)

def rendu_complet():
    forme = masque_forme()
    icone = cadre(drapeau(forme), forme)
    icone = eclair_zeus(icone, 318, 520, 640, angle=-8)       # Zeus à gauche
    return trident(icone, 712, 190, 850, 340, angle=10)      # Poséidon à droite


def rendu_petit():
    """16 et 32 px : drapeau, cadre doré simple (sans frise), éclair et trident agrandis."""
    forme = masque_forme(marge=10, rayon=170)
    icone = drapeau(forme)
    bord = ImageChops.subtract(forme, masque_forme(marge=90, rayon=110))
    icone = remplir(icone, bord, degrade(OR_CLAIR, OR))
    icone = eclair_zeus(icone, 330, 520, 720, angle=-8)
    return trident(icone, 700, 150, 900, 380, angle=10)


def main():
    complet, petit = rendu_complet(), rendu_petit()
    tailles = [256, 128, 64, 48, 32, 24, 16]
    images = [(petit if t <= 32 else complet).resize((t, t), Image.LANCZOS) for t in tailles]
    (ROOT / "docs").mkdir(exist_ok=True)
    images[0].save(ROOT / "src" / "app.ico", sizes=[(t, t) for t in tailles], append_images=images[1:])
    images[0].save(ROOT / "docs" / "icon-256.png")
    complet.resize((512, 512), Image.LANCZOS).save(ROOT / "tools" / "icon-preview.png")
    print("Icônes générées :", ROOT / "src" / "app.ico", ROOT / "docs" / "icon-256.png")


if __name__ == "__main__":
    main()
