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
    if (type === 'user') {
      const photo = document.createElement('img');
      photo.src = 'Persone professionelle.jpg';
      photo.alt = 'Utilisateur';
      photo.width = 36;
      photo.height = 36;
      photo.decoding = 'async';
      avatar.appendChild(photo);
    } else {
      const logo = document.createElement('img');
      logo.src = 'ChatPY_logo.PNG';
      logo.alt = 'ChatPy';
      logo.width = 36;
      logo.height = 36;
      logo.decoding = 'async';
      avatar.appendChild(logo);
    }
  
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

  // Recalculée à chaque Tab et non mise en cache à l'ouverture : basculer vers
  // l'inscription fait apparaître deux champs, qu'une liste figée ignorerait.
  function focusablesVisibles() {
    const tous = signupModal.querySelectorAll('a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])');
    return Array.prototype.slice.call(tous).filter((el) => el.offsetParent !== null);
  }

  // Le premier champ utile plutôt que la croix de fermeture : on ouvre ce
  // panneau pour s'y connecter, pas pour en sortir.
  const premier = signupModal.querySelector('#champEmail') || focusablesVisibles()[0];
  if (premier) {
    premier.focus();
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
      const focusableArr = focusablesVisibles();
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

/* Les boutons d'appel à l'action mènent au modal d'inscription… tant que
   personne n'est connecté. Une fois la session ouverte, proposer de créer un
   compte n'a plus de sens : ils deviennent une entrée vers le chat.
   Le drapeau est lu au moment du clic et non à l'abonnement, parce que
   /api/moi répond après que ces écouteurs sont posés. */
let compteConnecte = false;

document.querySelectorAll('[data-action="start"]').forEach((button) => {
  button.addEventListener('click', () => {
    if (compteConnecte) window.location.href = '/chat';
    else openSignupModal();
  });
});

function adapterAppelsALAction() {
  compteConnecte = true;
  document.querySelectorAll('[data-action="start"]').forEach((button) => {
    // Sans libellé de rechange, on laisse le texte d'origine : seul le
    // comportement change. C'est le cas du bouton de la barre de navigation,
    // que nav-compte.js remplace de toute façon par le menu du compte.
    if (button.dataset.labelConnecte) button.textContent = button.dataset.labelConnecte;
  });
}

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

setTimeout(runConversation, 800);

/* ── Retour des flows OAuth et ouverture à la demande ─────────────────────
   L'affichage du compte lui-même (avatar, menu, déconnexion) vit dans
   nav-compte.js, partagé avec /chat et /compte. Ne reste ici que ce qui est
   propre à la page d'accueil : le modal d'inscription. */

/* ── Connexion et inscription par email ───────────────────────────────────
   Le même formulaire sert aux deux : les champs propres à l'inscription (nom,
   confirmation) sont masqués par la classe form--connexion. Les deux routes
   répondent en JSON et ouvrent la session côté serveur. */

const formCompte = document.getElementById('formCompte');
const champNom = document.getElementById('champNom');
const champEmail = document.getElementById('champEmail');
const champMotDePasse = document.getElementById('champMotDePasse');
const champConfirmation = document.getElementById('champConfirmation');
const champRester = document.getElementById('champRester');
const formErreur = document.getElementById('formErreur');
const boutonSoumettre = document.getElementById('boutonSoumettre');
const lienBascule = document.getElementById('lienBascule');
const texteBascule = document.getElementById('texteBascule');
const lienOubli = document.getElementById('lienOubli');
const signupSubtitle = document.getElementById('signupSubtitle');
const signupTitle = document.getElementById('signupTitle');

let modeInscription = false;

function afficherMessage(texte, succes = false) {
  if (!formErreur) return;
  formErreur.textContent = texte;
  formErreur.classList.toggle('form-erreur--succes', succes);
  formErreur.hidden = false;
}

function effacerMessage() {
  if (formErreur) formErreur.hidden = true;
}

function appliquerMode() {
  formCompte.classList.toggle('form--connexion', !modeInscription);
  signupTitle.textContent = modeInscription ? 'Créer votre compte ChatPy' : 'Se connecter à ChatPy';
  signupSubtitle.textContent = modeInscription
    ? 'Un email et un mot de passe suffisent — aucune vérification par courriel.'
    : 'Retrouvez vos conversations et votre progression.';
  boutonSoumettre.textContent = modeInscription ? 'Créer mon compte' : 'Se connecter';
  texteBascule.textContent = modeInscription ? 'Vous avez déjà un compte ?' : "Vous n'avez pas de compte ?";
  lienBascule.textContent = modeInscription ? 'Se connecter' : "S'inscrire";
  // Le gestionnaire de mots de passe du navigateur doit savoir s'il s'agit
  // d'en proposer un nouveau ou de remplir l'existant.
  champMotDePasse.autocomplete = modeInscription ? 'new-password' : 'current-password';
  effacerMessage();
}

function basculerMode() {
  modeInscription = !modeInscription;
  appliquerMode();
  (modeInscription ? champNom : champEmail).focus();
}

if (formCompte) {
  lienBascule.addEventListener('click', basculerMode);
  lienBascule.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      basculerMode();
    }
  });

  // Il n'y a pas de réinitialisation possible : ce serveur n'envoie aucun
  // email. Le dire franchement vaut mieux qu'un lien qui ne fait rien.
  const expliquerOubli = () => afficherMessage(
    "Ce serveur n'envoie pas d'emails : il n'y a donc pas de réinitialisation "
    + 'de mot de passe. Vous pouvez créer un nouveau compte, ou vous connecter '
    + 'avec Google ou GitHub.');
  lienOubli.addEventListener('click', expliquerOubli);
  lienOubli.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      expliquerOubli();
    }
  });

  formCompte.addEventListener('submit', async (event) => {
    event.preventDefault();
    effacerMessage();

    const corps = {
      email: champEmail.value,
      mot_de_passe: champMotDePasse.value,
      rester_connecte: champRester.checked
    };
    if (modeInscription) {
      corps.nom = champNom.value;
      corps.confirmation = champConfirmation.value;
    }

    boutonSoumettre.disabled = true;
    try {
      const reponse = await fetch(modeInscription ? '/auth/inscription' : '/auth/connexion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(corps)
      });
      // Le serveur explique lui-même ce qui cloche (adresse invalide, mot de
      // passe trop court, trop de tentatives) : on relaie son message plutôt
      // que d'en inventer un moins précis.
      const donnees = await reponse.json().catch(() => ({}));
      if (!reponse.ok) {
        afficherMessage(donnees.error || "La connexion n'a pas abouti.");
        return;
      }
      // Rechargement complet plutôt qu'une mise à jour à la main : la barre de
      // navigation, les boutons d'appel à l'action et le chat se construisent
      // tous à partir de /api/moi, qu'ils réinterrogeront au chargement.
      window.location.reload();
    } catch (e) {
      afficherMessage('Serveur injoignable. Réessayez dans un instant.');
    } finally {
      boutonSoumettre.disabled = false;
    }
  });

  appliquerMode();
}

