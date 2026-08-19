import re
import os
import json
import random
import datetime
import tempfile
import threading
import unicodedata
from difflib import get_close_matches, SequenceMatcher

_DIR              = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE      = os.path.join(_DIR, ".chatpy_history.json")
FAQ_FILE          = os.path.join(_DIR, "faq.json")
AIDE_CONCEPTS_FILE = os.path.join(_DIR, "aide_concepts.json")
QUESTIONS_SANS_REPONSE_FILE = os.path.join(_DIR, "questions_sans_reponse.json")

# Nombre de messages conservés dans .chatpy_history.json.
#
# Ce plafond n'est pas une limite de confort mais de coût : le fichier est
# relu et réécrit *intégralement à chaque message*. À environ 220 octets par
# entrée, un plafond d'un million faisait 210 Mo d'écriture par message une
# fois atteint — de quoi mettre à genoux un site public bien avant d'y arriver.
# À 2 000, le fichier plafonne vers 450 Ko, ce qui reste instantané.
#
# Ce journal sert le contexte du bot, pas l'historique de qui que ce soit :
# les conversations que les utilisateurs consultent vivent dans
# conversations.json (par compte) ou dans leur navigateur. Le tronquer ne fait
# donc perdre à personne ses conversations.
HISTORIQUE_MAX_MESSAGES = 2000

# Commandes qui n'ont de sens que dans le terminal (elles pilotent la boucle
# interactive). Elles n'atteignent chatbot_response() que depuis le chat web.
COMMANDES_TERMINAL = ("clear", "historique")

QUIZ_NB_QUESTIONS = 10
QUIZ_MOTS_ARRET   = ("fin", "exit", "quitter", "terminé")
QUIZ_SEUIL_BONNE   = 70   # similarité ≥ 70% : réponse comptée juste
QUIZ_SEUIL_PRESQUE = 35   # entre 35% et 70% : sur la bonne piste

MOTS_AU_REVOIR = ["au revoir", "aurevoir", "a bientot", "à bientôt", "bye", "quit", "exit"]

# Mots (déjà normalisés : sans accents) qui ne portent pas le sujet d'une question.
# "comment faire une boucle" et "qu'est-ce qu'une boucle" doivent tous deux se
# résumer à {boucle} : c'est le vocabulaire restant qui distingue les questions.
MOTS_VIDES = frozenset({
    "le", "la", "les", "l", "un", "une", "des", "du", "de", "d", "en", "et",
    "ou", "a", "au", "aux", "ce", "cette", "ces", "c", "que", "qu", "qui",
    "quoi", "est", "sont", "je", "tu", "il", "elle", "on", "nous", "vous",
    "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "se", "s",
    "ne", "pas", "plus", "pour", "par", "dans", "sur", "avec", "sans",
    "comment", "pourquoi", "quand", "quel", "quelle", "quels", "quelles",
    "faire", "fait", "peut", "peux", "dois", "dis", "moi", "te", "y", "si",
    "sert", "veut", "dire", "donc", "alors", "tout", "tous", "toute",
    # génériques omniprésents dans les réponses de la FAQ (utile au quiz)
    "exemple", "utilisez", "utiliser", "utilise", "methode", "mot", "cle", "cles",
})

# Poids du recouvrement de vocabulaire dans le score de correspondance : le
# sujet évoqué compte plus que la ressemblance lettre à lettre, sinon
# "supprimer une variable" matche "déclarer une variable" avec 85% de confiance.
POIDS_MOTS = 0.55
SEUIL_CORRESPONDANCE = 0.5

# Sous SEUIL_CORRESPONDANCE on ne répond pas, mais entre ce seuil bas et lui la
# question de la FAQ reste assez proche pour valoir un « vouliez-vous dire ? ».
# Plus bas, les propositions deviennent du bruit qui ressemble à du hasard.
SEUIL_PROPOSITION = 0.3

# Sensibilité du bot, réglable par visiteur depuis /compte. Un seul curseur est
# exposé — le seuil à partir duquel le bot ose répondre plutôt que d'avouer
# qu'il n'a pas compris :
#   stricte — répond moins souvent, mais presque jamais à côté de la plaque ;
#   large   — répond plus souvent, au prix de rapprochements discutables.
# Toutes les valeurs restent au-dessus de SEUIL_PROPOSITION : en dessous, la
# bande des « vouliez-vous dire ? » se refermerait et un échec ne proposerait
# plus rien. Baisser le seuil ne fait donc jamais perdre le filet de rattrapage.
SENSIBILITES = {
    "stricte": 0.65,
    "normale": SEUIL_CORRESPONDANCE,
    "large": 0.38,
}
SENSIBILITE_DEFAUT = "normale"


def seuil_de_sensibilite(nom):
    """Seuil de réponse correspondant à un nom de sensibilité.

    Un nom inconnu (front plus récent que le serveur, requête bricolée à la
    main) retombe sur la normale au lieu d'être refusé : ce réglage est un
    confort d'affichage, pas une autorisation à contrôler.
    """
    return SENSIBILITES.get(nom, SENSIBILITES[SENSIBILITE_DEFAUT])

