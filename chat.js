const chatBody = document.getElementById('chatBody');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const quizBadge = document.getElementById('quizBadge');
const chatTitre = document.getElementById('chatTitre');

// Panneau d'historique
const chatLayout = document.getElementById('chatLayout');
const historiqueListe = document.getElementById('historiqueListe');
const historiqueNote = document.getElementById('historiqueNote');
const historiqueBascule = document.getElementById('historiqueBascule');
const historiqueVoile = document.getElementById('historiqueVoile');
const nouvelleBtn = document.getElementById('nouvelleBtn');
const rechercheInput = document.getElementById('rechercheInput');

// Ancienne clé du temps où une seule conversation était conservée. Plus jamais
// écrite : initialiser() la reverse dans l'historique, puis l'efface.
const ANCIENNE_CLE = 'chatpy.conversation.v1';
// Historique des visiteurs non connectés, dans leur navigateur.
const CLE_LOCALE = 'chatpy.conversations.v2';
// Panneau ouvert ou replié, sur grand écran.
const CLE_PANNEAU = 'chatpy.historique.ouvert';

// L'écran d'accueil est retiré du DOM au premier message ; on garde son HTML
// de départ pour pouvoir le réafficher lors d'une nouvelle conversation. Il est
// recapturé après personnalisation, pour que « Nouvelle conversation » réaffiche
// bien le prénom et non le « Bonjour 👋 » anonyme du gabarit.
let welcomeHTML = chatBody.innerHTML;

let quizActif = false;
// Identité du compte connecté, renseignée par initialiser(). Sert à l'avatar
// des bulles ; tant qu'elle est vide, on affiche le portrait générique.
let moiCompte = { connecte: false };

// Conversation affichée : { id, titre, cree, maj, quiz_actif, messages[] }.
// Elle vit en mémoire et n'est écrite qu'après chaque échange.
let conversation = null;
// Implémentation de stockage retenue à l'initialisation (serveur ou navigateur).
let magasin = null;

// ---------------------------------------------------------------------------
// Rendu des réponses
//
// Le bot renvoie du texte brut structuré par des marqueurs stables, générés
// par le backend (voir chatbot_response / _formater_concept) :
//   ✓ …            réponse FAQ (préfixe décoratif, retiré)
//   Exemple :      introduit un bloc de code
//   ━━ 🟢 …        en-tête de niveau, suivi d'un bloc de code
//   • …            puce de liste
//   ⚠️ / ℹ️ / 💡    notes ; 📖 titre ; 📚 sous-titre
//   💡 Confiance: N%   score de confiance
// On construit du DOM (jamais d'innerHTML à partir du texte) : aucune
// injection possible, et tout contenu non reconnu retombe en paragraphe.
// ---------------------------------------------------------------------------

const RE_CONFIANCE = /^\s*💡\s*Confiance\s*:\s*(\d+)\s*%/;

function el(tag, className, texte) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (texte != null) node.textContent = texte;
  return node;
}

// Un bloc de code, doublé d'un bouton « Copier » : sur un site qui enseigne
// Python, récupérer l'extrait est le geste le plus fréquent après l'avoir lu.
// Le clic est traité par délégation (voir plus bas), pour que les blocs restaurés
// depuis localStorage soient actifs eux aussi.
function blocCode(texte) {
  const wrap = el('div', 'code-block');
  wrap.appendChild(el('pre', null, texte));
  const btn = el('button', 'code-copy', 'Copier');
  btn.type = 'button';
  wrap.appendChild(btn);
  return wrap;
}

function estPuce(l) { return /^\s*•\s+/.test(l); }
function estNiveau(l) { return l.startsWith('━━'); }
function estExemple(l) { return /(^|\s)Exemple\s*:/.test(l); }
function estNote(l) { return /^\s*(⚠️|ℹ️|📖|📚|💡)/.test(l); }
// Frontière : une ligne qui clôt un bloc de code ou de prose en cours.
function estFrontiere(l) {
  return l.trim() === '' || estPuce(l) || estNiveau(l) || estNote(l);
}

