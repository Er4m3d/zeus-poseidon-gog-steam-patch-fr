using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;

namespace ZeusPatchFR
{
    /// <summary>
    /// Images de fond pour le 1280x720, générées à partir de celles du jeu :
    ///  - écrans de menu 1024x768 : image d'origine au centre (décalage +128, −24, celui du moteur pour ces écrans),
    ///    côtés remplis par l'image agrandie, floutée et assombrie ;
    ///  - écrans de chargement 800x600 : même principe, l'image d'origine agrandie à la hauteur de l'écran (960x720) ;
    ///  - cartes du monde 838x738 : image d'origine à gauche (coordonnées des villes inchangées), prolongée vers
    ///    l'est jusqu'au panneau latéral par une texture de mer prise dans la carte elle-même.
    /// </summary>
    public static class Images
    {
        /// <summary>pleineHauteur : l'image d'origine est agrandie à la hauteur de l'écran (écrans de chargement 800x600),
        /// au lieu d'être posée à sa taille.</summary>
        public static byte[] FondMenu(byte[] jpeg, int W, int H, bool pleineHauteur = false)
        {
            using (var src = Charger(jpeg))
            using (var dst = new Bitmap(W, H, PixelFormat.Format24bppRgb))
            using (var g = Graphics.FromImage(dst))
            {
                int lc = pleineHauteur ? src.Width * H / src.Height : src.Width, hc = pleineHauteur ? H : src.Height;
                int dx = (W - lc) / 2, dy = (H - hc) / 2;
                float echelle = Math.Max((float)W / src.Width, (float)H / src.Height);
                using (var petit = new Bitmap(Math.Max(1, W / 16), Math.Max(1, H / 16)))
                {
                    using (var gp = Graphics.FromImage(petit))
                    {
                        gp.InterpolationMode = InterpolationMode.HighQualityBilinear;
                        float cw = src.Width * echelle, ch = src.Height * echelle;
                        gp.DrawImage(src, (W - cw) / 2 / 16, (H - ch) / 2 / 16, cw / 16, ch / 16);
                    }
                    g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    g.PixelOffsetMode = PixelOffsetMode.Half;
                    g.DrawImage(petit, 0, 0, W, H);
                }
                using (var voile = new SolidBrush(Color.FromArgb(70, 0, 0, 0))) g.FillRectangle(voile, 0, 0, W, H);
                g.InterpolationMode = pleineHauteur ? InterpolationMode.HighQualityBicubic : InterpolationMode.NearestNeighbor;
                g.PixelOffsetMode = pleineHauteur ? PixelOffsetMode.Half : PixelOffsetMode.None;
                g.DrawImage(src, new Rectangle(dx, dy, lc, hc));
                g.PixelOffsetMode = PixelOffsetMode.None;
                if (dx > 0)
                {
                    const int L = 32;
                    var rg = new Rectangle(dx, 0, L, H);
                    using (var b = new LinearGradientBrush(rg, Color.FromArgb(90, 0, 0, 0), Color.FromArgb(0, 0, 0, 0), LinearGradientMode.Horizontal))
                        g.FillRectangle(b, rg);
                    var rd = new Rectangle(dx + lc - L, 0, L, H);
                    using (var b = new LinearGradientBrush(rd, Color.FromArgb(0, 0, 0, 0), Color.FromArgb(90, 0, 0, 0), LinearGradientMode.Horizontal))
                        g.FillRectangle(b, rd);
                }
                return Jpeg(dst);
            }
        }

