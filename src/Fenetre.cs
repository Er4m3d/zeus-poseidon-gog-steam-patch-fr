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
        readonly ComboBox listeJeux = new ComboBox(), listeZeus = new ComboBox(), listePoseidon = new ComboBox();
        readonly CheckBox caseTrad = new CheckBox(), caseRes = new CheckBox(), caseDieux = new CheckBox(), caseSon = new CheckBox(), caseAnim = new CheckBox();
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
            ClientSize = new Size(660, 710);
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch (Exception) { }

            var titre = new Label { Text = "Patch de traduction française", Font = new Font("Segoe UI", 14f, FontStyle.Bold), AutoSize = true, Location = new Point(16, 12) };
            var sous = new Label
            {
                Text = "Le Maître de l'Olympe : Zeus & Poséidon — versions GOG et Steam.\nLes fichiers français sont lus sur vos deux CD (jeu de base et extension) ; un seul lecteur suffit.",
                AutoSize = true, Location = new Point(18, 44), ForeColor = Color.DimGray, UseMnemonic = false
            };

            var g1 = Groupe("1.  Jeu à patcher", 84, 64);
            listeJeux.DropDownStyle = ComboBoxStyle.DropDownList; listeJeux.SetBounds(12, 26, 490, 24);
            var autreJeu = new Button { Text = "Autre dossier…", Bounds = new Rectangle(510, 25, 118, 26) };
            autreJeu.Click += (s, e) => ChoisirDossierJeu();
            listeJeux.SelectedIndexChanged += (s, e) => MajBoutons();
            g1.Controls.AddRange(new Control[] { listeJeux, autreJeu });

            GroupeCd("2.  CD 1 : Le Maître de l'Olympe - Zeus (jeu de base)", 156, listeZeus, Disque.Zeus);
            GroupeCd("3.  CD 2 : Le Maître de l'Atlantide - Poséidon (extension)", 228, listePoseidon, Disque.Poseidon);

            var g3 = Groupe("4.  Contenu", 300, 146);
            caseTrad.Text = "Traduction française : textes, voix, vidéos, campagnes, accents"; caseTrad.Checked = true; caseTrad.Enabled = false;
            caseRes.Text = "Affichage 1280 × 720 (remplace le mode 1024 × 768)"; caseRes.Checked = true;
            caseDieux.Text = "Corriger l'apparition des dieux et les animations au ralenti"; caseDieux.Checked = true;
            caseTrad.SetBounds(14, 22, 600, 22); caseRes.SetBounds(14, 46, 600, 22); caseDieux.SetBounds(14, 70, 600, 22);
            caseSon.Text = "Corriger les figements réguliers de l'image (sons d'ambiance et musique)"; caseSon.Checked = true; caseSon.SetBounds(14, 94, 600, 22);
            caseAnim.Text = "Ralentir les animations trop rapides (hippodrome, poste de commerce, pêche)"; caseAnim.Checked = true; caseAnim.SetBounds(14, 118, 600, 22);
            g3.Controls.AddRange(new Control[] { caseTrad, caseRes, caseDieux, caseSon, caseAnim });

            boutonInstaller.Text = "Installer"; boutonInstaller.SetBounds(16, 460, 150, 34); boutonInstaller.Font = new Font(Font, FontStyle.Bold);
            boutonDesinstaller.Text = "Désinstaller"; boutonDesinstaller.SetBounds(176, 460, 130, 34);
            boutonQuitter.Text = "Quitter"; boutonQuitter.SetBounds(528, 460, 116, 34);
            boutonInstaller.Click += (s, e) => Lancer(true);
            boutonDesinstaller.Click += (s, e) => Lancer(false);
            boutonQuitter.Click += (s, e) => Close();

            barre.SetBounds(16, 506, 628, 18);
            journal.Multiline = true; journal.ReadOnly = true; journal.ScrollBars = ScrollBars.Vertical;
            journal.SetBounds(16, 532, 628, 162); journal.BackColor = SystemColors.Window;

            Controls.AddRange(new Control[] { titre, sous, g1, g3, boutonInstaller, boutonDesinstaller, boutonQuitter, barre, journal });
            AcceptButton = boutonInstaller;

            travail.WorkerReportsProgress = true;
            travail.DoWork += Travail;
            travail.ProgressChanged += (s, e) => { barre.Maximum = 1000; barre.Value = Math.Min(1000, e.ProgressPercentage); };
            travail.RunWorkerCompleted += Fin;

            Load += (s, e) => { RemplirJeux(null); RemplirCd(listeZeus, Disque.Zeus, null); RemplirCd(listePoseidon, Disque.Poseidon, null); };
        }

        void GroupeCd(string texte, int y, ComboBox liste, Disque disque)
        {
            var g = Groupe(texte, y, 64);
            liste.DropDownStyle = ComboBoxStyle.DropDownList; liste.SetBounds(12, 26, 410, 24);
            var actualiser = new Button { Text = "Actualiser", Bounds = new Rectangle(430, 25, 90, 26) };
            actualiser.Click += (s, e) => RemplirCd(liste, disque, null);
            var autre = new Button { Text = "Dossier…", Bounds = new Rectangle(528, 25, 100, 26) };
            autre.Click += (s, e) => ChoisirDossierCd(liste, disque);
            g.Controls.AddRange(new Control[] { liste, actualiser, autre });
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

        /// <summary>Lecteurs CD ; celui qui contient déjà le bon disque est choisi, sinon le premier (un seul lecteur :
        /// le même pour les deux CD, l'installateur demandera de changer de disque).</summary>
        void RemplirCd(ComboBox liste, Disque disque, string dossier)
        {
            liste.Items.Clear();
            int choix = -1;
            foreach (var d in SourceCd.Lecteurs())
            {
                int i = liste.Items.Add(new ElementCd { Chemin = d.RootDirectory.FullName, Texte = SourceCd.Libelle(d) });
                if (choix < 0 && d.IsReady && SourceCd.Probleme(d.RootDirectory.FullName, disque) == null) choix = i;
            }
            if (dossier != null) choix = liste.Items.Add(new ElementCd { Chemin = dossier, Texte = dossier });
            if (choix < 0 && liste.Items.Count > 0) choix = 0;
            if (choix >= 0) liste.SelectedIndex = choix;
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

        void ChoisirDossierCd(ComboBox liste, Disque disque)
        {
            using (var dlg = new FolderBrowserDialog { Description = "Lecteur ou dossier du " + SourceCd.Nom(disque), ShowNewFolderButton = false })
            {
                if (dlg.ShowDialog(this) != DialogResult.OK) return;
                string err = SourceCd.Probleme(dlg.SelectedPath, disque);
                if (err != null) { MessageBox.Show(this, err, Text); return; }
                RemplirCd(liste, disque, dlg.SelectedPath);
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
        class Demande { public bool Installer; public string Jeu, Zeus, Poseidon; public Options Options; }

        void Lancer(bool installer)
        {
            var j = listeJeux.SelectedItem as InstallationJeu;
            if (j == null) return;
            if (Process.GetProcessesByName("Zeus").Length > 0) { MessageBox.Show(this, "Le jeu est ouvert : fermez-le avant de continuer.", Text); return; }
            var zeus = listeZeus.SelectedItem as ElementCd;
            var poseidon = listePoseidon.SelectedItem as ElementCd;
            if (installer)
            {
                if (zeus == null || poseidon == null) { MessageBox.Show(this, "Aucun lecteur CD trouvé : branchez un lecteur ou montez les images ISO des CD, puis cliquez sur « Actualiser ».", Text); return; }
            }
            else if (MessageBox.Show(this, "Remettre le jeu dans sa version anglaise d'origine ?", Text, MessageBoxButtons.YesNo) != DialogResult.Yes) return;

            journal.Clear();
            barre.Value = 0;
            travail.RunWorkerAsync(new Demande
            {
                Installer = installer, Jeu = j.Dossier, Zeus = zeus == null ? null : zeus.Chemin, Poseidon = poseidon == null ? null : poseidon.Chemin,
                Options = new Options { Resolution = caseRes.Checked, Dieux = caseDieux.Checked, Son = caseSon.Checked, Animations = caseAnim.Checked }
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
            if (d.Installer) inst.Installer(d.Jeu, d.Zeus, d.Poseidon, d.Options, DemanderCd); else inst.Desinstaller(d.Jeu);
            e.Result = d;
        }

        /// <summary>Appelée depuis le travail en arrière-plan : demande d'insérer un CD (OK = réessayer).</summary>
        bool DemanderCd(string message)
        {
            Ecrire(message);
            return (bool)Invoke(new Func<bool>(() =>
                MessageBox.Show(this, message, Text, MessageBoxButtons.OKCancel, MessageBoxIcon.Information) == DialogResult.OK));
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
