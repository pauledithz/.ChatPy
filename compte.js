/* ============================================================================
   Page /compte — profil de connexion et réglages d'affichage.
   ----------------------------------------------------------------------------
   La page est servie à tout le monde, connecté ou non : les réglages
   d'affichage n'ont rien à voir avec un compte, et exiger une connexion pour
   agrandir le texte serait absurde. Seule la carte « Identité » change.
   ========================================================================== */

(function () {
  'use strict';

  function T(cle, params) {
    return window.ChatPyI18n ? window.ChatPyI18n.t(cle, params) : cle;
  }

  // ── Carte « Identité » ────────────────────────────────────────────────────

  // Des noms propres : ils ne se traduisent dans aucune langue.
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
        ? T('compte.local')
        : T('compte.via', {
            fournisseur: FOURNISSEURS[fournisseur] || fournisseur || T('compte.fournisseur_inconnu')
          })
    ));
    return badge;
  }

  function rendreProfil(carte, moi) {
    var profil = el('div', 'profil');

    // Conteneur cliquable pour l'upload de photo
    var avatarWrap = el('div', 'profil-avatar-wrap');

    // ChatPyAvatar vient de nav-compte.js : même repli sur l'initiale que dans
    // la barre de navigation, à une autre taille.
    var avatarEl = window.ChatPyAvatar
      ? window.ChatPyAvatar(moi, 'profil-photo', 'profil-initiale', 72)
      : el('span', 'profil-photo profil-initiale', (moi.nom || '?').charAt(0).toUpperCase());
    avatarWrap.appendChild(avatarEl);

    // Overlay caméra au survol
    var overlay = el('div', 'profil-avatar-overlay');
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('width', '24');
    svg.setAttribute('height', '24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'white');
    svg.setAttribute('stroke-width', '1.7');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('aria-hidden', 'true');
    svg.innerHTML = '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>';
    overlay.appendChild(svg);
    overlay.setAttribute('title', T('compte.changer_photo'));
    avatarWrap.appendChild(overlay);

    // Input file caché
    var input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/jpeg,image/png,image/webp';
    input.className = 'profil-avatar-input';
    input.setAttribute('aria-label', T('compte.changer_photo'));
    avatarWrap.appendChild(input);

    // Clic sur le conteneur → ouvre le sélecteur de fichier
    avatarWrap.addEventListener('click', function () {
      input.click();
    });

    // Message d'erreur temporaire
    var msgErreur = el('div', 'profil-avatar-msg');

    input.addEventListener('change', function () {
      var fichier = input.files && input.files[0];
      if (!fichier) return;

      if (fichier.size > 2 * 1024 * 1024) {
        msgErreur.textContent = T('compte.photo_taille');
        msgErreur.className = 'profil-avatar-msg profil-avatar-msg--erreur';
        input.value = '';
        return;
      }

      var typesAcceptes = ['image/jpeg', 'image/png', 'image/webp'];
      if (typesAcceptes.indexOf(fichier.type) === -1) {
        msgErreur.textContent = T('compte.photo_format');
        msgErreur.className = 'profil-avatar-msg profil-avatar-msg--erreur';
        input.value = '';
        return;
      }

      msgErreur.textContent = '';
      msgErreur.className = 'profil-avatar-msg';

      var formData = new FormData();
      formData.append('photo', fichier);

      overlay.classList.add('profil-avatar-loading');

      fetch('/api/compte/photo', { method: 'POST', body: formData })
        .then(function (reponse) { return reponse.json().then(function (data) { return { ok: reponse.ok, data: data }; }); })
        .then(function (result) {
          overlay.classList.remove('profil-avatar-loading');
          if (!result.ok) {
            msgErreur.textContent = result.data.error || T('compte.photo_erreur');
            msgErreur.className = 'profil-avatar-msg profil-avatar-msg--erreur';
            return;
          }
          // Met à jour l'image sans recharger la page
          moi.photo = result.data.photo;
          if (avatarEl.tagName === 'IMG') {
            avatarEl.src = moi.photo;
            avatarEl.referrerPolicy = 'no-referrer';
          } else {
            var nouvelleImg = document.createElement('img');
            nouvelleImg.className = 'profil-photo';
            nouvelleImg.alt = '';
            nouvelleImg.width = 72;
            nouvelleImg.height = 72;
            nouvelleImg.decoding = 'async';
            nouvelleImg.referrerPolicy = 'no-referrer';
            nouvelleImg.src = moi.photo;
            nouvelleImg.addEventListener('error', function () {
              nouvelleImg.replaceWith(el('span', 'profil-photo profil-initiale', (moi.nom || '?').charAt(0).toUpperCase()));
            });
            avatarEl.replaceWith(nouvelleImg);
            avatarEl = nouvelleImg;
          }
        })
        .catch(function () {
          overlay.classList.remove('profil-avatar-loading');
          msgErreur.textContent = T('compte.photo_erreur');
          msgErreur.className = 'profil-avatar-msg profil-avatar-msg--erreur';
        });

      input.value = '';
    });

    avatarWrap.appendChild(msgErreur);
    profil.appendChild(avatarWrap);

    var infos = el('div', 'profil-infos');
    infos.appendChild(el('div', 'profil-nom', moi.nom || T('commun.compte_chatpy')));
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
      ? T('compte.invitation_oauth')
      : T('compte.invitation_simple')));

    var liens = el('div', 'compte-liens');
    var connexion = el('a', 'btn', T('nav.connexion'));
    connexion.href = '/?inscription=1';
    liens.appendChild(connexion);
    var chat = el('a', 'btn', T('nav.ouvrir_chat'));
    chat.href = '/chat';
    liens.appendChild(chat);
    vide.appendChild(liens);

    carte.appendChild(vide);
  }

  var carteIdentite = document.getElementById('carteIdentite');
  var chargement = document.getElementById('identiteChargement');

  /* Cette carte est bâtie en JavaScript à partir de /api/moi, et son texte
     dépend de données (le nom, le fournisseur) autant que du catalogue : plutôt
     que de semer des data-i18n qu'il faudrait ensuite recoller aux bonnes
     valeurs, on la redessine entièrement quand la langue change. Elle tient en
     quelques nœuds, et c'est le seul endroit de la page dans ce cas. */
  function rendreIdentite(moi) {
    if (!carteIdentite) return;
    // Tout sauf le titre de la carte, qui porte son propre data-i18n.
    var titre = carteIdentite.querySelector('.carte-titre');
    carteIdentite.replaceChildren();
    if (titre) carteIdentite.appendChild(titre);
    if (moi.connecte) rendreProfil(carteIdentite, moi);
    else rendreInvitation(carteIdentite, moi);
  }

  if (carteIdentite && window.ChatPyMoi) {
    window.ChatPyMoi.then(function (moi) {
      if (chargement) chargement.remove();
      rendreIdentite(moi);
      document.addEventListener('chatpy:langue', function () { rendreIdentite(moi); });
    });
  } else if (chargement) {
    // Sans serveur (page ouverte directement), l'identité est indisponible ;
    // les réglages, eux, restent utilisables.
    chargement.setAttribute('data-i18n', 'compte.identite_indisponible');
    chargement.textContent = T('compte.identite_indisponible');
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

  // ── Listes déroulantes ────────────────────────────────────────────────────
  // Même contrat que les segments (data-pref + ChatPyPrefs.definir), pour les
  // réglages à trop de valeurs pour tenir en boutons côte à côte : la langue.

  var listes = Array.prototype.slice.call(document.querySelectorAll('select[data-pref]'));

  listes.forEach(function (liste) {
    liste.addEventListener('change', function () {
      if (window.ChatPyPrefs) window.ChatPyPrefs.definir(liste.dataset.pref, liste.value);
    });
    if (window.ChatPyPrefs) liste.value = window.ChatPyPrefs.lire()[liste.dataset.pref];
  });

  function synchroniserListes() {
    if (!window.ChatPyPrefs) return;
    var prefs = window.ChatPyPrefs.lire();
    listes.forEach(function (liste) { liste.value = prefs[liste.dataset.pref]; });
  }

  // Une préférence peut aussi changer ailleurs : la bascule de thème de la
  // barre de navigation agit sur le même réglage que le premier groupe.
  document.addEventListener('chatpy:prefs', function () {
    groupes.forEach(synchroniser);
    synchroniserListes();
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

  // « Complètes » ne fait pas la même largeur que « Vollständig » : le curseur
  // se replace après la traduction, sinon il resterait aux mesures d'avant et
  // déborderait du segment actif. Reporté d'une frame, le temps que la nouvelle
  // mise en page soit calculée.
  document.addEventListener('chatpy:langue', function () {
    requestAnimationFrame(fixerCurseurs);
  });
})();
