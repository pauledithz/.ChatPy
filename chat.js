const chatBody = document.getElementById('chatBody');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatWelcome = document.getElementById('chatWelcome');

// L'écran d'accueil s'efface dès le premier message envoyé.
function masquerAccueil() {
  if (!chatWelcome || !chatWelcome.isConnected) return;
  chatWelcome.classList.add('hiding');
  setTimeout(() => chatWelcome.remove(), 300);
}

function addRow(type, text, isTyping) {
  const row = document.createElement('div');
  row.className = 'msg-row ' + (type === 'user' ? 'user-row' : '');

  const avatar = document.createElement('div');
  avatar.className = 'msg-mini-avatar ' + (type === 'user' ? 'avatar-user' : 'avatar-ai');
  const img = document.createElement('img');
  img.src = type === 'user' ? 'Persone professionelle.jpg' : 'ChatPY_logo.PNG';
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
    bubble.textContent = text;
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
  requestAnimationFrame(() => requestAnimationFrame(() => row.classList.add('visible')));
  return row;
}

async function sendMessage(message) {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  if (!response.ok) {
    throw new Error('Erreur serveur (' + response.status + ')');
  }
  const data = await response.json();
  return data.response;
}

chatForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  chatInput.value = '';
  chatInput.disabled = true;
  sendBtn.disabled = true;

  masquerAccueil();
  addRow('user', message, false);
  const typingRow = addRow('ai', '', true);

  try {
    const reply = await sendMessage(message);
    typingRow.remove();
    addRow('ai', reply, false);
  } catch (err) {
    typingRow.remove();
    addRow('ai', "❌ Impossible de contacter le serveur ChatPy. Réessayez dans un instant.", false);
  } finally {
    chatInput.disabled = false;
    sendBtn.disabled = false;
    chatInput.focus();
  }
});

chatInput.focus();
