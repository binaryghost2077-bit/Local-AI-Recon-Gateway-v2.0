import argparse
import sys
import os
import json
import time
import requests
import concurrent.futures

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

# Initialisiere die Rich-Console für ein sauberes CLI-Interface
console = Console()

class LocalAIReconGateway:
    def __init__(self, api_url="http://127.0.0.1:1234/v1/chat/completions", model="local-model", custom_prompt=None, api_key=None):
        self.api_url = api_url
        self.model = model
        self.api_key = api_key
        
        if custom_prompt:
            self.system_prompt = custom_prompt
        else:
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
            
        self.synthesis_prompt = (
            "Du bist ein Senior Penetration Tester. Du erhältst im Folgenden mehrere Markdown-Action-Pläne, "
            "die von anderen Analysten aus verschiedenen Teilen einer Recon-Logdatei extrahiert wurden.\n"
            "Deine Aufgabe:\n"
            "1. Aggregiere diese Pläne in einen einzigen, konsolidierten und deduplizierten Master Action Plan.\n"
            "2. Entferne Duplikate (z.B. wenn derselbe Port auf derselben IP mehrfach gemeldet wurde).\n"
            "3. Priorisiere die kritischsten Funde ganz oben.\n"
            "4. Behalte die 🚨 Markierungen bei.\n"
            "5. Antworte AUSSCHLIESSLICH mit dem finalen Markdown-Bericht. Keine einleitenden Sätze."
        )

    def chunk_data(self, text, max_chars=12000):
        """
        Zerlegt große Log-Dateien kontext-erhaltend (Zeile für Zeile), 
        um das Token-Limit nicht zu sprengen.
        """
        lines = text.split('\n')
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_len = len(line) + 1 # +1 für \n
            if current_length + line_len > max_chars and current_chunk:
                yield "\n".join(current_chunk)
                current_chunk = [line]
                current_length = line_len
            else:
                current_chunk.append(line)
                current_length += line_len
                
        if current_chunk:
            yield "\n".join(current_chunk)

    def _call_llm(self, messages, max_retries=3, temperature=0.1):
        """
        Interne Methode für den API-Aufruf mit Retry-Logik (Exponential Backoff).
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1500
        }
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(self.api_url, json=payload, headers=headers, timeout=600)
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
            except requests.exceptions.Timeout:
                console.print(f"[yellow][!] Timeout bei API-Aufruf. Versuch {attempt}/{max_retries}...[/yellow]")
            except requests.exceptions.ConnectionError:
                console.print(f"[yellow][!] Verbindungsfehler. Versuch {attempt}/{max_retries}...[/yellow]")
            except Exception as e:
                console.print(f"[yellow][!] API Fehler: {e}. Versuch {attempt}/{max_retries}...[/yellow]")
                
            if attempt < max_retries:
                time.sleep(2 ** attempt) # Exponential Backoff: 2s, 4s, 8s...
                
        console.print("[bold red][!] API-Aufruf nach mehreren Versuchen fehlgeschlagen.[/bold red]")
        return "Fehler: LLM API nicht erreichbar."

    def analyze_chunk(self, chunk):
        """
        Sendet den Daten-Chunk an das lokale LLM.
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Analysiere folgenden Recon-Auszug:\n\n{chunk}"}
        ]
        return self._call_llm(messages)

    def synthesize_reports(self, reports):
        """
        Erstellt einen aggregierten Abschlussbericht aus allen Teil-Analysen.
        """
        if not reports:
            return "Keine Daten zur Aggregation vorhanden."
            
        combined_reports = "\n\n---\n\n".join([f"Report {i+1}:\n{r}" for i, r in enumerate(reports)])
        
        messages = [
            {"role": "system", "content": self.synthesis_prompt},
            {"role": "user", "content": f"Hier sind die zu aggregierenden Berichte:\n\n{combined_reports}"}
        ]
        return self._call_llm(messages, temperature=0.2) # Etwas höhere Temp für Aggregation

