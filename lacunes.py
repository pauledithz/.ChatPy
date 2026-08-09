"""Trie le journal des lacunes pour dire quoi ajouter à faq.json.

questions_sans_reponse.json enregistre les échecs, mais la liste brute ne dit
pas quoi en faire : trois formulations d'un même sujet y pèsent trois lignes,
et surtout deux échecs très différents s'y ressemblent comme deux gouttes
d'eau. Une question à laquelle la FAQ répond déjà — sous un autre libellé —
demande un alias ; un sujet réellement absent demande une réponse à écrire.
Confondre les deux fait grossir la FAQ de doublons sans rien réparer.

Cet outil diagnostique donc chaque entrée contre la FAQ *actuelle*, regroupe
les formulations voisines, et classe le tout par urgence.

    python3 lacunes.py             rapport
    python3 lacunes.py --tout      sans la limite de 10 par section
    python3 lacunes.py --nettoyer  retire les entrées devenues obsolètes
"""
import json
import sys

import ia_en_python as ia


# Un pouce vers le bas pèse plus qu'un échec ordinaire : l'utilisateur a reçu
# une réponse — le bot a donc échoué *sans le dire*, et seul ce compteur le
# révèle. Un « je ne comprends pas », lui, est visible de tous.
POIDS_POUCE_BAS = 2

# Deux formulations au-dessus de ce score parlent du même sujet. Volontairement
# plus haut que SEUIL_CORRESPONDANCE : un regroupement abusif masque une lacune
# entière derrière une autre, alors qu'un regroupement raté ne coûte qu'une
# ligne de rapport en double.
SEUIL_REGROUPEMENT = 0.6

LIMITE_PAR_SECTION = 10

# Les quatre diagnostics, dans l'ordre où le rapport les présente : ce qui est
# à la fois invisible et faux d'abord, ce qui est déjà réglé en dernier.
SECTIONS = [
    ("mauvaise_reponse",
     "MAUVAISE RÉPONSE — la FAQ répond, mais à côté",
     "→ la question matche cette entrée : corrigez la réponse, ou écartez-les "
     "l'une de l'autre (vocabulaire plus distinctif)."),
    ("manquante",
     "SUJET MANQUANT — à écrire dans faq.json",
     "→ rien d'approchant dans la FAQ : c'est une vraie entrée à rédiger."),
    ("a_rapprocher",
     "À RAPPROCHER — l'entrée existe, le matching la rate",
     "→ n'écrivez pas de nouvelle entrée : rapprochez celle-ci (reformulation, "
     "vocabulaire commun)."),
    ("couverte",
     "DÉJÀ COUVERTE — journal périmé",
     "→ la FAQ y répond depuis : ces lignes ne servent plus qu'à brouiller le "
     "rapport."),
]


def charger_journal():
    """Lit le journal sans jamais y toucher. Retourne un dict, ou None si illisible.

    Volontairement plus prudent que _incrementer_journal(), qui met de côté un
    fichier corrompu pour pouvoir continuer à écrire : un outil de lecture n'a
    aucune raison de déplacer les données de l'utilisateur.
    """
    try:
        with open(ia.QUESTIONS_SANS_REPONSE_FILE, "r", encoding="utf-8") as f:
            donnees = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        print(f"⚠️  Journal illisible : {e}")
        return None

    if not isinstance(donnees, dict):
        print("⚠️  Journal au mauvais format (objet JSON attendu).")
        return None
    return donnees


def _entrees(journal):
    """Aplatit le journal en une liste de dicts, en tolérant les entrées anciennes.

    Les premières versions du journal n'avaient pas le champ 'pouces_bas', et
    une entrée peut avoir été écrite à la main : tout champ manquant vaut 0.
    """
    entrees = []
    for cle, valeur in journal.items():
        if not isinstance(valeur, dict):
            continue
        entrees.append({
            "cle": cle,
            "texte": valeur.get("texte", cle),
            "occurrences": _entier(valeur.get("occurrences")),
            "pouces_bas": _entier(valeur.get("pouces_bas")),
            "derniere_fois": valeur.get("derniere_fois", "?"),
        })
    return entrees


def _entier(valeur):
    return valeur if isinstance(valeur, int) and valeur >= 0 else 0


