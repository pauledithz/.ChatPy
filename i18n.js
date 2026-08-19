/* ============================================================================
   Langue de l'interface — catalogue et application au document.
   ----------------------------------------------------------------------------
   Chargé de façon *synchrone* dans le <head>, juste après preferences.js, dont
   il lit le réglage `langue`. Comme lui, il pose son attribut sur <html> avant
   la première peinture ; contrairement à lui, il doit aussi remplacer du texte,
   ce qui n'est possible qu'une fois le document parsé (voir « Le voile » plus
   bas).

   Ce qui est traduit : l'interface, et elle seule. Le chatbot répond en
   français — sa FAQ (faq.json) et ses fiches (aide_concepts.json) sont écrites
   dans cette langue, et son moteur de correspondance s'appuie sur une liste de
   mots vides française. C'est pourquoi l'écran d'accueil du chat affiche une
   note dans les autres langues (chat.note_langue) : mieux vaut le dire que
   laisser quelqu'un poser trois questions en allemand avant de comprendre.

   ── Le français est la source ────────────────────────────────────────────────
   Chaque texte reste écrit en français *dans le HTML*, et c'est lui qui
   s'affiche sans JavaScript. Le catalogue le répète pour une seule raison :
   revenir de l'anglais au français sans recharger la page. Sans l'entrée `fr`,
   il n'y aurait rien à réécrire par-dessus la traduction en place.

   ── Ajouter une langue ───────────────────────────────────────────────────────
   Ajouter son code dans LANGUES, son nom dans NOMS_LANGUES, une entrée dans
   SCHEMA.langue (preferences.js) et une <option> dans compte.html — puis une
   traduction à la même position dans *chaque* ligne de TEXTES. Une ligne trop
   courte n'échoue pas : la position manquante retombe sur le français, ce que
   tests/test_i18n.py signale plutôt que de le laisser passer inaperçu.
   ========================================================================== */

