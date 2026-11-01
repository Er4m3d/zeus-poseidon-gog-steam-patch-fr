using System;
using System.Collections.Generic;
using System.IO;
using System.Text;

namespace ZeusPatchFR
{
    public class Options
    {
        public bool Resolution = true;   // 1280 x 720
        public bool Dieux = true;        // apparition des dieux et animations au ralenti
        public bool Son = true;          // figements réguliers de l'image (moteur audio)
    }

    /// <summary>
    /// Installation et désinstallation. Tout fichier du jeu remplacé est d'abord copié dans
    /// « Sauvegarde_VO_Patch_FR » ; le manifeste liste chaque opération :
    ///   N|chemin  fichier ajouté (supprimé à la désinstallation)
    ///   R|chemin  fichier remplacé (original sauvegardé, restauré à la désinstallation)
    ///   M|chemin  fichier anglais mis de côté (remis à la désinstallation)
    /// </summary>
    public class Installateur
    {
        public event Action<string> Journal;
        public event Action<int, int> Progression;

        public const int Largeur = 1280, Hauteur = 720;
        const int Panneau = Largeur - 202;   // bord du panneau latéral (cartes du monde jusqu'à ce bord)

        string jeu, sauvegarde, manifeste;
        HashSet<string> deja;

        void Log(string m) { if (Journal != null) Journal(m); }
        void Avancer(int i, int n) { if (Progression != null) Progression(i, n); }

        void Preparer(string dossierJeu)
        {
            jeu = dossierJeu;
            sauvegarde = Path.Combine(jeu, Jeu.NomSauvegarde);
            manifeste = Path.Combine(sauvegarde, "manifeste.txt");
        }

