using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Text;

namespace ZeusPatchFR
{
    /// <summary>
    /// Lecture des archives InstallShield 6 (data1.hdr + data1.cab, data2.cab...) du CD de Poséidon.
    /// Données compressées en blocs « longueur 16 bits + deflate brut » ; un fichier peut être à cheval sur deux volumes.
    /// </summary>
    public class InstallShieldCab
    {
        const int SPLIT = 1, OBSCURCI = 2, COMPRESSE = 4, INVALIDE = 8;

        public class Fichier
        {
            public int Index, Drapeaux, Volume;
            public long Taille, TailleCompressee, Offset;
            public string Chemin, Md5;
        }

        readonly string dossier;
        readonly Dictionary<string, Fichier> parChemin = new Dictionary<string, Fichier>(StringComparer.OrdinalIgnoreCase);
        static readonly Encoding Cp1252 = Encoding.GetEncoding(1252);

        public InstallShieldCab(string dossierCd)
        {
            dossier = dossierCd;
            byte[] h = File.ReadAllBytes(Path.Combine(dossier, "data1.hdr"));
            if (BitConverter.ToUInt32(h, 0) != 0x28635349) throw new InvalidDataException("data1.hdr n'est pas une archive InstallShield.");
            int desc = BitConverter.ToInt32(h, 12);
            int table = desc + BitConverter.ToInt32(h, desc + 0x0C);
            int nbDossiers = BitConverter.ToInt32(h, desc + 0x1C);
            int nbFichiers = BitConverter.ToInt32(h, desc + 0x28);
            int table2 = BitConverter.ToInt32(h, desc + 0x2C);
            var dossiers = new string[nbDossiers];
            for (int i = 0; i < nbDossiers; i++) dossiers[i] = Chaine(h, table + BitConverter.ToInt32(h, table + 4 * i));
            for (int i = 0; i < nbFichiers; i++)
            {
                int p = table + table2 + i * 0x57;
                int drapeaux = BitConverter.ToUInt16(h, p);
                int nomOff = BitConverter.ToInt32(h, p + 0x3A);
                if ((drapeaux & INVALIDE) != 0 || nomOff == 0) continue;
                int dossierIdx = BitConverter.ToUInt16(h, p + 0x3E);
                string nom = Chaine(h, table + nomOff);
                string chemin = dossierIdx < nbDossiers ? (dossiers[dossierIdx] + "\\" + nom).TrimStart('\\') : nom;
                var md5 = new StringBuilder();
                for (int k = 0; k < 16; k++) md5.Append(h[p + 0x1A + k].ToString("X2"));
                parChemin[chemin] = new Fichier
                {
                    Index = i, Drapeaux = drapeaux, Chemin = chemin, Md5 = md5.ToString(),
                    Taille = BitConverter.ToInt64(h, p + 2), TailleCompressee = BitConverter.ToInt64(h, p + 10),
                    Offset = BitConverter.ToInt64(h, p + 18), Volume = BitConverter.ToUInt16(h, p + 0x55)
                };
            }
        }

        static string Chaine(byte[] b, int off)
        {
            int fin = off;
            while (b[fin] != 0) fin++;
            return Cp1252.GetString(b, off, fin - off);
        }

        public Fichier Trouver(string chemin)
        {
            Fichier f;
            return parChemin.TryGetValue(chemin, out f) ? f : null;
        }

        struct EnTeteVolume { public int Dernier; public long PremierOffset, DernierOffset, DernierTailleC; }

        EnTeteVolume Volume(int n)
        {
            var b = new byte[20 + 0x40];
            using (var s = File.OpenRead(Path.Combine(dossier, "data" + n + ".cab"))) s.Read(b, 0, b.Length);
            return new EnTeteVolume
            {
                Dernier = BitConverter.ToInt32(b, 20 + 12), PremierOffset = BitConverter.ToUInt32(b, 20 + 16),
                DernierOffset = BitConverter.ToUInt32(b, 20 + 28), DernierTailleC = BitConverter.ToUInt32(b, 20 + 36)
            };
        }

        static byte[] Lire(string fichier, long offset, long n)
        {
            var b = new byte[n];
            using (var s = File.OpenRead(fichier))
            {
                s.Seek(offset, SeekOrigin.Begin);
                int lu = 0;
                while (lu < n) { int k = s.Read(b, lu, (int)(n - lu)); if (k <= 0) throw new EndOfStreamException(); lu += k; }
            }
            return b;
        }

        public byte[] Extraire(Fichier f)
        {
            if ((f.Drapeaux & OBSCURCI) != 0) throw new NotSupportedException("Fichier obscurci : " + f.Chemin);
            long besoin = (f.Drapeaux & COMPRESSE) != 0 ? f.TailleCompressee : f.Taille;
            var vh = Volume(f.Volume);
            byte[] brut;
            if ((f.Drapeaux & SPLIT) != 0 && f.Index == vh.Dernier && vh.DernierTailleC != besoin)
            {
                // début à la fin de ce volume, suite au début du volume suivant
                byte[] a = Lire(Path.Combine(dossier, "data" + f.Volume + ".cab"), vh.DernierOffset, vh.DernierTailleC);
                var vh2 = Volume(f.Volume + 1);
                byte[] b = Lire(Path.Combine(dossier, "data" + (f.Volume + 1) + ".cab"), vh2.PremierOffset, besoin - a.Length);
                brut = new byte[besoin];
                Buffer.BlockCopy(a, 0, brut, 0, a.Length);
                Buffer.BlockCopy(b, 0, brut, a.Length, b.Length);
            }
            else brut = Lire(Path.Combine(dossier, "data" + f.Volume + ".cab"), f.Offset, besoin);
            if ((f.Drapeaux & COMPRESSE) == 0) return brut;

            using (var sortie = new MemoryStream((int)f.Taille))
            {
                int p = 0;
                while (p < brut.Length)
                {
                    int n = BitConverter.ToUInt16(brut, p); p += 2;
                    using (var bloc = new DeflateStream(new MemoryStream(brut, p, n), CompressionMode.Decompress))
                        bloc.CopyTo(sortie);
                    p += n;
                }
                return sortie.ToArray();
            }
        }
    }
}