def poids(entree):
    return entree["occurrences"] + POIDS_POUCE_BAS * entree["pouces_bas"]


def diagnostiquer(entree):
    """Confronte une entrée à la FAQ actuelle. Retourne (diagnostic, question FAQ, score).

    C'est le cœur de l'outil : le même échec journalisé appelle une correction
    différente selon ce que la FAQ contient *aujourd'hui*. Le score de la
    meilleure entrée FAQ range la question dans l'une des quatre familles.
    """
    norme = ia.normaliser_texte(entree["texte"])
    scores = ia._scanner_faq(norme)
    if not scores:
        return "manquante", None, 0

    question, score = scores[0]

    if score >= ia.SEUIL_CORRESPONDANCE * 100:
        # La FAQ répond. Reste à savoir depuis quand : si l'entrée porte un
        # pouce bas, l'utilisateur a bel et bien vu cette réponse et l'a
        # refusée — ce n'est pas du journal périmé, c'est un faux positif.
        if entree["pouces_bas"]:
            return "mauvaise_reponse", question, score
        return "couverte", question, score

    # Même garde que questions_proches() : sous le seuil de réponse, la
    # ressemblance des lettres suffit à faire remonter n'importe quoi
    # (« dresser un lama » → « décompresser un tuple »). Sans un mot de sujet
    # en commun, la question n'est pas « à rapprocher » d'une entrée existante,
    # elle est absente de la FAQ.
    if score >= ia.SEUIL_PROPOSITION * 100 and _sujet_commun(norme, question):
        return "a_rapprocher", question, score

    return "manquante", question, score


def _sujet_commun(message_norm, question_faq):
    """Vrai si la question et l'entrée FAQ partagent au moins un mot porteur de sens."""
    mots_message = ia._mots_significatifs(message_norm)
    mots_faq = ia._mots_significatifs(ia.normaliser_texte(question_faq))
    return ia._recouvrement_mots(mots_message, mots_faq) > 0


def regrouper(entrees):
    """Rassemble les formulations d'un même sujet. Retourne une liste de groupes.

    Agglomération gloutonne : chaque entrée rejoint le premier groupe dont le
    représentant lui ressemble assez. Les entrées arrivent triées par poids
    décroissant, donc c'est toujours la formulation la plus fréquente qui donne
    son titre au groupe.
    """
    groupes = []
    for entree in entrees:
        norme = ia.normaliser_texte(entree["texte"])
        for groupe in groupes:
            if ia._score_correspondance(norme, groupe["norme"]) >= SEUIL_REGROUPEMENT:
                groupe["membres"].append(entree)
                groupe["poids"] += poids(entree)
                break
        else:
            groupes.append({
                "norme": norme,
                "membres": [entree],
                "poids": poids(entree),
            })

    groupes.sort(key=lambda g: (g["poids"], g["membres"][0]["derniere_fois"]), reverse=True)
    return groupes


def analyser(journal):
    """Diagnostic par entrée, puis regroupement à l'intérieur de chaque famille.

    L'ordre compte : diagnostiquer d'abord garantit qu'un groupe ne mélange
    jamais deux corrections différentes, et que --nettoyer décide entrée par
    entrée plutôt que de supprimer un groupe entier sur la foi de son
    représentant.
    """
    entrees = sorted(_entrees(journal), key=poids, reverse=True)

    familles = {code: [] for code, _, _ in SECTIONS}
    for entree in entrees:
        diagnostic, question, score = diagnostiquer(entree)
        entree["faq_proche"] = question
        entree["faq_score"] = score
        familles[diagnostic].append(entree)

    return {code: regrouper(liste) for code, liste in familles.items()}