(function () {
  'use strict';

  // L'ordre fait foi : c'est l'index dans chaque ligne de TEXTES.
  var LANGUES = ['fr', 'en', 'es', 'de', 'it', 'pt'];

  // Chaque langue dans sa propre langue : un sélecteur qui écrit « Allemand »
  // n'aide personne qui cherche justement à quitter le français.
  var NOMS_LANGUES = {
    fr: 'Français',
    en: 'English',
    es: 'Español',
    de: 'Deutsch',
    it: 'Italiano',
    pt: 'Português'
  };

  /* Les textes, une ligne par clé, dans l'ordre de LANGUES.
     Regroupés par clé plutôt que par langue : c'est la seule disposition où
     l'oubli d'une traduction se voit à l'œil nu, et où corriger une formulation
     ne demande pas de sauter d'un bout du fichier à l'autre.

     {nom} est remplacé par t(cle, {nom: …}). */
  var TEXTES = {
    // ── Barre de navigation, partagée par les trois pages ───────────────────
    'nav.accueil': ['Accueil', 'Home', 'Inicio', 'Startseite', 'Home', 'Início'],
    'nav.chat': ['Chat', 'Chat', 'Chat', 'Chat', 'Chat', 'Chat'],
    'nav.fonctionnalites': ['Fonctionnalités', 'Features', 'Funciones', 'Funktionen', 'Funzionalità', 'Funcionalidades'],
    'nav.docs': ['Docs', 'Docs', 'Docs', 'Docs', 'Docs', 'Docs'],
    'nav.tarifs': ['Tarifs', 'Pricing', 'Precios', 'Preise', 'Prezzi', 'Preços'],
    'nav.connexion': ['Se connecter', 'Sign in', 'Iniciar sesión', 'Anmelden', 'Accedi', 'Entrar'],
    'nav.commencer': ['Commencer →', 'Get started →', 'Empezar →', 'Loslegen →', 'Inizia →', 'Começar →'],
    'nav.theme_clair': ['Passer au thème clair', 'Switch to light theme', 'Cambiar al tema claro', 'Zum hellen Design wechseln', 'Passa al tema chiaro', 'Mudar para o tema claro'],
    'nav.theme_sombre': ['Passer au thème sombre', 'Switch to dark theme', 'Cambiar al tema oscuro', 'Zum dunklen Design wechseln', 'Passa al tema scuro', 'Mudar para o tema escuro'],
    'nav.menu_compte': ['Menu du compte de {nom}', 'Account menu for {nom}', 'Menú de la cuenta de {nom}', 'Kontomenü von {nom}', 'Menu dell’account di {nom}', 'Menu da conta de {nom}'],
    'nav.ouvrir_chat': ['Ouvrir le chat', 'Open the chat', 'Abrir el chat', 'Chat öffnen', 'Apri la chat', 'Abrir o chat'],
    'nav.mon_compte': ['Mon compte', 'My account', 'Mi cuenta', 'Mein Konto', 'Il mio account', 'Minha conta'],
    'nav.deconnexion': ['Se déconnecter', 'Sign out', 'Cerrar sesión', 'Abmelden', 'Esci', 'Sair'],
    'nav.compte': ['Compte', 'Account', 'Cuenta', 'Konto', 'Account', 'Conta'],

    // ── Communs ─────────────────────────────────────────────────────────────
    'commun.compte_chatpy': ['Compte ChatPy', 'ChatPy account', 'Cuenta ChatPy', 'ChatPy-Konto', 'Account ChatPy', 'Conta ChatPy'],
    'commun.en_ligne': ['En ligne', 'Online', 'En línea', 'Online', 'Online', 'Online'],
    'commun.utilisateur': ['Utilisateur', 'User', 'Usuario', 'Benutzer', 'Utente', 'Usuário'],
    'commun.droits': ['© 2026 ChatPy — Tous droits réservés', '© 2026 ChatPy — All rights reserved', '© 2026 ChatPy — Todos los derechos reservados', '© 2026 ChatPy — Alle Rechte vorbehalten', '© 2026 ChatPy — Tutti i diritti riservati', '© 2026 ChatPy — Todos os direitos reservados'],

    // ── Page d'accueil ──────────────────────────────────────────────────────
    'accueil.badge': ['Disponible maintenant', 'Available now', 'Disponible ahora', 'Jetzt verfügbar', 'Disponibile ora', 'Disponível agora'],
    // Le seul texte injecté en HTML : le <span> porte le dégradé du titre et le
    // <br> tient la coupure. Contenu écrit ici, jamais reçu de l'extérieur.
    'accueil.h1': [
      'L’IA qui <span>comprend</span><br>vraiment vos besoins',
      'The AI that <span>truly understands</span><br>what you need',
      'La IA que <span>entiende</span><br>de verdad lo que necesitas',
      'Die KI, die <span>wirklich versteht</span>,<br>was Sie brauchen',
      'L’IA che <span>capisce</span><br>davvero ciò che ti serve',
      'A IA que <span>entende</span><br>de verdade o que você precisa'
    ],
    'accueil.accroche': [
      'ChatPy est un assistant intelligent conçu pour vous aider à penser, écrire, coder et créer — plus vite et mieux qu’avant.',
      'ChatPy is an intelligent assistant built to help you think, write, code and create — faster and better than before.',
      'ChatPy es un asistente inteligente diseñado para ayudarte a pensar, escribir, programar y crear, más rápido y mejor que antes.',
      'ChatPy ist ein intelligenter Assistent, der Ihnen hilft, zu denken, zu schreiben, zu programmieren und zu gestalten – schneller und besser als zuvor.',
      'ChatPy è un assistente intelligente pensato per aiutarti a pensare, scrivere, programmare e creare, più rapidamente e meglio di prima.',
      'O ChatPy é um assistente inteligente criado para ajudar você a pensar, escrever, programar e criar — mais rápido e melhor do que antes.'
    ],
    'accueil.essayer': ['Essayer gratuitement', 'Try it free', 'Probar gratis', 'Kostenlos testen', 'Prova gratis', 'Testar gratuitamente'],
    'accueil.ouvrir_chat': ['Ouvrir le chat →', 'Open the chat →', 'Abrir el chat →', 'Chat öffnen →', 'Apri la chat →', 'Abrir o chat →'],
    'accueil.demo': ['Voir la démo', 'Watch the demo', 'Ver la demo', 'Demo ansehen', 'Guarda la demo', 'Ver a demo'],
    'accueil.stat_satisfaction': ['Satisfaction', 'Satisfaction', 'Satisfacción', 'Zufriedenheit', 'Soddisfazione', 'Satisfação'],
    'accueil.stat_conversations': ['Conversations', 'Conversations', 'Conversaciones', 'Konversationen', 'Conversazioni', 'Conversas'],
    'accueil.stat_temps': ['Temps de réponse', 'Response time', 'Tiempo de respuesta', 'Antwortzeit', 'Tempo di risposta', 'Tempo de resposta'],
    'accueil.features_titre': ['Tout ce dont vous avez besoin', 'Everything you need', 'Todo lo que necesitas', 'Alles, was Sie brauchen', 'Tutto ciò che ti serve', 'Tudo o que você precisa'],
    'accueil.feat1_titre': ['Raisonnement avancé', 'Advanced reasoning', 'Razonamiento avanzado', 'Fortgeschrittenes Denken', 'Ragionamento avanzato', 'Raciocínio avançado'],
    'accueil.feat1_texte': [
      'ChatPy analyse et structure vos problèmes complexes avec clarté.',
      'ChatPy analyses and structures your complex problems with clarity.',
      'ChatPy analiza y estructura tus problemas complejos con claridad.',
      'ChatPy analysiert und strukturiert Ihre komplexen Probleme klar und verständlich.',
      'ChatPy analizza e struttura i tuoi problemi complessi con chiarezza.',
      'O ChatPy analisa e estrutura seus problemas complexos com clareza.'
    ],
    'accueil.feat2_titre': ['Génération de code', 'Code generation', 'Generación de código', 'Code-Generierung', 'Generazione di codice', 'Geração de código'],
    'accueil.feat2_texte': [
      'Python, JS, SQL et plus — du code propre, commenté et expliqué.',
      'Python, JS, SQL and more — clean code, commented and explained.',
      'Python, JS, SQL y más: código limpio, comentado y explicado.',
      'Python, JS, SQL und mehr – sauberer Code, kommentiert und erklärt.',
      'Python, JS, SQL e altro: codice pulito, commentato e spiegato.',
      'Python, JS, SQL e mais — código limpo, comentado e explicado.'
    ],
    'accueil.feat3_titre': ['Rédaction intelligente', 'Smart writing', 'Redacción inteligente', 'Intelligentes Schreiben', 'Scrittura intelligente', 'Redação inteligente'],
    'accueil.feat3_texte': [
      'Emails, rapports, articles — adapté à votre style et ton.',
      'Emails, reports, articles — matched to your style and tone.',
      'Correos, informes, artículos: adaptado a tu estilo y a tu tono.',
      'E-Mails, Berichte, Artikel – passend zu Ihrem Stil und Ton.',
      'Email, report, articoli: adattati al tuo stile e al tuo tono.',
      'E-mails, relatórios, artigos — adaptados ao seu estilo e tom.'
    ],
    'accueil.feat4_titre': ['Mémoire contextuelle', 'Contextual memory', 'Memoria contextual', 'Kontextbezogenes Gedächtnis', 'Memoria contestuale', 'Memória contextual'],
    'accueil.feat4_texte': [
      'ChatPy se souvient du fil de votre conversation pour des réponses cohérentes.',
      'ChatPy remembers the thread of your conversation, for answers that stay consistent.',
      'ChatPy recuerda el hilo de tu conversación para dar respuestas coherentes.',
      'ChatPy merkt sich den Verlauf Ihrer Unterhaltung – für stimmige Antworten.',
      'ChatPy ricorda il filo della conversazione, per risposte coerenti.',
      'O ChatPy lembra o fio da sua conversa para dar respostas coerentes.'
    ],
    'accueil.docs_label': ['Documentation', 'Documentation', 'Documentación', 'Dokumentation', 'Documentazione', 'Documentação'],
    'accueil.docs_titre': ['Guide rapide pour commencer', 'A quick guide to get started', 'Guía rápida para empezar', 'Kurzanleitung für den Einstieg', 'Guida rapida per iniziare', 'Guia rápido para começar'],
    'accueil.doc1_titre': ['Créer un compte', 'Create an account', 'Crear una cuenta', 'Konto erstellen', 'Crea un account', 'Criar uma conta'],
    'accueil.doc1_texte': [
      'Inscrivez-vous en moins d’une minute et configurez votre profil.',
      'Sign up in under a minute and set up your profile.',
      'Regístrate en menos de un minuto y configura tu perfil.',
      'Melden Sie sich in weniger als einer Minute an und richten Sie Ihr Profil ein.',
      'Iscriviti in meno di un minuto e configura il tuo profilo.',
      'Cadastre-se em menos de um minuto e configure seu perfil.'
    ],
    'accueil.doc2_titre': ['Lancer une conversation', 'Start a conversation', 'Iniciar una conversación', 'Unterhaltung starten', 'Avvia una conversazione', 'Iniciar uma conversa'],
    'accueil.doc2_texte': [
      'Posez une question, générez du code ou demandez un plan détaillé.',
      'Ask a question, generate code or request a detailed outline.',
      'Haz una pregunta, genera código o pide un plan detallado.',
      'Stellen Sie eine Frage, erzeugen Sie Code oder bitten Sie um einen ausführlichen Plan.',
      'Fai una domanda, genera codice o chiedi un piano dettagliato.',
      'Faça uma pergunta, gere código ou peça um plano detalhado.'
    ],
    'accueil.doc3_titre': ['Exporter vos résultats', 'Export your results', 'Exportar tus resultados', 'Ergebnisse exportieren', 'Esporta i risultati', 'Exportar seus resultados'],
    'accueil.doc3_texte': [
      'Sauvegardez vos réponses, snippets et idées pour votre workflow.',
      'Save your answers, snippets and ideas for your workflow.',
      'Guarda tus respuestas, fragmentos de código e ideas para tu flujo de trabajo.',
      'Speichern Sie Antworten, Snippets und Ideen für Ihren Workflow.',
      'Salva risposte, snippet e idee per il tuo flusso di lavoro.',
      'Salve suas respostas, trechos de código e ideias para o seu fluxo de trabalho.'
    ],
    'accueil.cta_titre': ['Prêt à essayer ChatPy ?', 'Ready to try ChatPy?', '¿Listo para probar ChatPy?', 'Bereit, ChatPy auszuprobieren?', 'Pronto a provare ChatPy?', 'Pronto para experimentar o ChatPy?'],
    'accueil.cta_texte': [
      'Rejoignez des milliers d’utilisateurs qui pensent déjà plus vite.',
      'Join the thousands of users who already think faster.',
      'Únete a miles de usuarios que ya piensan más rápido.',
      'Schließen Sie sich Tausenden an, die bereits schneller denken.',
      'Unisciti a migliaia di utenti che pensano già più velocemente.',
      'Junte-se a milhares de pessoas que já pensam mais rápido.'
    ],
    'accueil.cta_bouton': ['Créer un compte gratuit →', 'Create a free account →', 'Crear una cuenta gratis →', 'Kostenloses Konto erstellen →', 'Crea un account gratuito →', 'Criar uma conta grátis →'],

    // ── Démonstration animée du hero (script.js) ────────────────────────────
    'demo.q1': [
      'Peux-tu m’expliquer comment fonctionne une API REST ?',
      'Can you explain how a REST API works?',
      '¿Puedes explicarme cómo funciona una API REST?',
      'Kannst du mir erklären, wie eine REST-API funktioniert?',
      'Puoi spiegarmi come funziona un’API REST?',
      'Você pode me explicar como funciona uma API REST?'
    ],
    'demo.r1': [
      'Bien sûr ! Une API REST permet à deux applications de communiquer via HTTP. Tu envoies une requête (GET, POST, PUT…) à une URL, et le serveur te renvoie une réponse en JSON. C’est la base du web moderne. ✦',
      'Of course! A REST API lets two applications talk over HTTP. You send a request (GET, POST, PUT…) to a URL, and the server sends back a JSON response. It is the backbone of the modern web. ✦',
      '¡Claro! Una API REST permite que dos aplicaciones se comuniquen por HTTP. Envías una petición (GET, POST, PUT…) a una URL y el servidor te devuelve una respuesta en JSON. Es la base de la web moderna. ✦',
      'Klar! Eine REST-API lässt zwei Anwendungen über HTTP miteinander sprechen. Du schickst eine Anfrage (GET, POST, PUT …) an eine URL, und der Server antwortet mit JSON. Das ist die Grundlage des modernen Webs. ✦',
      'Certo! Un’API REST permette a due applicazioni di comunicare via HTTP. Invii una richiesta (GET, POST, PUT…) a un URL e il server ti risponde in JSON. È la base del web moderno. ✦',
      'Claro! Uma API REST permite que dois aplicativos conversem por HTTP. Você envia uma requisição (GET, POST, PUT…) para uma URL e o servidor devolve uma resposta em JSON. É a base da web moderna. ✦'
    ],
    'demo.q2': [
      'Génère-moi un script Python pour lire un fichier CSV.',
      'Write me a Python script to read a CSV file.',
      'Genérame un script de Python para leer un archivo CSV.',
      'Schreib mir ein Python-Skript, das eine CSV-Datei liest.',
      'Generami uno script Python per leggere un file CSV.',
      'Gere um script Python para ler um arquivo CSV.'
    ],
    'demo.r2': [
      'Voici un exemple simple avec pandas : import pandas as pd — df = pd.read_csv(\'fichier.csv\') — print(df.head()). Rapide, lisible, et facile à adapter à ton projet !',
      'Here is a simple example with pandas: import pandas as pd — df = pd.read_csv(\'file.csv\') — print(df.head()). Fast, readable, and easy to adapt to your project!',
      'Aquí tienes un ejemplo sencillo con pandas: import pandas as pd — df = pd.read_csv(\'archivo.csv\') — print(df.head()). Rápido, legible y fácil de adaptar a tu proyecto.',
      'Hier ein einfaches Beispiel mit pandas: import pandas as pd — df = pd.read_csv(\'datei.csv\') — print(df.head()). Schnell, lesbar und leicht an dein Projekt anzupassen!',
      'Ecco un esempio semplice con pandas: import pandas as pd — df = pd.read_csv(\'file.csv\') — print(df.head()). Veloce, leggibile e facile da adattare al tuo progetto!',
      'Veja um exemplo simples com pandas: import pandas as pd — df = pd.read_csv(\'arquivo.csv\') — print(df.head()). Rápido, legível e fácil de adaptar ao seu projeto!'
    ],
    'demo.q3': [
      'Comment améliorer les performances de mon site web ?',
      'How can I improve my website’s performance?',
      '¿Cómo puedo mejorar el rendimiento de mi sitio web?',
      'Wie kann ich die Performance meiner Website verbessern?',
      'Come posso migliorare le prestazioni del mio sito web?',
      'Como posso melhorar o desempenho do meu site?'
    ],
    'demo.r3': [
      'Plusieurs pistes : compresse tes images, minifie tes fichiers CSS/JS, active le cache navigateur, et utilise un CDN. Ces optimisations peuvent diviser ton temps de chargement par 2 ou 3. ⚡',
      'A few leads: compress your images, minify your CSS/JS, turn on browser caching, and use a CDN. These can cut your load time by half or more. ⚡',
      'Varias vías: comprime las imágenes, minifica el CSS y el JS, activa la caché del navegador y usa una CDN. Estas optimizaciones pueden dividir tu tiempo de carga entre 2 o 3. ⚡',
      'Mehrere Ansätze: Bilder komprimieren, CSS/JS minifizieren, Browser-Cache aktivieren und ein CDN nutzen. Damit lässt sich die Ladezeit oft halbieren oder dritteln. ⚡',
      'Diverse strade: comprimi le immagini, minifica CSS e JS, attiva la cache del browser e usa una CDN. Queste ottimizzazioni possono dimezzare o ridurre di un terzo il tempo di caricamento. ⚡',
      'Alguns caminhos: comprima as imagens, minifique o CSS e o JS, ative o cache do navegador e use uma CDN. Essas otimizações podem dividir seu tempo de carregamento por 2 ou 3. ⚡'
    ],
    'demo.q4': [
      'Aide-moi à rédiger un email professionnel pour un client.',
      'Help me write a professional email to a client.',
      'Ayúdame a redactar un correo profesional para un cliente.',
      'Hilf mir, eine professionelle E-Mail an einen Kunden zu schreiben.',
      'Aiutami a scrivere un’email professionale per un cliente.',
      'Ajude-me a escrever um e-mail profissional para um cliente.'
    ],
    'demo.r4': [
      'Avec plaisir ! Commence par un contexte clair, exprime ta demande de façon concise, et termine par une invitation à l’action. Dis-moi le sujet et je t’écris un brouillon complet en quelques secondes.',
      'Gladly! Open with clear context, state your request concisely, and close with a call to action. Tell me the topic and I will draft the whole thing in seconds.',
      '¡Con mucho gusto! Empieza con un contexto claro, expón tu petición de forma concisa y termina con una llamada a la acción. Dime el tema y te escribo un borrador completo en segundos.',
      'Sehr gern! Beginne mit klarem Kontext, formuliere dein Anliegen knapp und schließe mit einer Handlungsaufforderung. Nenne mir das Thema, und ich schreibe dir in Sekunden einen vollständigen Entwurf.',
      'Volentieri! Inizia con un contesto chiaro, esprimi la richiesta in modo conciso e chiudi con un invito all’azione. Dimmi l’argomento e ti scrivo una bozza completa in pochi secondi.',
      'Com prazer! Comece com um contexto claro, exponha seu pedido de forma concisa e termine com um convite à ação. Diga o assunto e eu escrevo um rascunho completo em segundos.'
    ],

    // ── Modale de connexion / inscription ───────────────────────────────────
    'modale.fermer': ['Fermer', 'Close', 'Cerrar', 'Schließen', 'Chiudi', 'Fechar'],
    'modale.titre_connexion': ['Se connecter à ChatPy', 'Sign in to ChatPy', 'Iniciar sesión en ChatPy', 'Bei ChatPy anmelden', 'Accedi a ChatPy', 'Entrar no ChatPy'],
    'modale.titre_inscription': ['Créer votre compte ChatPy', 'Create your ChatPy account', 'Crea tu cuenta de ChatPy', 'Ihr ChatPy-Konto erstellen', 'Crea il tuo account ChatPy', 'Criar sua conta ChatPy'],
    'modale.sous_titre_connexion': [
      'Retrouvez vos conversations et votre progression.',
      'Pick your conversations and your progress back up.',
      'Recupera tus conversaciones y tu progreso.',
      'Finden Sie Ihre Unterhaltungen und Ihren Fortschritt wieder.',
      'Ritrova le tue conversazioni e i tuoi progressi.',
      'Retome suas conversas e seu progresso.'
    ],
    'modale.sous_titre_inscription': [
      'Un email et un mot de passe suffisent — aucune vérification par courriel.',
      'An email and a password are all it takes — no email verification.',
      'Basta un correo y una contraseña, sin verificación por email.',
      'Eine E-Mail-Adresse und ein Passwort genügen – keine Bestätigungsmail.',
      'Bastano un’email e una password, senza verifica via email.',
      'Bastam um e-mail e uma senha — sem verificação por e-mail.'
    ],
    'modale.nom': ['Nom', 'Name', 'Nombre', 'Name', 'Nome', 'Nome'],
    'modale.nom_placeholder': ['Comment doit-on vous appeler ?', 'What should we call you?', '¿Cómo debemos llamarte?', 'Wie sollen wir Sie nennen?', 'Come dobbiamo chiamarti?', 'Como devemos chamar você?'],
    'modale.email': ['Email', 'Email', 'Correo electrónico', 'E-Mail', 'Email', 'E-mail'],
    'modale.email_placeholder': ['Entrer votre Email', 'Enter your email', 'Introduce tu correo', 'E-Mail-Adresse eingeben', 'Inserisci la tua email', 'Digite seu e-mail'],
    'modale.mot_de_passe': ['Mot de passe', 'Password', 'Contraseña', 'Passwort', 'Password', 'Senha'],
    'modale.mot_de_passe_placeholder': ['Entrer votre Mot de passe', 'Enter your password', 'Introduce tu contraseña', 'Passwort eingeben', 'Inserisci la tua password', 'Digite sua senha'],
    'modale.confirmation': ['Confirmer le mot de passe', 'Confirm password', 'Confirmar contraseña', 'Passwort bestätigen', 'Conferma la password', 'Confirmar a senha'],
    'modale.confirmation_placeholder': ['Retapez votre mot de passe', 'Type your password again', 'Vuelve a escribir tu contraseña', 'Passwort erneut eingeben', 'Riscrivi la password', 'Digite a senha novamente'],
    'modale.rester': ['Rester connecté', 'Stay signed in', 'Mantener la sesión iniciada', 'Angemeldet bleiben', 'Resta connesso', 'Continuar conectado'],
    'modale.oubli': ['Mot de passe oublié ?', 'Forgot your password?', '¿Olvidaste tu contraseña?', 'Passwort vergessen?', 'Password dimenticata?', 'Esqueceu a senha?'],
    'modale.soumettre_connexion': ['Se connecter', 'Sign in', 'Iniciar sesión', 'Anmelden', 'Accedi', 'Entrar'],
    'modale.soumettre_inscription': ['Créer mon compte', 'Create my account', 'Crear mi cuenta', 'Konto erstellen', 'Crea il mio account', 'Criar minha conta'],
    'modale.pas_de_compte': ['Vous n’avez pas de compte ?', 'Don’t have an account?', '¿No tienes cuenta?', 'Noch kein Konto?', 'Non hai un account?', 'Ainda não tem conta?'],
    'modale.deja_compte': ['Vous avez déjà un compte ?', 'Already have an account?', '¿Ya tienes cuenta?', 'Schon ein Konto?', 'Hai già un account?', 'Já tem uma conta?'],
    'modale.inscrire': ['S’inscrire', 'Sign up', 'Registrarse', 'Registrieren', 'Registrati', 'Cadastrar-se'],
    'modale.ou_avec': ['Ou avec', 'Or with', 'O con', 'Oder mit', 'Oppure con', 'Ou com'],
    'modale.oubli_explication': [
      'Ce serveur n’envoie pas d’emails : il n’y a donc pas de réinitialisation de mot de passe. Vous pouvez créer un nouveau compte, ou vous connecter avec Google ou GitHub.',
      'This server does not send emails, so there is no password reset. You can create a new account, or sign in with Google or GitHub.',
      'Este servidor no envía correos, así que no hay restablecimiento de contraseña. Puedes crear una cuenta nueva o iniciar sesión con Google o GitHub.',
      'Dieser Server versendet keine E-Mails, deshalb gibt es kein Zurücksetzen des Passworts. Sie können ein neues Konto erstellen oder sich mit Google oder GitHub anmelden.',
      'Questo server non invia email, quindi non esiste il ripristino della password. Puoi creare un nuovo account oppure accedere con Google o GitHub.',
      'Este servidor não envia e-mails, portanto não há redefinição de senha. Você pode criar uma nova conta ou entrar com o Google ou o GitHub.'
    ],
    'modale.echec': ['La connexion n’a pas abouti.', 'Sign-in did not go through.', 'No se ha podido iniciar sesión.', 'Die Anmeldung ist nicht durchgegangen.', 'Accesso non riuscito.', 'Não foi possível entrar.'],
    'modale.serveur_injoignable': [
      'Serveur injoignable. Réessayez dans un instant.',
      'Server unreachable. Try again in a moment.',
      'Servidor no disponible. Inténtalo de nuevo en un momento.',
      'Server nicht erreichbar. Versuchen Sie es gleich noch einmal.',
      'Server irraggiungibile. Riprova tra un istante.',
      'Servidor indisponível. Tente novamente em instantes.'
    ],
    'oauth.echec': [
      'La connexion a échoué ou a été annulée.',
      'Sign-in failed or was cancelled.',
      'El inicio de sesión ha fallado o se ha cancelado.',
      'Die Anmeldung ist fehlgeschlagen oder wurde abgebrochen.',
      'L’accesso non è riuscito o è stato annullato.',
      'A entrada falhou ou foi cancelada.'
    ],
    'oauth.email_non_verifie': [
      'Aucune adresse email vérifiée sur ce compte : connexion refusée.',
      'No verified email address on this account: sign-in refused.',
      'Esta cuenta no tiene ninguna dirección verificada: acceso denegado.',
      'Für dieses Konto ist keine E-Mail-Adresse bestätigt: Anmeldung abgelehnt.',
      'Nessun indirizzo email verificato su questo account: accesso rifiutato.',
      'Nenhum e-mail verificado nesta conta: entrada recusada.'
    ],

    // ── Page /chat ──────────────────────────────────────────────────────────
    // Le titre de l'onglet : data-i18n fonctionne sur <title> comme ailleurs,
    // son textContent étant ce que le navigateur affiche.
    'chat.titre_page': ['ChatPy — Chat', 'ChatPy — Chat', 'ChatPy — Chat', 'ChatPy — Chat', 'ChatPy — Chat', 'ChatPy — Chat'],
    'chat.historique_aria': ['Historique des conversations', 'Conversation history', 'Historial de conversaciones', 'Verlauf der Unterhaltungen', 'Cronologia delle conversazioni', 'Histórico de conversas'],
    'chat.nouvelle': ['Nouvelle conversation', 'New conversation', 'Nueva conversación', 'Neue Unterhaltung', 'Nuova conversazione', 'Nova conversa'],
    'chat.rechercher': ['Rechercher…', 'Search…', 'Buscar…', 'Suchen…', 'Cerca…', 'Pesquisar…'],
    'chat.rechercher_aria': ['Rechercher dans les conversations', 'Search the conversations', 'Buscar en las conversaciones', 'In den Unterhaltungen suchen', 'Cerca nelle conversazioni', 'Pesquisar nas conversas'],
    'chat.masquer_historique': ['Masquer l’historique', 'Hide history', 'Ocultar el historial', 'Verlauf ausblenden', 'Nascondi la cronologia', 'Ocultar o histórico'],
    'chat.afficher_historique': ['Afficher l’historique', 'Show history', 'Mostrar el historial', 'Verlauf einblenden', 'Mostra la cronologia', 'Mostrar o histórico'],
    'chat.quiz_badge': ['🎯 Quiz en cours', '🎯 Quiz in progress', '🎯 Cuestionario en curso', '🎯 Quiz läuft', '🎯 Quiz in corso', '🎯 Quiz em andamento'],
    'chat.bonjour': ['Bonjour 👋', 'Hello 👋', 'Hola 👋', 'Hallo 👋', 'Ciao 👋', 'Olá 👋'],
    'chat.bonjour_prenom': ['Bonjour {prenom} 👋', 'Hello {prenom} 👋', 'Hola {prenom} 👋', 'Hallo {prenom} 👋', 'Ciao {prenom} 👋', 'Olá {prenom} 👋'],
    'chat.accroche': [
      'Posez-moi une question sur Python, ou choisissez une suggestion ci-dessous.',
      'Ask me a question about Python, or pick a suggestion below.',
      'Hazme una pregunta sobre Python o elige una sugerencia.',
      'Stellen Sie mir eine Frage zu Python oder wählen Sie einen Vorschlag.',
      'Fammi una domanda su Python o scegli un suggerimento qui sotto.',
      'Faça uma pergunta sobre Python ou escolha uma sugestão abaixo.'
    ],
    /* Affichée uniquement hors français, par chat.js. Le bot ne connaît que le
       français : le taire ferait passer une limite connue pour une panne. */
    'chat.note_langue': [
      '',
      'ChatPy answers in French — ask your Python questions in French.',
      'ChatPy responde en francés: haz tus preguntas en francés.',
      'ChatPy antwortet auf Französisch – stellen Sie Ihre Fragen bitte auf Französisch.',
      'ChatPy risponde in francese: fai le tue domande in francese.',
      'O ChatPy responde em francês — faça suas perguntas em francês.'
    ],
    // Puces de l'écran d'accueil qui envoient une commande et non une phrase :
    // voir le commentaire de chat.html.
    'chat.chip_variables': ['Explique-moi les variables', 'Explain variables to me', 'Explícame las variables', 'Erkläre mir Variablen', 'Spiegami le variabili', 'Explique-me as variáveis'],
    'chat.chip_quiz': ['🎯 Lancer un quiz', '🎯 Start a quiz', '🎯 Empezar un cuestionario', '🎯 Quiz starten', '🎯 Avvia un quiz', '🎯 Iniciar um quiz'],
    'chat.chip_capacites': ['Que sais-tu faire ?', 'What can you do?', '¿Qué sabes hacer?', 'Was kannst du?', 'Cosa sai fare?', 'O que você sabe fazer?'],
    'chat.placeholder': ['Posez une question sur Python…', 'Ask a question about Python…', 'Haz una pregunta sobre Python…', 'Stellen Sie eine Frage zu Python…', 'Fai una domanda su Python…', 'Faça uma pergunta sobre Python…'],
    // « fin » n'est pas traduit : c'est la commande que le serveur attend.
    'chat.placeholder_quiz': [
      'Votre réponse… (tapez « fin » pour arrêter)',
      'Your answer… (type “fin” to stop)',
      'Tu respuesta… (escribe «fin» para parar)',
      'Ihre Antwort … (tippen Sie „fin“ zum Beenden)',
      'La tua risposta… (scrivi «fin» per fermarti)',
      'Sua resposta… (digite “fin” para parar)'
    ],
    'chat.copier': ['Copier', 'Copy', 'Copiar', 'Kopieren', 'Copia', 'Copiar'],
    'chat.copie': ['Copié', 'Copied', 'Copiado', 'Kopiert', 'Copiato', 'Copiado'],
    'chat.copie_echec': ['Échec', 'Failed', 'Error', 'Fehlgeschlagen', 'Errore', 'Falhou'],
    'chat.confiance': ['Confiance {score}%', 'Confidence {score}%', 'Confianza {score}%', 'Konfidenz {score}%', 'Affidabilità {score}%', 'Confiança {score}%'],
    'chat.feedback_label': ['Cette réponse vous a-t-elle aidé ?', 'Did this answer help?', '¿Te ha servido esta respuesta?', 'Hat diese Antwort geholfen?', 'Questa risposta ti è stata utile?', 'Esta resposta ajudou?'],
    'chat.feedback_utile': ['Réponse utile', 'Helpful answer', 'Respuesta útil', 'Hilfreiche Antwort', 'Risposta utile', 'Resposta útil'],
    'chat.feedback_inutile': ['Réponse inutile', 'Unhelpful answer', 'Respuesta poco útil', 'Nicht hilfreiche Antwort', 'Risposta inutile', 'Resposta inútil'],
    'chat.feedback_merci': ['👍 Merci pour votre retour !', '👍 Thanks for the feedback!', '👍 ¡Gracias por tu opinión!', '👍 Danke für Ihre Rückmeldung!', '👍 Grazie per il tuo riscontro!', '👍 Obrigado pelo retorno!'],
    'chat.feedback_note': [
      '👎 Merci — cette question est notée pour améliorer la FAQ.',
      '👎 Thanks — this question is logged to improve the FAQ.',
      '👎 Gracias: anotamos esta pregunta para mejorar la FAQ.',
      '👎 Danke – diese Frage wird notiert, um die FAQ zu verbessern.',
      '👎 Grazie: la domanda è annotata per migliorare le FAQ.',
      '👎 Obrigado — a pergunta foi anotada para melhorar a FAQ.'
    ],
    'chat.erreur_enregistrement': [
      '⚠ La dernière conversation n’a pas pu être enregistrée.',
      '⚠ The last conversation could not be saved.',
      '⚠ No se ha podido guardar la última conversación.',
      '⚠ Die letzte Unterhaltung konnte nicht gespeichert werden.',
      '⚠ Non è stato possibile salvare l’ultima conversazione.',
      '⚠ Não foi possível salvar a última conversa.'
    ],
    'chat.erreur_serveur': [
      '❌ Impossible de contacter le serveur ChatPy. Réessayez dans un instant.',
      '❌ Cannot reach the ChatPy server. Try again in a moment.',
      '❌ No se puede contactar con el servidor de ChatPy. Inténtalo de nuevo en un momento.',
      '❌ Der ChatPy-Server ist nicht erreichbar. Versuchen Sie es gleich noch einmal.',
      '❌ Impossibile contattare il server ChatPy. Riprova tra un istante.',
      '❌ Não foi possível contatar o servidor do ChatPy. Tente novamente em instantes.'
    ],
    'chat.groupe_aujourdhui': ['Aujourd’hui', 'Today', 'Hoy', 'Heute', 'Oggi', 'Hoje'],
    'chat.groupe_hier': ['Hier', 'Yesterday', 'Ayer', 'Gestern', 'Ieri', 'Ontem'],
    'chat.groupe_semaine': ['7 derniers jours', 'Last 7 days', 'Últimos 7 días', 'Letzte 7 Tage', 'Ultimi 7 giorni', 'Últimos 7 dias'],
    'chat.groupe_ancien': ['Plus ancien', 'Older', 'Más antiguas', 'Älter', 'Meno recenti', 'Mais antigas'],
    'chat.renommer': ['Renommer', 'Rename', 'Cambiar el nombre', 'Umbenennen', 'Rinomina', 'Renomear'],
    'chat.supprimer': ['Supprimer', 'Delete', 'Eliminar', 'Löschen', 'Elimina', 'Excluir'],
    'chat.vide_recherche': [
      'Aucune conversation ne correspond à cette recherche.',
      'No conversation matches this search.',
      'Ninguna conversación coincide con esta búsqueda.',
      'Keine Unterhaltung passt zu dieser Suche.',
      'Nessuna conversazione corrisponde a questa ricerca.',
      'Nenhuma conversa corresponde a esta pesquisa.'
    ],
    'chat.vide': [
      'Vos conversations apparaîtront ici au fil de vos questions.',
      'Your conversations will appear here as you ask questions.',
      'Tus conversaciones aparecerán aquí a medida que preguntes.',
      'Ihre Unterhaltungen erscheinen hier, sobald Sie Fragen stellen.',
      'Le tue conversazioni appariranno qui man mano che fai domande.',
      'Suas conversas aparecerão aqui conforme você fizer perguntas.'
    ],
    'chat.confirmer_suppression': [
      'Supprimer « {titre} » ?\n\nCette conversation sera définitivement perdue.',
      'Delete “{titre}”?\n\nThis conversation will be lost for good.',
      '¿Eliminar «{titre}»?\n\nEsta conversación se perderá definitivamente.',
      '„{titre}“ löschen?\n\nDiese Unterhaltung geht endgültig verloren.',
      'Eliminare «{titre}»?\n\nQuesta conversazione andrà persa definitivamente.',
      'Excluir “{titre}”?\n\nEsta conversa será perdida definitivamente.'
    ],
    'chat.note_compte': [
      'Conversations enregistrées sur votre compte : vous les retrouverez depuis n’importe quel appareil.',
      'Conversations saved to your account: you will find them again from any device.',
      'Conversaciones guardadas en tu cuenta: las encontrarás desde cualquier dispositivo.',
      'Unterhaltungen in Ihrem Konto gespeichert: Sie finden sie auf jedem Gerät wieder.',
      'Conversazioni salvate sul tuo account: le ritrovi da qualsiasi dispositivo.',
      'Conversas salvas na sua conta: você as encontra em qualquer aparelho.'
    ],
    'chat.note_local': [
      'Conversations enregistrées dans ce navigateur seulement. Connectez-vous pour les retrouver ailleurs.',
      'Conversations saved in this browser only. Sign in to find them elsewhere.',
      'Conversaciones guardadas solo en este navegador. Inicia sesión para encontrarlas en otros dispositivos.',
      'Unterhaltungen nur in diesem Browser gespeichert. Melden Sie sich an, um sie anderswo wiederzufinden.',
      'Conversazioni salvate solo in questo browser. Accedi per ritrovarle altrove.',
      'Conversas salvas apenas neste navegador. Entre na sua conta para encontrá-las em outros aparelhos.'
    ],

    // ── Page /compte ────────────────────────────────────────────────────────
    'compte.titre_page': [
      'ChatPy — Mon compte',
      'ChatPy — My account',
      'ChatPy — Mi cuenta',
      'ChatPy — Mein Konto',
      'ChatPy — Il mio account',
      'ChatPy — Minha conta'
    ],
    'compte.titre': ['Mon compte', 'My account', 'Mi cuenta', 'Mein Konto', 'Il mio account', 'Minha conta'],
    'compte.sous_titre': [
      'Votre identité de connexion et vos réglages d’affichage.',
      'Your sign-in identity and your display settings.',
      'Tu identidad de acceso y tus ajustes de visualización.',
      'Ihre Anmeldeidentität und Ihre Anzeigeeinstellungen.',
      'La tua identità di accesso e le impostazioni di visualizzazione.',
      'Sua identidade de acesso e suas configurações de exibição.'
    ],
    'compte.identite': ['Identité', 'Identity', 'Identidad', 'Identität', 'Identità', 'Identidade'],
    'compte.chargement': ['Chargement…', 'Loading…', 'Cargando…', 'Wird geladen …', 'Caricamento…', 'Carregando…'],
    'compte.identite_indisponible': [
      'Identité indisponible : le serveur ChatPy ne répond pas.',
      'Identity unavailable: the ChatPy server is not responding.',
      'Identidad no disponible: el servidor de ChatPy no responde.',
      'Identität nicht verfügbar: Der ChatPy-Server antwortet nicht.',
      'Identità non disponibile: il server ChatPy non risponde.',
      'Identidade indisponível: o servidor do ChatPy não responde.'
    ],
    'compte.local': ['Compte ChatPy (email et mot de passe)', 'ChatPy account (email and password)', 'Cuenta ChatPy (correo y contraseña)', 'ChatPy-Konto (E-Mail und Passwort)', 'Account ChatPy (email e password)', 'Conta ChatPy (e-mail e senha)'],
    'compte.via': ['Connecté via {fournisseur}', 'Signed in with {fournisseur}', 'Conectado con {fournisseur}', 'Angemeldet über {fournisseur}', 'Connesso tramite {fournisseur}', 'Conectado via {fournisseur}'],
    'compte.fournisseur_inconnu': ['un fournisseur externe', 'an external provider', 'un proveedor externo', 'einen externen Anbieter', 'un fornitore esterno', 'um provedor externo'],
    'compte.changer_photo': ['Changer la photo', 'Change photo', 'Cambiar foto', 'Foto ändern', 'Cambia foto', 'Alterar foto'],
    'compte.photo_erreur': ['Erreur lors de l\'envoi.', 'Upload error.', 'Error al enviar.', 'Fehler beim Hochladen.', 'Errore durante il caricamento.', 'Errore durante o envio.'],
    'compte.photo_format': ['Format non supporté. Utilisez JPEG, PNG ou WebP.', 'Unsupported format. Use JPEG, PNG or WebP.', 'Formato no compatible. Usa JPEG, PNG o WebP.', 'Nicht unterstütztes Format. Verwenden Sie JPEG, PNG oder WebP.', 'Formato non supportato. Usa JPEG, PNG o WebP.', 'Formato não suportado. Use JPEG, PNG ou WebP.'],
    'compte.photo_taille': ['Fichier trop volumineux (max 2 Mo).', 'File too large (max 2 MB).', 'Archivo demasiado grande (máx. 2 MB).', 'Datei zu groß (max. 2 MB).', 'File troppo grande (max 2 MB).', 'Arquivo muito grande (máx. 2 MB).'],
    'compte.invitation_oauth': [
      'Vous n’êtes pas connecté. Créez un compte, ou connectez-vous avec Google ou GitHub, pour retrouver vos conversations depuis n’importe quel appareil.',
      'You are not signed in. Create an account, or sign in with Google or GitHub, to find your conversations from any device.',
      'No has iniciado sesión. Crea una cuenta o entra con Google o GitHub para recuperar tus conversaciones desde cualquier dispositivo.',
      'Sie sind nicht angemeldet. Erstellen Sie ein Konto oder melden Sie sich mit Google oder GitHub an, um Ihre Unterhaltungen auf jedem Gerät wiederzufinden.',
      'Non hai effettuato l’accesso. Crea un account oppure accedi con Google o GitHub per ritrovare le tue conversazioni da qualsiasi dispositivo.',
      'Você não está conectado. Crie uma conta ou entre com o Google ou o GitHub para encontrar suas conversas em qualquer aparelho.'
    ],
    'compte.invitation_simple': [
      'Vous n’êtes pas connecté. Créez un compte avec votre email pour retrouver vos conversations depuis n’importe quel appareil.',
      'You are not signed in. Create an account with your email to find your conversations from any device.',
      'No has iniciado sesión. Crea una cuenta con tu correo para recuperar tus conversaciones desde cualquier dispositivo.',
      'Sie sind nicht angemeldet. Erstellen Sie ein Konto mit Ihrer E-Mail-Adresse, um Ihre Unterhaltungen auf jedem Gerät wiederzufinden.',
      'Non hai effettuato l’accesso. Crea un account con la tua email per ritrovare le tue conversazioni da qualsiasi dispositivo.',
      'Você não está conectado. Crie uma conta com seu e-mail para encontrar suas conversas em qualquer aparelho.'
    ],
    'compte.affichage': ['Affichage', 'Display', 'Visualización', 'Anzeige', 'Visualizzazione', 'Exibição'],

    'compte.langue': ['Langue', 'Language', 'Idioma', 'Sprache', 'Lingua', 'Idioma'],
    'compte.langue_aide': [
      'La langue de l’interface : menus, boutons et messages du site. Les réponses du chatbot restent en français.',
      'The language of the interface: menus, buttons and site messages. The chatbot’s answers stay in French.',
      'El idioma de la interfaz: menús, botones y mensajes del sitio. Las respuestas del chatbot siguen en francés.',
      'Die Sprache der Oberfläche: Menüs, Schaltflächen und Meldungen. Die Antworten des Chatbots bleiben auf Französisch.',
      'La lingua dell’interfaccia: menu, pulsanti e messaggi del sito. Le risposte del chatbot restano in francese.',
      'O idioma da interface: menus, botões e mensagens do site. As respostas do chatbot continuam em francês.'
    ],
    'compte.langue_auto': [
      'Automatique (langue du navigateur)',
      'Automatic (browser language)',
      'Automático (idioma del navegador)',
      'Automatisch (Browsersprache)',
      'Automatico (lingua del browser)',
      'Automático (idioma do navegador)'
    ],

    'compte.theme': ['Thème', 'Theme', 'Tema', 'Design', 'Tema', 'Tema'],
    'compte.theme_aide': [
      '« Auto » suit le réglage clair/sombre de votre système d’exploitation.',
      '“Auto” follows your operating system’s light/dark setting.',
      '«Auto» sigue el ajuste claro/oscuro de tu sistema operativo.',
      '„Auto“ folgt der Hell-/Dunkel-Einstellung Ihres Betriebssystems.',
      '«Auto» segue l’impostazione chiaro/scuro del tuo sistema operativo.',
      '“Auto” segue a configuração clara/escura do seu sistema operacional.'
    ],
    'compte.theme_auto': ['Auto', 'Auto', 'Auto', 'Auto', 'Auto', 'Auto'],
    'compte.theme_clair': ['Clair', 'Light', 'Claro', 'Hell', 'Chiaro', 'Claro'],
    'compte.theme_sombre': ['Sombre', 'Dark', 'Oscuro', 'Dunkel', 'Scuro', 'Escuro'],

    'compte.animations': ['Animations', 'Animations', 'Animaciones', 'Animationen', 'Animazioni', 'Animações'],
    'compte.animations_aide': [
      '« Réduites » supprime les apparitions au défilement et les transitions. Le réglage « mouvement réduit » de votre système est respecté même en mode auto.',
      '“Reduced” removes scroll reveals and transitions. Your system’s “reduced motion” setting is honoured even in automatic mode.',
      '«Reducidas» elimina las apariciones al desplazarse y las transiciones. El ajuste «movimiento reducido» de tu sistema se respeta incluso en modo automático.',
      '„Reduziert“ entfernt Einblendungen beim Scrollen und Übergänge. Die Einstellung „Bewegung reduzieren“ Ihres Systems wird auch im Automatikmodus beachtet.',
      '«Ridotte» elimina le comparse allo scorrimento e le transizioni. L’impostazione «riduci movimento» del tuo sistema è rispettata anche in modalità automatica.',
      '“Reduzidas” remove as aparições ao rolar e as transições. A configuração “reduzir movimento” do seu sistema é respeitada mesmo no modo automático.'
    ],
    'compte.animations_completes': ['Complètes', 'Full', 'Completas', 'Vollständig', 'Complete', 'Completas'],
    'compte.animations_reduites': ['Réduites', 'Reduced', 'Reducidas', 'Reduziert', 'Ridotte', 'Reduzidas'],

    'compte.taille': ['Taille du texte des conversations', 'Conversation text size', 'Tamaño del texto de las conversaciones', 'Textgröße der Unterhaltungen', 'Dimensione del testo delle conversazioni', 'Tamanho do texto das conversas'],
    'compte.taille_aide': [
      'S’applique aux messages et au champ de saisie de la page de chat.',
      'Applies to the messages and the input field on the chat page.',
      'Se aplica a los mensajes y al campo de entrada de la página de chat.',
      'Gilt für die Nachrichten und das Eingabefeld der Chat-Seite.',
      'Si applica ai messaggi e al campo di inserimento della pagina della chat.',
      'Aplica-se às mensagens e ao campo de digitação da página de chat.'
    ],
    'compte.taille_petite': ['Petite', 'Small', 'Pequeño', 'Klein', 'Piccolo', 'Pequeno'],
    'compte.taille_normale': ['Normale', 'Normal', 'Normal', 'Normal', 'Normale', 'Normal'],
    'compte.taille_grande': ['Grande', 'Large', 'Grande', 'Groß', 'Grande', 'Grande'],

    'compte.note_affichage': [
      'Ces réglages sont enregistrés dans ce navigateur, sur cet appareil. Ils fonctionnent que vous soyez connecté ou non.',
      'These settings are saved in this browser, on this device. They work whether you are signed in or not.',
      'Estos ajustes se guardan en este navegador, en este dispositivo. Funcionan tanto si has iniciado sesión como si no.',
      'Diese Einstellungen werden in diesem Browser auf diesem Gerät gespeichert. Sie funktionieren, ob Sie angemeldet sind oder nicht.',
      'Queste impostazioni sono salvate in questo browser, su questo dispositivo. Funzionano che tu sia connesso o no.',
      'Estas configurações ficam salvas neste navegador, neste aparelho. Funcionam estando você conectado ou não.'
    ],

    'compte.chatbot': ['Chatbot', 'Chatbot', 'Chatbot', 'Chatbot', 'Chatbot', 'Chatbot'],
    'compte.sensibilite': ['Sensibilité des réponses', 'Answer sensitivity', 'Sensibilidad de las respuestas', 'Antwortempfindlichkeit', 'Sensibilità delle risposte', 'Sensibilidade das respostas'],
    'compte.sensibilite_aide': [
      'À partir de quelle confiance ChatPy ose répondre. « Stricte » répond moins souvent mais se trompe rarement ; « large » tente sa chance plus volontiers. Dans les deux cas, les questions écartées vous sont proposées sous « Vouliez-vous dire ».',
      'How confident ChatPy must be before it answers. “Strict” answers less often but is rarely wrong; “broad” takes its chances more readily. Either way, the questions it set aside are offered under “Did you mean”.',
      'Con cuánta confianza se atreve ChatPy a responder. «Estricta» responde menos a menudo pero se equivoca poco; «amplia» se arriesga más. En ambos casos, las preguntas descartadas se ofrecen en «¿Quisiste decir?».',
      'Ab welcher Konfidenz ChatPy zu antworten wagt. „Streng“ antwortet seltener, irrt sich aber kaum; „weit“ versucht es eher. In beiden Fällen werden verworfene Fragen unter „Meinten Sie“ vorgeschlagen.',
      'Con quanta sicurezza ChatPy osa rispondere. «Stretta» risponde meno spesso ma sbaglia di rado; «ampia» tenta più volentieri. In entrambi i casi, le domande scartate ti vengono proposte sotto «Intendevi dire».',
      'A partir de qual confiança o ChatPy se arrisca a responder. “Estrita” responde menos, mas erra pouco; “ampla” arrisca com mais facilidade. Nos dois casos, as perguntas descartadas aparecem em “Você quis dizer”.'
    ],
    'compte.sensibilite_stricte': ['Stricte', 'Strict', 'Estricta', 'Streng', 'Stretta', 'Estrita'],
    'compte.sensibilite_normale': ['Normale', 'Normal', 'Normal', 'Normal', 'Normale', 'Normal'],
    'compte.sensibilite_large': ['Large', 'Broad', 'Amplia', 'Weit', 'Ampia', 'Ampla'],

    'compte.suggestions': ['Suggestions de suivi', 'Follow-up suggestions', 'Sugerencias de seguimiento', 'Anschlussvorschläge', 'Suggerimenti di approfondimento', 'Sugestões de continuação'],
    'compte.suggestions_aide': [
      'Les questions proposées en boutons sous les réponses, pour continuer sur le même sujet ou rattraper une question mal comprise.',
      'The questions offered as buttons under the answers, to keep going on the same topic or to recover from a misread question.',
      'Las preguntas que aparecen como botones bajo las respuestas, para seguir con el mismo tema o corregir una pregunta mal entendida.',
      'Die Fragen, die als Schaltflächen unter den Antworten erscheinen – um beim Thema zu bleiben oder eine missverstandene Frage aufzufangen.',
      'Le domande proposte come pulsanti sotto le risposte, per continuare sullo stesso argomento o recuperare una domanda fraintesa.',
      'As perguntas oferecidas como botões abaixo das respostas, para continuar no mesmo assunto ou corrigir uma pergunta mal compreendida.'
    ],
    'compte.affichees': ['Affichées', 'Shown', 'Visibles', 'Angezeigt', 'Mostrati', 'Exibidas'],
    'compte.masquees': ['Masquées', 'Hidden', 'Ocultas', 'Ausgeblendet', 'Nascosti', 'Ocultas'],

    'compte.retours': ['Retour sur les réponses', 'Feedback on answers', 'Valoración de las respuestas', 'Rückmeldung zu Antworten', 'Riscontro sulle risposte', 'Retorno sobre as respostas'],
    'compte.retours_aide': [
      'Les boutons 👍 et 👎 sous chaque réponse. Le pouce vers le bas est le seul moyen de nous signaler une réponse trouvée mais fausse : les masquer nous prive de ce signal.',
      'The 👍 and 👎 buttons under each answer. A thumbs-down is the only way to report an answer that was found but wrong: hiding them takes that signal away from us.',
      'Los botones 👍 y 👎 bajo cada respuesta. El pulgar hacia abajo es la única forma de avisarnos de una respuesta encontrada pero equivocada: ocultarlos nos priva de esa señal.',
      'Die Schaltflächen 👍 und 👎 unter jeder Antwort. Der Daumen nach unten ist der einzige Weg, uns eine gefundene, aber falsche Antwort zu melden: Ausblenden nimmt uns dieses Signal.',
      'I pulsanti 👍 e 👎 sotto ogni risposta. Il pollice verso il basso è l’unico modo per segnalarci una risposta trovata ma sbagliata: nasconderli ci priva di questo segnale.',
      'Os botões 👍 e 👎 abaixo de cada resposta. O polegar para baixo é a única forma de nos avisar de uma resposta encontrada mas errada: ocultá-los nos tira esse sinal.'
    ],
    'compte.affiches': ['Affichés', 'Shown', 'Visibles', 'Angezeigt', 'Mostrati', 'Exibidos'],
    'compte.masques': ['Masqués', 'Hidden', 'Ocultos', 'Ausgeblendet', 'Nascosti', 'Ocultos'],

    'compte.saisie': ['Indicateur de saisie', 'Typing indicator', 'Indicador de escritura', 'Schreibanzeige', 'Indicatore di scrittura', 'Indicador de digitação'],
    'compte.saisie_aide': [
      'Les trois points animés pendant que ChatPy prépare sa réponse. « Directe » l’affiche dès qu’elle arrive, sans attente visible.',
      'The three animated dots while ChatPy prepares its answer. “Instant” shows the answer as soon as it lands, with no visible wait.',
      'Los tres puntos animados mientras ChatPy prepara su respuesta. «Directa» la muestra en cuanto llega, sin espera visible.',
      'Die drei animierten Punkte, während ChatPy die Antwort vorbereitet. „Direkt“ zeigt sie sofort an, ohne sichtbare Wartezeit.',
      'I tre puntini animati mentre ChatPy prepara la risposta. «Diretta» la mostra appena arriva, senza attesa visibile.',
      'Os três pontos animados enquanto o ChatPy prepara a resposta. “Direta” a exibe assim que chega, sem espera visível.'
    ],
    'compte.saisie_animee': ['Animé', 'Animated', 'Animada', 'Animiert', 'Animata', 'Animado'],
    'compte.saisie_directe': ['Directe', 'Instant', 'Directa', 'Direkt', 'Diretta', 'Direta'],

    'compte.note_chatbot': [
      'Enregistrés dans ce navigateur, comme les réglages d’affichage. La sensibilité accompagne chaque question envoyée : elle ne change rien pour les autres visiteurs.',
      'Saved in this browser, like the display settings. The sensitivity travels with each question you send: it changes nothing for other visitors.',
      'Guardados en este navegador, como los ajustes de visualización. La sensibilidad acompaña a cada pregunta enviada: no cambia nada para los demás visitantes.',
      'In diesem Browser gespeichert, wie die Anzeigeeinstellungen. Die Empfindlichkeit begleitet jede gesendete Frage: Für andere Besucher ändert sich nichts.',
      'Salvate in questo browser, come le impostazioni di visualizzazione. La sensibilità accompagna ogni domanda inviata: non cambia nulla per gli altri visitatori.',
      'Salvas neste navegador, como as configurações de exibição. A sensibilidade acompanha cada pergunta enviada: não muda nada para os outros visitantes.'
    ]
  };

  // ── Résolution de la langue ────────────────────────────────────────────────

  function langueDuNavigateur() {
    var demandees = (window.navigator && (navigator.languages || [navigator.language])) || [];
    for (var i = 0; i < demandees.length; i++) {
      // « fr-CA », « pt-BR » : seule la partie avant le tiret nous concerne, ce
      // projet ne distingue pas les variantes régionales.
      var code = String(demandees[i] || '').toLowerCase().split('-')[0];
      if (LANGUES.indexOf(code) !== -1) return code;
    }
    return 'fr';
  }

  function langueChoisie() {
    var brut = window.ChatPyPrefs ? window.ChatPyPrefs.lire().langue : 'auto';
    return brut && brut !== 'auto' ? brut : langueDuNavigateur();
  }

  var langue = langueChoisie();

  function indexLangue() {
    var index = LANGUES.indexOf(langue);
    return index === -1 ? 0 : index;
  }

  /** Le texte d'une clé dans la langue courante, {jeton} remplacés. */
  function t(cle, params) {
    var ligne = TEXTES[cle];
    // Clé inconnue : on rend la clé elle-même. Une chaîne vide effacerait un
    // bouton sans rien dire ; « chat.renommer » à l'écran désigne le coupable.
    if (!ligne) return cle;
    // Une traduction absente retombe sur le français plutôt que sur du vide :
    // une phrase dans la mauvaise langue reste lisible, une phrase manquante non.
    var texte = ligne[indexLangue()];
    if (texte == null || texte === '') texte = ligne[0] || '';
    if (!params) return texte;
    return texte.replace(/\{(\w+)\}/g, function (entier, nom) {
      return Object.prototype.hasOwnProperty.call(params, nom) ? String(params[nom]) : entier;
    });
  }

  // ── Application au document ───────────────────────────────────────────────
  //
  //   data-i18n="cle"                        → textContent
  //   data-i18n-html="cle"                   → innerHTML (balisage du catalogue)
  //   data-i18n-attr="placeholder:cle;title:cle2" → attributs
  //
  // Le HTML garde son texte français : c'est lui qui s'affiche sans JavaScript,
  // et c'est aussi ce que voit un moteur de recherche qui n'exécute rien.

  function appliquerA(racine) {
    racine.querySelectorAll('[data-i18n]').forEach(function (noeud) {
      var valeur = t(noeud.getAttribute('data-i18n'));
      if (valeur !== '') noeud.textContent = valeur;
    });

    racine.querySelectorAll('[data-i18n-html]').forEach(function (noeud) {
      var valeur = t(noeud.getAttribute('data-i18n-html'));
      if (valeur !== '') noeud.innerHTML = valeur;
    });

    racine.querySelectorAll('[data-i18n-attr]').forEach(function (noeud) {
      noeud.getAttribute('data-i18n-attr').split(';').forEach(function (paire) {
        var morceaux = paire.split(':');
        if (morceaux.length !== 2) return;
        var attribut = morceaux[0].trim();
        var valeur = t(morceaux[1].trim());
        if (attribut && valeur !== '') noeud.setAttribute(attribut, valeur);
      });
    });
  }

  /* Le voile.

     Traduire demande un document parsé, donc au plus tôt DOMContentLoaded — et
     rien ne garantit que le navigateur n'aura pas déjà peint la page en
     français. Plutôt que ce clignotement, on masque brièvement le corps, mais
     seulement quand il y a effectivement quelque chose à réécrire (langue ≠ fr)
     et seulement depuis JavaScript : sans lui, la classe n'est jamais posée et
     la page s'affiche telle quelle, en français.

     Le garde-fou compte : si une erreur survenait pendant la traduction, une
     page durablement invisible serait bien pire qu'un clignotement. */
  var DELAI_MAX_VOILE = 1200;

  function poserVoile() {
    if (langue === 'fr') return;
    var style = document.createElement('style');
    style.id = 'i18n-voile';
    style.textContent = 'html.i18n-attente body { visibility: hidden !important; }';
    (document.head || document.documentElement).appendChild(style);
    document.documentElement.classList.add('i18n-attente');
    window.setTimeout(leverVoile, DELAI_MAX_VOILE);
  }

  function leverVoile() {
    document.documentElement.classList.remove('i18n-attente');
  }

  function traduireDocument() {
    try {
      appliquerA(document);
    } finally {
      leverVoile();
    }
  }

  // `lang` est toujours posé, jamais retiré : un document sans langue déclarée
  // dégrade la synthèse vocale et la coupure de mots. C'est aussi pour ça que
  // ce réglage n'est pas un simple `attribut` du SCHEMA de preferences.js, qui
  // efface l'attribut sur la valeur par défaut.
  document.documentElement.setAttribute('lang', langue);
  poserVoile();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', traduireDocument);
  } else {
    traduireDocument();
  }

  // Changer de langue depuis /compte réécrit la page en place : recharger
  // ferait perdre la position de défilement et, sur /chat, la conversation
  // affichée. Les scripts de page réagissent au même évènement pour retraduire
  // ce qu'ils ont eux-mêmes construit.
  document.addEventListener('chatpy:prefs', function (event) {
    if (!event.detail || event.detail.cle !== 'langue') return;
    langue = langueChoisie();
    document.documentElement.setAttribute('lang', langue);
    appliquerA(document);
    document.dispatchEvent(new CustomEvent('chatpy:langue', { detail: { langue: langue } }));
  });

  window.ChatPyI18n = {
    t: t,
    /** Le code réellement appliqué, « auto » résolu. */
    langue: function () { return langue; },
    langues: function () { return LANGUES.slice(); },
    nom: function (code) { return NOMS_LANGUES[code] || code; },
    /** Retraduit un fragment construit en JavaScript après coup. */
    appliquer: appliquerA
  };
})();
