(function () {
  'use strict';
  var form = document.getElementById('formSignalement');
  var etat = document.getElementById('etatSignalement');
  if (!form || !etat) return;

  if (window.ChatPyMoi) {
    window.ChatPyMoi.then(function (moi) {
      var champEmail = form.elements.email;
      if (moi && moi.connecte && moi.email && !champEmail.value) champEmail.value = moi.email;
    });
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    var bouton = form.querySelector('button[type="submit"]');
    bouton.disabled = true;
    etat.removeAttribute('data-erreur');
    etat.textContent = 'Envoi en cours…';
    var champs = new FormData(form);
    try {
      var reponse = await fetch('/api/signalements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          categorie: champs.get('categorie'),
          resume: champs.get('resume'),
          email: champs.get('email'),
          description: champs.get('description'),
          page: document.referrer || window.location.pathname
        })
      });
      var resultat = await reponse.json();
      if (!reponse.ok) throw new Error(resultat.error || 'Impossible d’envoyer le signalement.');
      form.reset();
      etat.textContent = 'Merci pour votre signalement ! Nous avons bien reçu votre message et reviendrons vers vous à l’adresse e-mail indiquée.';
    } catch (erreur) {
      etat.dataset.erreur = 'true';
      etat.textContent = erreur.message || 'Une erreur est survenue. Réessayez.';
    } finally {
      bouton.disabled = false;
    }
  });
})();