        // ------------------------------------------------------------------------------------ installation
        public void Installer(string dossierJeu, string dossierCd, Options opt)
        {
            Preparer(dossierJeu);
            if (File.Exists(manifeste))
            {
                Log("Une version du patch est déjà installée : retour à la version d'origine avant réinstallation...");
                Desinstaller(dossierJeu);
                Preparer(dossierJeu);
            }

            string exe = Path.Combine(jeu, "Zeus.exe");
            byte[] exeOrigine = File.ReadAllBytes(exe);
            if (Donnees.Md5(exeOrigine) != Donnees.Md5ZeusExeOrigine)
                throw new InvalidOperationException("Ce Zeus.exe n'est pas celui de la version GOG / Steam 2.1.4.0 d'origine. Aucune modification n'a été faite.");

            Log("Lecture du CD de Poséidon...");
            var cd = new SourceCd(dossierCd);
            var plan = Donnees.Plan();

            // contrôle préalable : tous les fichiers du CD sont présents (avant toute modification)
            foreach (var e in plan)
                if (e.Type == "CD" && !cd.ExisteEnClair(e.Source))
                    throw new FileNotFoundException("Fichier absent du CD : " + e.Source + ". Est-ce bien le CD français de « Le Maître de l'Atlantide - Poséidon » ?");
                else if (e.Type == "CAB" && cd.Cab.Trouver(e.Source) == null)
                    throw new FileNotFoundException("Fichier absent de l'archive du CD : " + e.Source);

            // Zeus.exe modifié, préparé avant toute écriture (la table de caractères française est lue sur le CD)
            var groupes = new List<string> { "COMMUN", "ACCENTS" };
            if (opt.Dieux) groupes.Add("DIEUX");
            if (opt.Son) groupes.Add("SON");
            if (opt.Resolution) groupes.Add("RESOLUTION");
            byte[] exePatche = Donnees.PatcherExe(exeOrigine, groupes, cd.Cab);

            Directory.CreateDirectory(sauvegarde);
            deja = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            int n = plan.Count + 4, i = 0;

            // 1. campagnes identiques à la version anglaise, copiées sous leur nom français
            foreach (var e in plan)
            {
                if (e.Type != "JEU") continue;
                Avancer(++i, n);
                byte[] b = File.ReadAllBytes(Path.Combine(jeu, e.Source));
                Verifier(b, e);
                Ecrire(e.Cible, b);
            }
            // 2. aventures et voix de campagne anglaises mises de côté (sinon en double dans la liste)
            foreach (var e in plan)
            {
                if (e.Type != "RETIRER") continue;
                Avancer(++i, n);
                if (File.Exists(Path.Combine(jeu, e.Cible))) MettreDeCote(e.Cible);
            }
            // 3. fichiers français du CD
            Log("Copie des fichiers français depuis le CD...");
            foreach (var e in plan)
            {
                if (e.Type != "CD" && e.Type != "CAB") continue;
                Avancer(++i, n);
                byte[] b = e.Type == "CD" ? cd.LireEnClair(e.Source) : cd.Cab.Extraire(cd.Cab.Trouver(e.Source));
                Verifier(b, e);
                if (e.Cible.Equals("Zeus_MM.eng", StringComparison.OrdinalIgnoreCase))
                    Remplacer(b, 0x13902, "Version 2.0", "Version 2.1");          // aide « À propos »
                if (opt.Resolution && e.Cible.Equals("Zeus_Text.eng", StringComparison.OrdinalIgnoreCase))
                    Remplacer(b, 0x91E8, "1024 x 768", "1280 x 720");             // libellé de l'option
                Ecrire(e.Cible, b);
            }
            SupprimerDossiersVides("Adventures");

            // 4. polices adaptées au français
            Avancer(++i, n);
            Log("Adaptation des polices...");
            byte[] sg3 = File.ReadAllBytes(Path.Combine(jeu, @"DATA\Zeus_fonts.sg3"));
            byte[] d555 = File.ReadAllBytes(Path.Combine(jeu, @"DATA\Zeus_fonts.555"));
            if (Donnees.Md5(sg3) != Donnees.Md5PolicesSg3 || Donnees.Md5(d555) != Donnees.Md5Polices555)
                throw new InvalidOperationException("Les polices du jeu (DATA\\Zeus_fonts) ne sont pas celles de la version GOG / Steam d'origine.");
            Polices.Transformer(sg3, d555);
            Ecrire(@"DATA\Zeus_fonts.sg3", sg3);
            Ecrire(@"DATA\Zeus_fonts.555", d555);

            // 5. images de fond 1280 x 720
            Avancer(++i, n);
            if (opt.Resolution)
            {
                Log("Création des images de fond 1280 x 720...");
                foreach (var f in Directory.GetFiles(Path.Combine(jeu, "DATA"), "*.jpg"))
                {
                    string rel = @"DATA\" + Path.GetFileName(f);
                    byte[] jpg = File.ReadAllBytes(f);
                    Size t = TailleJpeg(jpg);
                    if (t.W == 1024 && t.H == 768) Ecrire(rel, Images.FondMenu(jpg, Largeur, Hauteur));
                    else if (t.W == 838 && t.H == 738) Ecrire(rel, Images.CarteMonde(jpg, Panneau));
                }
            }

            // 6. Zeus.exe
            Avancer(++i, n);
            Log("Modification de Zeus.exe (" + string.Join(", ", groupes.ToArray()) + ")...");
            Ecrire("Zeus.exe", exePatche);

            // 7. option de résolution du jeu : « 1024 x 768 » devenu 1280 x 720 (octet 0x10 de Zeus.inf)
            Avancer(++i, n);
            string inf = Path.Combine(jeu, "Zeus.inf");
            if (opt.Resolution && File.Exists(inf))
            {
                byte[] b = File.ReadAllBytes(inf);
                if (b.Length > 0x10) { b[0x10] = 3; File.WriteAllBytes(inf, b); }
            }
            Avancer(n, n);
            Log("Installation terminée.");
        }

        static void Verifier(byte[] b, ElementPlan e)
        {
            if (Donnees.Md5(b) != e.Md5)
                throw new InvalidDataException("Fichier inattendu : " + e.Source + " (ce n'est pas le CD français de Poséidon attendu, ou le fichier est abîmé).");
        }

        static void Remplacer(byte[] b, int offset, string ancien, string nouveau)
        {
            var e = Encoding.GetEncoding(1252);
            byte[] a = e.GetBytes(ancien), n = e.GetBytes(nouveau);
            for (int i = 0; i < a.Length; i++) if (b[offset + i] != a[i]) return;   // texte inattendu : laissé tel quel
            Buffer.BlockCopy(n, 0, b, offset, n.Length);
        }