function renderAI(text) {
  const frag = document.createDocumentFragment();
  const lignes = text.split('\n');
  let i = 0;

  // Le « ✓ » décoratif fait doublon avec l'avatar du bot : on le retire.
  if (lignes.length && lignes[0].startsWith('✓ ')) {
    lignes[0] = lignes[0].slice(2);
  }

  // Collecte un bloc de code et l'ajoute au fragment.
  //   mode 'niveau' : échantillon riche d'une section « ━━ », qui peut contenir
  //     des lignes vides internes ; on ne s'arrête qu'au niveau/note suivant.
  //   mode 'exemple' : court extrait après « Exemple : », borné par la 1re ligne vide.
  function collecterCode(mode) {
    const code = [];
    while (i < lignes.length) {
      const l = lignes[i];
      if (mode === 'niveau') {
        if (estNiveau(l) || estNote(l)) break;
      } else if (l.trim() === '' || estFrontiere(l) || estExemple(l)) {
        break;
      }
      code.push(l);
      i++;
    }
    // Retire les lignes vides en tête et en fin (séparateurs de sections).
    while (code.length && code[0].trim() === '') code.shift();
    while (code.length && code[code.length - 1].trim() === '') code.pop();
    if (code.length) frag.appendChild(blocCode(code.join('\n')));
  }

  while (i < lignes.length) {
    const ligne = lignes[i];

    if (ligne.trim() === '') {
      i++;
      continue;
    }

    const conf = ligne.match(RE_CONFIANCE);
    if (conf) {
      const score = parseInt(conf[1], 10);
      const niveau = score >= 70 ? 'msg-badge--haut' : 'msg-badge--bas';
      frag.appendChild(el('span', 'msg-badge ' + niveau, 'Confiance ' + score + '%'));
      i++;
      continue;
    }

    if (estNiveau(ligne)) {
      frag.appendChild(el('div', 'msg-level', ligne.replace(/^━━\s*/, '')));
      i++;
      collecterCode('niveau');
      continue;
    }

    if (estExemple(ligne)) {
      // « Exemple : » peut porter du code sur la même ligne ou être seul.
      const suffixe = ligne.replace(/^.*?Exemple\s*:\s*/, '');
      i++;
      if (suffixe.trim() !== '') {
        frag.appendChild(blocCode(suffixe));
      }
      collecterCode('exemple');
      continue;
    }

    if (estPuce(ligne)) {
      const liste = el('ul', 'msg-list');
      while (i < lignes.length && estPuce(lignes[i])) {
        liste.appendChild(el('li', null, lignes[i].replace(/^\s*•\s+/, '')));
        i++;
      }
      frag.appendChild(liste);
      continue;
    }

    if (/^\s*📖/.test(ligne)) {
      frag.appendChild(el('div', 'msg-title', ligne.replace(/^\s*📖\s*/, '')));
      i++;
      continue;
    }

    if (estNote(ligne)) {
      frag.appendChild(el('div', 'msg-note', ligne.trim()));
      i++;
      continue;
    }

    // Paragraphe de prose : lignes consécutives jusqu'à une frontière.
    const prose = [];
    while (i < lignes.length && lignes[i].trim() !== '' && !estFrontiere(lignes[i]) && !estExemple(lignes[i])) {
      prose.push(lignes[i]);
      i++;
    }
    if (prose.length) {
      const p = el('p');
      const texte = prose.join('\n');
      // Met en valeur le libellé « Définition : » des fiches concept.
      const label = texte.match(/^(Définition\s*:)\s*/);
      if (label) {
        p.appendChild(el('strong', null, label[1]));
        p.appendChild(document.createTextNode(' ' + texte.slice(label[0].length)));
      } else {
        p.textContent = texte;
      }
      frag.appendChild(p);
    }
  }

  return frag;
}

// ---------------------------------------------------------------------------
// Affichage
// ---------------------------------------------------------------------------

// Suggestions de suivi en boutons : le backend les renvoie à part du texte
// (champ `suggestions`) précisément pour éviter la liste numérotée que
// l'utilisateur devrait recopier à la main.
function blocSuggestions(suggestions, titre) {
  const bloc = el('div', 'msg-suggest');
  if (titre) bloc.appendChild(el('div', 'msg-suggest-title', titre));
  const chips = el('div', 'msg-suggest-chips');
  for (const s of suggestions) {
    const chip = el('button', 'chat-chip chat-chip--sm', s);
    chip.type = 'button';
    chip.dataset.send = s;
    chips.appendChild(chip);
  }
  bloc.appendChild(chips);
  return bloc;
}

// Un pouce vers le bas est la seule façon de repérer une réponse trouvée mais
// mauvaise : le journal des lacunes, lui, ne voit que les échecs complets.
function blocFeedback(question) {
  const bloc = el('div', 'msg-feedback');
  bloc.dataset.question = question;
  bloc.appendChild(el('span', 'msg-feedback-label', 'Cette réponse vous a-t-elle aidé ?'));
  for (const [utile, emoji, libelle] of [['1', '👍', 'Réponse utile'],
                                         ['0', '👎', 'Réponse inutile']]) {
    const btn = el('button', 'msg-feedback-btn', emoji);
    btn.type = 'button';
    btn.dataset.utile = utile;
    btn.setAttribute('aria-label', libelle);
    bloc.appendChild(btn);
  }
  return bloc;
}

function masquerAccueil() {
  const chatWelcome = document.getElementById('chatWelcome');
  if (!chatWelcome || !chatWelcome.isConnected) return;
  chatWelcome.classList.add('hiding');
  setTimeout(() => chatWelcome.remove(), 300);
}