def _ligne_groupe(rang, groupe):
    """Une entrée du rapport : le sujet, son poids, ses variantes, son voisin FAQ."""
    principal = groupe["membres"][0]
    lignes = [f"  {rang}. ▲ {groupe['poids']}  « {principal['texte']} »"]

    autres = groupe["membres"][1:]
    if autres:
        apercu = " · ".join(f"« {m['texte']} »" for m in autres[:3])
        reste = f" (+{len(autres) - 3})" if len(autres) > 3 else ""
        lignes.append(f"        {len(autres)} autre(s) formulation(s) : {apercu}{reste}")

    detail = []
    if principal["occurrences"]:
        detail.append(f"{principal['occurrences']} échec(s)")
    if principal["pouces_bas"]:
        detail.append(f"{principal['pouces_bas']} pouce(s) bas")
    detail.append(f"vu le {principal['derniere_fois']}")
    lignes.append(f"        {', '.join(detail)}")

    if principal["faq_proche"]:
        lignes.append(f"        FAQ la plus proche : « {principal['faq_proche']} » "
                      f"({principal['faq_score']}%)")
    return "\n".join(lignes)


def rapport(familles, tout=False):
    """Affiche le rapport. Retourne le nombre d'entrées supprimables par --nettoyer."""
    total_groupes = sum(len(g) for g in familles.values())
    total_entrees = sum(len(gr["membres"]) for g in familles.values() for gr in g)

    ia.print_colored(
        f"\n🔎 Lacunes de la FAQ — {total_entrees} question(s) journalisée(s), "
        f"{total_groupes} sujet(s) après regroupement, "
        f"{len(ia.faq)} entrée(s) dans faq.json\n",
        "blue", bold=True)

    if not total_entrees:
        print("  Rien à signaler : le journal est vide.\n"
              "  Il se remplit tout seul quand une question reste sans réponse\n"
              "  ou reçoit un pouce vers le bas dans le chat web.\n")
        return 0

    couleurs = {"mauvaise_reponse": "red", "manquante": "yellow",
                "a_rapprocher": "yellow", "couverte": "green"}

    for code, titre, conseil in SECTIONS:
        groupes = familles[code]
        if not groupes:
            continue

        ia.print_colored(f"  ── {titre} ({len(groupes)})", couleurs[code], bold=True)
        print(f"     {conseil}\n")

        visibles = groupes if tout else groupes[:LIMITE_PAR_SECTION]
        for rang, groupe in enumerate(visibles, 1):
            print(_ligne_groupe(rang, groupe))
            print()

        caches = len(groupes) - len(visibles)
        if caches:
            print(f"     … {caches} sujet(s) de plus — relancez avec --tout\n")

    supprimables = sum(len(gr["membres"]) for gr in familles["couverte"])
    if supprimables:
        ia.print_colored(
            f"  💡 python3 lacunes.py --nettoyer  retire les {supprimables} entrée(s) "
            f"déjà couverte(s)\n", "blue")
    return supprimables


def nettoyer(familles):
    """Supprime du journal les seules entrées diagnostiquées « déjà couverte ».

    Le journal est relu juste avant l'écriture, et seules les clés visées sont
    retirées : le serveur Flask peut tourner pendant ce temps sans qu'un
    compteur incrémenté entre l'analyse et l'écriture soit perdu.
    """
    cles = {e["cle"] for groupe in familles["couverte"] for e in groupe["membres"]}
    if not cles:
        print("\n  Rien à nettoyer : aucune entrée n'est couverte par la FAQ actuelle.\n")
        return 0

    with ia._verrou_questions:
        journal = charger_journal()
        if journal is None:
            return 0

        retirees = [cle for cle in cles if cle in journal]
        for cle in retirees:
            del journal[cle]

        try:
            ia._ecrire_json_atomique(ia.QUESTIONS_SANS_REPONSE_FILE, journal)
        except OSError as e:
            print(f"\n⚠️  Écriture impossible : {e}\n")
            return 0

    ia.print_colored(f"\n  🧹 {len(retirees)} entrée(s) retirée(s) du journal.\n", "green")
    return len(retirees)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    inconnus = [a for a in argv if a not in ("--tout", "--nettoyer", "--aide", "-h", "--help")]
    if inconnus or any(a in ("--aide", "-h", "--help") for a in argv):
        if inconnus:
            print(f"❌ Option inconnue : {', '.join(inconnus)}")
        print(__doc__.strip())
        return 1 if inconnus else 0

    journal = charger_journal()
    if journal is None:
        return 1

    familles = analyser(journal)
    rapport(familles, tout="--tout" in argv)

    if "--nettoyer" in argv:
        nettoyer(familles)
    return 0


if __name__ == "__main__":
    sys.exit(main())