function signalerRetourOAuth() {
  // app.py redirige vers /?connexion=... après le passage chez le fournisseur.
  // Le message ne le nomme pas : les deux flows partagent ces mêmes codes.
  const etat = new URLSearchParams(window.location.search).get('connexion');
  if (!etat) return;

  if (etat === 'echec') {
    alert("La connexion a échoué ou a été annulée.");
  } else if (etat === 'email_non_verifie') {
    alert("Aucune adresse email vérifiée sur ce compte : connexion refusée.");
  }
  // Nettoie l'URL, sinon le message revient à chaque rechargement.
  window.history.replaceState({}, '', window.location.pathname);
}

function ouvrirDepuisAutrePage() {
  // Le modal n'existe que sur cette page : les liens « Se connecter » de /chat
  // et /compte y renvoient avec ?inscription=1 plutôt que de le dupliquer.
  if (new URLSearchParams(window.location.search).get('inscription') !== '1') return;
  openSignupModal();
  window.history.replaceState({}, '', window.location.pathname);
}

// nav-compte.js a déjà lancé la requête : on réutilise sa promesse au lieu
// d'interroger /api/moi une seconde fois.
if (window.ChatPyMoi) {
  window.ChatPyMoi.then((moi) => {
    if (moi.connecte) {
      closeSignupModal();
      adapterAppelsALAction();
    } else {
      ouvrirDepuisAutrePage();
    }
  });
} else {
  ouvrirDepuisAutrePage();
}

signalerRetourOAuth();
