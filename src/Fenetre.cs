using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace ZeusPatchFR
{
    public class Fenetre : Form
    {
        readonly ComboBox listeJeux = new ComboBox(), listeCd = new ComboBox();
        readonly CheckBox caseTrad = new CheckBox(), caseRes = new CheckBox(), caseDieux = new CheckBox(), caseSon = new CheckBox();
        readonly Button boutonInstaller = new Button(), boutonDesinstaller = new Button(), boutonQuitter = new Button();
        readonly ProgressBar barre = new ProgressBar();
        readonly TextBox journal = new TextBox();
        readonly BackgroundWorker travail = new BackgroundWorker();

        public Fenetre()
        {
            Text = "Patch FR — Le Maître de l'Olympe : Zeus & Poséidon";
            Font = new Font("Segoe UI", 9f);
            AutoScaleMode = AutoScaleMode.Dpi;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(660, 614);
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch (Exception) { }

            var titre = new Label { Text = "Patch de traduction française", Font = new Font("Segoe UI", 14f, FontStyle.Bold), AutoSize = true, Location = new Point(16, 12) };
            var sous = new Label
            {
                Text = "Le Maître de l'Olympe : Zeus & Poséidon — versions GOG et Steam.\nLes fichiers français sont lus sur votre CD de « Le Maître de l'Atlantide - Poséidon ».",
                AutoSize = true, Location = new Point(18, 44), ForeColor = Color.DimGray, UseMnemonic = false
            };

            var g1 = Groupe("1.  Jeu à patcher", 84, 64);
            listeJeux.DropDownStyle = ComboBoxStyle.DropDownList; listeJeux.SetBounds(12, 26, 490, 24);
            var autreJeu = new Button { Text = "Autre dossier…", Bounds = new Rectangle(510, 25, 118, 26) };
            autreJeu.Click += (s, e) => ChoisirDossierJeu();
            listeJeux.SelectedIndexChanged += (s, e) => MajBoutons();
            g1.Controls.AddRange(new Control[] { listeJeux, autreJeu });

            var g2 = Groupe("2.  CD français de Poséidon (ou image ISO montée)", 156, 64);
            listeCd.DropDownStyle = ComboBoxStyle.DropDownList; listeCd.SetBounds(12, 26, 410, 24);
            var actualiser = new Button { Text = "Actualiser", Bounds = new Rectangle(430, 25, 90, 26) };
            actualiser.Click += (s, e) => RemplirCd(null);
            var autreCd = new Button { Text = "Dossier…", Bounds = new Rectangle(528, 25, 100, 26) };
            autreCd.Click += (s, e) => ChoisirDossierCd();
            g2.Controls.AddRange(new Control[] { listeCd, actualiser, autreCd });

            var g3 = Groupe("3.  Contenu", 228, 122);
            caseTrad.Text = "Traduction française : textes, voix, vidéos, campagnes, accents"; caseTrad.Checked = true; caseTrad.Enabled = false;
            caseRes.Text = "Affichage 1280 × 720 (remplace le mode 1024 × 768)"; caseRes.Checked = true;
            caseDieux.Text = "Corriger l'apparition des dieux et les animations au ralenti"; caseDieux.Checked = true;
            caseTrad.SetBounds(14, 22, 600, 22); caseRes.SetBounds(14, 46, 600, 22); caseDieux.SetBounds(14, 70, 600, 22);
            caseSon.Text = "Corriger les figements réguliers de l'image (sons d'ambiance et musique)"; caseSon.Checked = true; caseSon.SetBounds(14, 94, 600, 22);
            g3.Controls.AddRange(new Control[] { caseTrad, caseRes, caseDieux, caseSon });

            boutonInstaller.Text = "Installer"; boutonInstaller.SetBounds(16, 364, 150, 34); boutonInstaller.Font = new Font(Font, FontStyle.Bold);
            boutonDesinstaller.Text = "Désinstaller"; boutonDesinstaller.SetBounds(176, 364, 130, 34);
            boutonQuitter.Text = "Quitter"; boutonQuitter.SetBounds(528, 364, 116, 34);
            boutonInstaller.Click += (s, e) => Lancer(true);
            boutonDesinstaller.Click += (s, e) => Lancer(false);
            boutonQuitter.Click += (s, e) => Close();

            barre.SetBounds(16, 410, 628, 18);
            journal.Multiline = true; journal.ReadOnly = true; journal.ScrollBars = ScrollBars.Vertical;
            journal.SetBounds(16, 436, 628, 162); journal.BackColor = SystemColors.Window;

            Controls.AddRange(new Control[] { titre, sous, g1, g2, g3, boutonInstaller, boutonDesinstaller, boutonQuitter, barre, journal });
            AcceptButton = boutonInstaller;

            travail.WorkerReportsProgress = true;
            travail.DoWork += Travail;
            travail.ProgressChanged += (s, e) => { barre.Maximum = 1000; barre.Value = Math.Min(1000, e.ProgressPercentage); };
            travail.RunWorkerCompleted += Fin;

            Load += (s, e) => { RemplirJeux(null); RemplirCd(null); };
        }

        GroupBox Groupe(string texte, int y, int h)
        {
            var g = new GroupBox { Text = texte, Bounds = new Rectangle(16, y, 628, h) };
            Controls.Add(g);
            return g;
        }

        void Ecrire(string m)
        {
            if (InvokeRequired) { BeginInvoke(new Action<string>(Ecrire), m); return; }
            journal.AppendText(m + Environment.NewLine);
        }

        // ------------------------------------------------------------------------------------------- listes
        void RemplirJeux(string choisir)
        {
            listeJeux.Items.Clear();
            foreach (var j in Jeu.Detecter()) listeJeux.Items.Add(j);
            if (choisir != null && Jeu.EstDossierJeu(choisir))
            {
                bool present = false;
                foreach (InstallationJeu j in listeJeux.Items) if (string.Equals(j.Dossier, choisir, StringComparison.OrdinalIgnoreCase)) { listeJeux.SelectedItem = j; present = true; }
                if (!present) listeJeux.SelectedIndex = listeJeux.Items.Add(new InstallationJeu { Plateforme = Jeu.PlateformeDe(choisir), Dossier = choisir, Patche = Jeu.EstPatche(choisir) });
            }
            else if (listeJeux.Items.Count > 0) listeJeux.SelectedIndex = 0;
            if (listeJeux.Items.Count == 0) Ecrire("Aucune installation GOG ou Steam trouvée : utilisez « Autre dossier… » (dossier contenant Zeus.exe).");
            MajBoutons();
        }

        void RemplirCd(string dossier)
        {
            listeCd.Items.Clear();
            int choix = -1;
            foreach (var d in SourceCd.Lecteurs())
            {
                int i = listeCd.Items.Add(new ElementCd { Chemin = d.RootDirectory.FullName, Texte = SourceCd.Libelle(d) });
                if (choix < 0 && d.IsReady && SourceCd.Probleme(d.RootDirectory.FullName) == null) choix = i;
            }
            if (dossier != null) choix = listeCd.Items.Add(new ElementCd { Chemin = dossier, Texte = dossier });
            if (choix < 0 && listeCd.Items.Count > 0) choix = 0;
            if (choix >= 0) listeCd.SelectedIndex = choix;
        }

        class ElementCd { public string Chemin, Texte; public override string ToString() { return Texte; } }

        void ChoisirDossierJeu()
        {
            using (var dlg = new FolderBrowserDialog { Description = "Dossier du jeu (celui qui contient Zeus.exe)", ShowNewFolderButton = false })
            {
                if (dlg.ShowDialog(this) != DialogResult.OK) return;
                if (!Jeu.EstDossierJeu(dlg.SelectedPath)) { MessageBox.Show(this, "Ce dossier ne contient pas Le Maître de l'Olympe (Zeus.exe, Zeus_Text.eng, Adventures).", Text); return; }
                RemplirJeux(dlg.SelectedPath.TrimEnd('\\'));
            }
        }

        void ChoisirDossierCd()
        {
            using (var dlg = new FolderBrowserDialog { Description = "Lecteur ou dossier du CD français de Poséidon", ShowNewFolderButton = false })
            {
                if (dlg.ShowDialog(this) != DialogResult.OK) return;
                string err = SourceCd.Probleme(dlg.SelectedPath);
                if (err != null) { MessageBox.Show(this, err, Text); return; }
                RemplirCd(dlg.SelectedPath);
            }
        }

        void MajBoutons()
        {
            var j = listeJeux.SelectedItem as InstallationJeu;
            bool libre = !travail.IsBusy;
            boutonInstaller.Enabled = libre && j != null;
            boutonDesinstaller.Enabled = libre && j != null && Jeu.EstPatche(j.Dossier);
        }

        // ----------------------------------------------------------------------------------------- travail
        class Demande { public bool Installer; public string Jeu, Cd; public Options Options; }

        void Lancer(bool installer)
        {
            var j = listeJeux.SelectedItem as InstallationJeu;
            if (j == null) return;
            if (Process.GetProcessesByName("Zeus").Length > 0) { MessageBox.Show(this, "Le jeu est ouvert : fermez-le avant de continuer.", Text); return; }
            var cd = listeCd.SelectedItem as ElementCd;
            if (installer)
            {
                string err = cd == null ? "Insérez le CD français de Poséidon (ou montez son image ISO), puis cliquez sur « Actualiser »." : SourceCd.Probleme(cd.Chemin);
                if (err != null) { MessageBox.Show(this, err, Text); return; }
            }
            else if (MessageBox.Show(this, "Remettre le jeu dans sa version anglaise d'origine ?", Text, MessageBoxButtons.YesNo) != DialogResult.Yes) return;

            journal.Clear();
            barre.Value = 0;
            travail.RunWorkerAsync(new Demande
            {
                Installer = installer, Jeu = j.Dossier, Cd = cd == null ? null : cd.Chemin,
                Options = new Options { Resolution = caseRes.Checked, Dieux = caseDieux.Checked, Son = caseSon.Checked }
            });
            MajBoutons();
            boutonInstaller.Enabled = boutonDesinstaller.Enabled = false;
        }

        void Travail(object sender, DoWorkEventArgs e)
        {
            var d = (Demande)e.Argument;
            var inst = new Installateur();
            inst.Journal += Ecrire;
            inst.Progression += (i, n) => travail.ReportProgress(n == 0 ? 0 : (int)(1000L * i / n));
            if (d.Installer) inst.Installer(d.Jeu, d.Cd, d.Options); else inst.Desinstaller(d.Jeu);
            e.Result = d;
        }

        void Fin(object sender, RunWorkerCompletedEventArgs e)
        {
            string dossier = listeJeux.SelectedItem is InstallationJeu ? ((InstallationJeu)listeJeux.SelectedItem).Dossier : null;
            RemplirJeux(dossier);
            if (e.Error != null)
            {
                Ecrire("ERREUR : " + e.Error.Message);
                MessageBox.Show(this, e.Error.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
            var d = (Demande)e.Result;
            if (!d.Installer) { MessageBox.Show(this, "Le jeu est revenu à sa version d'origine.", Text); return; }
            string plateforme = Jeu.PlateformeDe(d.Jeu);
            string conseil = plateforme == "Steam"
                ? "Dans Steam, n'utilisez pas « Vérifier l'intégrité des fichiers du jeu » : cela remettrait les fichiers anglais (relancez alors ce patch)."
                : "Dans GOG Galaxy, n'utilisez pas « Vérifier / Réparer » : cela remettrait les fichiers anglais (relancez alors ce patch).";
            MessageBox.Show(this, "Installation terminée : le jeu est en français.\n\n" + conseil, Text, MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
    }
}
