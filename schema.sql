-- Schéma de la base SQLite de ChatPy (chatpy.db).
--
-- Ce fichier est la seule définition du schéma : base_donnees.py l'exécute au
-- démarrage plutôt que de répéter les mêmes CREATE TABLE en Python. Tout est en
-- « IF NOT EXISTS », donc le rejouer sur une base déjà remplie ne coûte rien et
-- n'efface rien.
--
-- Une seule table pour l'instant : les personnes qui se connectent, quel que
-- soit leur moyen de connexion. Les conversations archivées restent dans
-- conversations.json (voir conversations.py) — les déplacer ici serait un autre
-- chantier, et rien ne le réclame tant que le fichier reste petit.

-- ── utilisateurs ────────────────────────────────────────────────────────────
-- Une ligne par compte, pour les trois moyens de connexion :
--
--   fournisseur = 'local'  → inscription par email + mot de passe (comptes.py)
--   fournisseur = 'google' → connexion Google  (empreinte NULL : le mot de
--   fournisseur = 'github' → connexion GitHub   passe reste chez eux)
--
-- La clé est le couple (fournisseur, id_externe) et non l'email : Google et
-- GitHub numérotent leurs comptes chacun de leur côté, et la même personne peut
-- très bien avoir les deux avec la même adresse. C'est la même clé de rangement
-- que celle des conversations (« google-42 »).
--
-- empreinte ne contient JAMAIS un mot de passe : c'est une empreinte scrypt
-- produite par werkzeug.security, dont on ne peut pas remonter au mot de passe.
CREATE TABLE IF NOT EXISTS utilisateurs (
    fournisseur         TEXT    NOT NULL,
    id_externe          TEXT    NOT NULL,
    nom                 TEXT    NOT NULL DEFAULT '',
    email               TEXT    NOT NULL,
    empreinte           TEXT,
    photo               TEXT    NOT NULL DEFAULT '',
    -- Horodatages ISO 8601 en UTC ("2026-08-12T09:30:00+00:00") : lisibles tels
    -- quels dans n'importe quel navigateur SQL, et triables comme du texte.
    cree                TEXT    NOT NULL,
    derniere_connexion  TEXT,
    nb_connexions       INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (fournisseur, id_externe),

    -- Un compte local sans empreinte serait un compte auquel on entre sans mot
    -- de passe. La base refuse d'en écrire un, même si le code se trompe.
    CHECK (empreinte IS NOT NULL OR fournisseur <> 'local'),
    CHECK (email <> '')
);

-- L'adresse est l'identifiant de connexion d'un compte local : deux comptes
-- locaux ne peuvent pas la partager, sinon la connexion ne saurait pas lequel
-- des deux vérifier. Index partiel, donc : la contrainte ne s'applique qu'aux
-- comptes locaux, et rien n'empêche d'avoir aussi un Google à la même adresse.
CREATE UNIQUE INDEX IF NOT EXISTS idx_utilisateurs_email_local
    ON utilisateurs (email)
    WHERE fournisseur = 'local';

-- Recherche par adresse, tous fournisseurs confondus (« qui est passé ? »).
CREATE INDEX IF NOT EXISTS idx_utilisateurs_email
    ON utilisateurs (email);
