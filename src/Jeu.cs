using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace ZeusPatchFR
{
    /// <summary>Une installation du jeu trouvée sur le PC.</summary>
    public class InstallationJeu
    {
        public string Plateforme;
        public string Dossier;
        public bool Patche;

        public override string ToString()
        {
            return Plateforme + "  —  " + Dossier + (Patche ? "   (patch FR installé)" : "");
        }
    }

    /// <summary>Détection des versions GOG (« Zeus and Poseidon ») et Steam (« Zeus + Poseidon »).</summary>
    public static class Jeu
    {
        const string GogId = "1207659039";
        const string SteamId = "566050";
        public const string NomSauvegarde = "Sauvegarde_VO_Patch_FR";

        public static bool EstDossierJeu(string d)
        {
            return !string.IsNullOrEmpty(d) && File.Exists(Path.Combine(d, "Zeus.exe"))
                && File.Exists(Path.Combine(d, "Zeus_Text.eng")) && Directory.Exists(Path.Combine(d, "Adventures"));
        }

        public static bool EstPatche(string d)
        {
            return File.Exists(Path.Combine(Path.Combine(d, NomSauvegarde), "manifeste.txt"));
        }

        public static string PlateformeDe(string d)
        {
            return d.IndexOf(@"\steamapps\", StringComparison.OrdinalIgnoreCase) >= 0 ? "Steam" : "GOG";
        }

        public static List<InstallationJeu> Detecter()
        {
            var candidats = new List<KeyValuePair<string, string>>();
            // GOG : registre (vue 32 bits) et emplacements usuels
            Ajouter(candidats, "GOG", LireRegistre(RegistryHive.LocalMachine, @"SOFTWARE\GOG.com\Games\" + GogId, "path"));
            Ajouter(candidats, "GOG", LireRegistre(RegistryHive.LocalMachine, @"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\" + GogId + "_is1", "InstallLocation"));
            foreach (var pf in new[] { Environment.GetEnvironmentVariable("ProgramFiles"), Environment.GetEnvironmentVariable("ProgramFiles(x86)") })
                if (pf != null) Ajouter(candidats, "GOG", Path.Combine(pf, @"GOG Galaxy\Games\Zeus and Poseidon"));
            Ajouter(candidats, "GOG", @"C:\GOG Games\Zeus and Poseidon");
            // Steam : dossier principal et bibliothèques secondaires (libraryfolders.vdf)
            foreach (var d in DossiersSteam()) Ajouter(candidats, "Steam", d);

            var vus = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            var res = new List<InstallationJeu>();
            foreach (var c in candidats)
            {
                string d = c.Value.TrimEnd('\\');
                if (!EstDossierJeu(d)) continue;
                d = Path.GetFullPath(d).TrimEnd('\\');
                if (!vus.Add(d)) continue;
                res.Add(new InstallationJeu { Plateforme = c.Key, Dossier = d, Patche = EstPatche(d) });
            }
            return res;
        }

        static IEnumerable<string> DossiersSteam()
        {
            var racines = new List<string>();
            string r = LireRegistre(RegistryHive.LocalMachine, @"SOFTWARE\Valve\Steam", "InstallPath");
            if (r != null) racines.Add(r);
            r = LireRegistre(RegistryHive.CurrentUser, @"Software\Valve\Steam", "SteamPath");
            if (r != null) racines.Add(r.Replace('/', '\\'));
            string pf86 = Environment.GetEnvironmentVariable("ProgramFiles(x86)");
            if (pf86 != null) racines.Add(Path.Combine(pf86, "Steam"));

            var biblios = new List<string>();
            foreach (var racine in racines)
            {
                biblios.Add(racine);
                string vdf = Path.Combine(racine, @"steamapps\libraryfolders.vdf");
                if (!File.Exists(vdf)) continue;
                foreach (Match m in Regex.Matches(File.ReadAllText(vdf), "\"path\"\\s+\"([^\"]+)\""))
                    biblios.Add(m.Groups[1].Value.Replace(@"\\", @"\"));
            }
            foreach (var b in biblios)
            {
                string nom = "Zeus + Poseidon";
                string acf = Path.Combine(b, @"steamapps\appmanifest_" + SteamId + ".acf");
                if (File.Exists(acf))
                {
                    var m = Regex.Match(File.ReadAllText(acf), "\"installdir\"\\s+\"([^\"]+)\"");
                    if (m.Success) nom = m.Groups[1].Value;
                }
                yield return Path.Combine(b, @"steamapps\common\" + nom);
            }
        }

        static void Ajouter(List<KeyValuePair<string, string>> l, string plateforme, string dossier)
        {
            if (!string.IsNullOrEmpty(dossier)) l.Add(new KeyValuePair<string, string>(plateforme, dossier));
        }

        static string LireRegistre(RegistryHive ruche, string cle, string valeur)
        {
            foreach (var vue in new[] { RegistryView.Registry32, RegistryView.Registry64 })
            {
                try
                {
                    using (var b = RegistryKey.OpenBaseKey(ruche, vue))
                    using (var k = b.OpenSubKey(cle))
                    {
                        if (k == null) continue;
                        var v = k.GetValue(valeur) as string;
                        if (!string.IsNullOrEmpty(v)) return v;
                    }
                }
                catch (Exception) { }
            }
            return null;
        }
    }
}
