using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace ZeusPatchFR
{
    /// <summary>Les deux CD français : le jeu de base et l'extension.</summary>
    public enum Disque { Zeus, Poseidon }

    /// <summary>Un CD français (lecteur, image ISO montée ou copie du CD).</summary>
    public class SourceCd
    {
        public readonly string Dossier;
        public readonly Disque Disque;
        InstallShieldCab cab;

        public SourceCd(string dossier, Disque disque)
        {
            Dossier = dossier;
            Disque = disque;
            string err = Probleme(dossier, disque);
            if (err != null) throw new InvalidOperationException(err);
        }

        public InstallShieldCab Cab
        {
            get { if (cab == null) cab = new InstallShieldCab(Dossier); return cab; }
        }

        public bool ExisteEnClair(string rel) { return File.Exists(Path.Combine(Dossier, rel)); }
        public byte[] LireEnClair(string rel) { return File.ReadAllBytes(Path.Combine(Dossier, rel)); }

        public static string Nom(Disque d)
        {
            return d == Disque.Zeus ? "CD 1 « Le Maître de l'Olympe - Zeus »" : "CD 2 « Le Maître de l'Atlantide - Poséidon »";
        }

        /// <summary>null si le dossier ressemble au CD français demandé, sinon la raison.</summary>
        public static string Probleme(string d, Disque disque)
        {
            if (string.IsNullOrEmpty(d) || !Directory.Exists(d)) return "Aucun disque dans le lecteur, ou dossier introuvable.";
            string ini = Path.Combine(d, "Setup.ini");
            string texte = File.Exists(ini) ? File.ReadAllText(ini, Encoding.GetEncoding(1252)) : "";
            if (disque == Disque.Zeus)
            {
                // InstallShield 5 : data1.cab seul (pas de data1.hdr) ; titre français dans Setup.ini
                if (!File.Exists(Path.Combine(d, "data1.cab")) || File.Exists(Path.Combine(d, "data1.hdr")) || !Directory.Exists(Path.Combine(d, @"Audio\Voice")))
                    return "Ce n'est pas le CD du jeu de base Zeus.";
                if (texte.IndexOf("Maître de l'Olympe - Zeus", StringComparison.OrdinalIgnoreCase) < 0)
                    return "Ce CD de Zeus n'est pas la version française.";
                return null;
            }
            if (!File.Exists(Path.Combine(d, "data1.hdr")) || !File.Exists(Path.Combine(d, "data2.cab")) || !Directory.Exists(Path.Combine(d, @"Audio\Voice")))
                return "Ce n'est pas le CD de Poséidon.";
            if (texte.IndexOf("0x040c", StringComparison.OrdinalIgnoreCase) < 0)
                return "Ce CD de Poséidon n'est pas la version française.";
            return null;
        }

        /// <summary>Lecteurs CD / DVD (y compris images ISO montées).</summary>
        public static List<DriveInfo> Lecteurs()
        {
            var l = new List<DriveInfo>();
            foreach (var d in DriveInfo.GetDrives())
                if (d.DriveType == DriveType.CDRom) l.Add(d);
            return l;
        }

        public static string Libelle(DriveInfo d)
        {
            try
            {
                if (!d.IsReady) return d.Name + "   (aucun disque)";
                string r = d.RootDirectory.FullName;
                string quoi = Probleme(r, Disque.Zeus) == null ? "   ✓ CD 1 : Zeus" : Probleme(r, Disque.Poseidon) == null ? "   ✓ CD 2 : Poséidon" : "";
                return d.Name + "   " + d.VolumeLabel + quoi;
            }
            catch (Exception) { return d.Name; }
        }
    }
}
