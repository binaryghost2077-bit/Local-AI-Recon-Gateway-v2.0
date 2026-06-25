import argparse
import sys
import os
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console()

class LocalAIReconGatewayFree:
    def __init__(self, api_url="http://127.0.0.1:1234/v1/chat/completions", model="local-model"):
        self.api_url = api_url
        self.model = model
        
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
        Standard-Wortbasiertes Chunking (Free Version)
        """
        words = text.split()
        for i in range(0, len(words), chunk_size):
            yield " ".join(words[i:i + chunk_size])

    def analyze_chunk(self, chunk):
        """
        Basis-Analyse ohne Retries oder Exponential Backoff
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Analysiere folgenden Recon-Auszug:\n\n{chunk}"}
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }

        headers = {"Content-Type": "application/json"}

        try:
            # Einfacher Call, bricht bei Timeout direkt ab
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        
        except requests.exceptions.ConnectionError:
            console.print("[bold red][!] Verbindungsfehler:[/bold red] Konnte keine Verbindung zum KI-Server herstellen.")
            sys.exit(1)
        except requests.exceptions.Timeout:
            console.print("[bold red][!] Timeout:[/bold red] Das Modell hat zu lange für die Antwort gebraucht (120s Limit).")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red][!] Unerwarteter Fehler:[/bold red] {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="KI-Recon-Gateway: Lokale LLM-Analyse (Free Edition)")
    parser.add_argument("-f", "--file", required=True, help="Pfad zur Recon-Logdatei (z.B. nmap_output.txt)")
    parser.add_argument("-e", "--endpoint", default="http://127.0.0.1:1234/v1/chat/completions", help="Lokaler KI-API-Endpoint")
    args = parser.parse_args()

    console.print(Panel.fit("[bold blue]Local AI Recon Gateway v1.0 (Free Edition)[/bold blue]\n[dim]Initializing basic offline analysis...[/dim]"))

    if not os.path.exists(args.file):
        console.print(f"[bold red]Fehler:[/bold red] Die Datei '{args.file}' wurde nicht gefunden.")
        sys.exit(1)

    with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
        recon_data = f.read()

    gateway = LocalAIReconGatewayFree(api_url=args.endpoint)
    chunks = list(gateway.chunk_data(recon_data))
    
    console.print(f"[*] Datei geladen. Zerlegt in [bold green]{len(chunks)}[/bold green] Chunks zur Basis-Verarbeitung.\n")
    console.print("[dim]Hinweis: Multithreading und Final Synthesis sind der Premium-Version vorbehalten.[/dim]\n")

    full_report = ""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Sende Daten an LLM (Sequenziell)...", total=len(chunks))
            
            for i, chunk in enumerate(chunks, 1):
                progress.update(task, description=f"[cyan]Analysiere Chunk {i}/{len(chunks)}...")
                analysis = gateway.analyze_chunk(chunk)
                full_report += f"### Analyse Teil {i}\n{analysis}\n\n"
                progress.advance(task)

    except KeyboardInterrupt:
        console.print("\n[bold yellow][!] Analyse vom Benutzer abgebrochen (Strg+C).[/bold yellow]")
        sys.exit(0)

    console.print(Panel("[bold green]✅ Analyse abgeschlossen![/bold green]"))
    console.print("\n[bold underline]KI-Ergebnis:[/bold underline]\n")
    
    console.print(Markdown(full_report))

if __name__ == "__main__":
    main()
