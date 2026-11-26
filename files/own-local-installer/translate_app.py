"""Translate the decoded Moonlight app UI from Italian to English.

Input:  ~/moonlight-web-test/backup/ownmoon-local.html
Output: ~/moonlight-web-test/backup/ownmoon-en.html

Protocol identifiers, localStorage keys, the Sidee install-token meta tag, and
the packed wrapper are deliberately left alone. Only user-visible text, ARIA
labels, and Italian comments are changed.
"""
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backup" / "ownmoon-local.html"
OUT = ROOT / "backup" / "ownmoon-en.html"

# Longer strings first so shorter generic replacements do not split them.
PAIRS = [
    ('<html lang="it">', '<html lang="en">'),
    ("  /* Il telecomando non ha una tastiera: questo tastierino è l'unico modo per\n"
     "     scrivere l'indirizzo con soli OK/frecce. Quattro colonne, layout base\n"
     "     1280 con scala al viewport (il webview misurato è 1920x1080). */",
     "  /* The remote has no keyboard: this keypad is the only way to enter\n"
     "     the address using only OK/arrows. Four columns, base 1280 layout\n"
     "     scaled to the viewport (the measured webview is 1920x1080). */"),
    ('<div class="brand">Moonlight<small>Sidee+</small></div>',
     '<div class="brand">Moonlight<small>Local</small></div>'),
    ("<p class=\"lead\">Moonlight trasmette i giochi dal tuo PC alla TV. Sul PC serve\n"
     "        <b>Sunshine-Web-RTC</b> con il server WebRTC attivo (porta 8000). TV e PC devono stare\n"
     "        sulla stessa rete locale.</p>",
     "<p class=\"lead\">Moonlight streams games from your PC to your TV. Your PC needs\n"
     "        <b>Sunshine-Web-RTC</b> with the WebRTC server enabled (port 8000). The TV and PC must be\n"
     "        on the same local network.</p>"),
    ("<h1>Il tuo PC, <em>sulla TV</em>.</h1>", "<h1>Your PC, <em>on your TV</em>.</h1>"),
    ('aria-label="Indirizzo del PC"', 'aria-label="PC address"'),
    ('aria-label="Tastierino indirizzo"', 'aria-label="Address keypad"'),
    ('aria-label="Cancella ultimo carattere"', 'aria-label="Delete last character"'),
    ("<p class=\"hint\">Scrivi l'indirizzo col <b>tastierino a schermo</b> (frecce + OK) o coi tasti\n"
     "        numerici del telecomando; <b>:</b> aggiunge la porta se non è 8000.\n"
     "        La prima volta il PC mostra un PIN: inseriscilo in Sunshine, alla voce <b>PIN</b>.\n"
     "        Dopo il primo accoppiamento la TV entra da sola. Il telecomando funziona come controller\n"
     "        (frecce, OK, Back). <b>Non serve installare nulla sulla TV oltre a Sidee.</b></p>",
     "<p class=\"hint\">Enter the address with the <b>on-screen keypad</b> (arrows + OK) or with the\n"
     "        remote's number keys; <b>:</b> adds the port when it is not 8000.\n"
     "        The first time, the PC shows a PIN: enter it in Sunshine under <b>PIN</b>.\n"
     "        After the first pairing, the TV connects automatically. The remote works as a controller\n"
     "        (arrows, OK, Back). <b>No extra TV installation is needed.</b></p>"),
    ("<h1>Inserisci il PIN <em>su Sunshine</em>.</h1>",
     "<h1>Enter the PIN <em>in Sunshine</em>.</h1>"),
    ("<div class=\"cap\">PIN di accoppiamento</div>", "<div class=\"cap\">Pairing PIN</div>"),
    ("<span>Apri Sunshine sul PC: <b>Web UI</b>, pagina <b>PIN</b>.</span>",
     "<span>Open Sunshine on the PC: <b>Web UI</b>, <b>PIN</b> page.</span>"),
    ("<span>Scegli questa TV nell'elenco e digita il PIN qui accanto.</span>",
     "<span>Select this TV in the list and enter the PIN shown here.</span>"),
    ("<span>Conferma: la TV si collega e mostra i giochi del PC.</span>",
     "<span>Confirm: the TV connects and shows your PC games.</span>"),
    ("<span>Il PIN scade dopo 5 minuti</span>", "<span>The PIN expires after 5 minutes</span>"),
    ("<div class=\"empty\" id=\"appsEmpty\" hidden>Il PC non ha ancora applicazioni in Sunshine.</div>",
     "<div class=\"empty\" id=\"appsEmpty\" hidden>The PC has no apps in Sunshine yet.</div>"),
    ("<div class=\"tip\">Back = esci · il gioco resta aperto sul PC</div>",
     "<div class=\"tip\">Back = exit · the game stays open on the PC</div>"),
    ('<button class="btn primary focusable" id="tapBtn">Premi OK per l\'audio</button>',
     '<button class="btn primary focusable" id="tapBtn">Press OK for audio</button>'),
    ("<span>Moonlight per Sidee+</span>", "<span>Moonlight Local</span>"),
    ("Credenziali o nonce non validi", "Invalid credentials or nonce"),
    (" · porta ", " · port "),
    ("Il PC non risponde su ", "The PC is not responding at "),
    (". Controlla che Sunshine-Web-RTC sia aperto e che la TV sia sulla stessa rete.",
     ". Check that Sunshine-Web-RTC is running and that the TV is on the same network."),
    ("Questo PC usa il vecchio Moonlight WebRTC Gateway. Installa Sunshine-Web-RTC.",
     "This PC uses the old Moonlight WebRTC Gateway. Install Sunshine-Web-RTC."),
    ("Connessione al PC interrotta. Riprova.", "Connection to PC interrupted. Try again."),
    ("Connessione rifiutata dal PC. Verifica l'indirizzo e la porta 8000.",
     "Connection refused by the PC. Check the address and port 8000."),
    ("Il PC non accetta l'accoppiamento TV: aggiorna Sunshine-Web-RTC.",
     "The PC does not accept TV pairing: update Sunshine-Web-RTC."),
    ("In attesa che confermi il PIN sul PC…", "Waiting for you to confirm the PIN on the PC…"),
    ("Il PIN è scaduto: eccone uno nuovo.", "The PIN expired: here is a new one."),
    ("Il PC ha inviato credenziali non valide. Riprova.",
     "The PC sent invalid credentials. Try again."),
    ("Nuovo PIN pronto.", "New PIN ready."),
    ("Accoppiato, carico le applicazioni…", "Paired, loading apps…"),
    ("Connesso · Sunshine pronto", "Connected · Sunshine ready"),
    ("Questa TV è disattivata in Sunshine. Riattivala da Troubleshooting.",
     "This TV is disabled in Sunshine. Re-enable it from Troubleshooting."),
    ("Il PC non riconosce più questa TV: nuovo accoppiamento.",
     "The PC no longer recognizes this TV: pairing again."),
    ("Accoppiamento annullato sul PC. Premi Nuovo PIN per riprovare.",
     "Pairing cancelled on the PC. Press New PIN to try again."),
    ("PIN errato sul PC: eccone uno nuovo.", "Wrong PIN on the PC: here is a new one."),
    ("Sunshine troppo vecchio per questa TV: aggiorna Sunshine-Web-RTC.",
     "Sunshine is too old for this TV: update Sunshine-Web-RTC."),
    ("Accoppiamento non riuscito: nuovo PIN.", "Pairing failed: new PIN."),
    ("Richiesta non riuscita", "Request failed"),
    ("In esecuzione sul PC", "Running on PC"),
    ("OK per avviare", "OK to launch"),
    ("OK avvia · Back torna ai PC", "OK starts · Back returns to PCs"),
    ("Nessuna app nel PC", "No apps on PC"),
    ("Il PC offre una sola qualità.", "The PC offers only one quality."),
    ("Il PC non ha annunciato qualità video.", "The PC did not announce any video quality."),
    ("Avvio di ", "Starting "),
    ("Connessione assente.", "No connection."),
    ("In diretta · ", "Live · "),
    ("Il PC ha interrotto la sessione.", "The PC ended the session."),
    ("Preparazione WebRTC…", "Preparing WebRTC…"),
    ("Connessione a Sunshine…", "Connecting to Sunshine…"),
    ("Avvio del gioco…", "Starting game…"),
    ("Connessione video persa. Torna alla libreria e riavvia.",
     "Video connection lost. Return to the library and restart."),
    ("WebRTC non disponibile su questa TV.", "WebRTC is not available on this TV."),
    ("Negoziazione video non riuscita.", "Video negotiation failed."),
    ("Rete    ", "Network "),
    (" · persi ", " · lost "),
    ("Segnale fermo", "Signal stalled"),
    ("Indirizzo non valido. Esempio: 192.168.1.20 oppure 192.168.1.20:8000",
     "Invalid address. Example: 192.168.1.20 or 192.168.1.20:8000"),
    ("Nuovo PIN: inseriscilo in Sunshine.", "New PIN: enter it in Sunshine."),
    ("Sidee+ · v", "Moonlight Local · v"),
    ("La pagina è servita in HTTPS e il PC parla WebSocket non cifrato (ws://), ",
     "The page is served over HTTPS and the PC uses unencrypted WebSocket (ws://), "),
    ("quindi il browser blocca la connessione. Apri Moonlight dalla tile Sidee sulla TV, ",
     "so the browser blocks the connection. Open Moonlight from the TV tile, "),
    ("oppure apri questa pagina in http:// dal PC (indirizzo del PC e porta 8000).",
     "or open this page over http:// from the PC (PC address and port 8000)."),
    ("Impossibile aprire la connessione: ", "Unable to open connection: "),
    ("Non connesso al PC", "Not connected to PC"),
    ("Connessione al PC interrotta. Riprova.", "Connection to PC interrupted. Try again."),
    ("In attesa del PC…", "Waiting for the PC…"),
    ("Connessione…", "Connecting…"),
    ("Connessione persa", "Connection lost"),
    ("In diretta", "Live"),
    ("Cancella ultimo carattere", "Delete last character"),
    ("PIN di accoppiamento", "Pairing PIN"),
    ("Nuovo PIN", "New PIN"),
    ("Riconnetti", "Reconnect"),
    ("Connetti", "Connect"),
    ("Cancella", "Clear"),
    ("Rimuovi", "Remove"),
    ("Annulla", "Cancel"),
    ("Non accoppiato", "Not paired"),
    ("Non connesso", "Not connected"),
    ("Disconnesso", "Disconnected"),
    ("Verifica…", "Verifying…"),
    ("Accoppiamento", "Pairing"),
    ("Connesso", "Connected"),
    ("Qualità: ", "Quality: "),
    ("Preparazione…", "Preparing…"),
    ("Chiusura…", "Closing…"),
    ("Applicazione", "Application"),
    ("applicazione", "application"),
]