// ---------------------------------------------------------------------------
// Avatars des bulles
// ---------------------------------------------------------------------------

function avatarBot() {
  const img = el('img');
  img.src = 'ChatPY_logo.PNG';
  img.alt = 'ChatPy';
  img.width = 36;
  img.height = 36;
  img.decoding = 'async';
  return img;
}

function initialeCompte() {
  // Repli quand le compte n'a pas de photo, ou que le fournisseur refuse de la
  // servir : une pastille à l'initiale vaut mieux qu'une image cassée.
  const pastille = el('span', null, (moiCompte.nom || '?').trim().charAt(0).toUpperCase() || '?');
  pastille.setAttribute('aria-hidden', 'true');
  return pastille;
}

function avatarUtilisateur() {
  if (!moiCompte.connecte) {
    // Personne de connecté : le portrait de démonstration, comme avant.
    const generique = el('img');
    generique.src = 'perso.JPG';
    generique.alt = 'Utilisateur';
    generique.width = 36;
    generique.height = 36;
    generique.decoding = 'async';
    return generique;
  }

  if (!moiCompte.photo) return initialeCompte();

  const photo = el('img', 'avatar-compte');
  photo.alt = '';
  photo.width = 36;
  photo.height = 36;
  photo.decoding = 'async';
  // Sans ça, le CDN de Google (et celui de GitHub) reçoit notre origine en
  // Referer et répond une erreur au lieu de l'image : l'avatar s'affiche cassé.
  photo.referrerPolicy = 'no-referrer';
  photo.addEventListener('error', () => photo.replaceWith(initialeCompte()));
  photo.src = moiCompte.photo;
  return photo;
}

// `extras` (réponses du bot uniquement) : { suggestions, titre, question }.
// `question` est le message qui a produit la réponse — c'est lui qu'un pouce
// vers le bas signale au serveur, pas la réponse.
function addRow(type, text, isTyping, animate = true, extras = null) {
  const row = document.createElement('div');
  row.className = 'msg-row ' + (type === 'user' ? 'user-row' : '');

  const avatar = document.createElement('div');
  avatar.className = 'msg-mini-avatar ' + (type === 'user' ? 'avatar-user' : 'avatar-ai');
  avatar.appendChild(type === 'user' ? avatarUtilisateur() : avatarBot());

  const bubble = document.createElement('div');
  if (isTyping) {
    bubble.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
  } else {
    bubble.className = 'msg ' + (type === 'user' ? 'msg-user' : 'msg-ai');
    if (type === 'user') {
      bubble.textContent = text;
    } else {
      bubble.appendChild(renderAI(text));
      if (extras && extras.suggestions && extras.suggestions.length) {
        bubble.appendChild(blocSuggestions(extras.suggestions, extras.titre));
      }
      if (extras && extras.question) {
        bubble.appendChild(blocFeedback(extras.question));
      }
    }
  }

  if (type === 'user') {
    row.appendChild(bubble);
    row.appendChild(avatar);
  } else {
    row.appendChild(avatar);
    row.appendChild(bubble);
  }

  chatBody.appendChild(row);
  chatBody.scrollTop = chatBody.scrollHeight;
  if (animate) {
    requestAnimationFrame(() => requestAnimationFrame(() => row.classList.add('visible')));
  } else {
    row.classList.add('visible');
  }
  return row;
}

function majQuizUI() {
  quizBadge.hidden = !quizActif;
  chatInput.placeholder = quizActif
    ? 'Votre réponse… (tapez « fin » pour arrêter)'
    : 'Posez une question sur Python…';
}

// ---------------------------------------------------------------------------
// Magasin de conversations
//
// Deux implémentations derrière une même interface : le serveur pour un compte
// connecté (l'historique suit alors d'un appareil à l'autre), le localStorage
// sinon — sans compte, il n'existe aucun endroit stable où ranger quoi que ce
// soit côté serveur. Les deux sont asynchrones, y compris la locale, pour que
// le reste du fichier n'ait jamais à savoir laquelle est active.
//
//   lister(recherche)  → [{ id, titre, maj, nb_messages }], plus récente en tête
//   obtenir(id)        → conversation complète, ou null
//   enregistrer(conv)  → résumé, ou null si l'écriture a échoué
//   renommer(id, titre)→ booléen
//   supprimer(id)      → booléen
// ---------------------------------------------------------------------------

function nouvelIdentifiant() {
  // Horodatage pour l'ordre naturel, suffixe aléatoire contre la collision
  // entre deux onglets ouverts la même milliseconde.
  return 'c' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
}

function resumeDe(conv) {
  return {
    id: conv.id,
    titre: conv.titre,
    maj: conv.maj || Date.now(),
    nb_messages: conv.messages.length
  };
}

