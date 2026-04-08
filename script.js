const API_URL = 'http://localhost:5000/api';
let conversationHistory = [];
let allCategories = {};

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    setupEventListeners();
    loadQuickQuestions();
    focusInput();
});

// Setup Event Listeners
function setupEventListeners() {
    // Formulaire de chat
    document.getElementById('chatForm').addEventListener('submit', handleSendMessage);

    // Bouton nouvelle conversation
    document.getElementById('newChatBtn').addEventListener('click', startNewConversation);

    // Modal
    const modal = document.getElementById('questionsModal');
    const closeBtn = document.querySelector('.close');
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Charger les catégories
async function loadCategories() {
    try {
        const response = await fetch(`${API_URL}/questions`);
        const data = await response.json();
        allCategories = data;

        // Afficher les catégories dans la sidebar
        const categoriesList = document.getElementById('categoriesList');
        categoriesList.innerHTML = '';

        Object.keys(data).forEach(category => {
            const li = document.createElement('li');
            li.textContent = `📚 ${category}`;
            li.addEventListener('click', () => showCategory(category));
            categoriesList.appendChild(li);
        });

        // Ajouter option "Voir toutes les questions"
        const allQuestionsLi = document.createElement('li');
        allQuestionsLi.textContent = '📋 Toutes les questions';
        allQuestionsLi.style.fontWeight = '600';
        allQuestionsLi.style.marginTop = '15px';
        allQuestionsLi.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
        allQuestionsLi.addEventListener('click', showAllQuestions);
        categoriesList.appendChild(allQuestionsLi);
    } catch (error) {
        console.error('Erreur lors du chargement des catégories:', error);
    }
}

// Afficher une catégorie spécifique
function showCategory(category) {
    const questions = allCategories[category];
    const modal = document.getElementById('questionsModal');
    const content = document.getElementById('allQuestionsContent');

    let html = `<h3>${category}</h3><ul>`;
    Object.keys(questions).forEach(q => {
        html += `<li><strong>${q}</strong></li>`;
    });
    html += '</ul>';

    content.innerHTML = html;
    modal.style.display = 'block';
}

// Afficher toutes les questions
function showAllQuestions() {
    const modal = document.getElementById('questionsModal');
    const content = document.getElementById('allQuestionsContent');

    let html = '';
    Object.keys(allCategories).forEach(category => {
        const questions = allCategories[category];
        html += `
            <div class="modal-category">
                <h3>📚 ${category}</h3>
                <ul>
        `;
        Object.keys(questions).forEach(q => {
            html += `<li>• ${q}</li>`;
        });
        html += '</ul></div>';
    });

    content.innerHTML = html;
    modal.style.display = 'block';
}

// Charger les questions rapides (aléatoires)
function loadQuickQuestions() {
    const quickQuestionsDiv = document.getElementById('quickQuestions');
    quickQuestionsDiv.innerHTML = '';

    // Obtenir quelques questions aléatoires
    let allQuestions = [];
    Object.values(allCategories).forEach(category => {
        allQuestions.push(...Object.keys(category));
    });

    // Mélanger et prendre 3-4 questions
    const shuffled = allQuestions.sort(() => Math.random() - 0.5);
    const selected = shuffled.slice(0, 4);

    selected.forEach(question => {
        const btn = document.createElement('button');
        btn.className = 'quick-btn';
        btn.textContent = question.substring(0, 30) + (question.length > 30 ? '...' : '');
        btn.addEventListener('click', () => {
            document.getElementById('messageInput').value = question;
            handleSendMessage(new Event('submit'));
        });
        quickQuestionsDiv.appendChild(btn);
    });
}

// Envoyer un message
async function handleSendMessage(e) {
    e.preventDefault();

    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    // Ajouter le message utilisateur au chat
    addMessage(message, 'user');
    input.value = '';
    focusInput();

    // Ajouter le loading
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error('Erreur du serveur');
        }

        const data = await response.json();
        removeLoadingMessage(loadingId);

        // Ajouter la réponse du bot
        addMessage(data.response, 'bot');

        // Ajouter à l'historique
        conversationHistory.push({
            user: message,
            bot: data.response
        });

        // Recharger les questions rapides
        loadQuickQuestions();
    } catch (error) {
        removeLoadingMessage(loadingId);
        addMessage('❌ Erreur: Impossible de se connecter au serveur. Assurez-vous que le serveur Flask est en cours d\'exécution sur http://localhost:5000', 'bot');
        console.error('Erreur:', error);
    }
}

// Ajouter un message au chat
function addMessage(text, sender) {
    const messagesContainer = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Formater le texte (gestion des sauts de ligne et du code)
    const formattedText = formatMessageText(text);
    contentDiv.innerHTML = formattedText;

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll au bas
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Formater le texte du message
function formatMessageText(text) {
    // Convertir les sauts de ligne en <br>
    let formatted = text.replace(/\n/g, '<br>');

    // Ajouter des balises <p> pour chaque ligne
    const lines = formatted.split('<br>');
    formatted = lines.map(line => {
        if (line.trim()) {
            return `<p>${escapeHtml(line)}</p>`;
        }
        return '';
    }).join('');

    return formatted;
}

// Échapper le HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Ajouter un message de chargement
function addLoadingMessage() {
    const messagesContainer = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.id = 'loading-' + Date.now();

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = '<div class="loading"><span></span><span></span><span></span></div>';

    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);

    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    return messageDiv.id;
}

// Supprimer le message de chargement
function removeLoadingMessage(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// Démarrer une nouvelle conversation
function startNewConversation() {
    conversationHistory = [];
    document.getElementById('messagesContainer').innerHTML = `
        <div class="message bot-message">
            <div class="message-content">
                <p>👋 Bienvenue sur ChatPy ! Je suis ton assistant Python personnel.</p>
                <p>Pose-moi une question sur Python et je te donnerai la réponse. Vous pouvez aussi consulter la liste des questions disponibles.</p>
            </div>
        </div>
    `;
    loadQuickQuestions();
    focusInput();
}

// Focus sur l'input
function focusInput() {
    document.getElementById('messageInput').focus();
}

// Support des raccourcis clavier
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        const input = document.getElementById('messageInput');
        if (document.activeElement === input) {
            return; // Laisser le formulaire gérer
        }
    }
});