# Deduplicate while preserving order.
seen = set()
PAIRS = [p for p in PAIRS if not (p in seen or seen.add(p))]


def main():
    text = SRC.read_text(encoding="utf-8")
    for old, new in PAIRS:
        count = text.count(old)
        if count:
            text = text.replace(old, new)
            print("replaced %2d  %s" % (count, old[:70].replace("\n", " ")))
        else:
            print("MISSING     %s" % old[:70].replace("\n", " "))

    OUT.write_text(text, encoding="utf-8")
    raw = text.encode("utf-8")
    print("wrote", OUT, len(raw), "bytes")
    print("sha256", hashlib.sha256(raw).hexdigest())

    leftovers = []
    for token in ["Il tuo", "sulla TV", "trasmette", "porta ", "Indirizzo", "Connetti",
                  "Riconnetti", "Cancella", "In attesa", "Qualità", "Preparazione",
                  "Connessione", "Connesso", "Non connesso", "Disconnesso", "Verifica",
                  "Accoppiamento", "Nuovo PIN", "Annulla", "scade", "(applicazioni)",
                  "applicazioni", "Avvio", "In diretta", "Chiusura", "Rete ", "persi",
                  "Indirizzo non valido", "Sidee+"]:
        if token in text:
            leftovers.append(token)
    print("leftovers", ",".join(leftovers) if leftovers else "none")
    if leftovers:
        sys.exit(2)


if __name__ == "__main__":
    main()