const magasinServeur = {
  async lister(recherche) {
    const url = '/api/conversations' + (recherche ? '?q=' + encodeURIComponent(recherche) : '');
    const reponse = await fetch(url);
    if (!reponse.ok) return [];
    return (await reponse.json()).conversations || [];
  },
  async obtenir(id) {
    const reponse = await fetch('/api/conversations/' + encodeURIComponent(id));
    return reponse.ok ? reponse.json() : null;
  },
  async enregistrer(conv) {
    const reponse = await fetch('/api/conversations/' + encodeURIComponent(conv.id), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(conv)
    });
    return reponse.ok ? reponse.json() : null;
  },
  async renommer(id, titre) {
    const reponse = await fetch('/api/conversations/' + encodeURIComponent(id), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titre })
    });
    return reponse.ok;
  },
  async supprimer(id) {
    const reponse = await fetch('/api/conversations/' + encodeURIComponent(id), { method: 'DELETE' });
    return reponse.ok;
  }
};

// Plafond local, bien plus bas que côté serveur : le quota de localStorage
// tourne autour de 5 Mo pour *tout* le domaine.
const MAX_CONVERSATIONS_LOCALES = 30;

function lireLocal() {
  try {
    const donnees = JSON.parse(localStorage.getItem(CLE_LOCALE));
    return Array.isArray(donnees) ? donnees : [];
  } catch (e) {
    return [];
  }
}

function ecrireLocal(liste) {
  try {
    localStorage.setItem(CLE_LOCALE, JSON.stringify(liste));
    return true;
  } catch (e) {
    // Quota dépassé : on sacrifie les plus anciennes plutôt que de perdre celle
    // en cours, la seule que l'utilisateur ait sous les yeux.
    try {
      localStorage.setItem(CLE_LOCALE, JSON.stringify(liste.slice(0, 5)));
      return true;
    } catch (e2) {
      return false;
    }
  }
}

// Les diacritiques que NFD vient de détacher (bloc « Combining Diacritical
// Marks »). Le motif est construit depuis une chaîne ASCII plutôt qu'écrit en
// littéral /[…]/ : ces caractères sont invisibles dans un éditeur, et un
// copier-coller malheureux les remplacerait sans que rien ne le signale.
const DIACRITIQUES = new RegExp('[\\u0300-\\u036f]', 'g');

function normaliser(texte) {
  // Même intention que normaliser_texte côté serveur : une recherche ne doit
  // dépendre ni de la casse ni des accents.
  return (texte || '').toLowerCase().normalize('NFD').replace(DIACRITIQUES, '');
}

const magasinLocal = {
  async lister(recherche) {
    const q = normaliser(recherche);
    return lireLocal()
      .filter((c) => !q
        || normaliser(c.titre).includes(q)
        || c.messages.some((m) => normaliser(m.text).includes(q)))
      .sort((a, b) => (b.maj || 0) - (a.maj || 0))
      .map(resumeDe);
  },
  async obtenir(id) {
    return lireLocal().find((c) => c.id === id) || null;
  },
  async enregistrer(conv) {
    const enregistree = { ...conv, maj: Date.now() };
    const liste = lireLocal().filter((c) => c.id !== conv.id);
    liste.push(enregistree);
    liste.sort((a, b) => (b.maj || 0) - (a.maj || 0));
    return ecrireLocal(liste.slice(0, MAX_CONVERSATIONS_LOCALES)) ? resumeDe(enregistree) : null;
  },
  async renommer(id, titre) {
    const liste = lireLocal();
    const cible = liste.find((c) => c.id === id);
    if (!cible) return false;
    cible.titre = titre;
    return ecrireLocal(liste);
  },
  async supprimer(id) {
    const liste = lireLocal();
    const restantes = liste.filter((c) => c.id !== id);
    if (restantes.length === liste.length) return false;
    return ecrireLocal(restantes);
  }
};

// ---------------------------------------------------------------------------
// Conversation courante
// ---------------------------------------------------------------------------

function conversationVide() {
  return {
    id: nouvelIdentifiant(),
    titre: '',
    cree: Date.now(),
    maj: Date.now(),
    quiz_actif: false,
    messages: []
  };
}

function titreDeduit(conv) {
  const premiere = conv.messages.find((m) => m.type === 'user');
  if (!premiere) return 'Nouvelle conversation';
  return premiere.text.replace(/\s+/g, ' ').trim().slice(0, 80) || 'Nouvelle conversation';
}

function majTitreEntete() {
  chatTitre.textContent = conversation && conversation.messages.length
    ? (conversation.titre || titreDeduit(conversation))
    : 'ChatPy';
}

