# Registre des agents — Bulletin RDC 2026

## Vue d'ensemble

| Agent | Fichier | Modèle | Rôle |
|---|---|---|---|
| Orchestrateur | `agent_orchestrateur.md` | `claude-sonnet-4.6` | Dispatcher central |
| Rédacteur | `agent_redacteur.md` | `claude-sonnet-4.6` | Passe 3 — rédaction |
| Structureur | `agent_structureur.md` | `claude-haiku-4.5` | Passe 1 — structure |
| Analyste sources | `agent_analyste_sources.md` | `claude-sonnet-4.5` | Passe 2 — notes |
| Chercheur web | `agent_chercheur_web.md` | `gpt-5.4` | PROC-001 — recherche |
| Réviseur | `agent_reviseur.md` | `claude-haiku-4.5` | PROC-003/004 — révision |
| Technicien | `agent_technicien.md` | `gpt-5.3-codex` | Scripts, build |

## Règle de dispatch (résumé)

```
Tâche reçue par l'Orchestrateur
    │
    ├── Créer fichier vide ?           → Structureur (Haiku)
    ├── Lire sources + notes ?         → Analyste sources (Sonnet 4.5)
    ├── Rédiger section ?              → Rédacteur (Sonnet 4.6)
    ├── Vérifier / réviser ?           → Réviseur (Haiku)
    ├── Recherche internet ?           → Chercheur web (GPT-5.4)
    └── Script / build ?               → Technicien (Codex)
```

## Règle de volume
Maximum **4 sources** ou **2 sections** par agent et par tâche.
Les tâches volumineuses sont découpées et lancées en parallèle.
