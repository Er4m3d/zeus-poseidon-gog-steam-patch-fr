using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;

namespace ZeusPatchFR
{
    /// <summary>Une ligne du plan d'installation (data/plan.txt, intégré à l'exe).</summary>
    public class ElementPlan
    {
        public string Type;      // CD, CAB, JEU, RETIRER
        public string Cible;     // chemin dans le dossier du jeu
        public string Source;    // chemin sur le CD, dans l'archive, ou dans le jeu
        public string Md5;
        public long Taille;
    }

    /// <summary>Une modification de Zeus.exe (data/patch_exe.txt, intégré à l'exe).</summary>
    public class ModificationExe
    {
        public string Groupe;
        public int Offset;
        public byte[] Nouveau;           // octets à écrire, ou null s'ils sont lus sur le CD :
        public string CabFichier, CabMd5;  // fichier de l'archive du CD et empreinte des octets attendus
        public int CabOffset, CabTaille;
    }

    public static class Donnees
    {
        public const string Md5ZeusExeOrigine = "7423A12681188325CAB04F72B7DC64F1";   // Zeus.exe GOG / Steam 2.1.4.0
        public const string Md5PolicesSg3 = "F4C95D43340C7D8A233850AE65BC3861";      // DATA\Zeus_fonts.sg3 GOG / Steam
        public const string Md5Polices555 = "573B6C1588C3FA0B2E46250F3A953F34";      // DATA\Zeus_fonts.555 GOG / Steam

        static IEnumerable<string> Lignes(string ressource)
        {
            using (var s = Assembly.GetExecutingAssembly().GetManifestResourceStream("ZeusPatchFR." + ressource))
            using (var r = new StreamReader(s, Encoding.UTF8))
            {
                string l;
                while ((l = r.ReadLine()) != null)
                    if (l.Length > 0 && l[0] != '#') yield return l;
            }
        }

        public static List<ElementPlan> Plan()
        {
            var res = new List<ElementPlan>();
            foreach (var l in Lignes("plan.txt"))
            {
                var p = l.Split('|');
                if (p[0] == "RETIRER") res.Add(new ElementPlan { Type = p[0], Cible = p[1] });
                else res.Add(new ElementPlan { Type = p[0], Cible = p[1], Source = p[2], Md5 = p[3], Taille = long.Parse(p[4]) });
            }
            return res;
        }

        public static List<ModificationExe> PatchExe()
        {
            var res = new List<ModificationExe>();
            foreach (var l in Lignes("patch_exe.txt"))
            {
                var p = l.Split('|');
                var m = new ModificationExe { Groupe = p[0], Offset = Convert.ToInt32(p[1], 16) };
                if (p[2].StartsWith("CAB:"))
                {
                    var c = p[2].Split(':');
                    m.CabFichier = c[1]; m.CabOffset = Convert.ToInt32(c[2], 16); m.CabTaille = int.Parse(c[3]); m.CabMd5 = c[4];
                }
                else m.Nouveau = Hex(p[2]);
                res.Add(m);
            }
            return res;
        }

        static byte[] Hex(string h)
        {
            var b = new byte[h.Length / 2];
            for (int i = 0; i < b.Length; i++) b[i] = Convert.ToByte(h.Substring(2 * i, 2), 16);
            return b;
        }

        public static string Md5(byte[] donnees)
        {
            using (var m = MD5.Create())
            {
                var sb = new StringBuilder();
                foreach (var x in m.ComputeHash(donnees)) sb.Append(x.ToString("X2"));
                return sb.ToString();
            }
        }

        /// <summary>Applique les groupes choisis à l'exe d'origine (dont l'empreinte MD5 a déjà été vérifiée) ;
        /// les octets venant du CD sont extraits de l'archive et contrôlés par leur empreinte.</summary>
        public static byte[] PatcherExe(byte[] exe, ICollection<string> groupes, InstallShieldCab cab)
        {
            var res = (byte[])exe.Clone();
            var fichiers = new Dictionary<string, byte[]>(StringComparer.OrdinalIgnoreCase);
            foreach (var m in PatchExe())
            {
                if (!groupes.Contains(m.Groupe)) continue;
                byte[] nouveau = m.Nouveau;
                if (nouveau == null)
                {
                    byte[] f;
                    if (!fichiers.TryGetValue(m.CabFichier, out f))
                    {
                        var fc = cab.Trouver(m.CabFichier);
                        if (fc == null) throw new FileNotFoundException("Fichier absent de l'archive du CD : " + m.CabFichier);
                        fichiers[m.CabFichier] = f = cab.Extraire(fc);
                    }
                    nouveau = new byte[m.CabTaille];
                    if (m.CabOffset + m.CabTaille <= f.Length) Buffer.BlockCopy(f, m.CabOffset, nouveau, 0, m.CabTaille);
                    if (Md5(nouveau) != m.CabMd5)
                        throw new InvalidDataException("Données inattendues dans " + m.CabFichier + " du CD.");
                }
                Buffer.BlockCopy(nouveau, 0, res, m.Offset, nouveau.Length);
            }
            return res;
        }
    }
}