        void Ecrire(string rel, byte[] contenu)
        {
            string cible = Path.Combine(jeu, rel);
            if (deja.Add(rel))
            {
                if (File.Exists(cible))
                {
                    string s = Path.Combine(sauvegarde, rel);
                    Directory.CreateDirectory(Path.GetDirectoryName(s));
                    File.Copy(cible, s, true);
                    Noter("R", rel);
                }
                else Noter("N", rel);
            }
            Directory.CreateDirectory(Path.GetDirectoryName(cible));
            if (File.Exists(cible)) File.SetAttributes(cible, FileAttributes.Normal);
            File.WriteAllBytes(cible, contenu);
        }

        void MettreDeCote(string rel)
        {
            string s = Path.Combine(sauvegarde, rel);
            Directory.CreateDirectory(Path.GetDirectoryName(s));
            if (File.Exists(s)) File.Delete(s);
            File.Move(Path.Combine(jeu, rel), s);
            Noter("M", rel);
        }

        void Noter(string type, string rel)
        {
            File.AppendAllText(manifeste, type + "|" + rel + "\r\n", new UTF8Encoding(false));
        }

        // --------------------------------------------------------------------------------- désinstallation
        public void Desinstaller(string dossierJeu)
        {
            Preparer(dossierJeu);
            if (!File.Exists(manifeste)) throw new InvalidOperationException("Le patch FR n'est pas installé dans ce dossier.");
            var lignes = File.ReadAllLines(manifeste, Encoding.UTF8);
            int i = 0, erreurs = 0;
            Log("Restauration de la version d'origine...");
            foreach (var l in lignes)
            {
                Avancer(++i, lignes.Length);
                int p = l.IndexOf('|');
                if (p < 1) continue;
                string type = l.Substring(0, p), rel = l.Substring(p + 1);
                string cible = Path.Combine(jeu, rel), s = Path.Combine(sauvegarde, rel);
                try
                {
                    if (type == "N") { if (File.Exists(cible)) { File.SetAttributes(cible, FileAttributes.Normal); File.Delete(cible); } }
                    else if (File.Exists(s))
                    {
                        Directory.CreateDirectory(Path.GetDirectoryName(cible));
                        if (File.Exists(cible)) { File.SetAttributes(cible, FileAttributes.Normal); File.Delete(cible); }
                        File.Move(s, cible);
                    }
                }
                catch (Exception ex) { erreurs++; Log("  impossible de restaurer " + rel + " : " + ex.Message); }
            }
            SupprimerDossiersVides("Adventures");
            SupprimerDossiersVides("Audio");
            if (erreurs > 0) throw new IOException(erreurs + " fichier(s) n'ont pas pu être restaurés ; la sauvegarde est conservée dans " + sauvegarde);
            Directory.Delete(sauvegarde, true);
            Log("Le jeu est revenu à sa version d'origine.");
        }

        void SupprimerDossiersVides(string sousDossier)
        {
            string b = Path.Combine(jeu, sousDossier);
            if (!Directory.Exists(b)) return;
            var dossiers = new List<string>(Directory.GetDirectories(b, "*", SearchOption.AllDirectories));
            dossiers.Sort((x, y) => y.Length.CompareTo(x.Length));
            foreach (var d in dossiers)
                if (Directory.GetFileSystemEntries(d).Length == 0) Directory.Delete(d);
        }

        // ------------------------------------------------------------------------------------------ outils
        struct Size { public int W, H; }

        static Size TailleJpeg(byte[] j)
        {
            // segments JPEG jusqu'au marqueur SOFn (largeur / hauteur), sans décoder l'image
            int p = 2;
            while (p + 9 < j.Length && j[p] == 0xFF)
            {
                byte m = j[p + 1];
                int len = (j[p + 2] << 8) | j[p + 3];
                if (m >= 0xC0 && m <= 0xCF && m != 0xC4 && m != 0xC8 && m != 0xCC)
                    return new Size { H = (j[p + 5] << 8) | j[p + 6], W = (j[p + 7] << 8) | j[p + 8] };
                p += 2 + len;
            }
            return new Size();
        }
    }
}
