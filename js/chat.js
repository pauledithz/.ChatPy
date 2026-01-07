const form = document.getElementById('chat-form');
const promptEl = document.getElementById('prompt');
const messagesEl = document.getElementById('messages');
const statusEl = document.getElementById('status');

function appendMessage(role, text) {
  const el = document.createElement('div');
  el.className = `message ${role}`;
  el.innerText = text;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setStatus(text) {
  statusEl.textContent = text || '';
}

async function sendToServer(message) {
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!res.ok) {
      throw new Error(`Erreur ${res.status}`);
    }

    const data = await res.json();
    return data.reply ?? data.output ?? '';
  } catch (err) {
    // fallback: réponse simulée
    return `Désolé, le serveur n'est pas disponible. Réponse simulée: ${message}`;
  }
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = promptEl.value.trim();
  if (!text) return;

  appendMessage('user', text);
  promptEl.value = '';
  promptEl.style.height = '';

  setStatus('Envoi...');
  promptEl.disabled = true;

  const reply = await sendToServer(text);

  appendMessage('bot', reply);
  setStatus('');
  promptEl.disabled = false;
  promptEl.focus();
});

// auto-resize textarea
promptEl.addEventListener('input', () => {
  promptEl.style.height = 'auto';
  promptEl.style.height = `${promptEl.scrollHeight}px`;
});

// quick welcome
appendMessage('bot', "Bonjour — je suis SawerBot. Posez une question !");
