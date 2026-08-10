/* ============================================================================
   Page /compte — profil de connexion et réglages d'affichage.
   ----------------------------------------------------------------------------
   La page est servie à tout le monde, connecté ou non : les réglages
   d'affichage n'ont rien à voir avec un compte, et exiger une connexion pour
   agrandir le texte serait absurde. Seule la carte « Identité » change.
   ========================================================================== */

(function () {
  'use strict';

  // ── Carte « Identité » ────────────────────────────────────────────────────

  var FOURNISSEURS = {
    google: 'Google',
    github: 'GitHub'
  };

  function el(balise, classe, texte) {
    var noeud = document.createElement(balise);
    if (classe) noeud.className = classe;
    if (texte != null) noeud.textContent = texte;
    return noeud;
  }

  function badgeFournisseur(fournisseur) {
    var badge = el('span', 'profil-fournisseur');
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.7');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.innerHTML = '<path d="M12 2.5 4 6v6c0 4.6 3.4 8.4 8 9.5 4.6-1.1 8-4.9 8-9.5V6z"/><path d="m9 12 2 2 4-4"/>';
    badge.appendChild(svg);
    // Un compte local n'est « via » personne : il a été créé ici même. Un
    // fournisseur inconnu (ajout futur, session d'une ancienne version) retombe
    // sur son code brut plutôt que d'afficher une chaîne vide.
    badge.appendChild(document.createTextNode(
      fournisseur === 'local'
        ? 'Compte ChatPy (email et mot de passe)'
        : 'Connecté via ' + (FOURNISSEURS[fournisseur] || fournisseur || 'un fournisseur externe')
    ));
    return badge;
  }

  function rendreProfil(carte, moi) {
    var profil = el('div', 'profil');

    // ChatPyAvatar vient de nav-compte.js : même repli sur l'initiale que dans
    // la barre de navigation, à une autre taille.
    profil.appendChild(window.ChatPyAvatar
      ? window.ChatPyAvatar(moi, 'profil-photo', 'profil-initiale', 72)
      : el('span', 'profil-photo profil-initiale', (moi.nom || '?').charAt(0).toUpperCase()));

    var infos = el('div', 'profil-infos');
    infos.appendChild(el('div', 'profil-nom', moi.nom || 'Compte ChatPy'));
    if (moi.email) infos.appendChild(el('div', 'profil-email', moi.email));
    infos.appendChild(badgeFournisseur(moi.fournisseur));
    profil.appendChild(infos);

    carte.appendChild(profil);
  }

  function rendreInvitation(carte, moi) {
    var vide = el('div', 'compte-vide');
    vide.appendChild(el('div', 'compte-vide-icone', '👤'));

    // La connexion par email et mot de passe ne dépend d'aucune configuration :
    // elle est toujours proposée, contrairement à Google et GitHub.
    vide.appendChild(el('p', null, moi.oauth_disponible
      ? "Vous n'êtes pas connecté. Créez un compte, ou connectez-vous avec "
        + 'Google ou GitHub, pour retrouver vos conversations depuis '
        + "n'importe quel appareil."
      : "Vous n'êtes pas connecté. Créez un compte avec votre email pour "
        + "retrouver vos conversations depuis n'importe quel appareil."));

    var liens = el('div', 'compte-liens');
    var connexion = el('a', 'btn', 'Se connecter');
    connexion.href = '/?inscription=1';
    liens.appendChild(connexion);
    var chat = el('a', 'btn', 'Ouvrir le chat');
    chat.href = '/chat';
    liens.appendChild(chat);
    vide.appendChild(liens);

    carte.appendChild(vide);
  }

  var carteIdentite = document.getElementById('carteIdentite');
  var chargement = document.getElementById('identiteChargement');

  if (carteIdentite && window.ChatPyMoi) {
    window.ChatPyMoi.then(function (moi) {
      if (chargement) chargement.remove();
      if (moi.connecte) rendreProfil(carteIdentite, moi);
      else rendreInvitation(carteIdentite, moi);
    });
  } else if (chargement) {
    // Sans serveur (page ouverte directement), l'identité est indisponible ;
    // les réglages, eux, restent utilisables.
    chargement.textContent = 'Identité indisponible : le serveur ChatPy ne répond pas.';
  }

  // ── Sélecteurs segmentés ──────────────────────────────────────────────────

  var groupes = Array.prototype.slice.call(document.querySelectorAll('.segments[data-pref]'));

  function segmentActif(groupe) {
    return groupe.querySelector('.segment[aria-checked="true"]');
  }

  function placerCurseur(groupe) {
    var curseur = groupe.querySelector('.segments-curseur');
    var actif = segmentActif(groupe);
    if (!curseur || !actif) return;
    curseur.style.width = actif.offsetWidth + 'px';
    // Le groupe est positionné et porte 3px de rembourrage : offsetLeft les
    // inclut, et le curseur part déjà de left:3px.
    curseur.style.transform = 'translateX(' + (actif.offsetLeft - 3) + 'px)';
  }

  function synchroniser(groupe) {
    if (!window.ChatPyPrefs) return;
    var valeurCourante = window.ChatPyPrefs.lire()[groupe.dataset.pref];
    groupe.querySelectorAll('.segment').forEach(function (segment) {
      var choisi = segment.dataset.valeur === valeurCourante;
      segment.setAttribute('aria-checked', choisi ? 'true' : 'false');
      // Un seul arrêt de tabulation par groupe, comme l'attend un radiogroup :
      // on entre dedans au Tab, on circule aux flèches.
      segment.tabIndex = choisi ? 0 : -1;
    });
    placerCurseur(groupe);
  }

  groupes.forEach(function (groupe) {
    groupe.addEventListener('click', function (event) {
      var segment = event.target.closest('.segment');
      if (!segment || !window.ChatPyPrefs) return;
      window.ChatPyPrefs.definir(groupe.dataset.pref, segment.dataset.valeur);
    });

    // Flèches gauche/droite : navigation attendue dans un groupe de boutons
    // radio, et sans elle le groupe est inutilisable au clavier.
    groupe.addEventListener('keydown', function (event) {
      if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
      var segments = Array.prototype.slice.call(groupe.querySelectorAll('.segment'));
      var index = segments.indexOf(segmentActif(groupe));
      if (index === -1) return;
      event.preventDefault();
      var suivant = (index + (event.key === 'ArrowRight' ? 1 : -1) + segments.length) % segments.length;
      if (window.ChatPyPrefs) {
        window.ChatPyPrefs.definir(groupe.dataset.pref, segments[suivant].dataset.valeur);
      }
      segments[suivant].focus();
    });

    synchroniser(groupe);
  });

  // Une préférence peut aussi changer ailleurs : la bascule de thème de la
  // barre de navigation agit sur le même réglage que le premier groupe.
  document.addEventListener('chatpy:prefs', function () {
    groupes.forEach(synchroniser);
  });

  // Le curseur est posé une première fois sans transition, puis on la rétablit
  // pour les clics suivants. Les largeurs dépendent de la police : tant qu'elle
  // n'est pas chargée, la mesure est fausse, d'où le second placement.
  function fixerCurseurs() {
    groupes.forEach(placerCurseur);
  }

  requestAnimationFrame(function () {
    fixerCurseurs();
    requestAnimationFrame(function () {
      groupes.forEach(function (groupe) {
        var curseur = groupe.querySelector('.segments-curseur');
        if (curseur) curseur.classList.remove('sans-transition');
      });
    });
  });

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(fixerCurseurs);
  }
  window.addEventListener('resize', fixerCurseurs);
})();
