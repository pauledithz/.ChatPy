/* ============================================================================
   Animations de la page d'accueil.
   ----------------------------------------------------------------------------
   Principe directeur : rien dans le HTML n'est masqué au départ. C'est ce
   script qui pose la classe .reveal (opacité 0) juste avant d'observer
   l'élément. Si le JavaScript ne s'exécute pas — erreur, navigateur ancien,
   page ouverte hors serveur — la page reste entièrement lisible au lieu de
   rester blanche, ce qui est le défaut classique des animations au scroll.

   Deux réglages coupent tout : prefers-reduced-motion du système, et le choix
   « animations réduites » de /compte. Les deux sont consultés ici *et* dans le
   CSS, parce que ce script fait des choses que le CSS ne peut pas annuler
   (compter des nombres, par exemple).
   ========================================================================== */

(function () {
  'use strict';

  function mouvementReduit() {
    if (window.ChatPyPrefs && window.ChatPyPrefs.lire().animations === 'reduites') return true;
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  var reduit = mouvementReduit();
  var supporteObserver = 'IntersectionObserver' in window;

  // ── 1. Révélation au défilement ───────────────────────────────────────────
  // Chaque groupe décrit un conteneur et les éléments à révéler dedans, en
  // cascade. Le décalage est calculé par conteneur : sur la page il y a deux
  // sections .features, et leurs cartes ne doivent pas hériter d'un rang
  // continu de la première à la dernière (la dernière carte attendrait une
  // demi-seconde de trop).
  var GROUPES = [
    { conteneur: '.stats', cibles: '.stat', pas: 0.09 },
    { conteneur: '.features', cibles: '.section-label, .section-title', pas: 0.08 },
    { conteneur: '.features', cibles: '.feat-card', pas: 0.07 },
    { conteneur: '.cta-section', cibles: 'h2, p, .btn-primary', pas: 0.09 }
  ];

  var observateur = null;
  if (supporteObserver) {
    observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (entree) {
        if (!entree.isIntersecting) return;
        entree.target.classList.add('vu');
        // Une fois révélé, un élément n'a plus rien à dire : on arrête de
        // l'observer plutôt que de repayer le coût à chaque défilement.
        observateur.unobserve(entree.target);
        lancerCompteur(entree.target);
      });
    }, {
      threshold: 0.15,
      // Déclenche un peu avant que l'élément touche le bas de l'écran, pour que
      // l'animation soit déjà finie quand le regard arrive dessus.
      rootMargin: '0px 0px -60px 0px'
    });
  }

  function preparerRevelations() {
    if (reduit || !observateur) return;
    GROUPES.forEach(function (groupe) {
      document.querySelectorAll(groupe.conteneur).forEach(function (conteneur) {
        var cibles = conteneur.querySelectorAll(groupe.cibles);
        cibles.forEach(function (cible, rang) {
          cible.classList.add('reveal');
          cible.style.setProperty('--reveal-delai', (rang * groupe.pas).toFixed(2) + 's');
          observateur.observe(cible);
        });
      });
    });
  }

  // ── 2. Compteurs de statistiques ──────────────────────────────────────────
  // Le HTML porte déjà la valeur finale en texte : c'est elle qui s'affiche si
  // ce script ne tourne pas, ou si le mouvement est réduit.

  function formater(valeur, decimales, suffixe) {
    return valeur.toFixed(decimales) + suffixe;
  }

  function lancerCompteur(element) {
    var champs = element.matches('[data-compteur]')
      ? [element]
      : element.querySelectorAll('[data-compteur]');

    Array.prototype.forEach.call(champs, function (champ) {
      if (champ.dataset.compte === 'fait') return;
      champ.dataset.compte = 'fait';

      var cible = parseFloat(champ.dataset.compteur);
      if (isNaN(cible)) return;
      var decimales = parseInt(champ.dataset.decimales || '0', 10);
      var suffixe = champ.dataset.suffixe || '';
      var duree = 1400;
      var depart = null;

      function etape(horodatage) {
        if (depart === null) depart = horodatage;
        var avancee = Math.min((horodatage - depart) / duree, 1);
        // Décélération cubique : le nombre part vite puis se pose, ce qui rend
        // la valeur finale lisible au lieu de s'arrêter net.
        var douce = 1 - Math.pow(1 - avancee, 3);
        champ.textContent = formater(cible * douce, decimales, suffixe);
        if (avancee < 1) requestAnimationFrame(etape);
        else champ.textContent = formater(cible, decimales, suffixe);
      }

      champ.textContent = formater(0, decimales, suffixe);
      requestAnimationFrame(etape);
    });
  }

  // ── 3. Halo qui suit le curseur sur les cartes ────────────────────────────
  // Écouteur unique par grille plutôt qu'un par carte : le survol d'une grille
  // de huit cartes ne doit pas coûter huit abonnements.

  function suivreCurseur() {
    document.querySelectorAll('.features-grid').forEach(function (grille) {
      grille.addEventListener('pointermove', function (event) {
        var carte = event.target.closest('.feat-card');
        if (!carte) return;
        var boite = carte.getBoundingClientRect();
        carte.style.setProperty('--souris-x', ((event.clientX - boite.left) / boite.width * 100).toFixed(1) + '%');
        carte.style.setProperty('--souris-y', ((event.clientY - boite.top) / boite.height * 100).toFixed(1) + '%');
      });
    });
  }

  // ── 4. Barre de navigation qui se resserre ────────────────────────────────

  function navAuDefilement() {
    var nav = document.querySelector('.nav');
    if (!nav) return;
    var enAttente = false;

    function evaluer() {
      enAttente = false;
      nav.classList.toggle('nav--compacte', window.scrollY > 40);
    }

    window.addEventListener('scroll', function () {
      // Le scroll se déclenche bien plus souvent que l'écran ne se rafraîchit :
      // on ne calcule qu'une fois par image.
      if (enAttente) return;
      enAttente = true;
      requestAnimationFrame(evaluer);
    }, { passive: true });

    evaluer();
  }

  // L'entrée en cascade du hero est volontairement absente d'ici : elle est
  // écrite en CSS (.hero > *), parce que ce script tourne au DOMContentLoaded,
  // soit potentiellement après la première peinture — le hero clignoterait.

  // ── Mise en route ─────────────────────────────────────────────────────────

  function demarrer() {
    preparerRevelations();
    suivreCurseur();
    navAuDefilement();
    // Sans observateur (ou en mouvement réduit) les compteurs ne seraient
    // jamais déclenchés : on affiche directement la valeur finale, déjà
    // présente dans le HTML — il n'y a donc rien à faire.
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrer);
  } else {
    demarrer();
  }
})();