        public static byte[] CarteMonde(byte[] jpeg, int largeur)
        {
            using (var src = Charger(jpeg))
            {
                int w0 = src.Width, H = src.Height;
                int[] s = Pixels(src);
                const int T = 96;
                // carré de mer : uniquement des pixels à dominante bleue, luminosité la plus uniforme
                int bx = 0, by = 0; double meilleure = double.MaxValue;
                for (int y = 0; y + T <= H; y += 24)
                    for (int x = 0; x + T <= w0; x += 24)
                    {
                        double n = 0, som = 0, som2 = 0; bool mer = true;
                        for (int yy = y; yy < y + T && mer; yy += 8)
                            for (int xx = x; xx < x + T; xx += 8)
                            {
                                int c = s[yy * w0 + xx], r = (c >> 16) & 255, gg = (c >> 8) & 255, b = c & 255;
                                if (!(b > r + 30 && b > gg)) { mer = false; break; }
                                double l = r * 0.3 + gg * 0.59 + b * 0.11; som += l; som2 += l * l; n++;
                            }
                        if (!mer) continue;
                        double v = som2 / n - (som / n) * (som / n);
                        if (v < meilleure) { meilleure = v; bx = x; by = y; }
                    }

                var d = new int[largeur * H];
                for (int y = 0; y < H; y++)
                    for (int x = 0; x < largeur; x++)
                    {
                        if (x < w0) { d[y * largeur + x] = s[y * w0 + x]; continue; }
                        d[y * largeur + x] = Tuile(s, w0, bx, by, T, x - w0, y);
                    }
                // fondu de la carte vers la mer sur ses 48 derniers pixels
                const int L = 48;
                for (int i = 0; i < L; i++)
                {
                    int a = 255 * (i + 1) / (L + 1), x = w0 - L + i;
                    for (int y = 0; y < H; y++)
                        d[y * largeur + x] = Melange(s[y * w0 + x], Tuile(s, w0, bx, by, T, x - w0 + 10 * T, y), a);
                }
                using (var dst = new Bitmap(largeur, H, PixelFormat.Format32bppRgb))
                {
                    var bd = dst.LockBits(new Rectangle(0, 0, largeur, H), ImageLockMode.WriteOnly, PixelFormat.Format32bppRgb);
                    for (int y = 0; y < H; y++) Marshal.Copy(d, y * largeur, bd.Scan0 + y * bd.Stride, largeur);
                    dst.UnlockBits(bd);
                    return Jpeg(dst);
                }
            }
        }

        /// <summary>Texture de mer : le carré choisi, répété en miroir alterné (pas de raccord visible).</summary>
        static int Tuile(int[] s, int w0, int bx, int by, int T, int x, int y)
        {
            int tx = ((x % T) + T) % T, ty = y % T;
            if (((x / T) & 1) == 1) tx = T - 1 - tx;
            if (((y / T) & 1) == 1) ty = T - 1 - ty;
            return s[(by + ty) * w0 + bx + tx];
        }

        static int Melange(int c0, int c1, int a)
        {
            int r = (((c0 >> 16) & 255) * (255 - a) + ((c1 >> 16) & 255) * a) / 255;
            int g = (((c0 >> 8) & 255) * (255 - a) + ((c1 >> 8) & 255) * a) / 255;
            int b = ((c0 & 255) * (255 - a) + (c1 & 255) * a) / 255;
            return (r << 16) | (g << 8) | b;
        }

        static Bitmap Charger(byte[] jpeg)
        {
            using (var ms = new MemoryStream(jpeg))
            using (var img = Image.FromStream(ms))
                return new Bitmap(img);
        }

        static int[] Pixels(Bitmap b)
        {
            var px = new int[b.Width * b.Height];
            var bd = b.LockBits(new Rectangle(0, 0, b.Width, b.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppRgb);
            for (int y = 0; y < b.Height; y++) Marshal.Copy(bd.Scan0 + y * bd.Stride, px, y * b.Width, b.Width);
            b.UnlockBits(bd);
            return px;
        }

        static byte[] Jpeg(Bitmap b)
        {
            ImageCodecInfo codec = null;
            foreach (var c in ImageCodecInfo.GetImageEncoders()) if (c.MimeType == "image/jpeg") codec = c;
            using (var p = new EncoderParameters(1))
            using (var ms = new MemoryStream())
            {
                p.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, 92L);
                b.Save(ms, codec, p);
                return ms.ToArray();
            }
        }
    }
}
