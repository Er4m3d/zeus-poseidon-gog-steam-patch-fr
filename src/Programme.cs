using System;
using System.IO;
using System.Windows.Forms;

[assembly: System.Reflection.AssemblyTitle("Patch FR - Le Maître de l'Olympe : Zeus & Poséidon")]
[assembly: System.Reflection.AssemblyProduct("Patch FR Zeus & Poséidon (GOG / Steam)")]
[assembly: System.Reflection.AssemblyVersion("2.4.0.0")]
[assembly: System.Reflection.AssemblyFileVersion("2.4.0.0")]

namespace ZeusPatchFR
{
    static class Programme
    {
        /// <summary>
        /// Sans argument : fenêtre. En ligne de commande (sans fenêtre) :
        ///   ZeusPatchFR.exe --installer --jeu "dossier du jeu" --cd-zeus D:\ --cd-poseidon E:\ [--sans-resolution] [--sans-son] [--sans-animations] [--journal fichier]
        ///   (les deux CD doivent être accessibles en même temps : deux lecteurs, images ISO montées ou copies des CD)
        ///   ZeusPatchFR.exe --desinstaller --jeu "dossier du jeu" [--journal fichier]
        /// </summary>
        [STAThread]
        static int Main(string[] args)
        {
            if (args.Length == 0)
            {
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.Run(new Fenetre());
                return 0;
            }

            string jeu = Valeur(args, "--jeu"), cdZeus = Valeur(args, "--cd-zeus"), cdPoseidon = Valeur(args, "--cd-poseidon"), journal = Valeur(args, "--journal");
            bool installer = Present(args, "--installer"), desinstaller = Present(args, "--desinstaller");
            Action<string> ecrire = m => { if (journal != null) File.AppendAllText(journal, m + Environment.NewLine); };
            try
            {
                if (jeu == null || !Jeu.EstDossierJeu(jeu) || installer == desinstaller || (installer && (cdZeus == null || cdPoseidon == null)))
                    throw new ArgumentException("Usage : --installer --jeu <dossier> --cd-zeus <lecteur> --cd-poseidon <lecteur> [--sans-resolution] [--sans-son] [--sans-animations] [--journal <fichier>]  |  --desinstaller --jeu <dossier>");
                var inst = new Installateur();
                inst.Journal += ecrire;
                if (installer) inst.Installer(jeu, cdZeus, cdPoseidon, new Options { Resolution = !Present(args, "--sans-resolution"), Son = !Present(args, "--sans-son"), Animations = !Present(args, "--sans-animations") && !Present(args, "--sans-dieux") }, null);
                else inst.Desinstaller(jeu);
                return 0;
            }
            catch (Exception ex)
            {
                ecrire("ERREUR : " + ex.Message);
                return 1;
            }
        }

        static bool Present(string[] a, string nom) { return Array.IndexOf(a, nom) >= 0; }

        static string Valeur(string[] a, string nom)
        {
            int i = Array.IndexOf(a, nom);
            return i >= 0 && i + 1 < a.Length ? a[i + 1] : null;
        }
    }
}
