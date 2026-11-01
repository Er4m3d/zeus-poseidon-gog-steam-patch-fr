using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace ZeusPatchFR
{
    /// <summary>Le CD français de « Le Maître de l'Atlantide - Poséidon » (lecteur, image ISO montée ou copie du CD).</summary>
    public class SourceCd
    {
        public readonly string Dossier;
        InstallShieldCab cab;

        public SourceCd(string dossier)
        {
            Dossier = dossier;
            string err = Probleme(dossier);
            if (err != null) throw new InvalidOperationException(err);
        }

        public InstallShieldCab Cab
        {
            get { if (cab == null) cab = new InstallShieldCab(Dossier); return cab; }
        }

        public bool ExisteEnClair(string rel) { return File.Exists(Path.Combine(Dossier, rel)); }
        public byte[] LireEnClair(string rel) { return File.ReadAllBytes(Path.Combine(Dossier, rel)); }

        /// <summary>null si le dossier ressemble au CD français de Poséidon, sinon la raison.</summary>
        public static string Probleme(string d)
        {
            if (string.IsNullOrEmpty(d) || !Directory.Exists(d)) return "Dossier ou lecteur introuvable.";
            if (!File.Exists(Path.Combine(d, "data1.hdr")) || !File.Exists(Path.Combine(d, "data2.cab")) || !Directory.Exists(Path.Combine(d, @"Audio\Voice")))
                return "Ce n'est pas le CD de Poséidon (data1.hdr, data2.cab ou Audio\\Voice absents).";
            string ini = Path.Combine(d, "Setup.ini");
            if (!File.Exists(ini) || File.ReadAllText(ini, Encoding.GetEncoding(1252)).IndexOf("0x040c", StringComparison.OrdinalIgnoreCase) < 0)
                return "Ce CD de Poséidon n'est pas la version française.";
            return null;
        }

        /// <summary>Lecteurs CD / DVD (y compris images ISO montées) contenant un disque.</summary>
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
                return d.Name + "   " + d.VolumeLabel + (Probleme(d.RootDirectory.FullName) == null ? "   ✓ CD français de Poséidon" : "");
            }
            catch (Exception) { return d.Name; }
        }
    }
}
