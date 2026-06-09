import argparse
import sys
import os
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Initialisiere die Rich-Console für ein sauberes CLI-Interface
console = Console()

class LocalAIReconGateway:
    def __init__(self, api_url="http://127.0.0.1:1234/v1/chat/completions", model="local-model"):
        self.api_url = api_url
        self.model = model
        
        # Der ultimative System-Prompt mit strikten Anti-Halluzinations-Regeln
        self.system_prompt = (
            "Du bist ein Senior Penetration Tester und Bug Bounty Hunter. "
            "Deine Aufgabe ist es, rohe Recon-Daten schonungslos zu filtern. "
            "REGELN:\n"
            "1. IGNORIERE Standard-Dienste (wie Port 80/443, normale SSH-Ports), es sei denn, die Software-Version ist stark veraltet.\n"
            "2. FOKUSSIERE dich ausschließlich auf kritische Angriffsvektoren: Exponierte Datenbanken (MySQL), Source-Code-Leaks (wie .git), "
            "veraltete Versionen (z.B. OpenSSH < 7.5) und interne Panels.\n"
            "3. Erstelle keine Zusammenfassung! Liefere direkt einen priorisierten 'Action Plan' in Markdown.\n"
            "4. Kennzeichne kritische Funde mit 🚨.\n"
            "5. STRIKTE REGEL: HALLUZINIERE NICHT! Erfinde niemals CVE-Nummern. Nenne nur CVEs, wenn sie absolut zweifelsfrei zur erkannten Version passen.\n"
            "6. STRIKTE REGEL: Behaupte nicht, dass du Dateien speicherst, JSON-Dateien erstellst oder externe Aktionen durchführst. Du bist nur ein Text-Analysator."
        )

    def chunk_data(self, text, chunk_size=3000):
        """
        Zerlegt große Log-Dateien in handhabbare Chunks, um das Token-Limit 
        lokaler LLMs (z.B. 4k oder 8k Context Window) nicht zu sprengen.
        """
        words = text.split()
        for i in range(0, len(words), chunk_size):
            yield " ".join(words[i:i + chunk_size])

    def analyze_chunk(self, chunk):
        """
        Sendet den Daten-Chunk an das lokale LLM (z.B. LM Studio oder Ollama).
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Analysiere folgenden Recon-Auszug:\n\n{chunk}"}
            ],
            "temperature": 0.1, # Temperatur weiter gesenkt (0.1), um Halluzinationen radikal zu minimieren
            "max_tokens": 1000
        }

        try:
            # Timeout von 120 Sekunden
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        
        except requests.exceptions.ConnectionError:
            console.print("[bold red][!] Verbindungsfehler:[/bold red] Konnte keine Verbindung zum lokalen KI-Server herstellen.")
            console.print(f"Stelle sicher, dass LM Studio / Ollama läuft und Port {self.api_url} erreichbar ist.")
            sys.exit(1)
        except requests.exceptions.Timeout:
            console.print("[bold red][!] Timeout:[/bold red] Das lokale Modell hat zu lange für die Antwort gebraucht.")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red][!] Unerwarteter Fehler:[/bold red] {e}")
            sys.exit(1)

def main():
    # 1. CLI-Argumente definieren
    parser = argparse.ArgumentParser(description="KI-Recon-Gateway: Lokale LLM-Analyse für Bug Bounties")
    parser.add_argument("-f", "--file", required=True, help="Pfad zur Recon-Logdatei (z.B. nmap_output.txt)")
    parser.add_argument("-e", "--endpoint", default="http://127.0.0.1:1234/v1/chat/completions", help="Lokaler KI-API-Endpoint (Standard: LM Studio)")
    args = parser.parse_args()

    console.print(Panel.fit("[bold blue]🛡️ Local AI Recon Gateway v1.0[/bold blue]\n[dim]Initializing offline analysis...[/dim]"))

    # 2. Datei-Validierung
    if not os.path.exists(args.file):
        console.print(f"[bold red]Fehler:[/bold red] Die Datei '{args.file}' wurde nicht gefunden.")
        sys.exit(1)

    with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
        recon_data = f.read()

    gateway = LocalAIReconGateway(api_url=args.endpoint)
    chunks = list(gateway.chunk_data(recon_data))
    
    console.print(f"[*] Datei geladen. Zerlegt in [bold green]{len(chunks)}[/bold green] Chunks für die lokale Verarbeitung.\n")

    # 3. Verarbeitung mit visuellem Feedback
    full_report = ""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Sende Daten an lokales LLM... Bitte warten.", total=len(chunks))
            
            for i, chunk in enumerate(chunks, 1):
                progress.update(task, description=f"[cyan]Analysiere Chunk {i}/{len(chunks)} über lokales LLM...")
                analysis = gateway.analyze_chunk(chunk)
                full_report += f"### Analyse Teil {i}\n{analysis}\n\n"
                progress.advance(task)

    except KeyboardInterrupt:
        console.print("\n[bold yellow][!] Analyse vom Benutzer abgebrochen (Strg+C).[/bold yellow]")
        sys.exit(0)

    # 4. Ergebnis-Ausgabe
    console.print(Panel("[bold green]✅ Analyse abgeschlossen![/bold green]"))
    console.print("\n[bold underline]KI-Ergebnis:[/bold underline]\n")
    
    from rich.markdown import Markdown
    console.print(Markdown(full_report))

if __name__ == "__main__":
    main()