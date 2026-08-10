/* ============================================================================
   Préférences d'affichage — thème, animations, taille du texte.
   ----------------------------------------------------------------------------
   Ce fichier est chargé de façon *synchrone* dans le <head> de chaque page,
   avant tout contenu. C'est volontaire : les attributs data-theme / data-taille
   doivent être posés sur <html> avant la première peinture, sinon la page
   s'affiche une fraction de seconde dans le mauvais thème avant de basculer.
   Un `defer` ou un script en fin de <body> produirait exactement ce flash.

   Les réglages vivent dans localStorage et non dans la session serveur : ils
   décrivent l'affichage de *cet* appareil (un écran de bureau et un téléphone
   n'appellent pas les mêmes choix), et ils doivent fonctionner déconnecté.
   ========================================================================== */

(function () {
  'use strict';

  var CLE = 'chatpy.prefs.v1';

  // Valeurs admises. Toute autre valeur (fichier trafiqué, ancienne version)
  // retombe sur le défaut plutôt que de poser un attribut inconnu.
  var SCHEMA = {
    theme: { valeurs: ['auto', 'clair', 'sombre'], defaut: 'auto', attribut: 'data-theme' },
    animations: { valeurs: ['auto', 'reduites'], defaut: 'auto', attribut: 'data-animations' },
    taille: { valeurs: ['petite', 'normale', 'grande'], defaut: 'normale', attribut: 'data-taille' }
  };

  var racine = document.documentElement;

  function lireStockage() {
    // localStorage lève en navigation privée stricte et sur certains file://.
    // Une préférence perdue n'est pas un motif pour casser la page.
    try {
      var brut = window.localStorage.getItem(CLE);
      var objet = brut ? JSON.parse(brut) : null;
      return objet && typeof objet === 'object' ? objet : {};
    } catch (e) {
      return {};
    }
  }

  function ecrireStockage(prefs) {
    try {
      window.localStorage.setItem(CLE, JSON.stringify(prefs));
    } catch (e) {
      /* quota, mode privé : le réglage vaut pour la session en cours, tant pis */
    }
  }

  function normaliser(brut) {
    var prefs = {};
    for (var cle in SCHEMA) {
      var regle = SCHEMA[cle];
      prefs[cle] = regle.valeurs.indexOf(brut[cle]) === -1 ? regle.defaut : brut[cle];
    }
    return prefs;
  }

  var prefs = normaliser(lireStockage());

  function appliquer() {
    for (var cle in SCHEMA) {
      var regle = SCHEMA[cle];
      // Le défaut ne pose aucun attribut : le CSS de base et les media queries
      // (prefers-color-scheme, prefers-reduced-motion) reprennent la main, ce
      // qui est exactement le sens de « auto ».
      if (prefs[cle] === regle.defaut) {
        racine.removeAttribute(regle.attribut);
      } else {
        racine.setAttribute(regle.attribut, prefs[cle]);
      }
    }
  }

  appliquer();

  function themeSysteme() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches
      ? 'clair'
      : 'sombre';
  }

  var api = {
    /** Copie des réglages courants (theme, animations, taille). */
    lire: function () {
      return {
        theme: prefs.theme,
        animations: prefs.animations,
        taille: prefs.taille
      };
    },

    /** Le thème réellement rendu à l'écran, « auto » résolu. */
    themeEffectif: function () {
      return prefs.theme === 'auto' ? themeSysteme() : prefs.theme;
    },

    /**
     * Change un réglage, l'applique et le persiste.
     * Une valeur inconnue est ignorée : mieux vaut garder l'ancienne que
     * poser un attribut que le CSS ne sait pas interpréter.
     */
    definir: function (cle, valeur) {
      var regle = SCHEMA[cle];
      if (!regle || regle.valeurs.indexOf(valeur) === -1) return false;
      if (prefs[cle] === valeur) return true;
      prefs[cle] = valeur;
      appliquer();
      ecrireStockage(prefs);
      // Les écrans qui affichent l'état (bascule de la nav, sélecteurs de
      // /compte) se remettent à jour en écoutant cet évènement, plutôt qu'en
      // se sondant les uns les autres.
      document.dispatchEvent(new CustomEvent('chatpy:prefs', {
        detail: { cle: cle, valeur: valeur, prefs: api.lire() }
      }));
      return true;
    },

    /**
     * Bascule clair ↔ sombre. Depuis « auto », on part du thème réellement
     * affiché : le clic doit toujours produire le changement visible attendu.
     */
    basculerTheme: function () {
      var cible = api.themeEffectif() === 'sombre' ? 'clair' : 'sombre';
      api.definir('theme', cible);
      return cible;
    }
  };

  window.ChatPyPrefs = api;

  // En mode « auto », un changement de thème du système doit être répercuté
  // aux composants qui affichent l'état (l'icône de la bascule, par exemple).
  // Le CSS, lui, suit déjà tout seul via prefers-color-scheme.
  if (window.matchMedia) {
    var media = window.matchMedia('(prefers-color-scheme: light)');
    var surChangement = function () {
      if (prefs.theme !== 'auto') return;
      document.dispatchEvent(new CustomEvent('chatpy:prefs', {
        detail: { cle: 'theme', valeur: 'auto', prefs: api.lire() }
      }));
    };
    // addEventListener sur un MediaQueryList n'existe pas sur les Safari
    // anciens, qui n'ont que addListener.
    if (media.addEventListener) media.addEventListener('change', surChangement);
    else if (media.addListener) media.addListener(surChangement);
  }
})();
