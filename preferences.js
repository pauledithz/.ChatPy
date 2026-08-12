/* ============================================================================
   Préférences — affichage (thème, animations, taille) et chatbot.
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
  //
  // `attribut: null` désigne un réglage que le CSS ne peut pas appliquer seul :
  // il est lu par le script concerné via ChatPyPrefs.lire(). Les autres se
  // règlent entièrement en CSS, ce qui a un avantage concret pour le chat —
  // masquer les suggestions ou les pouces vaut aussi pour les messages déjà
  // affichés, sans rien redessiner.
  var SCHEMA = {
    // La langue de l'interface. `attribut: null` parce que l'attribut à poser
    // est `lang` sur <html>, et que la règle « le défaut n'écrit rien » ne vaut
    // pas ici : un document doit toujours déclarer sa langue. C'est i18n.js qui
    // s'en charge, en même temps qu'il remplace les textes — ce que le CSS ne
    // saurait de toute façon pas faire.
    langue: { valeurs: ['auto', 'fr', 'en', 'es', 'de', 'it', 'pt'], defaut: 'auto', attribut: null },
    theme: { valeurs: ['auto', 'clair', 'sombre'], defaut: 'auto', attribut: 'data-theme' },
    animations: { valeurs: ['auto', 'reduites'], defaut: 'auto', attribut: 'data-animations' },
    taille: { valeurs: ['petite', 'normale', 'grande'], defaut: 'normale', attribut: 'data-taille' },
    suggestions: { valeurs: ['visibles', 'masquees'], defaut: 'visibles', attribut: 'data-suggestions' },
    retours: { valeurs: ['visibles', 'masques'], defaut: 'visibles', attribut: 'data-retours' },
    // L'indicateur de saisie se supprime à la source dans chat.js : le masquer
    // en CSS laisserait la ligne — et donc l'avatar — occuper le vide.
    saisie: { valeurs: ['animee', 'directe'], defaut: 'animee', attribut: null },
    // Seul réglage qui voyage jusqu'au serveur : chat.js le joint à chaque
    // envoi sur /api/chat, où il choisit le seuil de confiance du bot.
    sensibilite: { valeurs: ['stricte', 'normale', 'large'], defaut: 'normale', attribut: null }
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
      if (!regle.attribut) continue;
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
    /** Copie des réglages courants, une clé par entrée du SCHEMA. Copie et non
     *  référence : un appelant qui bricole l'objet ne doit pas modifier l'état
     *  réel sans passer par definir(), qui seul persiste et prévient. */
    lire: function () {
      var copie = {};
      for (var cle in SCHEMA) copie[cle] = prefs[cle];
      return copie;
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