// L'enregistrement est différé : un échange, c'est un message envoyé puis une
// réponse reçue à une seconde d'intervalle. Écrire à chaque fois enverrait deux
// requêtes là où une seule, après la réponse, suffit.
let minuteurEnregistrement = null;
// Vrai dès qu'un message a été ajouté depuis le dernier enregistrement. Sans ce
// drapeau, changer de conversation la réécrirait telle quelle : « maj » serait
// repoussée et la liste finirait triée par dernière *ouverture* au lieu de
// dernière *utilisation*, ce qui remonterait en tête ce qu'on ne fait que
// consulter.
let modifie = false;

function planifierEnregistrement() {
  if (minuteurEnregistrement) clearTimeout(minuteurEnregistrement);
  minuteurEnregistrement = setTimeout(enregistrerMaintenant, 400);
}

async function enregistrerMaintenant() {
  if (minuteurEnregistrement) {
    clearTimeout(minuteurEnregistrement);
    minuteurEnregistrement = null;
  }
  if (!modifie || !conversation || conversation.messages.length === 0) return;

  conversation.titre = conversation.titre || titreDeduit(conversation);
  conversation.quiz_actif = quizActif;

  const resume = await magasin.enregistrer(conversation);
  if (!resume) {
    historiqueNote.textContent = "⚠ La dernière conversation n'a pas pu être enregistrée.";
    return;
  }
  conversation.maj = resume.maj;
  modifie = false;
  await rafraichirListe();
}

function ajouterMessage(type, text, extras = null) {
  if (!conversation) conversation = conversationVide();
  conversation.messages.push(extras ? { type, text, extras } : { type, text });
  modifie = true;
  planifierEnregistrement();
}

/**
 * Remplace le fil affiché.
 * `restaurerQuiz` n'est vrai qu'au tout premier chargement : l'état du quiz vit
 * dans le cookie de session du serveur, pas dans la conversation. Le restaurer
 * en changeant de conversation ferait croire à un quiz que le serveur ignore.
 */
function afficherConversation(conv, restaurerQuiz = false) {
  conversation = conv;
  modifie = false;
  quizActif = restaurerQuiz ? Boolean(conv.quiz_actif) : false;

  if (conv.messages.length === 0) {
    chatBody.innerHTML = welcomeHTML;
  } else {
    chatBody.replaceChildren();
    for (const m of conv.messages) {
      addRow(m.type, m.text, false, false, m.extras || null);
    }
  }

  majQuizUI();
  majTitreEntete();
  chatBody.scrollTop = chatBody.scrollHeight;
}

/** Clôt proprement un quiz en cours avant de quitter la conversation.
 *  Sans ça, le premier message de la suivante serait pris pour une réponse. */
async function terminerQuizSiBesoin() {
  if (!quizActif) return;
  try {
    await sendMessage('fin');
  } catch (e) {
    /* serveur injoignable : on change de conversation quand même */
  }
  quizActif = false;
  majQuizUI();
}

// ---------------------------------------------------------------------------
// Envoi
// ---------------------------------------------------------------------------

async function sendMessage(message) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  if (!response.ok) {
    throw new Error('Erreur serveur (' + response.status + ')');
  }
  return response.json();
}

async function envoyer(message) {
  chatInput.value = '';
  chatInput.disabled = true;
  sendBtn.disabled = true;

  masquerAccueil();
  addRow('user', message, false);
  ajouterMessage('user', message);
  // Le titre se fige sur la première question : l'en-tête doit le refléter
  // tout de suite, sans attendre l'enregistrement.
  majTitreEntete();
  const typingRow = addRow('ai', '', true);

  try {
    const data = await sendMessage(message);
    typingRow.remove();
    quizActif = Boolean(data.quiz_actif);
    majQuizUI();
    // Le serveur seul sait si la réponse vient de la FAQ ou du quiz : le message
    // qui clôt un quiz repasse quizActif à faux sans être une réponse de la FAQ.
    const extras = !data.feedback_possible ? null : {
      suggestions: data.suggestions || [],
      titre: data.titre_suggestions || '',
      question: message
    };
    addRow('ai', data.response, false, true, extras);
    ajouterMessage('ai', data.response, extras);
  } catch (err) {
    typingRow.remove();
    addRow('ai', '❌ Impossible de contacter le serveur ChatPy. Réessayez dans un instant.', false);
  } finally {
    chatInput.disabled = false;
    sendBtn.disabled = false;
    chatInput.focus();
  }
}

// ---------------------------------------------------------------------------
// Événements
// ---------------------------------------------------------------------------

chatForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (message) envoyer(message);
});

async function copierCode(btn) {
  const pre = btn.parentElement.querySelector('pre');
  if (!pre) return;
  if (btn._resetTimer) clearTimeout(btn._resetTimer);
  if (!btn.dataset.label) btn.dataset.label = btn.textContent;
  const libelle = btn.dataset.label;
  try {
    await navigator.clipboard.writeText(pre.textContent);
    btn.textContent = 'Copié';
  } catch (e) {
    // Presse-papiers refusé (contexte non sécurisé, permission) : on le dit
    // plutôt que de laisser croire à une copie réussie.
    btn.textContent = 'Échec';
  }
  btn.classList.add('code-copy--fait');
  btn._resetTimer = setTimeout(() => {
    btn.textContent = libelle;
    btn.classList.remove('code-copy--fait');
    btn._resetTimer = null;
  }, 1500);
}

