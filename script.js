const conversations = [
    {
      user: "Peux-tu m'expliquer comment fonctionne une API REST ?",
      ai: "Bien sûr ! Une API REST permet à deux applications de communiquer via HTTP. Tu envoies une requête (GET, POST, PUT…) à une URL, et le serveur te renvoie une réponse en JSON. C'est la base du web moderne. ✦"
    },
    {
      user: "Génère-moi un script Python pour lire un fichier CSV.",
      ai: "Voici un exemple simple avec pandas : import pandas as pd — df = pd.read_csv('fichier.csv') — print(df.head()). Rapide, lisible, et facile à adapter à ton projet !"
    },
    {
      user: "Comment améliorer les performances de mon site web ?",
      ai: "Plusieurs pistes : compresse tes images, minifie tes fichiers CSS/JS, active le cache navigateur, et utilise un CDN. Ces optimisations peuvent diviser ton temps de chargement par 2 ou 3. ⚡"
    },
    {
      user: "Aide-moi à rédiger un email professionnel pour un client.",
      ai: "Avec plaisir ! Commence par un contexte clair, exprime ta demande de façon concise, et termine par une invitation à l'action. Dis-moi le sujet et je t'écris un brouillon complet en quelques secondes."
    }
  ];
  
  let currentConv = 0;
  const chatBody = document.getElementById('chatBody');
const inputText = document.getElementById('inputText');
const sendBtn = document.getElementById('sendBtn');
const chatPreview = document.querySelector('.chat-preview');

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function addRow(type, content, isTyping) {
    const row = document.createElement('div');
    row.className = 'msg-row ' + (type === 'user' ? 'user-row' : '');
  
    const avatar = document.createElement('div');
    avatar.className = 'msg-mini-avatar ' + (type === 'user' ? 'avatar-user' : 'avatar-ai');
    avatar.textContent = type === 'user' ? 'U' : 'CP';
  
    const bubble = document.createElement('div');
  
    if (isTyping) {
      bubble.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';
    } else {
      bubble.className = 'msg ' + (type === 'user' ? 'msg-user' : 'msg-ai');
      bubble.textContent = '';
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
  
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { row.classList.add('visible'); });
    });
  
    return { row, bubble };
  }
  
  async function typeInInput(text) {
    inputText.textContent = '';
    const chars = text.split('');
    for (let i = 0; i < chars.length; i++) {
      inputText.textContent += chars[i];
      await sleep(38 + Math.random() * 30);
    }
  }
  
  async function typeInBubble(bubble, text) {
    bubble.textContent = '';
    const cursor = document.createElement('span');
    cursor.className = 'cursor';
    bubble.appendChild(cursor);
    const chars = text.split('');
    for (let i = 0; i < chars.length; i++) {
      bubble.insertBefore(document.createTextNode(chars[i]), cursor);
      chatBody.scrollTop = chatBody.scrollHeight;
      await sleep(18 + Math.random() * 20);
    }
    cursor.remove();
  }
  
  async function runConversation() {
    const conv = conversations[currentConv % conversations.length];
    currentConv++;
  
    await typeInInput(conv.user);
    await sleep(300);
  
    sendBtn.classList.add('active');
    await sleep(200);
    sendBtn.classList.remove('active');
    inputText.textContent = '';
  
    const { bubble: userBubble } = addRow('user', conv.user, false);
    userBubble.className = 'msg msg-user';
    userBubble.textContent = conv.user;
  
    await sleep(600);
  
    const { row: typingRow, bubble: typingBubble } = addRow('ai', '', true);
    await sleep(1400 + Math.random() * 600);
  
    typingRow.remove();
  
    const { bubble: aiBubble } = addRow('ai', '', false);
    aiBubble.className = 'msg msg-ai';
    await typeInBubble(aiBubble, conv.ai);
  
    await sleep(3200);
  
    const allRows = chatBody.querySelectorAll('.msg-row');
    for (const r of allRows) {
      r.style.transition = 'opacity 0.5s ease';
      r.style.opacity = '0';
    }
    await sleep(600);
    chatBody.innerHTML = '';
  
    await sleep(800);
    runConversation();
  }
  
  setTimeout(runConversation, 800);

function scrollToTarget(selector) {
  const element = document.querySelector(selector);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

document.querySelectorAll('.nav-links a').forEach((link) => {
  link.addEventListener('click', (event) => {
    const target = link.getAttribute('href');
    if (!target || !target.startsWith('#')) return;
    event.preventDefault();
    scrollToTarget(target);
  });
});

document.querySelectorAll('[data-action="start"]').forEach((button) => {
  button.addEventListener('click', () => {
    scrollToTarget('#tarifs');
  });
});

document.querySelectorAll('[data-action="demo"]').forEach((button) => {
  button.addEventListener('click', () => {
    if (!chatPreview) return;
    chatPreview.scrollIntoView({ behavior: 'smooth', block: 'center' });
    chatPreview.animate(
      [
        { boxShadow: '0 0 0 rgba(255,255,255,0)' },
        { boxShadow: '0 0 0 3px rgba(255,255,255,0.25)' },
        { boxShadow: '0 0 0 rgba(255,255,255,0)' }
      ],
      { duration: 900, easing: 'ease-out' }
    );
  });
});