# Réponse d'échec, renvoyée telle quelle : les front-ends la reconnaissent pour
# proposer des questions proches plutôt que de laisser l'utilisateur sans issue.
REPONSE_INCOMPRISE = ("❌ Désolé, je ne comprends pas votre question ou elle ne se situe pas dans "
                      "le catalogue de questions. Essayez de poser une question sur Python ou "
                      "tapez 'help' pour l'aide.")

TITRE_QUESTIONS_LIEES = "Questions liées"
TITRE_QUESTIONS_PROCHES = "Vouliez-vous dire"

# Le serveur Flask est multi-thread : deux requêtes peuvent écrire en même temps.
_verrou_historique = threading.Lock()
_verrou_questions  = threading.Lock()


def _ecrire_json_atomique(chemin, donnees):
    """Écrit le JSON dans un fichier temporaire voisin, puis le renomme.

    os.replace() est atomique : un lecteur voit soit l'ancienne version complète,
    soit la nouvelle, jamais un fichier à moitié écrit. Un simple open(chemin, 'w')
    tronque le fichier avant d'écrire, et le perd si le process meurt entre-temps.
    """
    dossier = os.path.dirname(chemin) or "."
    fd, tmp = tempfile.mkstemp(dir=dossier, prefix=".tmp_chatpy_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, chemin)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _mettre_de_cote(chemin, raison):
    """Renomme un fichier illisible au lieu de l'écraser en silence."""
    sauvegarde = chemin + ".corrompu"
    try:
        os.replace(chemin, sauvegarde)
        print(f"⚠️  {raison}\n    Fichier mis de côté dans '{os.path.basename(sauvegarde)}'.")
    except OSError:
        print(f"⚠️  {raison}")


def normaliser_texte(texte):
    texte = unicodedata.normalize('NFKD', texte)
    texte = texte.encode('ASCII', 'ignore').decode('ASCII')
    texte = re.sub(r'[^\w\s]', ' ', texte)
    texte = re.sub(r'\s+', ' ', texte).strip()
    return texte.lower()


def calcul_similarite(texte1, texte2):
    return SequenceMatcher(None, texte1, texte2).ratio()


def _contient_mot(message, mots):
    """Vrai si l'un des mots/phrases apparaît comme mot(s) entier(s) dans message (pas comme sous-chaîne)."""
    return any(re.search(r'\b' + re.escape(mot) + r'\b', message) for mot in mots)


def _mots_significatifs(texte_norm):
    """Mots porteurs de sens d'un texte déjà passé par normaliser_texte()."""
    return {m for m in texte_norm.split() if m not in MOTS_VIDES and len(m) > 1}


def _recouvrement_mots(mots_a, mots_b):
    """Part des mots de mots_a retrouvés dans mots_b (à une faute de frappe près),
    rapportée au plus grand des deux ensembles pour pénaliser le vocabulaire manquant."""
    if not mots_a or not mots_b:
        return 0.0
    retrouves = sum(1 for mot in mots_a if get_close_matches(mot, mots_b, n=1, cutoff=0.8))
    return retrouves / max(len(mots_a), len(mots_b))


def _score_correspondance(message_norm, question_norm):
    """Score hybride entre 0 et 1 : ressemblance des lettres + recouvrement du vocabulaire.

    La similarité de caractères seule confond des questions au sens opposé qui ne
    diffèrent que d'un mot ("supprimer"/"déclarer" une variable) ; le vocabulaire
    seul rate les fautes de frappe. Les deux combinés se corrigent mutuellement.
    """
    sim_car = calcul_similarite(message_norm, question_norm)
    recouvrement = _recouvrement_mots(_mots_significatifs(message_norm),
                                      _mots_significatifs(question_norm))
    return (1 - POIDS_MOTS) * sim_car + POIDS_MOTS * recouvrement


def _charger_json(chemin, nom):
    try:
        with open(chemin, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Fichier '{nom}' introuvable — relancez depuis le dossier du projet.")
        return {}
    except json.JSONDecodeError as e:
        print(f"⚠️  Erreur de format dans '{nom}' : {e}")
        return {}


# Chargement de la FAQ et des concepts depuis les fichiers JSON
faq_categories = _charger_json(FAQ_FILE, "faq.json")
aide_concepts   = _charger_json(AIDE_CONCEPTS_FILE, "aide_concepts.json")

faq = {}
for _cat, _questions in faq_categories.items():
    faq.update(_questions)

norm_vers_original = {normaliser_texte(q): q for q in faq}


def _scanner_faq(message_normalise):
    """Toute la FAQ notée face au message, de la meilleure à la moins bonne.

    Retourne des paires (question d'origine, confiance en %). Le seul passage
    coûteux du matching : chatbot_response() en tire sa réponse, et
    questions_proches() les quasi-correspondances qu'il a écartées.
    """
    scores = [(original_q, int(_score_correspondance(message_normalise, norm_q) * 100))
              for norm_q, original_q in norm_vers_original.items()]
    scores.sort(key=lambda paire: paire[1], reverse=True)
    return scores


def questions_proches(message, limite=3, seuil=None):
    """Questions de la FAQ trop peu sûres pour être répondues, mais assez proches
    pour être proposées après un « je ne comprends pas ».

    Le score seul ne suffit pas : la ressemblance des lettres fait remonter des
    questions sans aucun rapport ("dresser un lama" → "décompresser un tuple").
    On exige donc au moins un mot de sujet en commun, à une faute près.

    `seuil` est le plafond de la bande, c'est-à-dire le seuil de réponse
    effectivement appliqué. Il doit rester celui qui a servi à répondre, sinon
    la bande et la réponse se désaccordent : en sensibilité stricte, une
    question écartée à 60% doit reparaître ici, et non tomber dans le vide.
    """
    if seuil is None:
        seuil = SEUIL_CORRESPONDANCE
    message_normalise = normaliser_texte(message)
    mots_message = _mots_significatifs(message_normalise)
    if not mots_message:
        return []

    proches = []
    for q, conf in _scanner_faq(message_normalise):
        if not SEUIL_PROPOSITION * 100 <= conf < seuil * 100:
            continue
        if _recouvrement_mots(mots_message, _mots_significatifs(normaliser_texte(q))) > 0:
            proches.append(q)
        if len(proches) == limite:
            break
    return proches


def _formater_concept(concept):
    """Formate un concept de aide_concepts.json pour l'affichage terminal."""
    lignes = [f"📖 {concept['titre']}", ""]
    lignes.append(f"Définition : {concept['definition']}")
    lignes.append("")

    for niveau in concept["niveaux"]:
        lignes.append(f"━━ {niveau['niveau']}")
        lignes.append(niveau["code"])
        lignes.append("")

    if concept.get("erreurs_courantes"):
        lignes.append("⚠️  Erreurs courantes :")
        for err in concept["erreurs_courantes"]:
            lignes.append(f"  • {err}")
        lignes.append("")

    if concept.get("a_retenir"):
        lignes.append(f"💡 À retenir : {concept['a_retenir']}")

    return "\n".join(lignes)


def _vaut_la_peine_d_etre_logguee(message):
    """Le journal ne sert à repérer les trous de la FAQ que s'il ne contient que de vraies questions.

    Un mot isolé ('quoi', 'comment') ou un pavé de plusieurs milliers de caractères
    ne désigne aucun sujet à ajouter : c'est du bruit qui noie les vraies lacunes.
    """
    norm = normaliser_texte(message)
    return len(norm.split()) >= 2 and 5 <= len(norm) <= 200


def _logger_question_sans_reponse(message):
    """Enregistre une question sans réponse dans questions_sans_reponse.json pour repérer les trous de la FAQ."""
    _incrementer_journal(message, "occurrences")


def signaler_reponse_inutile(message):
    """Enregistre une question dont la réponse a été jugée inutile (pouce vers le bas).

    Une réponse trouvée mais mauvaise est invisible dans le journal, qui ne
    retient que les échecs complets : ce compteur-là repère les questions qui
    matchent une entrée de la FAQ, mais pas la bonne.
    """
    _incrementer_journal(message, "pouces_bas")


def _incrementer_journal(message, champ):
    """Incrémente un compteur du journal des lacunes pour cette question."""
    if not _vaut_la_peine_d_etre_logguee(message):
        return

    cle = normaliser_texte(message)
    aujourdhui = datetime.date.today().isoformat()

    # Lecture + modification + écriture doivent être indivisibles, sinon deux
    # requêtes simultanées se marchent dessus et un compteur est perdu.
    with _verrou_questions:
        try:
            with open(QUESTIONS_SANS_REPONSE_FILE, 'r', encoding='utf-8') as f:
                donnees = json.load(f)
            if not isinstance(donnees, dict):
                raise ValueError("le journal doit être un objet JSON")
        except FileNotFoundError:
            donnees = {}
        except (json.JSONDecodeError, ValueError):
            _mettre_de_cote(QUESTIONS_SANS_REPONSE_FILE, "Journal des questions sans réponse illisible.")
            donnees = {}

        entree = donnees.get(cle)
        if not isinstance(entree, dict):
            entree = {"texte": message, "occurrences": 0, "pouces_bas": 0}
            donnees[cle] = entree
        # Les entrées écrites avant l'ajout des pouces n'ont pas le champ.
        entree[champ] = entree.get(champ, 0) + 1
        entree["derniere_fois"] = aujourdhui

        try:
            _ecrire_json_atomique(QUESTIONS_SANS_REPONSE_FILE, donnees)
        except OSError:
            pass


def _chercher_concept(sujet):
    """Retourne le concept correspondant au sujet, ou None si introuvable."""
    sujet_norm = normaliser_texte(sujet)

    # Correspondance directe sur la clé
    if sujet_norm in aide_concepts:
        return aide_concepts[sujet_norm]

    # Recherche par mots-clés dans chaque concept. La correspondance par
    # sous-chaîne est réservée aux sujets d'au moins 3 lettres : "e" est une
    # sous-chaîne de presque tous les mots-clés et renverrait le premier concept venu.
    for concept in aide_concepts.values():
        for mot in concept.get("mots_cles", []):
            mot_norm = normaliser_texte(mot)
            if sujet_norm == mot_norm:
                return concept
            if len(sujet_norm) >= 3 and (sujet_norm in mot_norm or mot_norm in sujet_norm):
                return concept

    # Fuzzy matching sur les clés
    matches = get_close_matches(sujet_norm, aide_concepts.keys(), n=1, cutoff=0.5)
    if matches:
        return aide_concepts[matches[0]]

    return None


def chatbot_response(message, seuil=None, trace=None):
    """Réponse du bot, en texte.

    `seuil` est la confiance minimale pour oser répondre ; None applique
    SEUIL_CORRESPONDANCE, c'est-à-dire la sensibilité normale.

    `trace`, si un dict est fourni, reçoit sous la clé "question" l'entrée de la
    FAQ effectivement retenue — rien du tout pour une commande, une salutation
    ou un échec. Les suggestions de suivi en ont besoin : les chercher à partir
    du message tapé exigeait la formulation exacte, alors que tout le pipeline
    ci-dessous existe justement pour absorber les reformulations. Un paramètre
    de sortie plutôt qu'un tuple parce que cette fonction est l'entrée du
    pipeline pour le CLI et une vingtaine de tests : changer son type de retour
    les aurait tous touchés pour un besoin qui ne concerne que repondre().
    Le dict appartient à l'appelant, donc rien n'est partagé entre threads.
    """
    if seuil is None:
        seuil = SEUIL_CORRESPONDANCE
    message = message.lower().strip()

    # aide <sujet> — explication progressive débutant → avancé
    if message.startswith("aide "):
        sujet = message[5:].strip()
        concept = _chercher_concept(sujet)
        if concept:
            return _formater_concept(concept)
        else:
            sujets_dispo = ", ".join(aide_concepts.keys())
            return (f"❌ Concept '{sujet}' introuvable.\n"
                    f"Sujets disponibles : {sujets_dispo}\n"
                    f"Exemple : aide variable  |  aide boucle  |  aide classe")

    # Commandes spéciales
    if message in ["help", "aide", "?"]:
        return ("Commandes disponibles :\n"
                "  liste              — toutes les questions par catégorie\n"
                "  liste <catégorie>  — questions d'une seule catégorie (ex: liste fonctions)\n"
                "  cherche <mot>      — questions contenant un mot-clé (ex: cherche liste)\n"
                "  aide <sujet>       — explication détaillée débutant→avancé (ex: aide boucle)\n"
                "  quiz               — tester vos connaissances Python\n"
                "  historique         — relire la conversation ⚠️ utilisable uniquement via terminal\n"
                "  clear              — effacer l'écran (l'historique reste sauvegardé) ⚠️ utilisable uniquement via terminal\n"
                "  au revoir          — quitter\n\n"
                "Ou posez directement une question sur Python.")

    # Commandes réservées au terminal : la boucle CLI les intercepte avant d'arriver
    # ici, donc on n'y passe que depuis le chat web, où elles n'ont pas de sens.
    if message in COMMANDES_TERMINAL:
        return (f"💡 Désolé, la commande '{message}' ne marche pas ici, dans le chat web.\n"
                f"Elle a été faite pour la version terminal de ChatPy, où elle fonctionne "
                f"(lancez : python3 ia_en_python.py).\n"
                f"Ici, posez directement une question sur Python ou tapez 'help'.")

    # liste <catégorie> — afficher uniquement une catégorie
    if message.startswith("liste "):
        nom_cat = message[6:].strip()
        nom_cat_norm = normaliser_texte(nom_cat)

        cats_trouvees = [c for c in faq_categories if nom_cat_norm in normaliser_texte(c)]

        if not cats_trouvees:
            noms_norm = {normaliser_texte(c): c for c in faq_categories}
            matches = get_close_matches(nom_cat_norm, noms_norm.keys(), n=2, cutoff=0.4)
            cats_trouvees = [noms_norm[m] for m in matches]

        if cats_trouvees:
            result = ""
            for cat in cats_trouvees:
                result += f"📚 {cat}:\n"
                for q in faq_categories[cat]:
                    result += f"  • {q}\n"
                result += "\n"
            return result.strip()
        else:
            dispo = ", ".join(faq_categories.keys())
            return f"❌ Catégorie '{nom_cat}' introuvable.\nCatégories disponibles : {dispo}"

    # cherche <mot> — rechercher un mot-clé dans toutes les questions
    if message.startswith("cherche "):
        mot_cle = message[8:].strip()
        mot_cle_norm = normaliser_texte(mot_cle)

        resultats = []
        for cat, questions in faq_categories.items():
            for q in questions:
                if mot_cle_norm in normaliser_texte(q):
                    resultats.append((cat, q))

        if resultats:
            result = f"🔍 Questions contenant '{mot_cle}' :\n"
            cat_actuelle = None
            for cat, q in resultats:
                if cat != cat_actuelle:
                    result += f"\n📚 {cat}:\n"
                    cat_actuelle = cat
                result += f"  • {q}\n"
            return result
        else:
            return (f"❌ Aucune question ne contient '{mot_cle}'.\n"
                    f"Essayez un mot plus général ou tapez 'liste' pour tout voir.")

    if message == "liste":
        result = "Voici les questions que je peux répondre :\n\n"
        for category, questions in faq_categories.items():
            result += f"\n📚 {category}:\n"
            for q in questions.keys():
                result += f"  • {q}\n"
        return result

    message_normalise = normaliser_texte(message)

    # 1. Recherche exacte normalisée
    if message_normalise in norm_vers_original:
        original_q = norm_vers_original[message_normalise]
        if trace is not None:
            trace["question"] = original_q
        return f"✓ {faq[original_q]}\n\n💡 Confiance: 100%"

    # 2. Recherche par score hybride (lettres + vocabulaire) sur toute la FAQ.
    # Un seul passage remplace l'ancien duo fuzzy matching / similarité brute :
    # il tolère les fautes de frappe ET les reformulations ("c'est quoi une liste").
    scores = _scanner_faq(message_normalise)
    meilleures_correspondances = [
        (q, faq[q], conf) for q, conf in scores if conf >= seuil * 100
    ]

    if meilleures_correspondances:
        meilleure_q, best_answer, confiance = meilleures_correspondances[0]
        if trace is not None:
            trace["question"] = meilleure_q
        response = f"✓ {best_answer}\n\n💡 Confiance: {confiance}%"
        if confiance < 70 and len(meilleures_correspondances) > 1:
            response += "\n\nℹ️ D'autres réponses possibles :\n"
            for q, _, conf in meilleures_correspondances[1:3]:
                response += f"  • {q} ({conf}%)\n"
        return response

    # Réponses conversationnelles
    if _contient_mot(message, ["bonjour", "salut", "hello", "hi"]):
        return "👋 Bonjour ! Posez-moi une question sur Python ou tapez 'help' pour l'aide."
    elif _contient_mot(message, ["ça va bien", "tu vas bien"]):
        return "🤖 Je suis une Intelligence Artificielle, donc je vais toujours bien ! Comment puis-je vous aider avec Python aujourd'hui ?"
    elif _contient_mot(message, ["ton nom", "appelles", "qui es-tu"]):
        return "📖 Je suis un chatbot Python qui peut répondre à des questions sur le code."
    elif _contient_mot(message, ["merci"]):
        return "😊 De rien ! N'hésitez pas si vous avez d'autres questions sur Python."
    elif _contient_mot(message, MOTS_AU_REVOIR):
        return "👋 Au revoir ! Continue à apprendre Python le plus possible !"
    else:
        # Le journal des lacunes reste jugé au seuil par défaut, jamais à celui
        # du visiteur : une question que la FAQ traite très bien, laissée sans
        # réponse parce que ce visiteur a demandé « stricte », n'est pas une
        # lacune de la FAQ. La consigner enverrait lacunes.py réécrire une
        # entrée qui n'a rien à se reprocher.
        if not scores or scores[0][1] < SEUIL_CORRESPONDANCE * 100:
            _logger_question_sans_reponse(message)
        return REPONSE_INCOMPRISE


def print_colored(text, color, bold=False):
    codes = {
        "blue":   ("\033[94m",   "\033[1;94m"),
        "green":  ("\033[92m",   "\033[1;92m"),
        "yellow": ("\033[93m",   "\033[1;93m"),
        "red":    ("\033[91m",   "\033[1;91m"),
    }
    normal, gras = codes.get(color, ("\033[0m", "\033[1m"))
    code = gras if bold else normal
    print(f"{code}{text}\033[0m")


def choisir_question_quiz(derniere_question=None):
    """Tire une question au hasard, sans reposer celle qui vient d'être posée.

    Retourne (question, réponse), ou None si la FAQ est vide.
    """
    questions = list(faq.items())
    if not questions:
        return None
    if derniere_question is not None and len(questions) > 1:
        questions = [qr for qr in questions if qr[0] != derniere_question]
    return random.choice(questions)


def evaluer_reponse_quiz(reponse, bonne_reponse):
    """Compare la réponse de l'utilisateur à celle attendue.

    La réponse de la FAQ contient du code d'exemple que personne ne restitue mot
    pour mot : exiger une ressemblance lettre à lettre condamnait des réponses
    justes. On retient le meilleur de deux angles — la formulation complète, ou
    la part des mots significatifs de l'utilisateur retrouvés dans la réponse
    attendue (répondre "append" à "comment ajouter un élément à une liste" suffit).

    Retourne (similarité en %, verdict) où verdict vaut "bonne", "presque" ou "fausse".
    """
    reponse_norm = normaliser_texte(reponse)
    attendue_norm = normaliser_texte(bonne_reponse)

    sim_texte = calcul_similarite(reponse_norm, attendue_norm)

    mots_reponse = _mots_significatifs(reponse_norm)
    mots_attendus = _mots_significatifs(attendue_norm)
    if mots_reponse and mots_attendus:
        retrouves = sum(1 for mot in mots_reponse
                        if get_close_matches(mot, mots_attendus, n=1, cutoff=0.8))
        precision = retrouves / len(mots_reponse)
    else:
        precision = 0.0

    sim = int(max(sim_texte, precision) * 100)
    if sim >= QUIZ_SEUIL_BONNE:
        return sim, "bonne"
    if sim >= QUIZ_SEUIL_PRESQUE:
        return sim, "presque"
    return sim, "fausse"


def _bilan_quiz(score, total):
    if total == 0:
        return "Quiz terminé. Aucune question répondue."
    return f"📊 Score final : {score}/{total} ({int(score / total * 100)}%)\n\nTapez 'quiz' pour rejouer."


# ── Quiz côté web ────────────────────────────────────────────────────────────
# Le chat web est sans état : chaque message est une requête HTTP isolée. Le quiz
# est donc une machine à états dont l'état (dict sérialisable) est confié à
# l'appelant — app.py le range dans la session Flask, propre à chaque navigateur.
# On n'y stocke que l'énoncé : la réponse attendue ne quitte jamais le serveur.

def demarrer_quiz(nb_questions=QUIZ_NB_QUESTIONS):
    """Ouvre une session de quiz. Retourne (état, message) ; état vaut None si impossible."""
    tirage = choisir_question_quiz()
    if tirage is None:
        return None, "❌ Le quiz est indisponible : aucune question n'est chargée."

    question, _ = tirage
    etat = {"question": question, "score": 0, "total": 0, "max": nb_questions}
    entete = (f"🎯 Mode Quiz — {nb_questions} questions, répondez de mémoire.\n"
              f"Tapez 'fin' à tout moment pour arrêter.")
    return etat, f"{entete}\n\n❓ (1/{nb_questions}) {question} ?"


def repondre_quiz(etat, message):
    """Corrige une réponse et enchaîne. Retourne (état, message) ; état vaut None quand le quiz est fini."""
    if message.strip().lower() in QUIZ_MOTS_ARRET:
        return None, _bilan_quiz(etat["score"], etat["total"])

    bonne_reponse = faq.get(etat["question"])
    if bonne_reponse is None:          # la FAQ a changé sous les pieds du joueur
        return None, "❌ Question introuvable, le quiz est interrompu."

    sim, verdict = evaluer_reponse_quiz(message, bonne_reponse)
    etat["total"] += 1
    if verdict == "bonne":
        etat["score"] += 1
        entete = f"✅ Bonne réponse ! (similarité : {sim}%)"
    elif verdict == "presque":
        entete = f"⚠️ Presque ! (similarité : {sim}%)"
    else:
        entete = f"❌ Pas tout à fait. (similarité : {sim}%)"

    blocs = [entete, f"💡 Réponse attendue :\n{bonne_reponse}"]

    if etat["total"] >= etat["max"]:
        blocs.append(_bilan_quiz(etat["score"], etat["total"]))
        return None, "\n\n".join(blocs)

    tirage = choisir_question_quiz(etat["question"])
    if tirage is None:
        blocs.append(_bilan_quiz(etat["score"], etat["total"]))
        return None, "\n\n".join(blocs)

    etat["question"] = tirage[0]
    blocs.append(f"❓ ({etat['total'] + 1}/{etat['max']}) {etat['question']} ?")
    return etat, "\n\n".join(blocs)


def mode_quiz(nb_questions_max=QUIZ_NB_QUESTIONS):
    """Lance une session de quiz interactif sur les questions de la FAQ (terminal)."""
    tirage = choisir_question_quiz()
    if tirage is None:
        print_colored("❌ Le quiz est indisponible : aucune question n'est chargée.", "red")
        return

    question, bonne_reponse = tirage
    score = 0
    total = 0

    print_colored(f"\n🎯 Mode Quiz — {nb_questions_max} questions, répondez de mémoire, tapez 'fin' pour arrêter avant la fin.\n", "yellow", bold=True)

    while total < nb_questions_max:
        print_colored(f"❓ ({total + 1}/{nb_questions_max}) {question} ?", "blue")

        try:
            reponse = input("📝 Votre réponse : ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if reponse.lower() in QUIZ_MOTS_ARRET:
            break

        sim, verdict = evaluer_reponse_quiz(reponse, bonne_reponse)
        total += 1

        if verdict == "bonne":
            score += 1
            print_colored(f"✅ Bonne réponse ! (similarité : {sim}%)", "green")
        elif verdict == "presque":
            print_colored(f"⚠️  Presque ! (similarité : {sim}%)", "yellow")
        else:
            print_colored(f"❌ Pas tout à fait. (similarité : {sim}%)", "red")

        print(f"💡 Réponse attendue :\n{bonne_reponse}\n")

        tirage = choisir_question_quiz(question)
        if tirage is None:
            break
        question, bonne_reponse = tirage

    print_colored(f"\n{_bilan_quiz(score, total)}\n", "blue", bold=True)


class ChatBot:
    """Classe pour gérer le chatbot avec mémoire de conversation"""
    def __init__(self):
        self.historique = []
        self._charger_historique()
        self.relations = {
            "qu'est-ce qu'une fonction": ["comment faire une fonction", "comment documenter une fonction"],
            "comment faire une fonction": ["comment faire une exception", "comment documenter une fonction"],
            "qu'est-ce qu'une liste": ["comment ajouter un élément à une liste", "comment trier une liste"],
            "comment faire une boucle": ["comment faire une condition", "comment arrêter un programme"],
            "comment déclarer une variable": ["comment afficher un message", "comment convertir une chaîne en entier"],
        }

    def _charger_historique(self):
        if not os.path.exists(HISTORY_FILE):
            return
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                donnees = json.load(f)
        except json.JSONDecodeError:
            # Ne pas repartir de zéro en silence : l'ancien fichier est conservé.
            _mettre_de_cote(HISTORY_FILE, "Historique de conversation illisible.")
            return
        except OSError as e:
            print(f"⚠️  Historique illisible ({e}) — la session démarre sans historique.")
            return

        if not isinstance(donnees, list):
            _mettre_de_cote(HISTORY_FILE, "Historique de conversation au mauvais format (liste attendue).")
            return

        self.historique = [
            m for m in donnees
            if isinstance(m, dict) and isinstance(m.get("role"), str) and isinstance(m.get("message"), str)
        ]
        ignores = len(donnees) - len(self.historique)
        if ignores:
            print(f"⚠️  {ignores} entrée(s) d'historique mal formée(s) ignorée(s).")

    def _sauvegarder_historique(self):
        """Plafonne puis écrit l'historique. À appeler sous _verrou_historique."""
        # Le fichier est réécrit intégralement à chaque message : on plafonne
        # pour qu'il ne grossisse pas sans fin.
        if len(self.historique) > HISTORIQUE_MAX_MESSAGES:
            del self.historique[:-HISTORIQUE_MAX_MESSAGES]
        try:
            _ecrire_json_atomique(HISTORY_FILE, self.historique)
        except OSError:
            pass

    def ajouter_message(self, role, message):
        self.historique.append({"role": role, "message": message})

    @staticmethod
    def _voisines_de_categorie(question_faq):
        """Les autres questions de la catégorie, en partant de la suivante.

        En tournant plutôt qu'en repartant du début : sinon toutes les
        questions d'une même catégorie proposeraient les deux mêmes voisines.
        """
        for questions in faq_categories.values():
            liste = list(questions)
            if question_faq in liste:
                depart = liste.index(question_faq)
                return [liste[(depart + n) % len(liste)] for n in range(1, len(liste))]
        return []

    def obtenir_suggestions(self, question_faq):
        """Questions à proposer après une réponse trouvée.

        `question_faq` est l'entrée de la FAQ retenue, jamais le message tapé.
        C'est tout l'objet du correctif : chercher à partir du texte brut
        revenait à exiger la formulation exacte du dictionnaire ci-dessous, si
        bien que « c'est quoi une liste » ne proposait rien alors que
        « qu'est-ce qu'une liste » fonctionnait.

        Rien n'est filtré sur les questions déjà posées. `bot` est un singleton
        partagé par tout le site et par le CLI : un tel ensemble ne ferait que
        grossir, et les suggestions s'éteindraient peu à peu pour tout le monde
        jusqu'au redémarrage du serveur.
        """
        if not question_faq:
            return []
        question_norm = normaliser_texte(question_faq)

        # Les relations écrites à la main priment : elles sont choisies pour
        # leur pertinence et peuvent traverser les catégories.
        for q_source, q_liees in self.relations.items():
            if normaliser_texte(q_source) == question_norm:
                return q_liees[:2]

        # À défaut, les voisines de catégorie. Sans ce repli, 50 des 55
        # questions de la FAQ n'auraient jamais la moindre suggestion — le
        # dictionnaire ci-dessus n'en couvre que cinq.
        return self._voisines_de_categorie(question_faq)[:2]

    def repondre(self, message, sensibilite=None):
        """Réponse complète : le texte, plus les questions à proposer ensuite.

        Les suggestions sortent à part du texte pour que le chat web les affiche
        en boutons cliquables ; traiter_message() les remet en texte pour le CLI.
        Deux cas les alimentent, et un seul des deux s'applique à la fois :
        après une réponse trouvée, les questions liées prolongent le sujet ;
        après un échec, les quasi-correspondances offrent un rattrapage.

        `sensibilite` est le réglage du visiteur ("stricte", "normale",
        "large") ; il n'est pas mémorisé ici. L'instance `bot` est un singleton
        partagé par tout le site et par le CLI : la retenir en attribut ferait
        subir à chacun le choix du dernier arrivé.
        """
        seuil = seuil_de_sensibilite(sensibilite) if sensibilite else SEUIL_CORRESPONDANCE
        # trace récupère la question de la FAQ retenue : c'est elle qui commande
        # les suggestions, et non le message tapé. Elle remplace aussi le test
        # « "Confiance:" in response », qui devinait le succès en reniflant le
        # texte de la réponse.
        trace = {}
        response = chatbot_response(message, seuil, trace)

        suggestions, titre = [], ""
        if trace.get("question"):
            suggestions = self.obtenir_suggestions(trace["question"])
            titre = TITRE_QUESTIONS_LIEES
        elif response == REPONSE_INCOMPRISE:
            suggestions = questions_proches(message, seuil=seuil)
            titre = TITRE_QUESTIONS_PROCHES

        # Ajout ET écriture sous le même verrou : deux requêtes web simultanées
        # ne peuvent ainsi ni entrelacer leurs paires question/réponse, ni
        # écraser l'ajout de l'autre pendant la sauvegarde.
        with _verrou_historique:
            self.ajouter_message("utilisateur", message)
            self.ajouter_message("assistant", response)
            self._sauvegarder_historique()
        return {"response": response,
                "suggestions": suggestions,
                "titre_suggestions": titre if suggestions else ""}

    def traiter_message(self, message):
        """Réponse en un seul bloc de texte, suggestions comprises (CLI)."""
        resultat = self.repondre(message)
        response = resultat["response"]
        if resultat["suggestions"]:
            response += f"\n\n📌 {resultat['titre_suggestions']}:\n"
            for i, sug in enumerate(resultat["suggestions"], 1):
                response += f"  {i}. {sug}\n"
        return response

    def afficher_historique(self):
        print("\n📜 Historique:\n")
        for msg in self.historique:
            if msg["role"] == "utilisateur":
                print_colored(f"Vous: {msg['message']}", "blue")
            else:
                print(f"IA: {msg['message']}\n")


bot = ChatBot()


def afficher_demarrage():
    VERSION = "v1.5.3"
    nb_questions = len(faq)
    nb_categories = len(faq_categories)
    nb_concepts = len(aide_concepts)

    def colorize(texte, color, bold=False):
        codes = {"blue": ("\033[94m", "\033[1;94m"), "green": ("\033[92m", "\033[1;92m"), "yellow": ("\033[93m", "\033[1;93m")}
        normal, gras = codes.get(color, ("\033[0m", "\033[1m"))
        code = gras if bold else normal
        return f"{code}{texte}\033[0m"

    lignes_mascotte = [
        r"       ____  _           _   ____",
        r"      / ___|| |__   __ _| |_|  _ \ _   _",
        r"     | |    | '_ \ / _` | __| |_) | | | |",
        r"     | |___ | | | | (_| | |_|  __/| |_| |",
        r"      \____||_| |_|\__,_|\__|_|    \__, |",
        r"                                   |___/ ",
    ]

    lignes_info = [
        colorize(f"ChatPy {VERSION}  —  Chatbot FAQ Python", "blue", bold=True),
        "",
        f"📚  {nb_questions} questions · {nb_categories} catégories · {nb_concepts} concepts",
        "🐍  Fonctionne 100% hors-ligne",
        "",
        colorize("💡  Tapez 'help' pour voir les commandes", "yellow"),
    ]

    largeur = max(len(l) for l in lignes_mascotte)
    nb_lignes = max(len(lignes_mascotte), len(lignes_info))

    print()
    for i in range(nb_lignes):
        ligne_m = lignes_mascotte[i] if i < len(lignes_mascotte) else ""
        info = lignes_info[i] if i < len(lignes_info) else ""
        print(f"{colorize(ligne_m.ljust(largeur), 'blue', bold=True)}  │  {info}")
    print()


if __name__ == "__main__":
    afficher_demarrage()

    while True:
        try:
            user_input = input("📝 Vous: ").strip()
            if not user_input:
                continue

            if user_input.lower() == "historique":
                bot.afficher_historique()
                continue

            if user_input.lower() == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                print_colored("🧹 Écran effacé. L'historique est conservé dans le fichier.", "yellow")
                print()
                continue

            if user_input.lower() == "quiz":
                mode_quiz()
                continue

            response = bot.traiter_message(user_input)
            print_colored("\n✨ Bot:", "blue")
            print(response)
            print()

            if _contient_mot(user_input.lower(), MOTS_AU_REVOIR):
                print_colored("À bientôt ! Continue à apprendre Python tout les jours ! 🚀", "blue", bold=True)
                break
        except KeyboardInterrupt:
            print("\n\nAu revoir !")
            break
        except EOFError:
            break