async function envoyerFeedback(btn) {
  const bloc = btn.closest('.msg-feedback');
  const question = bloc.dataset.question;
  const utile = btn.dataset.utile === '1';
  // Le bloc entier est remplacé : le vote ne se rejoue pas, et le retour est
  // immédiat même si la requête échoue — rien de vital n'en dépend côté client.
  bloc.replaceWith(el('div', 'msg-feedback msg-feedback--envoye',
    utile ? '👍 Merci pour votre retour !'
          : '👎 Merci — cette question est notée pour améliorer la FAQ.'));
  try {
    await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, utile })
    });
  } catch (e) {
    /* signalement best-effort : inutile d'importuner l'utilisateur */
  }
}

// Délégation : fonctionne aussi sur l'écran d'accueil recréé après un reset,
// et sur les messages restaurés depuis localStorage.
chatBody.addEventListener('click', (event) => {
  const chip = event.target.closest('.chat-chip');
  if (chip && chip.dataset.send) {
    envoyer(chip.dataset.send);
    return;
  }

  const copie = event.target.closest('.code-copy');
  if (copie) {
    copierCode(copie);
    return;
  }

  const pouce = event.target.closest('.msg-feedback-btn');
  if (pouce) envoyerFeedback(pouce);
});

// ---------------------------------------------------------------------------
// Panneau d'historique
// ---------------------------------------------------------------------------

const ICONE_CRAYON = '<path d="M11.4 2.6a1.6 1.6 0 0 1 2.2 2.2L6.3 12l-2.8.7.7-2.8z"/>';
const ICONE_POUBELLE = '<path d="M3 4.5h10M6.4 4.5V3h3.2v1.5M4.6 4.5l.5 8.2h5.8l.5-8.2"/>';

function iconeSvg(chemin) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 16 16');
  svg.setAttribute('aria-hidden', 'true');
  // Chaîne littérale écrite ici, jamais de donnée utilisateur.
  svg.innerHTML = chemin;
  return svg;
}

// Résumés actuellement à l'écran, et renommage éventuellement en cours (son
// identifiant), pour qu'un rafraîchissement ne balaie pas la saisie.
let resumesAffiches = [];
let renommageEnCours = null;

function groupeDe(maj) {
  const jour = 86400000;
  const minuit = new Date();
  minuit.setHours(0, 0, 0, 0);
  const debut = minuit.getTime();
  if (maj >= debut) return "Aujourd'hui";
  if (maj >= debut - jour) return 'Hier';
  if (maj >= debut - 7 * jour) return '7 derniers jours';
  return 'Plus ancien';
}

function boutonAction(libelle, chemin, action) {
  const bouton = el('button', 'historique-item-action');
  bouton.type = 'button';
  bouton.title = libelle;
  bouton.setAttribute('aria-label', libelle);
  bouton.appendChild(iconeSvg(chemin));
  bouton.addEventListener('click', action);
  return bouton;
}

function elementConversation(resume) {
  const actif = conversation && resume.id === conversation.id;
  const item = el('div', 'historique-item' + (actif ? ' historique-item--actif' : ''));

  const ouvrir = el('button', 'historique-item-ouvrir', resume.titre);
  ouvrir.type = 'button';
  ouvrir.title = resume.titre;
  ouvrir.addEventListener('click', () => ouvrirConversation(resume.id));
  item.appendChild(ouvrir);

  item.appendChild(boutonAction('Renommer', ICONE_CRAYON, () => demarrerRenommage(item, resume)));
  const suppr = boutonAction('Supprimer', ICONE_POUBELLE, () => supprimerConversation(resume));
  suppr.classList.add('historique-item-action--suppr');
  item.appendChild(suppr);

  return item;
}

function rendreListe() {
  historiqueListe.replaceChildren();

  if (resumesAffiches.length === 0) {
    historiqueListe.appendChild(el('div', 'historique-vide', rechercheInput.value.trim()
      ? 'Aucune conversation ne correspond à cette recherche.'
      : 'Vos conversations apparaîtront ici au fil de vos questions.'));
    return;
  }

  let groupeCourant = null;
  let conteneur = null;
  for (const resume of resumesAffiches) {
    const groupe = groupeDe(resume.maj);
    if (groupe !== groupeCourant) {
      groupeCourant = groupe;
      conteneur = el('div', 'historique-groupe');
      conteneur.appendChild(el('div', 'historique-groupe-titre', groupe));
      historiqueListe.appendChild(conteneur);
    }
    conteneur.appendChild(elementConversation(resume));
  }
}