def main():
    parser = argparse.ArgumentParser(description="KI-Recon-Gateway: Lokale LLM-Analyse für Bug Bounties (Premium)")
    parser.add_argument("-f", "--file", required=True, help="Pfad zur Recon-Logdatei (z.B. nmap_output.txt)")
    parser.add_argument("-e", "--endpoint", default="http://127.0.0.1:1234/v1/chat/completions", help="Lokaler KI-API-Endpoint (Standard: LM Studio)")
    parser.add_argument("-t", "--threads", type=int, default=1, help="Anzahl paralleler Anfragen (Vorsicht bei lokalen LLMs)")
    parser.add_argument("-o", "--output", help="Pfad zum Speichern des Master Action Plans als Markdown-Datei")
    parser.add_argument("-j", "--json", help="Pfad zum Speichern aller rohen Chunk-Ergebnisse als JSON (für Automatisierung)")
    parser.add_argument("-p", "--prompt", help="Pfad zu einer Datei mit einem benutzerdefinierten System-Prompt")
    parser.add_argument("-k", "--api-key", help="API Key für das LLM Backend (z.B. LM Studio)")
    parser.add_argument("-m", "--model", default="local-model", help="Modell-Name (z.B. orpheus-3b-german-ft.gguf)")
    args = parser.parse_args()

    console.print(Panel.fit("[bold blue]Local AI Recon Gateway v2.0 (Premium)[/bold blue]\n[dim]Initializing advanced offline analysis...[/dim]"))

    if not os.path.exists(args.file):
        console.print(f"[bold red]Fehler:[/bold red] Die Datei '{args.file}' wurde nicht gefunden.")
        sys.exit(1)

    custom_prompt = None
    if args.prompt:
        if not os.path.exists(args.prompt):
            console.print(f"[bold red]Fehler:[/bold red] Prompt-Datei '{args.prompt}' nicht gefunden.")
            sys.exit(1)
        with open(args.prompt, 'r', encoding='utf-8') as pf:
            custom_prompt = pf.read()

    with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
        recon_data = f.read()

    gateway = LocalAIReconGateway(api_url=args.endpoint, model=args.model, custom_prompt=custom_prompt, api_key=args.api_key)
    chunks = list(gateway.chunk_data(recon_data))
    
    console.print(f"[*] Datei geladen. Kontext-erhaltend zerlegt in [bold green]{len(chunks)}[/bold green] Chunks.")
    if args.threads > 1:
        console.print(f"[*] Nutze Multithreading mit [bold yellow]{args.threads}[/bold yellow] Threads.\n")
    else:
        console.print("")

    # Chunk Processing via ThreadPoolExecutor
    chunk_reports = [None] * len(chunks)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console
        ) as progress:
            
            task = progress.add_task(f"[cyan]Analysiere {len(chunks)} Chunks via LLM...", total=len(chunks))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
                # Submit tasks and keep track of index to maintain order
                future_to_index = {executor.submit(gateway.analyze_chunk, chunk): i for i, chunk in enumerate(chunks)}
                
                for future in concurrent.futures.as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        analysis = future.result()
                        chunk_reports[idx] = analysis
                    except Exception as exc:
                        chunk_reports[idx] = f"Fehler bei Chunk {idx+1}: {exc}"
                    finally:
                        progress.advance(task)

    except KeyboardInterrupt:
        console.print("\n[bold yellow][!] Analyse vom Benutzer abgebrochen (Strg+C).[/bold yellow]")
        sys.exit(0)

    # Export JSON if requested
    if args.json:
        try:
            with open(args.json, 'w', encoding='utf-8') as jf:
                json.dump({"chunks": chunk_reports}, jf, indent=4)
            console.print(f"[*] Rohe Chunk-Ergebnisse gespeichert in: [green]{args.json}[/green]")
        except Exception as e:
            console.print(f"[bold red]Fehler beim Speichern der JSON-Datei:[/bold red] {e}")

    # Final Synthesis
    master_plan = ""
    if len(chunk_reports) > 1:
        console.print("[cyan]Erstelle aggregierten Master Action Plan (Final Synthesis)...[/cyan]")
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
                progress.add_task("[cyan]Aggregiere Ergebnisse...", total=None)
                master_plan = gateway.synthesize_reports(chunk_reports)
        except KeyboardInterrupt:
            console.print("\n[bold yellow][!] Aggregation abgebrochen.[/bold yellow]")
            sys.exit(0)
    else:
        # If only one chunk, the master plan is just the first chunk's report
        master_plan = chunk_reports[0] if chunk_reports else "Keine Daten analysiert."

    console.print(Panel("[bold green]✅ Analyse komplett abgeschlossen![/bold green]"))
    console.print("\n[bold underline]KI Master Action Plan:[/bold underline]\n")
    console.print(Markdown(master_plan))
    
    # Export Markdown if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as mf:
                mf.write(master_plan)
            console.print(f"\n[*] Master Action Plan erfolgreich gespeichert in: [bold green]{args.output}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Fehler beim Speichern der Markdown-Datei:[/bold red] {e}")

if __name__ == "__main__":
    main()