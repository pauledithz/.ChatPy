/* ============================================================================
   Zone de compte de la barre de navigation — partagée par /, /chat et /compte.
   ----------------------------------------------------------------------------
   Le serveur est seul à savoir qui est connecté : l'identité vit dans un cookie
   signé et HttpOnly, donc illisible depuis ici. On la demande à /api/moi, une
   seule fois par page, et on publie la promesse dans window.ChatPyMoi pour que
   chat.js et compte.js s'en servent au lieu de refaire la requête.

   Le contenu déconnecté est déjà dans le HTML (bouton « Commencer » ou lien
   « Se connecter ») : si le fetch échoue — page ouverte en file://, serveur
   arrêté — la nav reste utilisable telle quelle.
   ========================================================================== */

(function () {
  'use strict';

  // Raccourci vers le catalogue de i18n.js. À défaut de ce fichier — 404 parce
  // qu'il manque à FICHIERS_PUBLICS, par exemple — t() rend la clé, ce qui se
  // voit tout de suite, plutôt qu'un libellé vide qui ferait disparaître le
  // bouton sans explication.
  function T(cle, params) {
    return window.ChatPyI18n ? window.ChatPyI18n.t(cle, params) : cle;
  }

  var navCompte = document.getElementById('navCompte');

  // Une seule requête par page, partagée. Le .catch() rend une identité vide
  // plutôt que de rejeter : aucun appelant n'a besoin de gérer l'erreur.
  window.ChatPyMoi = fetch('/api/moi')
    .then(function (reponse) { return reponse.ok ? reponse.json() : null; })
    .then(function (moi) { return moi || { connecte: false, oauth_disponible: false }; })
    .catch(function () { return { connecte: false, oauth_disponible: false }; });

  // ── Liens vers l'accueil ──────────────────────────────────────────────────
  // Connecté, « / » redirige vers le chat (voir index() dans app.py) : les
  // liens qui y mènent deviennent des rebonds. Le logo repart donc vers le
  // chat, et l'entrée « Accueil » disparaît au lieu de promettre une page que
  // le serveur refusera. Fait ici et non dans le HTML de chaque page : c'est
  // /api/moi qui tranche, et ce fichier est le seul à l'interroger.

  function adapterLiensAccueil() {
    var logo = document.querySelector('.nav-logo[href="/"]');
    if (logo) logo.href = '/chat';
    document.querySelectorAll('.nav-links a[href="/"]').forEach(function (lien) {
      lien.remove();
    });
  }

  window.ChatPyMoi.then(function (moi) {
    if (moi.connecte) adapterLiensAccueil();
  });

  // ── Fabriques ─────────────────────────────────────────────────────────────

  function icone(chemin, taille) {
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 ' + (taille || 24) + ' ' + (taille || 24));
    svg.setAttribute('aria-hidden', 'true');
    // Chaînes littérales écrites ici, jamais de donnée utilisateur : pas de
    // surface d'injection.
    svg.innerHTML = chemin;
    return svg;
  }

  var ICONES = {
    chat: '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5z"/>',
    profil: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    sortie: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    lune: '<path class="icone-lune" d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    soleil: '<g class="icone-soleil"><circle cx="12" cy="12" r="4.2"/><path d="M12 1.5v2M12 20.5v2M4.5 4.5l1.4 1.4M18.1 18.1l1.4 1.4M1.5 12h2M20.5 12h2M4.5 19.5l1.4-1.4M18.1 5.9l1.4-1.4"/></g>',
    chevron: '<path d="m3 6 5 5 5-5"/>'
  };

  function initialeAvatar(nom, classe) {
    // Repli quand la photo du compte est absente ou refuse de se charger : mieux
    // vaut une pastille avec l'initiale qu'une icône d'image cassée.
    var pastille = document.createElement('span');
    pastille.className = classe;
    pastille.setAttribute('aria-hidden', 'true');
    pastille.textContent = (nom || '?').trim().charAt(0).toUpperCase() || '?';
    return pastille;
  }

  /** L'avatar du compte : sa photo, ou une pastille à l'initiale à défaut. */
  function avatar(moi, classe, classeInitiale, taille) {
    if (!moi.photo) return initialeAvatar(moi.nom, classe + ' ' + classeInitiale);
    var image = document.createElement('img');
    image.className = classe;
    image.alt = '';
    image.width = taille;
    image.height = taille;
    image.decoding = 'async';
    // Sans ça, le CDN de Google (et celui de GitHub) reçoit notre origine en
    // Referer et répond une erreur au lieu de l'image : l'avatar s'affiche cassé.
    image.referrerPolicy = 'no-referrer';
    image.addEventListener('error', function () {
      image.replaceWith(initialeAvatar(moi.nom, classe + ' ' + classeInitiale));
    });
    image.src = moi.photo;
    return image;
  }

  // Partagé avec compte.js et chat.js, qui affichent le même avatar dans
  // d'autres tailles : une seule gestion du repli sur l'initiale.
  window.ChatPyAvatar = avatar;

  function itemMenu(cle, cheminIcone, options) {
    options = options || {};
    var item = document.createElement(options.href ? 'a' : 'button');
    item.className = 'compte-menu-item' + (options.classe ? ' ' + options.classe : '');
    item.setAttribute('role', 'menuitem');
    if (options.href) {
      item.href = options.href;
    } else {
      item.type = 'button';
    }
    item.appendChild(icone(cheminIcone));
    // Le libellé dans un <span data-i18n> plutôt qu'en nœud texte nu : i18n.js
    // repasse sur tout le document au changement de langue, et ce menu se
    // retrouve donc retraduit sans que ce fichier ait à le reconstruire.
    var libelle = document.createElement('span');
    libelle.setAttribute('data-i18n', cle);
    libelle.textContent = T(cle);
    item.appendChild(libelle);
    if (options.onClick) item.addEventListener('click', options.onClick);
    return item;
  }

  // ── Bascule de thème ──────────────────────────────────────────────────────
  // Disponible connecté ou non : c'est un réglage d'affichage, pas un privilège
  // de compte. Le choix à trois états (auto/clair/sombre) vit dans /compte ;
  // ici on ne fait que basculer, geste le plus fréquent.

  function creerBasculeTheme() {
    var bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.className = 'bascule-theme';
    bouton.appendChild(icone(ICONES.lune + ICONES.soleil));

    function majLibelle() {
      // Une clé par destination plutôt qu'un « Passer au thème » + le nom du
      // thème : la phrase ne se construit pas de la même façon partout, et en
      // allemand le verbe ne tient pas au même bout.
      var texte = window.ChatPyPrefs && window.ChatPyPrefs.themeEffectif() === 'sombre'
        ? T('nav.theme_clair')
        : T('nav.theme_sombre');
      bouton.setAttribute('aria-label', texte);
      bouton.title = texte;
    }

    majLibelle();
    bouton.addEventListener('click', function () {
      if (window.ChatPyPrefs) window.ChatPyPrefs.basculerTheme();
    });
    document.addEventListener('chatpy:prefs', majLibelle);
    return bouton;
  }

  // ── Menu du compte connecté ───────────────────────────────────────────────

  async function seDeconnecter() {
    // POST et non GET : voir le commentaire de /auth/logout dans app.py.
    try {
      await fetch('/auth/logout', { method: 'POST' });
    } catch (e) {
      /* réseau coupé : on recharge quand même, le serveur tranchera */
    }
    // Retour à l'accueil : /compte n'a plus rien à montrer une fois déconnecté.
    window.location.href = '/';
  }

  function creerMenuCompte(moi) {
    var conteneur = document.createElement('div');
    conteneur.className = 'nav-compte-menu-wrap';

    var bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.className = 'compte-bouton';
    bouton.setAttribute('aria-haspopup', 'menu');
    bouton.setAttribute('aria-expanded', 'false');
    // Le nom est une donnée, pas un texte du catalogue : cet intitulé se
    // reconstruit à chaque changement de langue au lieu de porter un data-i18n,
    // que i18n.js réécrirait sans savoir quel nom y insérer.
    function majAriaLabel() {
      bouton.setAttribute('aria-label', T('nav.menu_compte', { nom: moi.nom }));
    }
    majAriaLabel();
    bouton.appendChild(avatar(moi, 'nav-photo', 'nav-initiale', 28));

    var prenom = document.createElement('span');
    prenom.className = 'compte-bouton-nom';
    // Le prénom seul : le nom complet et l'email sont dans l'en-tête du menu.
    var prenomTexte = (moi.nom || '').trim().split(/\s+/)[0];
    if (prenomTexte) {
      prenom.textContent = prenomTexte;
    } else {
      // Personne sans nom : le mot « Compte », lui, se traduit.
      prenom.setAttribute('data-i18n', 'nav.compte');
      prenom.textContent = T('nav.compte');
    }
    bouton.appendChild(prenom);
    var chevron = icone(ICONES.chevron, 16);
    chevron.setAttribute('class', 'compte-chevron');
    bouton.appendChild(chevron);

    var menu = document.createElement('div');
    menu.className = 'compte-menu';
    menu.setAttribute('role', 'menu');

    var entete = document.createElement('div');
    entete.className = 'compte-menu-entete';
    var nomComplet = document.createElement('div');
    nomComplet.className = 'compte-menu-nom';
    if (moi.nom) {
      nomComplet.textContent = moi.nom;
    } else {
      nomComplet.setAttribute('data-i18n', 'commun.compte_chatpy');
      nomComplet.textContent = T('commun.compte_chatpy');
    }
    entete.appendChild(nomComplet);
    if (moi.email) {
      var email = document.createElement('div');
      email.className = 'compte-menu-email';
      email.textContent = moi.email;
      email.title = moi.email;
      entete.appendChild(email);
    }
    menu.appendChild(entete);

    menu.appendChild(itemMenu('nav.ouvrir_chat', ICONES.chat, { href: '/chat' }));
    menu.appendChild(itemMenu('nav.mon_compte', ICONES.profil, { href: '/compte' }));

    var separateur = document.createElement('div');
    separateur.className = 'compte-menu-separateur';
    menu.appendChild(separateur);

    menu.appendChild(itemMenu('nav.deconnexion', ICONES.sortie, {
      classe: 'compte-menu-item--sortie',
      onClick: seDeconnecter
    }));

    document.addEventListener('chatpy:langue', majAriaLabel);

    conteneur.appendChild(bouton);
    conteneur.appendChild(menu);

    // ── Ouverture / fermeture ───────────────────────────────────────────────
    var ouvert = false;

    function fermer(rendreLeFocus) {
      if (!ouvert) return;
      ouvert = false;
      menu.classList.remove('ouvert');
      bouton.setAttribute('aria-expanded', 'false');
      document.removeEventListener('click', surClicExterieur, true);
      document.removeEventListener('keydown', surTouche);
      if (rendreLeFocus) bouton.focus();
    }

    function surClicExterieur(event) {
      if (!conteneur.contains(event.target)) fermer(false);
    }

    function surTouche(event) {
      if (event.key === 'Escape') {
        event.stopPropagation();
        fermer(true);
      }
    }

    function ouvrir() {
      if (ouvert) return;
      ouvert = true;
      menu.classList.add('ouvert');
      bouton.setAttribute('aria-expanded', 'true');
      // En phase de capture : un clic sur un élément qui arrête la propagation
      // fermerait quand même le menu, comme l'utilisateur s'y attend.
      document.addEventListener('click', surClicExterieur, true);
      document.addEventListener('keydown', surTouche);
    }

    bouton.addEventListener('click', function (event) {
      event.stopPropagation();
      if (ouvert) fermer(false); else ouvrir();
    });

    // Un clic sur une entrée navigue ou agit : dans les deux cas le menu ferme.
    menu.addEventListener('click', function () { fermer(false); });

    return conteneur;
  }

  // ── Assemblage ────────────────────────────────────────────────────────────

  // Une page peut n'avoir aucune zone de compte (ouverture en file://, gabarit
  // partiel) : tout ce qui précède reste publié, seul l'affichage est sauté.
  if (!navCompte) return;

  // La bascule de thème est posée tout de suite, sans attendre le réseau : elle
  // ne dépend pas du compte, et sur une page ouverte sans serveur elle reste le
  // seul réglage disponible.
  navCompte.insertBefore(creerBasculeTheme(), navCompte.firstChild);

  window.ChatPyMoi.then(function (moi) {
    if (!moi.connecte) return;
    // Le contenu déconnecté (bouton « Commencer », lien « Se connecter ») n'a
    // plus lieu d'être ; la bascule de thème, elle, reste.
    var aSupprimer = [];
    for (var i = 0; i < navCompte.children.length; i++) {
      var enfant = navCompte.children[i];
      if (!enfant.classList.contains('bascule-theme')) aSupprimer.push(enfant);
    }
    aSupprimer.forEach(function (enfant) { enfant.remove(); });
    navCompte.appendChild(creerMenuCompte(moi));
  });
})();