async function rafraichirListe() {
  // Un renommage en cours de saisie ne doit pas disparaître sous les doigts
  // parce qu'un message vient d'être enregistré.
  if (renommageEnCours) return;
  resumesAffiches = await magasin.lister(rechercheInput.value.trim());
  rendreListe();
}

async function ouvrirConversation(id) {
  if (conversation && conversation.id === id) {
    fermerSiTiroir();
    return;
  }
  // Ce qui est en cours d'écriture appartient à la conversation qu'on quitte.
  await enregistrerMaintenant();
  await terminerQuizSiBesoin();

  const conv = await magasin.obtenir(id);
  if (!conv) {
    // Supprimée depuis un autre onglet : la liste était périmée.
    await rafraichirListe();
    return;
  }
  afficherConversation(conv);
  rendreListe();
  fermerSiTiroir();
  chatInput.focus();
}

async function nouvelleConversation() {
  await enregistrerMaintenant();
  await terminerQuizSiBesoin();
  // La précédente reste dans l'historique : c'est toute la différence avec
  // l'ancien bouton, qui l'effaçait.
  afficherConversation(conversationVide());
  await rafraichirListe();
  fermerSiTiroir();
  chatInput.focus();
}

function demarrerRenommage(item, resume) {
  if (renommageEnCours) return;
  const ouvrir = item.querySelector('.historique-item-ouvrir');
  if (!ouvrir) return;

  const champ = document.createElement('input');
  champ.type = 'text';
  champ.className = 'historique-item-renommer';
  champ.value = resume.titre;
  champ.maxLength = 80;
  renommageEnCours = resume.id;

  let termine = false;
  async function finir(valider) {
    if (termine) return;
    termine = true;
    renommageEnCours = null;

    const titre = champ.value.trim();
    if (valider && titre && titre !== resume.titre && await magasin.renommer(resume.id, titre)) {
      resume.titre = titre;
      if (conversation && conversation.id === resume.id) {
        conversation.titre = titre;
        majTitreEntete();
      }
    }
    rendreListe();
  }

  champ.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') { event.preventDefault(); finir(true); }
    else if (event.key === 'Escape') { event.preventDefault(); finir(false); }
  });
  // Cliquer ailleurs vaut validation : c'est le geste le plus courant, et
  // perdre la saisie serait plus surprenant que l'enregistrer.
  champ.addEventListener('blur', () => finir(true));

  ouvrir.replaceWith(champ);
  champ.focus();
  champ.select();
}

async function supprimerConversation(resume) {
  if (!window.confirm(`Supprimer « ${resume.titre} » ?\n\nCette conversation sera définitivement perdue.`)) return;
  if (!await magasin.supprimer(resume.id)) return;

  // Si c'était celle à l'écran, on repart d'un fil vierge : laisser affichée
  // une conversation qui n'existe plus induirait en erreur au message suivant.
  if (conversation && conversation.id === resume.id) {
    await terminerQuizSiBesoin();
    afficherConversation(conversationVide());
  }
  await rafraichirListe();
}

// ── Ouverture / repli du panneau ────────────────────────────────────────────

const ecranEtroit = window.matchMedia('(max-width: 860px)');

function appliquerEtatPanneau(ouvert) {
  chatLayout.classList.toggle('chat-layout--replie', !ouvert);
  historiqueBascule.setAttribute('aria-expanded', ouvert ? 'true' : 'false');
  historiqueBascule.setAttribute('aria-label', ouvert ? "Masquer l'historique" : "Afficher l'historique");
  // Le voile n'a de sens qu'en mode tiroir, où le panneau recouvre le fil.
  historiqueVoile.hidden = !(ouvert && ecranEtroit.matches);
}

function fermerSiTiroir() {
  if (ecranEtroit.matches) appliquerEtatPanneau(false);
}

function initPanneau() {
  let ouvert = true;
  if (ecranEtroit.matches) {
    // En tiroir, ouvert par défaut masquerait la conversation à l'arrivée.
    ouvert = false;
  } else {
    try { ouvert = localStorage.getItem(CLE_PANNEAU) !== '0'; } catch (e) { /* défaut */ }
  }
  appliquerEtatPanneau(ouvert);
}

historiqueBascule.addEventListener('click', () => {
  const ouvrir = chatLayout.classList.contains('chat-layout--replie');
  appliquerEtatPanneau(ouvrir);
  // La préférence n'est retenue que sur grand écran : le tiroir doit toujours
  // repartir fermé, quel qu'ait été le dernier geste.
  if (!ecranEtroit.matches) {
    try { localStorage.setItem(CLE_PANNEAU, ouvrir ? '1' : '0'); } catch (e) { /* tant pis */ }
  }
});

historiqueVoile.addEventListener('click', () => appliquerEtatPanneau(false));
nouvelleBtn.addEventListener('click', nouvelleConversation);

