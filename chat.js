const chatBody = document.getElementById('chatBody');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const quizBadge = document.getElementById('quizBadge');
const resetBtn = document.getElementById('resetBtn');

const STORAGE_KEY = 'chatpy.conversation.v1';
// L'écran d'accueil est retiré du DOM au premier message ; on garde son HTML
// de départ pour pouvoir le réafficher lors d'une nouvelle conversation.
const welcomeHTML = chatBody.innerHTML;

let quizActif = false;

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
    if (code.length) frag.appendChild(el('pre', null, code.join('\n')));
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
        frag.appendChild(el('pre', null, suffixe));
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

function masquerAccueil() {
  const chatWelcome = document.getElementById('chatWelcome');
  if (!chatWelcome || !chatWelcome.isConnected) return;
  chatWelcome.classList.add('hiding');
  setTimeout(() => chatWelcome.remove(), 300);
}

function addRow(type, text, isTyping, animate = true) {
  const row = document.createElement('div');
  row.className = 'msg-row ' + (type === 'user' ? 'user-row' : '');

  const avatar = document.createElement('div');
  avatar.className = 'msg-mini-avatar ' + (type === 'user' ? 'avatar-user' : 'avatar-ai');
  const img = document.createElement('img');
  img.src = type === 'user' ? 'perso.JPG' : 'ChatPY_logo.PNG';
  img.alt = type === 'user' ? 'Utilisateur' : 'ChatPy';
  img.width = 36;
  img.height = 36;
  img.decoding = 'async';
  avatar.appendChild(img);

  const bubble = document.createElement('div');
  if (isTyping) {
    bubble.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
  } else {
    bubble.className = 'msg ' + (type === 'user' ? 'msg-user' : 'msg-ai');
    if (type === 'user') {
      bubble.textContent = text;
    } else {
      bubble.appendChild(renderAI(text));
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
// Persistance (par navigateur, via localStorage)
// ---------------------------------------------------------------------------

function chargerConversation() {
  let data;
  try {
    data = JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch (e) {
    data = null;
  }
  if (!data || !Array.isArray(data.messages) || data.messages.length === 0) return;

  masquerAccueil();
  for (const m of data.messages) {
    addRow(m.type, m.text, false, false);
  }
  quizActif = Boolean(data.quizActif);
  majQuizUI();
  resetBtn.hidden = false;
}

function sauvegarderMessage(type, text) {
  let data;
  try {
    data = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch (e) {
    data = {};
  }
  if (!Array.isArray(data.messages)) data.messages = [];
  data.messages.push({ type, text });
  data.quizActif = quizActif;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (e) {
    /* quota dépassé : on ignore, la conversation reste affichée */
  }
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
  resetBtn.hidden = false;
  addRow('user', message, false);
  sauvegarderMessage('user', message);
  const typingRow = addRow('ai', '', true);

  try {
    const data = await sendMessage(message);
    typingRow.remove();
    quizActif = Boolean(data.quiz_actif);
    majQuizUI();
    addRow('ai', data.response, false);
    sauvegarderMessage('ai', data.response);
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

// Délégation : fonctionne aussi sur l'écran d'accueil recréé après un reset.
chatBody.addEventListener('click', (event) => {
  const chip = event.target.closest('.chat-chip');
  if (chip && chip.dataset.send) envoyer(chip.dataset.send);
});

resetBtn.addEventListener('click', async () => {
  // Un quiz vit côté serveur (cookie de session) : on le clôt proprement
  // avant d'effacer l'affichage, sinon le prochain message serait pris pour
  // une réponse au quiz.
  if (quizActif) {
    try { await sendMessage('fin'); } catch (e) { /* on efface quand même */ }
  }
  quizActif = false;
  localStorage.removeItem(STORAGE_KEY);
  chatBody.innerHTML = welcomeHTML;
  resetBtn.hidden = true;
  majQuizUI();
  chatInput.focus();
});

chargerConversation();
majQuizUI();
chatInput.focus();
