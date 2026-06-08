# PROC-007 — Lancer ou relancer le serveur de prévisualisation

## Déclencheur

- L'utilisateur souhaite ouvrir ou rafraîchir la prévisualisation du bulletin.
- L'utilisateur constate que la prévisualisation est inaccessible ou bloquée.
- L'utilisateur relance le serveur après une session de travail.

## Objectif

Démarrer le serveur de prévisualisation de manière fiable, en évitant les erreurs
connues (port occupé, double fenêtre de navigateur, processus zombie).

---

## Règles à respecter

1. **Ne jamais lancer `serveur_preview.py` directement depuis un terminal déjà utilisé** sans vérifier que le port 8765 est libre.
2. **Le serveur gère lui-même la libération du port** depuis la version PROC-007 (automatique).
3. **Une seule instance** doit être active à tout moment.
4. **La fenêtre du navigateur ne s'ouvre qu'une fois** (premier démarrage) — les relances rafraîchissent l'onglet existant via SSE.

---

## Étapes

### Étape 1 — Lancer la commande de démarrage

Depuis un terminal PowerShell dans le dossier du projet :

```powershell
cd "c:\Users\M.Diouf\OneDrive\Bureau\RDC Bulletin V1\Bulletin_rdc_2026_agents"
py 09_scripts/serveur_preview.py
```

**Ce que le script fait automatiquement :**
1. Vérifie si le port 8765 est déjà occupé.
2. Si oui → tue les anciens processus (par PID), attend 1 seconde.
3. Lance le build initial (assembleur + conversion HTML).
4. Démarre le watcher de fichiers.
5. Si c'est un **premier démarrage** → ouvre `http://localhost:8765` dans le navigateur.
6. Si c'est une **relance** → ne rouvre pas de fenêtre. L'onglet existant se rafraîchit automatiquement via SSE.

### Étape 2 — Vérifier les messages de démarrage

Le terminal doit afficher :

```
============================================================
  Serveur de prévisualisation — Bulletin RDC 2026
============================================================

[INIT] Vérification du port 8765…
[INIT] Port 8765 libre.          ← ou "libéré" si relance
[INIT] Construction initiale de la page…
[ASSEMBLEUR] OK
[PREVIEW] Page mise à jour
[WATCHER] Surveillance des fichiers activée
[OK] Serveur demarre -> http://localhost:8765
[OK] Ctrl+C pour arrêter
```

Si `[ASSEMBLEUR] Erreur` apparaît → consulter PROC-007 § Résolution des problèmes.

### Étape 3 — Ouvrir la prévisualisation (premier démarrage uniquement)

Le navigateur s'ouvre automatiquement. Si ce n'est pas le cas :

```
http://localhost:8765
```

Conserver cet onglet ouvert pendant toute la session. Il se rafraîchit automatiquement dès qu'un fichier `.md`, `.yml` ou `.css` est modifié.

### Étape 4 — Arrêter le serveur

Appuyer sur `Ctrl+C` dans le terminal.

> ⚠️ Ne pas fermer le terminal sans arrêter le serveur (Ctrl+C). Sinon le processus continue de tourner en arrière-plan et occupera le port 8765 lors du prochain démarrage. Le script gère ce cas, mais mieux vaut l'éviter.

---

## Option avancée : démarrage sans ouverture du navigateur

```powershell
py 09_scripts/serveur_preview.py --no-browser
```

Utile quand le navigateur est déjà ouvert sur la bonne URL et qu'on ne veut aucune action automatique.

---

## Résolution des problèmes

### Le port n'est toujours pas libre après le démarrage

```powershell
netstat -ano | findstr "LISTENING" | findstr ":8765"
# Relever le PID dans la dernière colonne, puis :
Stop-Process -Id <PID> -Force
```

Relancer ensuite `py 09_scripts/serveur_preview.py`.

### `[ASSEMBLEUR] Erreur`

1. Ouvrir `build_config.yml` et vérifier les chemins des fichiers.
2. Vérifier que `10_output/` existe et est accessible en écriture.
3. Relancer manuellement l'assembleur pour voir l'erreur complète :
   ```powershell
   py 09_scripts/assembler_markdown.py
   ```

### La prévisualisation ne se met pas à jour après modification d'un fichier

1. Vérifier que le terminal affiche `[WATCHER] Modification détectée : <fichier>`.
2. Si le watcher ne réagit pas : arrêter (Ctrl+C) et relancer le serveur.
3. Vérifier que le fichier modifié est bien dans un dossier surveillé (hors `10_output/`).

### La validation interactive (clic sur un élément annoté) renvoie une erreur

1. Vérifier que l'élément cliqué a bien `data-val-id`, `data-val-status` ET `data-val-file`.
2. Vérifier que le chemin dans `data-val-file` est relatif à la racine du workspace.
3. Consulter AGENTS.md § « Annotation des données sourçées ».

---

## Livrables

- Serveur actif et accessible sur `http://localhost:8765`.
- Terminal affichant `[OK] Serveur demarre`.
- Aucun doublon de processus sur le port 8765.
- Onglet navigateur unique maintenu entre les sessions.
