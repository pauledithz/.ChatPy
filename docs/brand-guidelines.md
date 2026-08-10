# ChatPy — Charte de marque v1.0

> Dernière mise à jour : 2026-08-10
> Statut : Version initiale — extraite du code existant, pas inventée

Ce document décrit la marque **telle qu'elle est réellement implémentée** dans
`style.css`, `Index.html`, `chat.html`, `ChatPY_logo.PNG` et les réponses du bot
dans `ia_en_python.py`. Chaque valeur ci-dessous a été relevée dans le code, pas
choisie sur catalogue. Les écarts constatés sont listés en §8 — ils ne sont pas
corrigés ici, ce document décrit l'existant et sert de référence pour les
corriger.

## Référence rapide

| Élément | Valeur |
|---------|--------|
| Primary Color | #0A0A0A |
| Secondary Color | #FFFFFF |
| Accent Color | #4ADE80 |
| Primary Font | system-ui (pile système) |
| Display Font | Fraunces (serif, italique) |
| Voice | Pédagogue, Direct, Honnête, Sobre |
| Langue | Français, vouvoiement |

---

## 1. Palette de couleurs

ChatPy est une marque **achromatique et sombre**. Il n'y a pas de couleur de
marque au sens habituel : l'identité tient dans le contraste encre/blanc et dans
une seule note chromatique. Toute couleur supplémentaire ajoutée à l'interface
affaiblit la marque plutôt qu'elle ne l'enrichit.

### Primary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Ink | #0A0A0A | rgb(10,10,10) | Fond de page (`html`, `body`) |
| Ink Dark | #000000 | rgb(0,0,0) | Texte sur surface inversée (bouton primaire) |
| Ink Light | #1A1A1A | rgb(26,26,26) | Cartes, badges, surfaces élevées |

### Secondary Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Pure White | #FFFFFF | rgb(255,255,255) | Titres, bouton primaire, bulle du bot |
| Text Body | #F0F0F0 | rgb(240,240,240) | Corps de texte (`body`) |
| Muted | #AAAAAA | rgb(170,170,170) | Texte secondaire, liens de nav, bouton secondaire |

### Accent Colors

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Signal Green | #4ADE80 | rgb(74,222,128) | Pastille « En ligne », confirmation quiz |

