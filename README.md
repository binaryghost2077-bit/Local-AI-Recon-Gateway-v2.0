# Local AI Recon Gateway v2.0 

Das **Local AI Recon Gateway** ist ein leistungsstarkes Tool für Penetration Tester und Bug Bounty Hunter. Es nutzt lokale LLMs (z.B. über LM Studio, Ollama etc.), um rohe Recon-Daten (wie `nmap`- oder Subdomain-Scans) schonungslos zu filtern, zu analysieren und kritische Angriffsvektoren zu identifizieren. Das Tool umgeht Token-Limits großer Dateien durch intelligentes Chunking und aggregiert die Ergebnisse am Ende in einen konsolidierten "Master Action Plan".

## 🚀 Features

- **Lokale LLM Analyse:** Voller Datenschutz durch die Nutzung lokaler Modelle (LM Studio etc.), keine Daten verlassen deinen Rechner.
- **Intelligentes Chunking:** Zerlegt große Log-Dateien kontext-erhaltend (Zeilenbasiert), um das Token-Limit des LLMs nicht zu überschreiten.
- **Auto-Aggregation (Synthesis):** Die Ergebnisse der einzelnen Chunks werden durch einen weiteren LLM-Durchlauf dedupliziert und zu einem finalen Markdown-Bericht zusammengefasst.
- **Multithreading-Support:** Parallele Verarbeitung der Chunks für einen enormen Geschwindigkeits-Boost.
- **Strikter System-Prompt:** Fokussierung auf *echte* Schwachstellen (Source-Code-Leaks, veraltete Versionen, exponierte Datenbanken) und strenge Anti-Halluzinations-Regeln (keine erfundenen CVEs).
- **JSON & Markdown Export:** Perfekt für die Weiterverarbeitung in automatisierten Pipelines oder direkt als lesbarer Report.

## 🛠️ Voraussetzungen

1. **Python 3.7+**
2. Installierte Abhängigkeiten:
   ```bash
   pip install -r requirements.txt
   ```
   *(Das Script benötigt u.a. `requests` und `rich` für das CLI-Interface)*
3. Ein laufendes **lokales KI-Backend** (Standardmäßig auf `http://127.0.0.1:1234/v1/chat/completions` für LM Studio konfiguriert).

## 💻 Verwendung

```bash
python recon_gateway.py -f <Pfad_zur_Logdatei> [Optionen]
```

### Parameter-Übersicht

| Argument | Kurz | Beschreibung | Standard |
| :--- | :---: | :--- | :--- |
| `--file` | `-f` | **(Erforderlich)** Pfad zur Recon-Logdatei (z.B. `nmap_output.txt`) | - |
| `--endpoint` | `-e` | Lokaler KI-API-Endpoint (z.B. LM Studio, Ollama) | `http://127.0.0.1:1234/v1/chat/completions` |
| `--threads` | `-t` | Anzahl paralleler Anfragen. (Vorsicht bei ressourcenhungrigen lokalen LLMs!) | `1` |
| `--output` | `-o` | Pfad zum Speichern des fertigen *Master Action Plans* als `.md` Datei | - |
| `--json` | `-j` | Pfad zum Speichern aller rohen Chunk-Ergebnisse als `.json` | - |
| `--prompt` | `-p` | Pfad zu einer Datei mit einem benutzerdefinierten System-Prompt | - |
| `--api-key` | `-k` | API Key für das LLM Backend (falls benötigt) | - |
| `--model` | `-m` | Modell-Name (wird der API übermittelt, z.B. `local-model`) | `local-model` |

### Anwendungsbeispiele

**Einfacher Scan einer Nmap-Ausgabe:**
```bash
python recon_gateway.py -f nmap_scan.txt
```

**Verarbeitung mit 4 Threads und Speichern der Ergebnisse:**
```bash
python recon_gateway.py -f subfinder_httpx_results.txt -t 4 -o final_report.md
```

**Nutzung mit angepasstem Modell und Benutzer-Prompt:**
```bash
python recon_gateway.py -f recon.log -m orpheus-3b-german-ft.gguf -p custom_prompt.txt
```

## 🧠 Wie es funktioniert

1. **Einlesen & Splitten:** Das Gateway liest die Log-Datei ein und schneidet sie an Zeilenumbrüchen ab, sobald ein Limit von ca. 12.000 Zeichen (konfigurierbar im Code) pro Chunk erreicht ist.
2. **LLM-Analyse:** Jeder Chunk wird einzeln (ggf. parallel) an das LLM gesendet. Das Modell filtert Standard-Dienste heraus und extrahiert mit einem `🚨`-Tag kritische Funde.
3. **Master Synthesis:** Liegen mehrere Chunks vor, werden die individuellen Reports noch einmal dem LLM vorgelegt. Es fasst die Ergebnisse zusammen, dedupliziert mehrfache Meldungen (z.B. gleicher Port auf gleicher IP) und priorisiert die kritischsten Angriffsvektoren ganz oben.
4. **Export:** Das CLI (gebaut mit `rich`) gibt den Markdown-Bericht visuell ansprechend im Terminal aus und speichert ihn auf Wunsch als Datei ab.
