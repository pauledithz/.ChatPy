import re
import os
import json
import random
import unicodedata
from difflib import get_close_matches, SequenceMatcher

_DIR              = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE      = os.path.join(_DIR, ".chatpy_history.json")
FAQ_FILE          = os.path.join(_DIR, "faq.json")
AIDE_CONCEPTS_FILE = os.path.join(_DIR, "aide_concepts.json")


def normaliser_texte(texte):
    texte = unicodedata.normalize('NFKD', texte)
    texte = texte.encode('ASCII', 'ignore').decode('ASCII')
    texte = re.sub(r'[^\w\s]', ' ', texte)
    texte = re.sub(r'\s+', ' ', texte).strip()
    return texte.lower()


def calcul_similarite(texte1, texte2):
    return SequenceMatcher(None, texte1, texte2).ratio()


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
                "  au revoir          — quitter\n\n"
                "Ou posez directement une question sur Python.")

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
    if any(word in message for word in ["bonjour", "salut", "hello", "hi"]):
        return "👋 Bonjour ! Posez-moi une question sur Python ou tapez 'help' pour l'aide."
    elif any(word in message for word in ["ça va bien", "tu vas bien"]):
        return "🤖 Je suis une Intelligence Artificielle, donc je vais toujours bien ! Comment puis-je vous aider avec Python aujourd'hui ?"
    elif any(word in message for word in ["nom", "appelles", "qui es-tu"]):
        return "📖 Je suis un chatbot Python qui peut répondre à des questions sur le code."
    elif "merci" in message:
        return "😊 De rien ! N'hésitez pas si vous avez d'autres questions sur Python."
    elif any(word in message for word in ["au revoir", "bye", "quit", "exit"]):
        return "👋 Au revoir ! Continue à apprendre Python le plus possible !"
    else:
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


def mode_quiz():
    """Lance une session de quiz interactif sur les questions de la FAQ."""
    questions = list(faq.items())
    score = 0
    total = 0

    print_colored("\n🎯 Mode Quiz — répondez de mémoire, tapez 'fin' pour arrêter.\n", "yellow", bold=True)

    while True:
        question, bonne_reponse = random.choice(questions)
        print_colored(f"❓ {question} ?", "blue")

        try:
            reponse = input("📝 Votre réponse : ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if reponse.lower() in ("fin", "exit", "quit"):
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
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.historique = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.historique = []

    def _sauvegarder_historique(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.historique, f, ensure_ascii=False, indent=2)
        except IOError:
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
    VERSION = "v1.0.0"
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

            if user_input.lower() == "quiz":
                mode_quiz()
                continue

            response = bot.traiter_message(user_input)
            print_colored("\n✨ Bot:", "blue")
            print(response)
            print()

            if any(word in user_input.lower() for word in ["au revoir", "bye", "quit", "exit"]):
                print_colored("À bientôt ! Continue à apprendre Python tout les jours ! 🚀", "blue", bold=True)
                break
        except KeyboardInterrupt:
            print("\n\nAu revoir !")
            break
        except EOFError:
            break
