# 🛡️ Local AI Recon Gateway (Free Edition)

Ein leichtgewichtiges CLI-Tool, das lokale Large Language Models (LLMs) nutzt, um rohe Recon-Daten (wie Nmap-Scans, FFuf-Logs oder Gobuster-Outputs) automatisch zu analysieren und Schwachstellen zu priorisieren – komplett offline!

> **Hinweis:** Dies ist die **Free Edition** des Tools. Sie demonstriert die grundlegenden Fähigkeiten der KI-gestützten Recon-Analyse, ist aber für große Scans und Pipelines in ihren Funktionen limitiert.

---

## 🚀 Features der Free Edition

*   **Lokale Offline-Analyse:** Verbindet sich mit deinem lokalen LLM (z.B. über LM Studio, Ollama oder text-generation-webui). Deine Daten verlassen niemals deinen PC.
*   **Intelligente Filterung:** Der integrierte System-Prompt ignoriert irrelevante Standard-Dienste (wie Port 80/443 ohne Befund) und fokussiert sich auf harte Angriffsvektoren (offene Datenbanken, veraltete SSH-Server, Git-Leaks).
*   **Anti-Halluzination:** Strenge Regeln verhindern, dass das Modell Fake-CVEs erfindet.
*   **Visuelles CLI:** Wunderschöne und übersichtliche Terminal-Ausgabe dank der `rich`-Bibliothek.
*   **Auto-Chunking:** Große Dateien werden automatisch in handhabbare Stücke zerlegt, um das Token-Limit (Context Window) deines Modells nicht zu sprengen.

## ⚖️ Premium Edition vs. Free Edition

Die Free Edition ist ideal zum Ausprobieren. Für den harten Bug-Bounty-Alltag gibt es die **Premium Edition**, die folgende exklusive Features bietet:

| Feature | Free Edition | Premium Edition 💎 |
| :--- | :--- | :--- |
| **Multithreading** | ❌ (Sequenziell, sehr langsam bei großen Logs) | ✅ (Parallele Verarbeitung für massiven Speed-Boost) |
| **Master-Plan Aggregation** | ❌ (Hängt Antworten einfach aneinander) | ✅ (Führt am Ende alle Chunks durch einen weiteren KI-Call dedupliziert zu einem Master-Plan zusammen) |
| **Intelligentes Chunking** | ❌ (Stumpfes Splitten nach Wörtern, Kontext kann verloren gehen) | ✅ (Zeilenweises Splitten, um Log-Strukturen intakt zu halten) |
| **Retry-Logik (Exponential Backoff)**| ❌ (Bricht bei Timeout oder Serverüberlastung sofort ab) | ✅ (Automatische Wiederholungen bei Timeouts) |
| **Automatischer Datei-Export** | ❌ (Nur Konsolen-Ausgabe) | ✅ (Export als Markdown `.md` und Rohdaten als `.json`) |
| **API-Key & Custom Model Support**| ❌ (Nur Standard-Endpoint) | ✅ (Support für API-Keys und spezifische LLM-Auswahl) |

---

## 🛠️ Installation & Voraussetzungen

1.  **Python 3.8+** muss installiert sein.
2.  Installiere die benötigten Python-Bibliotheken:
    ```bash
    pip install requests rich
    ```
3.  Starte dein lokales KI-Backend (z.B. **LM Studio**). Stelle sicher, dass der lokale Server (Local Inference Server) gestartet ist und ohne API-Key auf `http://127.0.0.1:1234` lauscht.

## 💻 Nutzung

Das Skript wird über die Kommandozeile bedient.

### Standard-Analyse
Liest eine Log-Datei ein und sendet sie an den Standard-Endpunkt (`127.0.0.1:1234`):
```bash
python recon_gateway_free.py -f mein_nmap_scan.txt
```

### Eigener Endpunkt
Falls dein lokales LLM auf einem anderen Port oder PC im Netzwerk läuft:
```bash
python recon_gateway_free.py -f mein_nmap_scan.txt -e http://192.168.1.100:1234/v1/chat/completions
```

### Hilfe anzeigen
```bash
python recon_gateway_free.py --help
```

---
*Erstellt für die lokale Bug-Bounty-Automatisierung.*
