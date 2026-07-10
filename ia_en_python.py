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

# Nombre de messages conservés dans .chatpy_history.json. Le fichier est réécrit
# en entier à chaque message : sans plafond, il grossit indéfiniment.
HISTORIQUE_MAX_MESSAGES = 1000

# Commandes qui n'ont de sens que dans le terminal (elles pilotent la boucle
# interactive). Elles n'atteignent chatbot_response() que depuis le chat web.
COMMANDES_TERMINAL = ("clear", "historique", "quiz")

MOTS_AU_REVOIR = ["au revoir", "aurevoir", "a bientot", "à bientôt", "bye", "quit", "exit"]

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

        if cle in donnees:
            donnees[cle]["occurrences"] += 1
            donnees[cle]["derniere_fois"] = aujourdhui
        else:
            donnees[cle] = {"texte": message, "occurrences": 1, "derniere_fois": aujourdhui}

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

    # Recherche par mots-clés dans chaque concept
    for concept in aide_concepts.values():
        for mot in concept.get("mots_cles", []):
            if sujet_norm in normaliser_texte(mot) or normaliser_texte(mot) in sujet_norm:
                return concept

    # Fuzzy matching sur les clés
    matches = get_close_matches(sujet_norm, aide_concepts.keys(), n=1, cutoff=0.5)
    if matches:
        return aide_concepts[matches[0]]

    return None


def chatbot_response(message):
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
                "  historique         — relire la conversation\n"
                "  clear              — effacer l'écran (l'historique reste sauvegardé)\n"
                "  au revoir          — quitter\n\n"
                "Ou posez directement une question sur Python.")

    # Commandes réservées au terminal : la boucle CLI les intercepte avant d'arriver
    # ici, donc on n'y passe que depuis le chat web, où elles n'ont pas de sens.
    if message in COMMANDES_TERMINAL:
        return (f"ℹ️ La commande '{message}' n'existe que dans la version terminal de ChatPy "
                f"(python3 ia_en_python.py).\n"
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
        return f"✓ {faq[original_q]}\n\n💡 Confiance: 100%"

    # 2. Fuzzy matching
    matches = get_close_matches(message_normalise, norm_vers_original.keys(), n=3, cutoff=0.6)
    if matches:
        original_q = norm_vers_original[matches[0]]
        confiance = int(calcul_similarite(message_normalise, matches[0]) * 100)
        return f"✓ {faq[original_q]}\n\n💡 Confiance: {confiance}%"

    # 3. Recherche par similarité
    meilleures_correspondances = []
    for norm_q, original_q in norm_vers_original.items():
        sim = calcul_similarite(message_normalise, norm_q)
        if sim > 0.5:
            meilleures_correspondances.append((original_q, faq[original_q], int(sim * 100)))

    if meilleures_correspondances:
        meilleures_correspondances.sort(key=lambda x: x[2], reverse=True)
        _, best_answer, confiance = meilleures_correspondances[0]
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
        _logger_question_sans_reponse(message)
        return "❌ Désolé, je ne comprends pas votre question. Essayez de poser une question sur Python ou tapez 'help' pour l'aide."


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


def mode_quiz(nb_questions_max=10):
    """Lance une session de quiz interactif sur les questions de la FAQ."""
    questions = list(faq.items())
    score = 0
    total = 0
    derniere_question = None

    print_colored(f"\n🎯 Mode Quiz — {nb_questions_max} questions, répondez de mémoire, tapez 'fin' pour arrêter avant la fin.\n", "yellow", bold=True)

    while total < nb_questions_max:
        question, bonne_reponse = random.choice(questions)
        while question == derniere_question and len(questions) > 1:
            question, bonne_reponse = random.choice(questions)
        derniere_question = question

        print_colored(f"❓ ({total + 1}/{nb_questions_max}) {question} ?", "blue")

        try:
            reponse = input("📝 Votre réponse : ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if reponse.lower() in ("fin", "exit", "quitter"):
            break

        sim = int(calcul_similarite(normaliser_texte(reponse), normaliser_texte(bonne_reponse)) * 100)
        total += 1

        if sim >= 70:
            score += 1
            print_colored(f"✅ Bonne réponse ! (similarité : {sim}%)", "green")
        elif sim >= 35:
            print_colored(f"⚠️  Presque ! (similarité : {sim}%)", "yellow")
        else:
            print_colored(f"❌ Pas tout à fait. (similarité : {sim}%)", "red")

        print(f"💡 Réponse attendue :\n{bonne_reponse}\n")

    if total > 0:
        print_colored(f"\n📊 Score final : {score}/{total} ({int(score/total*100)}%)\n", "blue", bold=True)
    else:
        print("Aucune question répondue.\n")


class ChatBot:
    """Classe pour gérer le chatbot avec mémoire de conversation"""
    def __init__(self):
        self.historique = []
        self.dernieres_categories = []
        self.questions_posees = set()
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
        with _verrou_historique:
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

    def obtenir_contexte(self):
        if len(self.historique) >= 2:
            return self.historique[-2:]
        return []

    def obtenir_suggestions(self, question):
        question_norm = normaliser_texte(question)
        suggestions = []
        for q_source, q_liees in self.relations.items():
            if normaliser_texte(q_source) in question_norm or question_norm in normaliser_texte(q_source):
                suggestions = q_liees
                break
        suggestions = [s for s in suggestions if s not in self.questions_posees]
        return suggestions[:2]

    def traiter_message(self, message):
        self.ajouter_message("utilisateur", message)
        response = chatbot_response(message)
        suggestions = self.obtenir_suggestions(message)
        if suggestions and "Confiance:" in response:
            response += "\n\n📌 Questions liées:\n"
            for i, sug in enumerate(suggestions, 1):
                response += f"  {i}. {sug}\n"
        self.ajouter_message("assistant", response)
        self.questions_posees.add(normaliser_texte(message))
        self._sauvegarder_historique()
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