// Appliqué tout de suite, sans attendre /api/moi : sur mobile, le panneau
// s'afficherait sinon en grand par-dessus la conversation le temps de la
// requête, avant de se refermer d'un coup.
initPanneau();

// Franchir la limite des 860px change la nature du panneau (colonne ou tiroir) :
// il faut repartir de l'état par défaut du nouveau mode.
if (ecranEtroit.addEventListener) ecranEtroit.addEventListener('change', initPanneau);
else if (ecranEtroit.addListener) ecranEtroit.addListener(initPanneau);

let minuteurRecherche = null;
rechercheInput.addEventListener('input', () => {
  if (minuteurRecherche) clearTimeout(minuteurRecherche);
  // Attendre une pause de frappe : sinon chaque lettre part en requête.
  minuteurRecherche = setTimeout(rafraichirListe, 220);
});

// ---------------------------------------------------------------------------
// Démarrage
//
// Rien ne s'initialise avant de savoir qui est connecté : la clé de sauvegarde
// et l'écran d'accueil en dépendent tous les deux. Charger la conversation
// d'abord puis découvrir le compte reviendrait à afficher un instant celle de
// quelqu'un d'autre.
// ---------------------------------------------------------------------------

// Identifiant fixe de la conversation reprise de l'ancien format. Fixe et non
// tiré au sort : si l'effacement de l'ancienne clé échouait, la migration
// rejouerait au chargement suivant et créerait un doublon à chaque fois.
const ID_REPRISE = 'reprise-v1';

function ancienneCle() {
  // Strictement la clé de l'identité courante. Reverser la conversation
  // anonyme d'un navigateur partagé dans le compte qui vient de s'y connecter
  // donnerait à quelqu'un les questions d'un autre.
  return moiCompte.connecte
    ? `${ANCIENNE_CLE}.${moiCompte.fournisseur}-${moiCompte.id}`
    : ANCIENNE_CLE;
}

async function migrerAncienneConversation() {
  const cle = ancienneCle();
  let donnees = null;
  try {
    donnees = JSON.parse(localStorage.getItem(cle));
  } catch (e) {
    donnees = null;
  }
  if (!donnees || !Array.isArray(donnees.messages) || donnees.messages.length === 0) {
    try { localStorage.removeItem(cle); } catch (e) { /* rien à nettoyer */ }
    return;
  }

  const reprise = conversationVide();
  reprise.id = ID_REPRISE;
  reprise.messages = donnees.messages.filter(
    (m) => m && (m.type === 'user' || m.type === 'ai') && typeof m.text === 'string'
  );
  if (reprise.messages.length === 0) return;
  reprise.titre = titreDeduit(reprise);

  if (await magasin.enregistrer(reprise)) {
    try { localStorage.removeItem(cle); } catch (e) { /* déjà migrée, tant pis */ }
  }
}

function personnaliserAccueil() {
  if (!moiCompte.connecte) return;
  const titre = chatBody.querySelector('.chat-welcome-title');
  if (!titre) return;
  const prenom = (moiCompte.nom || '').trim().split(/\s+/)[0];
  if (prenom) titre.textContent = `Bonjour ${prenom} 👋`;
}

async function initialiser(moi) {
  moiCompte = moi || { connecte: false };
  // Connecté : le serveur, et l'historique suit d'un appareil à l'autre.
  // Sinon : le navigateur, exactement comme avant l'arrivée des comptes.
  magasin = moiCompte.connecte ? magasinServeur : magasinLocal;

  personnaliserAccueil();
  // Recapturé ici et pas au chargement du script : « Nouvelle conversation »
  // doit réafficher l'accueil personnalisé, pas le gabarit anonyme.
  welcomeHTML = chatBody.innerHTML;

  historiqueNote.textContent = moiCompte.connecte
    ? 'Conversations enregistrées sur votre compte : vous les retrouverez depuis n’importe quel appareil.'
    : 'Conversations enregistrées dans ce navigateur seulement. Connectez-vous pour les retrouver ailleurs.';

  initPanneau();
  await migrerAncienneConversation();

  resumesAffiches = await magasin.lister('');
  // On rouvre la plus récente : reprendre là où on s'était arrêté est ce que
  // faisait déjà l'ancienne version, et ce qu'on attend en revenant sur la page.
  const derniere = resumesAffiches.length
    ? await magasin.obtenir(resumesAffiches[0].id)
    : null;
  afficherConversation(derniere || conversationVide(), true);
  rendreListe();

  chatInput.focus();
}

// nav-compte.js publie la requête /api/moi et absorbe ses erreurs. S'il n'a pas
// été chargé, on démarre en anonyme plutôt que d'attendre indéfiniment.
(window.ChatPyMoi || Promise.resolve({ connecte: false })).then(initialiser);
