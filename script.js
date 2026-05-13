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
const signupModal = document.getElementById('signupModal');
const signupPanel = document.getElementById('signupPanel');
const mainContent = document.getElementById('mainContent');
let lastFocusedElement = null;
let _modalKeydownHandler = null;

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
  
  let conversationRunning = false;

async function runConversation() {
  if (conversationRunning) return;
  conversationRunning = true;
  try {
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
  } catch (e) {
    console.error('runConversation error', e);
  } finally {
    conversationRunning = false;
    // Schedule next conversation loop with a small delay to avoid stack recursion
    setTimeout(runConversation, 800);
  }
}


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

function openSignupModal() {
  if (!signupModal) return;
  // save last focused element
  lastFocusedElement = document.activeElement;

  // show modal and mark main content hidden for assistive tech
  signupModal.classList.remove('open');
  // Force reflow so staggered animation restarts every time.
  void signupModal.offsetWidth;
  signupModal.classList.add('open');
  signupModal.setAttribute('aria-hidden', 'false');
  if (mainContent) mainContent.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = 'hidden';

  // focus the first focusable control in the modal (fallback to panel)
  const focusable = signupModal.querySelectorAll('a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])');
  const focusableArr = Array.prototype.slice.call(focusable).filter(el => el.offsetParent !== null);
  if (focusableArr.length) {
    focusableArr[0].focus();
  } else if (signupPanel) {
    signupPanel.focus();
  }

  // trap focus inside modal
  _modalKeydownHandler = function(e) {
    if (e.key === 'Escape') {
      closeSignupModal();
      return;
    }
    if (e.key === 'Tab') {
      if (focusableArr.length === 0) {
        e.preventDefault();
        return;
      }
      const first = focusableArr[0];
      const last = focusableArr[focusableArr.length - 1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  };
  document.addEventListener('keydown', _modalKeydownHandler);
}

function closeSignupModal() {
  if (!signupModal) return;
  signupModal.classList.remove('open');
  signupModal.setAttribute('aria-hidden', 'true');
  if (mainContent) mainContent.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = '';
  if (_modalKeydownHandler) {
    document.removeEventListener('keydown', _modalKeydownHandler);
    _modalKeydownHandler = null;
  }
  if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
    lastFocusedElement.focus();
  }
}

document.querySelectorAll('[data-action="start"]').forEach((button) => {
  button.addEventListener('click', openSignupModal);
});

document.querySelectorAll('[data-action="close-signup"]').forEach((button) => {
  button.addEventListener('click', closeSignupModal);
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') {
    closeSignupModal();
  }
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
