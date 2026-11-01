using System;
using System.Collections.Generic;
using System.IO;

namespace ZeusPatchFR
{
    /// <summary>
    /// Adapte les polices GOG / Steam (DATA\Zeus_fonts.sg3 + .555) à la table de caractères de l'exe français :
    ///  1. polices n° 1, 2, 8 et 16 : GOG y a interverti les glyphes de cinq paires (à/â, è/ê, ì/î, ò/ô, ù/û) ;
    ///     on remet l'ordre français ;
    ///  2. glyphe du ç : décalé vers le bas dans les polices GOG ; on le remonte pour aligner son corps sur celui
    ///     du « c » de la même police (image réencodée à sa place).
    /// Les polices françaises d'origine ne sont pas sur le CD de Poséidon (elles viennent du CD de Zeus).
    /// </summary>
    public static class Polices
    {
        const int Debut = 680 + 200 * 200;   // fiches d'images : 64 octets chacune
        const int Premiere = 201, Glyphes = 134;
        static readonly int[] PolicesInversees = { 1, 2, 8, 16 };
        static readonly int[,] Paires = { { 83, 84 }, { 87, 88 }, { 91, 92 }, { 95, 96 }, { 99, 100 } };

        static int Fiche(int image) { return Debut + 64 * image; }
        static int Image(int police, int glyphe) { return Premiere + police * Glyphes + glyphe - 1; }

        /// <summary>
        /// Le moteur suppose que les données des images se suivent dans le .555, dans l'ordre des fiches :
        /// les positions restent croissantes et contiguës, et la taille des fichiers ne change pas.
        /// </summary>
        public static void Transformer(byte[] sg3, byte[] d555)
        {
            int nbImages = BitConverter.ToInt32(sg3, 16);

            // 1. paires : les données des deux glyphes sont permutées dans leur zone commune, les fiches suivent
            foreach (int p in PolicesInversees)
                for (int k = 0; k < Paires.GetLength(0); k++)
                {
                    int fa = Fiche(Image(p, Paires[k, 0])), fb = Fiche(Image(p, Paires[k, 1]));
                    int oa = BitConverter.ToInt32(sg3, fa), la = BitConverter.ToInt32(sg3, fa + 4);
                    int ob = BitConverter.ToInt32(sg3, fb), lb = BitConverter.ToInt32(sg3, fb + 4);
                    if (ob != oa + la) throw new InvalidDataException("Polices : données de glyphes non contiguës.");
                    var da = new byte[la]; var db = new byte[lb];
                    Buffer.BlockCopy(d555, oa, da, 0, la); Buffer.BlockCopy(d555, ob, db, 0, lb);
                    Buffer.BlockCopy(db, 0, d555, oa, lb); Buffer.BlockCopy(da, 0, d555, oa + lb, la);
                    var ficheA = new byte[64];
                    Buffer.BlockCopy(sg3, fa, ficheA, 0, 64); Buffer.BlockCopy(sg3, fb, sg3, fa, 64); Buffer.BlockCopy(ficheA, 0, sg3, fb, 64);
                    Array.Copy(BitConverter.GetBytes(oa), 0, sg3, fa, 4); Array.Copy(BitConverter.GetBytes(lb), 0, sg3, fa + 4, 4);
                    Array.Copy(BitConverter.GetBytes(oa + lb), 0, sg3, fb, 4); Array.Copy(BitConverter.GetBytes(la), 0, sg3, fb + 4, 4);
                }

            // 2. ç remonté et réencodé à sa place (le codage ligne par ligne garde la même longueur)
            for (int p = 0; Image(p, 101) < nbImages; p++)
            {
                int fc = Fiche(Image(p, 3)), fcc = Fiche(Image(p, 101));
                if (sg3[fcc + 51] == 0) continue;                       // glyphe non compressé : inchangé
                var c = Decoder(sg3, d555, fc);
                var cc = Decoder(sg3, d555, fcc);
                int k = HautVide(cc) - HautVide(c);
                if (k <= 0) continue;
                int w = cc.GetLength(1), h = cc.GetLength(0);
                var nouv = new int[h, w];
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++) nouv[y, x] = y + k < h ? cc[y + k, x] : -1;
                byte[] code = Encoder(nouv);
                int off = BitConverter.ToInt32(sg3, fcc), n = BitConverter.ToInt32(sg3, fcc + 4);
                if (code.Length > n) continue;                          // ne tient pas : glyphe laissé tel quel
                Buffer.BlockCopy(code, 0, d555, off, code.Length);
                for (int i = code.Length; i + 1 < n; i += 2) { d555[off + i] = 255; d555[off + i + 1] = 0; }   // remplissage neutre
                if ((n - code.Length) % 2 == 1) d555[off + n - 1] = 0;
            }
        }

        /// <summary>Pixels d'une image (−1 = transparent, sinon couleur RGB555).</summary>
        static int[,] Decoder(byte[] sg3, byte[] d555, int fiche)
        {
            int off = BitConverter.ToInt32(sg3, fiche), n = BitConverter.ToInt32(sg3, fiche + 4);
            int w = BitConverter.ToUInt16(sg3, fiche + 20), h = BitConverter.ToUInt16(sg3, fiche + 22);
            bool compresse = sg3[fiche + 51] != 0;
            var px = new int[h, w];
            int i = 0, p = off, fin = off + n;
            while (i < w * h)
            {
                if (compresse)
                {
                    if (p >= fin) { px[i / w, i % w] = -1; i++; continue; }
                    int b = d555[p++];
                    if (b == 255) { int t = d555[p++]; for (int j = 0; j < t && i < w * h; j++, i++) px[i / w, i % w] = -1; }
                    else for (int j = 0; j < b && i < w * h; j++, i++) { px[i / w, i % w] = BitConverter.ToUInt16(d555, p); p += 2; }
                }
                else { px[i / w, i % w] = p + 1 < fin ? BitConverter.ToUInt16(d555, p) : -1; p += 2; i++; }
            }
            return px;
        }

        /// <summary>Sprite compressé, ligne par ligne : (255, n) = n pixels transparents ; (n, pixels) = n pixels opaques.</summary>
        static byte[] Encoder(int[,] px)
        {
            int h = px.GetLength(0), w = px.GetLength(1);
            var o = new List<byte>();
            for (int y = 0; y < h; y++)
            {
                int x = 0;
                while (x < w)
                {
                    if (px[y, x] < 0)
                    {
                        int n = 0;
                        while (x < w && px[y, x] < 0 && n < 255) { n++; x++; }
                        o.Add(255); o.Add((byte)n);
                    }
                    else
                    {
                        var run = new List<int>();
                        while (x < w && px[y, x] >= 0 && run.Count < 254) run.Add(px[y, x++]);
                        o.Add((byte)run.Count);
                        foreach (int v in run) { o.Add((byte)(v & 0xFF)); o.Add((byte)(v >> 8)); }
                    }
                }
            }
            return o.ToArray();
        }

        static int HautVide(int[,] px)
        {
            for (int y = 0; y < px.GetLength(0); y++)
                for (int x = 0; x < px.GetLength(1); x++)
                    if (px[y, x] > 0) return y;
            return px.GetLength(0);
        }
    }
}
