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
// ---------------------------------------------------------------------------

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Le bot renvoie du texte brut. Les échantillons de code arrivent sur les
// lignes qui suivent un en-tête « ━━ » (niveau d'aide), jusqu'à la ligne vide
// suivante : on les regroupe dans un <pre> à chasse fixe. Le reste garde ses
// retours à la ligne grâce au white-space: pre-wrap de la bulle.
function renderAI(text) {
  const lignes = text.split('\n');
  let html = '';
  let i = 0;
  while (i < lignes.length) {
    const ligne = lignes[i];
    if (ligne.startsWith('━━')) {
      html += escapeHtml(ligne) + '\n';
      i++;
      const code = [];
      while (i < lignes.length && lignes[i].trim() !== '' && !lignes[i].startsWith('━━')) {
        code.push(lignes[i]);
        i++;
      }
      if (code.length) {
        html += '<pre>' + escapeHtml(code.join('\n')) + '</pre>';
      }
    } else {
      html += escapeHtml(ligne);
      if (i < lignes.length - 1) html += '\n';
      i++;
    }
  }
  return html;
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
      bubble.innerHTML = renderAI(text);
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