> **Note pour les générateurs de tokens.** Les échelles de nuances calculées à
> partir d'un quasi-noir ou d'un quasi-blanc dégénèrent (toutes les nuances
> s'écrasent sur du gris). Pour ChatPy, la rampe neutre ci-dessous est la source
> de vérité, pas une échelle 50→900 générée.

### Rampe neutre (source de vérité)

Relevée par recensement des hex dans `style.css` (les valeurs les plus fréquentes
en tête). C'est la palette de travail réelle de l'interface.

| Token proposé | Hex | Occurrences | Usage constaté |
|---|---|---|---|
| `--ink-950` | #0A0A0A | 9 | Fond de page, arrêts des dégradés du hero |
| `--ink-900` | #0D0D0D | 3 | Barre de navigation (sticky) |
| `--ink-850` | #111111 | 7 | Texte sur fond blanc, surfaces profondes |
| `--surface-800` | #161616 | 3 | Surfaces secondaires |
| `--surface-700` | #1A1A1A | 14 | Cartes fonctionnalités, `hero-badge` |
| `--surface-650` | #1E1E1E | 3 | Bulle utilisateur (`.msg-user`) |
| `--border-600` | #2A2A2A | 15 | Filets 0.5px (nav, cartes) — **le plus utilisé** |
| `--border-500` | #333333 | 7 | Bordures de boutons, `hero-badge` |
| `--muted-400` | #555555 | 12 | Libellés de section, footer, statut du chat |
| `--muted-350` | #666666 | 8 | Texte tertiaire, hover de bordure |
| `--muted-300` | #8A8A8A | 1 | Mot en exergue du H1 (serif italique) |
| `--muted-250` | #AAAAAA | 7 | Texte secondaire, liens |
| `--text-100` | #F0F0F0 | 6 | Corps de texte |
| `--text-0` | #FFFFFF | 23 | Titres, surfaces inversées — **le plus utilisé** |

### Couleurs sémantiques

| État | Hex (texte / fond) | Usage constaté |
|------|-----|-------|
| Succès | #166534 sur #DCFCE7 | Badge pouce haut (`.msg-badge--haut`), copie de code réussie |
| Avertissement | #92400E sur #FEF3C7 | Badge pouce bas (`.msg-badge--bas`) |
| En ligne | #4ADE80 | Pastille de statut |
| Bordure succès | #86C79B | Bouton « copié » |

Les badges de feedback sont les **seules zones claires** de l'interface : ce sont
des jetons de statut, volontairement détachés du fond sombre. Ne pas étendre ce
traitement à d'autres composants.

### Accessibilité

Ratios calculés (formule WCAG 2.1) sur le fond de page `#0A0A0A` :

| Paire | Ratio | Verdict WCAG 2.1 |
|---|---|---|
| #FFFFFF sur #0A0A0A | 19.80:1 | AAA |
| #F0F0F0 sur #0A0A0A | 17.37:1 | AAA |
| #4ADE80 sur #0A0A0A | 11.36:1 | AAA |
| #AAAAAA sur #0A0A0A | 8.52:1 | AAA |
| #8A8A8A sur #0A0A0A | 5.73:1 | AA ; AAA en grand texte (cas du H1) |
| #666666 sur #0A0A0A | 3.45:1 | **Échec** en texte normal ; AA en grand texte seulement |
| #555555 sur #0A0A0A | 2.66:1 | **Échec partout**, y compris en grand texte — voir §8 |

Rappel des seuils : AA exige 4.5:1 en texte normal et 3:1 en grand texte
(≥ 24px, ou ≥ 18.66px en gras) ; AAA exige 7:1 et 4.5:1.

`#555555` porte les libellés de section (12px), le logo du footer (15px) et le
statut du chat (11px) : sous le seuil, quelle que soit la taille. `#666666` ne
passe qu'en grand texte. Toute nouvelle utilisation de texte gris doit rester à
`#AAAAAA` ou plus clair.

Les paires de composants sont toutes conformes :

| Composant | Paire | Ratio |
|---|---|---|
| Bulle ChatPy | #111111 sur #FFFFFF | 18.88:1 |
| Bulle utilisateur | #DDDDDD sur #1E1E1E | 12.27:1 |
| Badge pouce haut | #166534 sur #DCFCE7 | 6.49:1 |
| Badge pouce bas | #92400E sur #FEF3C7 | 6.37:1 |

---

## 2. Typographie

### Pile de polices

Telle que définie dans `style.css` :

```css
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  "Helvetica Neue", Arial, "Noto Sans", sans-serif;
--font-serif: "Fraunces", "Iowan Old Style", "Palatino Linotype", Palatino,
  Georgia, serif;
--font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
```

**Fraunces est la seule police chargée par le réseau** (Google Fonts, axes
`ital,opsz,wght@0,9..144,300..600;1,9..144,300..600`). Sans et mono sont des
piles système : aucune requête, aucun décalage de rendu. C'est un choix de
marque autant que de performance — voir §8 pour la contrepartie.

### Emploi de la serif — la signature

Fraunces n'apparaît **qu'en italique, sur un seul mot** : le mot mis en exergue
dans le H1 du hero (`comprend`), en `#8A8A8A` pour le détacher du blanc autour.

C'est la signature typographique de ChatPy. Sa force vient de sa rareté : un
seul mot par page, jamais un titre entier, jamais du corps de texte. Élargir
l'usage de Fraunces détruit l'effet.

### Échelle typographique

Relevée dans `style.css` ; les tailles fluides utilisent `clamp()`.

| Élément | Taille | Graisse | Interlignage | Interlettrage |
|---------|--------|---------|--------------|---------------|
| H1 (hero) | `clamp(2.5rem, 6vw, 4rem)` | 500 | 1.15 | -1.5px |
| Titre de section | `clamp(1.5rem, 3vw, 2rem)` | 500 | — | -0.5px |
| Logo de nav | 20px | 500 | — | -0.5px |
| Corps | 16px | 400 | 1.5 | — |
| Bouton | 15px | 500 | — | — |
| Libellé de section | 12px | 400 | — | 1.5px, majuscules |
| Statut du chat | 11px | 400 | — | — |

**Graisse 500 partout, jamais 700.** Aucun titre de ChatPy n'est en gras
appuyé : la hiérarchie passe par la taille et l'interlettrage négatif, pas par
la graisse. C'est cohérent avec la sobriété de la palette.

---

## 3. Logo

### Description

Médaillon circulaire : un serpent en trait fin, blanc, lové dans une bulle de
conversation, surmontant le mot-symbole « ChatPy » et la baseline
« AI Python Explainer ». Le serpent-dans-la-bulle dit les deux moitiés du
produit — Python et le dialogue — sans texte.

### Variantes disponibles

| Variante | Fichier | Cas d'usage |
|----------|---------|-------------|
| Médaillon complet | `ChatPY_logo.PNG` | **Seule variante existante** |

État réel : un unique PNG de 1024×1024, 228 Ko, **sans canal alpha** (fond noir
cuit dans l'image). Voir §8 — c'est la principale dette d'identité visuelle.

### Emplois constatés

| Contexte | Rendu | Fichier |
|---|---|---|
| Favicon | 16–32px | `Index.html`, `chat.html` |
| Logo de nav | 54×54px | `Index.html:17`, `chat.html:17` |
| Avatar du chat | 44×44px | `Index.html:78`, `chat.html:26` |

### Zone de protection

Minimum : la moitié du diamètre du médaillon de chaque côté. Dans la nav, le
`gap: 8px` entre l'image et le mot-symbole est en dessous de cette règle — c'est
un lock-up assumé (image + texte forment un ensemble), pas une violation.

### Tailles minimales

| Contexte | Largeur minimale |
|---|---|
| Numérique — médaillon avec baseline | 96px (en dessous, « AI Python Explainer » devient illisible) |
| Numérique — médaillon seul | 24px |
| Impression | 20mm |

À 44px et 54px, les emplois actuels sont **sous le seuil de lisibilité de la
baseline** : le logo y fonctionne comme une marque graphique, ce qui est
acceptable, mais justifie une variante icône dédiée (§8).

### Interdits

- Ne pas placer le logo sur fond clair — le fond noir est cuit dans le PNG et
  produirait un carré noir visible.
- Ne pas recoloriser le trait : le blanc sur noir est l'identité.
- Ne pas ajouter d'ombre, de contour ou d'effet.
- Ne pas déformer le cercle ni recadrer le médaillon.
- Ne pas réécrire le mot-symbole dans une autre police pour « faire un logo » :
  utiliser le fichier.

### Casse du nom

Le nom de la marque s'écrit **« ChatPy »** — C et P majuscules, `y` minuscule.
C'est ce que portent le logo, `<title>`, la nav, le footer et tous les textes.
Le nom de fichier `ChatPY_logo.PNG` contredit cette casse (§8).

---

## 4. Voix et ton

### Ce que ChatPy est réellement

Un **tuteur Python francophone** : une FAQ à correspondance floue, avec score de
confiance, quiz, et fiches de concepts. Il n'y a pas de modèle de langage
derrière — les réponses sortent de `faq.json` et `aide_concepts.json`. La voix
doit tenir cette promesse-là, ni plus ni moins. C'est le point le plus important
de ce document (§8).

### Personnalité

| Trait | Description |
|-------|-------------|
| **Pédagogue** | Explique, propose la suite, ne laisse jamais sans issue |
| **Direct** | Va au fait ; phrases courtes ; pas de préambule |
| **Honnête** | Annonce ce qu'il ne sait pas, affiche son score de confiance |
| **Sobre** | Pas d'enthousiasme forcé, pas de superlatif |

### Grille de voix

| Trait | Nous sommes | Nous ne sommes pas |
|-------|-------------|--------------------|
| Pédagogue | Guidant, on propose « Questions liées » | Condescendant, on n'explique pas ce qui n'est pas demandé |
| Direct | Concis, une idée par phrase | Télégraphique ou sec |
| Honnête | « Je ne comprends pas votre question » | Inventif — jamais de réponse plausible mais fausse |
| Sobre | Neutre et posé | Mou, ni euphorique |

### Règles de langue

1. **Vouvoiement, sans exception.** « Posez-moi une question », « N'hésitez
   pas ». Une seule réponse tutoie aujourd'hui (§8).
2. **Un emoji en tête de réponse, jamais dans le corps.** Convention en place :
   👋 salutation/adieu · 🤖 identité · 📖 explication · 😊 remerciement ·
   ❌ échec · 🎯 quiz.
3. **Toujours offrir une porte de sortie.** Chaque réponse d'échec renvoie vers
   `help` ou vers des questions proches. C'est structurel dans
   `REPONSE_INCOMPRISE` et `questions_proches()`.
4. **Les commandes en `code`.** `help`, `aide <sujet>`, `liste`, `cherche <mot>`,
   `quiz` s'écrivent en style code, jamais en majuscules ou en gras.

### Ton selon le contexte

| Contexte | Ton | Exemple réel |
|---------|------|---------|
| Accueil | Ouvrant, orientant | « 👋 Bonjour ! Posez-moi une question sur Python ou tapez 'help' pour l'aide. » |
| Réponse trouvée | Neutre, factuel | Réponse FAQ + « Questions liées » |
| Échec | Calme, jamais désolé deux fois | « ❌ Désolé, je ne comprends pas votre question… » |
| Confiance faible | Transparent | Affiche le score en %, propose « Vouliez-vous dire » |
| Quiz | Encourageant, bref | Score annoncé sans commentaire de valeur |
| Marketing (landing) | Concret, vérifiable | voir §5 |

### Termes proscrits

| À éviter | Raison |
|----------|--------|
| « révolutionnaire », « nouvelle génération » | Claim invérifiable pour une FAQ locale |
| « IA qui comprend » | Faux : c'est de la correspondance floue, pas de la compréhension |
| « seamless », « leverage », anglicismes de pitch | La marque parle français |
| « simplement », « il suffit de » | Minimise la difficulté devant un débutant |
| Chiffres de traction non sourcés | voir §8 |

---

## 5. Cadre de messagerie

### Positionnement

> ChatPy répond aux questions de débutants sur Python, en français, avec un
> score de confiance affiché — et vous dit quand il ne sait pas.

### Preuves à l'appui (toutes vérifiables dans le produit)

| Promesse | Preuve dans le produit |
|---|---|
| Répond en français aux questions Python | `faq.json`, correspondance floue tolérante aux fautes |
| Vous dit quand il ne sait pas | `REPONSE_INCOMPRISE` + « Vouliez-vous dire » |
| Affiche sa confiance | Score en % sous le seuil de 70 % |
| Explique les concepts par niveau | `aide <sujet>` — 🟢 débutant / 🟡 intermédiaire / 🔴 avancé |
| Vous fait réviser | Mode `quiz`, noté, CLI et web |
| S'améliore avec vos retours | Pouce bas → `questions_sans_reponse.json` → `lacunes.py` |
| Fonctionne sans compte ni dépendance | CLI en stdlib pur ; `/chat` accessible sans connexion |

### Hiérarchie des messages

1. **Accroche** — ce que c'est, en une phrase, sans promettre une IA générale.
2. **Différenciateur** — l'honnêteté du score de confiance ; peu d'assistants
   admettent leur ignorance.
3. **Preuve** — le mode quiz et les fiches par niveau.
4. **Appel à l'action** — « Essayer » (pas « Créer un compte » : le chat ne
   demande aucune connexion).

### Exemples de réécriture

Le contenu actuel de `Index.html` promet un produit différent de celui livré.
Réécritures proposées, à valider avant application :

**H1**
- Avant : « L'IA qui **comprend** vraiment vos besoins »
- Après : « Vos questions Python, **répondues** en français »
  (garde la structure `<span>` serif italique sur un mot)

**Sous-titre**
- Avant : « ChatPy est un assistant intelligent conçu pour vous aider à penser,
  écrire, coder et créer — plus vite et mieux qu'avant. »
- Après : « ChatPy répond à vos questions sur Python, explique les concepts
  niveau par niveau, et vous fait réviser par quiz. »

**Cartes de fonctionnalités**
- Avant : « Raisonnement avancé » / « Génération de code — Python, JS, SQL » /
  « Rédaction intelligente » / « Mémoire contextuelle »
- Après : « Score de confiance » / « Fiches par niveau » / « Mode quiz » /
  « Suggestions liées »

**Appel à l'action final**
- Avant : « Créer un compte gratuit → »
- Après : « Ouvrir le chat → » (le chat ne requiert pas de compte)

---

## 6. Imagerie

### Style

- **Fond :** toujours sombre (`#0A0A0A`). Aucune image ne doit introduire de
  grande zone claire dans la page.
- **Trait :** fin, blanc, géométrique — cohérent avec le serpent du logo.
- **Grille :** le hero utilise une trame SVG (pas 40px et 160px, blanc à 7 % et
  12 % d'opacité, plus une diagonale à 30° à 4 %), estompée au centre par un
  dégradé radial. C'est le motif de fond de la marque.
- **Lueur :** dégradé radial blanc à 4 % en haut de page. Discret par principe.

### Icônes

L'interface utilise des **glyphes typographiques**, pas une bibliothèque
d'icônes : `✦` `{ }` `✍` `◈` pour les fonctionnalités, `1` `2` `3` pour les
étapes. Les rares SVG (envoi, fournisseurs OAuth) sont inline.

Conserver cette approche : un glyphe ou un chiffre plutôt qu'une icône dessinée.
Elle coûte zéro octet et supporte la typographie de la marque.

### Interdits visuels

| À éviter | Raison |
|---|---|
| Photos en fond clair | Rompent le fond encre |
| Dégradés colorés, néon | La marque est achromatique |
| Icônes multicolores | Seules exceptions : les logos OAuth (Google, Yahoo), qui doivent garder leurs couleurs officielles |
| Ombres portées | Absentes de toute la feuille de style ; l'élévation passe par les filets 0.5px |
| Coins très arrondis (> 16px) | L'échelle de rayon s'arrête à 20px (pilules) |

### Consigne pour la génération d'images

```
Minimal monochrome illustration on a near-black background (#0A0A0A).
Thin white line work, 1px strokes, geometric and precise. No color except a
single mint-green accent (#4ADE80) if a status or highlight is needed. Subtle
white grid pattern at 7% opacity. No shadows, no gradients other than a faint
radial glow. Calm, technical, editorial. Generous negative space.
```

---

## 7. Composants

### Boutons

| Type | Fond | Texte | Bordure | Rayon |
|------|------|-------|---------|-------|
| Primaire | #FFFFFF | #000000 | aucune | 8px |
| Primaire (survol) | #DDDDDD | #000000 | aucune | 8px |
| Secondaire | transparent | #AAAAAA | 0.5px #333333 | 8px |
| Secondaire (survol) | transparent | #FFFFFF | 0.5px #666666 | 8px |

L'inversion totale du bouton primaire (blanc plein sur page noire) est le geste
d'appel à l'action de la marque. Un seul par écran.

### Bulles de conversation

| Rôle | Fond | Texte | Rayon |
|------|------|-------|-------|
| Utilisateur | #1E1E1E | #DDDDDD | 14px 14px 2px 14px |
| ChatPy | #FFFFFF | #111111 | 14px 14px 14px 2px |

Le coin de 2px pointe vers l'émetteur. **La bulle du bot est claire, celle de
l'utilisateur sombre** — l'inverse de la convention courante ; c'est délibéré :
la réponse est le contenu, elle porte le contraste maximal.

### Rayons de bordure

| Élément | Rayon |
|---------|-------|
| Boutons, champs | 8px |
| Cartes | 12px |
| Bulles de chat | 14px (avec un coin à 2px) |
| Pilules, badges, pastilles | 20px / 50% |

### Filets

**0.5px, jamais 1px.** `#2A2A2A` sur fond de page, `#333333` sur les surfaces.
C'est le détail le plus systématique de la feuille de style (15 occurrences) et
la principale source de la finesse perçue de l'interface.

### Bloc de tokens prêt à l'emploi

À coller dans le `:root` de `style.css` si l'équipe adopte les tokens couleur
(voir §8 — non appliqué à ce jour) :

```css
:root {
  /* Fonds */
  --ink-950: #0a0a0a;   /* page */
  --ink-900: #0d0d0d;   /* nav */
  --ink-850: #111111;
  --surface-800: #161616;
  --surface-700: #1a1a1a; /* cartes */
  --surface-650: #1e1e1e; /* bulle utilisateur */

  /* Filets */
  --border-600: #2a2a2a;
  --border-500: #333333;

  /* Texte */
  --text-0: #ffffff;
  --text-100: #f0f0f0;
  --muted-250: #aaaaaa;
  --muted-300: #8a8a8a;
  --muted-350: #666666;
  --muted-400: #555555;

  /* Sémantique */
  --signal-green: #4ade80;
  --success-fg: #166534;
  --success-bg: #dcfce7;
  --warning-fg: #92400e;
  --warning-bg: #fef3c7;
}
```

---

## 8. Écarts constatés

Relevés lors de cet audit, classés du plus au moins conséquent. **Aucun n'est
corrigé par ce document.**

### 8.1 La landing page vend un autre produit — critique

`Index.html` annonce « L'IA qui comprend vraiment vos besoins », un assistant qui
aide à « penser, écrire, coder et créer », avec « Raisonnement avancé »,
« Génération de code Python, JS, SQL », « Rédaction intelligente » et « Mémoire
contextuelle ».

Le produit livré est une FAQ Python francophone à correspondance floue, sans
modèle de langage. Aucune des quatre fonctionnalités annoncées n'existe. Les
vraies forces — score de confiance, fiches par niveau, quiz, journal des
lacunes — ne sont mentionnées nulle part.

C'est un problème de marque avant d'être un problème de code : la première
impression promet ce que la première conversation dément. Réécritures en §5.

### 8.2 Statistiques invérifiables — critique

`Index.html:95-99` affiche « 98 % Satisfaction », « 2M+ Conversations »,
« 0.3s Temps de réponse ». Rien dans le produit ne mesure ces valeurs ;
l'historique est un unique fichier local partagé. Ce sont des chiffres
d'espace réservé restés en place.

Options : les retirer, ou les remplacer par des compteurs réels et vérifiables
(nombre d'entrées FAQ, de concepts, de questions de quiz).

### 8.3 Le logo n'existe qu'en PNG opaque — important

Un seul fichier, 1024×1024, 228 Ko, sans transparence :
- **228 Ko pour un rendu de 54px** — le poids dominant de la page.
- **Fond noir cuit** : le logo ne peut pas être posé sur un fond clair, ce qui
  interdit tout support imprimé, e-mail clair, ou favicon sur onglet clair.
- **Aucune variante icône** : à 44px, la baseline « AI Python Explainer » est
  illisible mais toujours rendue.

À produire : un SVG monochrome transparent, une variante icône sans baseline, et
des PNG dimensionnés (32/64/128) pour les favicons.

### 8.4 Casse du nom de fichier du logo — mineur

`ChatPY_logo.PNG` contredit la casse de la marque (« ChatPy »). Le fichier est
référencé dans `Index.html`, `chat.html` et l'allow-list `FICHIERS_PUBLICS`
d'`app.py:26` — un renommage doit toucher les trois, sans quoi l'asset renvoie
un 404.

### 8.5 Rupture de vouvoiement — mineur

`ia_en_python.py:447` : « 👋 Au revoir ! **Continue** à apprendre Python le plus
possible ! » — seule réponse du bot à tutoyer. Toutes les autres vouvoient.
Correction : « Continuez à apprendre Python. »

### 8.6 Contraste du texte gris sous le seuil AA — important

`#555555` sur `#0A0A0A` donne 2.66:1, très en dessous du minimum AA de 4.5:1 —
et même du seuil de 3:1 réservé au grand texte. Concerne les libellés de section
(12px), le logo du footer (15px) et le statut du chat (11px). `#666666` (3.45:1)
échoue aussi en texte normal. Remonter ces deux teintes à `#AAAAAA` (8.52:1)
règle le problème sans changer l'aspect général de la page.

### 8.7 Les couleurs n'ont aucune source de vérité dans le code — important

`style.css` définit trois tokens de police et **zéro token de couleur** :
**165 valeurs hex écrites en dur, pour 40 teintes distinctes** — `#fff` 23 fois,
`#2a2a2a` 15 fois, `#1a1a1a` 14 fois. Changer la teinte des filets suppose
aujourd'hui 15 modifications manuelles, sans filet de sécurité.

Le bloc `:root` de §7 est prêt à être collé ; l'adoption suppose de remplacer les
occurrences littérales, ce qui touche l'ensemble de la feuille de style et
demande une relecture visuelle. À planifier séparément.

### 8.8 Dépendance réseau pour Fraunces — à surveiller

Le reste du projet revendique zéro dépendance externe (stdlib pure côté CLI), et
sans-serif/mono sont des piles système. Fraunces est chargée depuis Google Fonts
par `Index.html:8-10` et `chat.html:8-10` : hors ligne ou derrière un filtre, la
signature typographique de la marque disparaît au profit du repli Palatino, et
deux `preconnect` externes partent à chaque visite. Auto-héberger le fichier
woff2 (une seule graisse variable suffit) supprimerait le point de défaillance —
au prix d'une entrée de plus dans `FICHIERS_PUBLICS`.

---

## Journal des versions

| Version | Date | Changements |
|---------|------|-------------|
| 1.0 | 2026-08-10 | Charte initiale, extraite du code existant ; 8 écarts relevés |
