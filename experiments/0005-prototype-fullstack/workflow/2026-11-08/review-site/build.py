#!/usr/bin/env python3
"""Build the OWNER walk-through site (D037) from the item list below.

Run from the repo root: python3 experiments/0005-prototype-fullstack/workflow/2026-11-08/review-site/build.py
Writes index.html and one page per group into this directory. BEAML snippets are colored with
integrations/zed-beaml/preview.py --chat. Source of the items: ../../2026-11-07/owner-review.md.
"""
import html, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../../.."))
PREVIEW = os.path.join(ROOT, "integrations/zed-beaml/preview.py")


def beaml(code):
    with tempfile.NamedTemporaryFile("w", suffix=".beaml", delete=False) as f:
        f.write(code.strip("\n") + "\n")
    out = subprocess.run([sys.executable, PREVIEW, "--chat", f.name], capture_output=True, text=True, check=True).stdout
    os.unlink(f.name)
    return re.sub(r"<div class=h>.*?</div>", "", out, count=1)


def ex(code):
    """Hand-colored Elixir: keywords, atoms, strings, comments."""
    s = html.escape(code.strip("\n"))
    s = re.sub(r"(#[^\n]*)", r"<i class=m>\1</i>", s)
    s = re.sub(r"(&quot;[^&]*?&quot;)", r"<i class=s>\1</i>", s)
    s = re.sub(r"(?<![\w:])(:[a-z_]+)", r"<i class=c>\1</i>", s)
    s = re.sub(r"\b(def|defmodule|do|end|case|fn|when)\b", r"<i class=k>\1</i>", s)
    s = re.sub(r"\b([A-Z][A-Za-z]+(?:\.[A-Z][A-Za-z]+)*)\b", r"<i class=t>\1</i>", s)
    return "<pre>" + s + "</pre>"


def text(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


# status: decided | default | open | parked
# An item: dict(id, title, status, by, what, why, code=[html], options=[(letter, text, built?)], ref)
G = []


def group(slug, title, lead, items):
    G.append(dict(slug=slug, title=title, lead=lead, items=items))


def it(id, title, status, by, what, why="", code=(), options=(), note="", dl=""):
    return dict(id=id, title=title, status=status, by=by, what=what, why=why, code=list(code), options=list(options), note=note, dl=dl)


# ---------------------------------------------------------------- 1
group("01-review", "Schlussreview Slice 6: drei hohe Einwände",
      "Der Devil's Advocate hat am Ende des Slice drei Einwände mit Stufe hoch stehen lassen. Jeder braucht eine Entscheidung von dir. Sie stehen vor allen anderen Punkten.",
      [
          it("A1", "Der PASS beweist weniger als die These", "open", "Opus (Schlussreview)",
             "Die These lautet: BEAML trägt die Kette vom Formular bis zur Zeile in Postgres. Gebaut und grün ist davon nur die String-Kette `Note`. Der echte `Order`-Pfad mit `Amount` und `Channel` wartet auf M4. Ein vertauschtes `Channel`-Literal baut noch (DL-140 ist beschlossen, nicht gebaut). Aus einem Block kommt man nur per SQL-Delete heraus. Die v2→v3-Umstellung lief über ein Python-Skript.",
             "Wenn README und Register weiter „PASS“ sagen, liest ein Dritter mehr hinein als gezeigt wurde.",
             [beaml('''
// Das läuft heute durch die ganze Kette:
type Note { text: String }
// Das wartet auf M4 (Konstruktor- und Enum-Feld in einer Zeile):
type Order { order_id: String amount: Amount channel: Channel }
''')],
             [("A", "PASS-Wortlaut behalten", False),
              ("B", "Anspruch eingrenzen: „String-Kette, Blocks bewiesen, noch keine Fate-Form“ in README, Register und Pages", False)]),
          it("A2", "Eine nicht dekodierbare Zeile bricht die Listenseite", "open", "Opus (Schlussreview)",
             "Der Build zählt eine kaputte Zeile (falscher Digest, SQL-`UPDATE` ohne neuen Digest) als „nicht dekodierbar“ und geht durch. Zur Laufzeit scheitert dann der ganze `db.list`-Aufruf (QDB-4 A: eine schlechte Zeile, keine Liste).",
             "Der Build sagt grün, die Seite /orders ist leer oder rot. Das ist genau der Fall, den BEAML verhindern soll.",
             [],
             [("A", "Build blockt bei einer nicht dekodierbaren Zeile", False),
              ("B", "`db.list` überspringt die Zeile und meldet sie", False),
              ("C", "Ausfall hinnehmen (wie gebaut)", True)],
             note="Hängt mit QDB-4 und P4c zusammen (Seite „Zeilen“)."),
          it("A3", "Der Compiler prüft nicht, woher der Zeilen-Snapshot kommt", "open", "Opus (Schlussreview)",
             "`--stored` liest `rows.jsonl` und daneben `snapshot-meta.json`. Fehlt die Meta-Datei, exit 0. Gelesen wird nur `row_count`. `run.py run` setzt die Datenbank zurück und prüft gegen 0 Zeilen.",
             "Ein Build gegen die falsche oder leere Datenbank sieht aus wie ein Build gegen Produktion.",
             [],
             [("A", "Compiler verlangt die Meta-Datei und prüft Datenbankname und Abfragezeit", False),
              ("B", "`--stored` fragt die Tabelle selbst live ab (DL-127-Wortlaut)", False),
              ("C", "wie gebaut, nur die Host-Prüfung N8c", True)]),
      ])

# ---------------------------------------------------------------- 2
group("02-order-chain", "M4: die echte Order-Kette",
      "Alles hier dreht sich um eine Regel: D6B-39 verbietet in einem verketteten TYPE ein Konstruktor- oder Enum-Feld. Darum läuft der `Order`-Pfad noch nicht über Zeilen.",
      [
          it("M4", "Darf eine verkettete Zeile Amount und Channel tragen?", "parked", "OWNER geparkt (D036); gebauter Stand Fable (Repair)",
             "Ein `migrate Order v1 -> v2` wäre heute ein Build-Fehler, weil `Order` die Felder `amount: Amount` (Konstruktor) und `channel: Channel` (Enum) hat. Gebaut ist: nichts geändert, D6B-39 gilt, Test N18 pinnt den heutigen Hilfetext.",
             "Kritischer Pfad: ohne M4 kein `Order`-Chain, und mit M3 und M5 auch keine Fate-Formen (N9).",
             [beaml('''
type Amount { value: String currency: String }
enum Channel { Web = "web"  App = "app"  Unknown(String) }
type Order { order_id: String amount: Amount channel: Channel }
// Heute ein Build-Fehler, sobald eine Kette dranhängt:
type Order v2 { order_id: String amount: Amount channel: Channel note: String }
migrate Order v1 -> v2 { add note: String = "" }
''')],
             [("A", "D6B-39 bleibt; der DL-102-Hilfetext sagt „stelle die vorige Klausel oder das Literal wieder her“", False),
              ("B", "D6B-39 vor der ersten FATE OPERATION aufheben", False)]),
          it("QDB-8", "Der verkettete Lesepfad läuft solange auf Note", "default", "Fable (Default, offen)",
             "Weil `Order` nicht verkettet werden darf, prüfen die Tests N7/N7b die MIGRATE CHAIN über Zeilen an einem String-TYPE `Note { text: String }`. Das ist gebaut und grün (`note_v2`: v1-Zeilen migrieren beim Lesen, keine DDL).",
             "",
             [beaml('''
type Note v2 { text: String tag: String }
migrate Note v1 -> v2 { add tag: String = "" }
''')],
             [("A", "N7/N7b auf M4 blocken", False),
              ("B", "String-TYPE `Note` mit eigener Kette", True),
              ("C", "M4 jetzt beantworten", False)]),
          it("N9", "Der strengere Amount braucht eine Fate-Form", "parked", "OWNER geparkt (über M3, M4, M5)",
             "Die Variante `stricter` lehnt Beträge ohne Währung ab. `--stored` blockt den Build gegen echte Zeilen, wie gewollt. Der kleinste Ausweg wäre `quarantine amount`; die Form gibt es noch nicht.",
             "Heute kommt man nur mit einem SQL-Delete aus dem Block.",
             [beaml('''
fn Amount _, "" -> Amount ! BadAmount = BadAmount {}
// Eine gespeicherte Zeile mit currency "" blockt jetzt den Build.
''')],
             []),
      ])

# ---------------------------------------------------------------- 3
group("03-encoder", "Wie eine Seite einen BEAML-Wert anzeigt",
      "Die Listenseite muss aus dem BEAML-Wert `Order` etwas machen, das HEEx rendern kann. Die Frage ist, welche Funktion der Host dafür ruft.",
      [
          it("ENC", "Der Host ruft `Orders.__beaml_encode_order/1`", "default", "Opus (GREEN exp0005); C konkretisiert von Opus (TEST)",
             "Die Seite /orders ruft heute den compiler-internen Encoder. Das ist der kleinste Weg: keine Compiler-Änderung, das Literal `\"web\"` bleibt in BEAML. Aber ein Doppelunterstrich-Name ist ein Interface gegen die Sprache, das wir nie versprochen haben.",
             "Jede Umbenennung im Compiler bricht die App still.",
             [ex('''
# order_list_live.ex, mount/3
{:ok, assign(socket, items: Enum.map(items, &Orders.__beaml_encode_order/1))}
'''), beaml('''
// Option C: der Compiler erzeugt pro TYPE eine öffentliche Projektion
// (Name noch offen, z. B. project_order/1). Kein neues Schlüsselwort.
type Order { order_id: String amount: Amount channel: Channel }
''')],
             [("A", "Host ruft den generierten internen Encoder", True),
              ("B", "Host matcht das Enum-Tupel selbst", False),
              ("C", "Compiler erzeugt eine öffentliche `project_<type>/1`", False)]),
      ])

# ---------------------------------------------------------------- 4
group("04-rows", "Zeilen: Inhalt und Form-Prüfung",
      "Was steht in einer gespeicherten Zeile, und was prüft `--stored` daran?",
      [
          it("Q5-10", "Was steht im `value` einer Zeile?", "default", "Fable (Default, offen)",
             "Gebaut: die Zeile trägt den Record-Kern v3 (version, trace_id, operation, type, value, value_sha256, …), nicht nur die nackte Projektion. So ist eine Zeile dasselbe Ding wie ein RESPONSE RECORD und `--stored` liest beide mit einem Leser (DL-127, DL-143).",
             "",
             [],
             [("A", "nackte Projektion", False), ("B", "Record-Kern v3 in der Zeile", True)]),
          it("P4c", "Fehlendes oder falsch getyptes String-Feld in einer Zeile", "default", "Fable (Default, offen)",
             "Vorher: eine Zeile ohne das Feld `text` galt als geprüft und `db.list` fiel zur Laufzeit. Jetzt blockt der Build mit dem DL-102-Text. Eine Zeile wird an ihrer eigenen gespeicherten TYPE VERSION geprüft (TEST-Repair).",
             "",
             [],
             [("A", "Build blockt mit DL-102-Text", True), ("B", "als nicht dekodierbar zählen", False)]),
          it("P4c-http", "Dieselbe Lücke bei http RESPONSE RECORDS", "default", "Opus (GREEN P4c); auf Migrate gehoben vom TEST-Review",
             "Für http-Records bleibt die Lücke offen: ein Record mit fehlendem String-Feld geht durch. Ein Guard N32e hält den Stand fest.",
             "",
             [],
             [("A", "Lücke behalten", True), ("B", "http nach dem Versions-Fix mit prüfen", False)]),
          it("P4c-text", "Ein Fehlertext für beide Fälle", "default", "Opus (RED P4c)",
             "Fehlender Schlüssel und Nicht-String-Wert geben denselben Text: `TYPE <T>: 1 stored ROW of table <t> has no String value for field <f>` plus Quelle und DL-102-Hilfezeile.",
             "", [], [("A", "ein Text", True), ("B", "zwei Texte", False)]),
          it("QDB-4", "Eine schlechte Zeile lässt den ganzen `db.list` fallen", "default", "Opus (PLAN db-transport)",
             "Gebaut: `db.list` gibt `{:error, decode}` zurück, sobald eine Zeile nicht dekodiert. Das ist der Laufzeitteil von A2.",
             "", [], [("A", "wie gebaut", True)]),
          it("QDB-3", "Neueste Zeile gewinnt bei `db.get`", "default", "Opus (PLAN db-transport)",
             "Mehrere Zeilen zum selben Schlüssel: die zuletzt geschriebene zählt.", "", [], [("A", "wie gebaut", True)]),
      ])

# ---------------------------------------------------------------- 5
group("05-names", "Namen: Modul, Rejected, reservierte Namen",
      "Welche Namen erzeugt der Compiler, und welche darf der Host nicht benutzen?",
      [
          it("Q6E-1", "Welche Quellen heißen nach dem Dateinamen?", "default", "Opus (PLAN multi-effect)",
             "`orders.beaml` erzeugt heute `defmodule Orders`, aber nur, wenn die Datei eine ENTRY LINE hat. Alle anderen Quellen heißen weiter `BeamlSpike`. Grund: sonst wandern alle sechs Byte-Pins.",
             "Zwei Regeln für einen Namen sind schwer zu erklären.",
             [beaml('''
// orders.beaml  ->  defmodule Orders (hat eine ENTRY LINE)
effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
''')],
             [("A", "jede Quelle (alle Byte-Pins wandern)", False), ("C", "nur eine Quelle mit ENTRY LINE", True)]),
          it("Q6E-2", "Wo wohnt das `Rejected`-Struct?", "default", "Opus (PLAN multi-effect)",
             "Gebaut: `Orders.Rejected{reason: \"decode\"}`. DL-133 hatte die Form mit `BeamlSpike.Rejected` benannt; die Docs merken das an.",
             "", [ex('''{:error, %Orders.Rejected{reason: "decode"}}''')],
             [("A", "`<Modul>.Rejected`", True), ("B", "ein festes `BeamlSpike.Rejected`", False)]),
          it("Q5-6", "Modulname aus dem Dateinamen, keine `module`-Zeile", "default", "Opus (PLAN exp0005)",
             "Kein neues Schlüsselwort. Der Stamm `orders` wird `Orders`.", "", [],
             [("A", "aus dem Dateinamen", True), ("B", "eine `module`-Zeile", False)]),
          it("RESV", "`BeamlDb` und `System` sind als Modulname gesperrt", "default", "Opus (GREEN db-transport)",
             "Eine Datei `beaml_db.beaml` gäbe das Modul `BeamlDb`, das der erzeugte Code selbst ruft. Build-Fehler, wie D6B-203 für `System`.", "", [],
             [("A", "wie gebaut", True)]),
      ])

# ---------------------------------------------------------------- 6
group("06-db", "Datenbank-Transporte",
      "Wie `db.put`, `db.get` und `db.list` den Host rufen, was dabei aufgezeichnet wird und wie `--stored` an die Zeilen kommt.",
      [
          it("QDB-2", "Die Host-Signaturen", "default", "Opus (PLAN db-transport); JSON von Fable (Repair)",
             "Gebaut: `BeamlDb.put(table, {type, version}, json)`, `get/3`, `list/3`. Der erzeugte Code kodiert den Kern mit OTP `:json`; `get` und `list` geben JSON-Binaries zurück. Ein fester Modulname, kein Behaviour.",
             "Der Host muss genau dieses Modul mit genau diesen drei Funktionen liefern.",
             [beaml('''
effect orders.save Order -> Order ! StoreError = db.put("records")
effect orders.list OrderQuery -> OrderList ! StoreError = db.list("records")
'''), ex('''
defmodule Proto.BeamlDb do
  def put(table, {type, version}, json), do: ...   # {:ok, json} | {:error, reason}
  def get(table, {type, version}, key_json), do: ...
  def list(table, {type, version}, query_json), do: ...
end
''')],
             [("A", "fest `BeamlDb.put/3, get/3, list/3`", True), ("B", "konfiguriertes Modul mit Behaviour (Q5-8 B) / `put/4` (QDB-2 B)", False)]),
          it("QDB-6b", "Ein gescheiterter db-Aufruf schreibt ein rejected-Record", "default", "Fable (Default, offen)",
             "Bei http schreibt ein Transportfehler kein Record. Bei db schon: `outcome: rejected, reason: transport`. Zwei Ströme, zwei Regeln.", "", [],
             [("A", "ja, ein rejected-Record", True), ("B", "kein Record, wie http", False)]),
          it("QDB-1", "Der Schlüssel von `db.get` ist ein String-Feld des Key-TYPE", "default", "Opus (PLAN db-transport)",
             "Der Key-TYPE hat genau ein String-Feld, dessen Name ist der Schlüssel. Q5-1 (Zeilen-`id` statt TYPE-Feld) ist damit B. In 0005 ungenutzt.", "",
             [beaml('''
type OrderKey { order_id: String }
effect orders.get OrderKey -> Order ! StoreError = db.get("records")
''')],
             [("A", "ein String-Feld im Key-TYPE", True), ("B", "Schlüssel im Aufruf / Zeilen-id", False)]),
          it("GET", "`BeamlDb.get/3` sucht mit `@>` Containment", "default", "Opus (GREEN exp0005)",
             "Gebaut, ungenutzt: Key-Map als JSON, `value->'value' @> key`, neueste Zeile, `{:ok, nil}` wenn keine. TEST O2: migrierte Felder werden nicht gefunden; ein leerer Schlüssel trifft jede Zeile.",
             "", [], [("A", "Containment, neueste Zeile", True), ("B", "ein Feld pro Aufruf mit Unique-Index", False)]),
          it("QDB-5", "db-Aufrufe landen im Strom `responses`", "default", "Opus (PLAN db-transport)",
             "Kein eigener Strom. Kern v3 plus `request`.", "", [], [("A", "Strom `responses`", True), ("B", "eigener Strom mit Zeilenreferenzen", False)]),
          it("QDB-7", "Der ROW SNAPSHOT: `rows.jsonl` plus `snapshot-meta.json`", "default", "Opus (PLAN db-transport)",
             "`mix beaml.stored DIR` schreibt die Zeilen als JSONL neben die Records; `row_count` in der Meta wird geprüft. Siehe A3.", "", [],
             [("A", "`rows.jsonl` daneben, Meta geprüft", True), ("B", "eine gemischte Datei", False)]),
          it("Q5-4", "`--stored` über Postgres läuft über eine Host-Task", "default", "Opus (PLAN exp0005)",
             "Der Compiler ruft kein `psql`. Der Host schreibt den Snapshot, der Compiler liest Dateien.", "", [],
             [("A", "Compiler ruft `psql`", False), ("B", "Host-Task `mix beaml.stored` schreibt den Snapshot", True)]),
          it("STORED-ARG", "`mix beaml.stored DIR` nimmt das Snapshot-Verzeichnis", "default", "Opus (RED exp0005)",
             "Ein Argument. `run.py` ruft danach den Compiler.", "", [],
             [("A", "Verzeichnis, run.py ruft den Compiler", True), ("B", "Quelle, die Task ruft den Compiler", False)]),
          it("SNAP-SET", "`--stored` liest nur die Zeilen, keine alten Capture-Records", "default", "Opus (RED exp0005)",
             "`mix beaml.stored` schreibt ein leeres `responses.jsonl`. Die Capture-Dateien früherer Läufe (Q5-7 A) sind kein Store.", "", [],
             [("A", "nur STORED ROWS", True), ("B", "auch Capture-Records früherer Läufe", False)]),
          it("Q5-7", "Capture-Ströme als JSONL pro Lauf", "default", "Opus (PLAN exp0005)",
             "Keine Tabelle `records` für die Aufzeichnung.", "", [], [("A", "JSONL pro Lauf", True), ("B", "Zeilen in `records`", False)]),
          it("Q5-2", "`db.list`: neueste zuerst, 100, fest im Host", "default", "Opus (PLAN exp0005)",
             "`OrderQuery {}` ist leer. Reihenfolge und Limit stehen im Host.", "", [],
             [("A", "fest im Host", True), ("B", "Felder in `OrderQuery`", False)]),
          it("ORPHAN", "Verwaiste Zeilen blocken wie verwaiste Records", "default", "Opus (RED db-stored)",
             "Eine Zeile, deren `operation` keinen EFFECT und keine RETIRE LINE mehr hat, blockt mit dem DL-040-Text und der Hilfe `declare: retire <op> keep <n> days`. Eine RETIRE LINE gibt die Zeilen frei (gezählt, nicht geprüft). Was `retire` für Zeilen bedeutet, bleibt M5.", "", [],
             [("A", "blocken mit DL-040-Text", True), ("B", "nur auf operation blocken", False), ("C", "als nicht dekodierbar zählen", False)]),
          it("OFFCHAIN", "Eine Zeile einer TYPE VERSION ohne Kette blockt", "default", "Opus (RED db-stored)",
             "Eine akzeptierte Zeile `Note v3`, wenn es nur `v1 -> v2` gibt: Pfadtext, Build blockt.", "", [],
             [("A", "blocken mit Pfadtext", True), ("B", "als nicht dekodierbar zählen", False)]),
      ])

# ---------------------------------------------------------------- 7
group("07-record-v3", "Record-Format v3",
      "Ein Format für alle Ströme (DL-143). Die acht Fragen, die der Plan als Default entschieden hat, und die Zählzeilen-Regel.",
      [
          it("CORE", "Der Kern: 14 Schlüssel", "decided", "13ue (DL-141 bis DL-143)",
             "version 3, trace_id, span_id, artifact_id, operation, attempt, type, value, value_sha256, redacted, unknown_keys, unknown_fields, outcome, reason. http hängt `request` und `status` an.", "", [], [], dl="DL-143"),
          it("QV3-1", "Marker `version: 3`", "default", "Opus (PLAN record-v3)", "Kein `format`-Schlüssel, kein Dateiname.", "", [],
             [("A", "`version: 3`", True), ("B", "`format`-Schlüssel", False), ("C", "Dateiname", False)]),
          it("QV3-2", "Ein `span_id`", "default", "Opus (PLAN record-v3)", "Keine Client/Server-Trennung, kein `span_kind`.", "", [],
             [("A", "ein `span_id`", True), ("B", "Client- und Server-Span als Extras", False), ("C", "`span_id` plus `span_kind`", False)]),
          it("QV3-3", "Transport-Extras flach", "default", "Opus (PLAN record-v3)", "`status` und `request` stehen oben, nicht unter `transport: {}`.", "", [],
             [("A", "flach", True), ("B", "verschachtelt", False)]),
          it("QV3-4", "`outcome`/`reason`: erst Status, dann Decode", "default", "Opus (PLAN record-v3)",
             "`reason` ist `status`, `decode` oder `constructor`, gleich dem Live-Fehlergrund. Weiter als der DL-136-Wortlaut.", "", [],
             [("A", "Status, dann Decode", True), ("B", "nur Status", False)]),
          it("QV3-5", "Alte v2-Dateien einmal umgeschrieben", "default", "Opus (PLAN record-v3)",
             "15 Fixtures per `convert_v3.py`. Der Leser kennt nur v3.", "", [],
             [("A", "einmaliges Umschreiben, Leser nur v3", True), ("B", "Leser nimmt v2 und v3", False)]),
          it("QV3-6", "Der Digest deckt `redacted`, `unknown_keys`, `value`", "default", "Opus (PLAN record-v3)",
             "Nicht `unknown_fields`, `outcome`, `reason` (D6B-58 unverändert).", "", [],
             [("A", "drei Schlüssel", True), ("B", "auch outcome/reason/unknown_fields", False)]),
          it("QV3-8", "Ein rejected RESPONSE RECORD überspringt auch Pfad- und Versionszählung", "default", "Opus (PLAN-Repair record-v3); groß durch Fable",
             "Ein Ausfall ist keine TYPE-Änderung (DL-136 Because). Verwaist- und Held-Prüfungen lesen trotzdem jedes Record.", "", [],
             [("A", "nur die Wertprüfungen überspringen", False), ("B", "auch TYPE-Pfad und W2-Versionszählung", True)]),
          it("COUNT", "Die Zählzeilen-Regel: wann drucken?", "default", "Fable (zusammengelegt); Zeilen-Zeile Opus (RED db-stored)",
             "RESPONSE RECORDS drucken `N records, K checked, M rejected at capture` nur wenn M > 0. ROW SNAPSHOTS drucken `rows: N rows, K checked, M not decodable` immer. Zwei Regeln für dieselbe Frage: ist eine gedruckte Zahl der Beweis, dass die Prüfung lief, oder ist Stille der Normalfall?",
             "Bei A verliert der Test N20b seinen Beweis „3 checked“.", [],
             [("A", "Stille ist normal (beide nur bei M > 0)", False), ("B", "gedruckte Zahl beweist die Prüfung (beide immer)", False), ("—", "gebaut: geteilt, A für Records, B für Zeilen", True)]),
          it("D035", "Digest-Hälfte von DL-136 (P2b)", "open", "Fable (Ruling O3 unter DL-144)",
             "Ein falscher `value_sha256` wird gezählt, nicht geprüft. P2 druckt `digest not verified (P2b)`. Bauen oder offen lassen?", "", [],
             [("A", "in Schritt P2b bauen", False), ("B", "offen lassen", False)]),
          it("PDB-18", "`unknown_fields` einer Liste heißen `items.<i>.<feld>`", "default", "Fable (Flag)",
             "", "", [], [("A", "wie gebaut", True)]),
      ])

# ---------------------------------------------------------------- 8
group("08-entry", "ENTRY LINE und Seiten",
      "Was die ENTRY LINE aufzeichnet und wie die drei Seiten der Demo-App sie rufen.",
      [
          it("ENTRY", "Die ENTRY LINE", "decided", "13ue (DL-130, DL-131)",
             "Auswärts-Form, ein erzeugtes `ui_<event>/1` pro Zeile, Drift zwischen Kopf und Funktion ist ein Compile-Fehler.",
             "", [beaml('''
effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
'''), ex('''
def handle_event("place", params, socket) do
  case Orders.ui_place(params) do
    {:ok, _order} -> {:noreply, push_navigate(socket, to: ~p"/orders")}
    {:error, failure} -> ...
  end
end
''')], [], dl="DL-130"),
          it("G6D-04", "Ein reines ENTRY-Ziel schreibt kein ENTRY RECORD", "default", "Opus (GREEN slice6d); Repair durch Fable (TEST O2)",
             "Zielt die ENTRY LINE auf eine Funktion ohne auswärtigen EFFECT, in einer Datei, die sonst EFFECTS hat, gibt es kein ENTRY RECORD und kein `Replay.entry`. Diese UI-Events erreichen keinen `--stored`-Check und keinen REPLAY RUN. Die Begründung (kein `Replay`-Modul) gilt dort nicht.",
             "", [], [("A", "wie gebaut", True), ("B", "ENTRY RECORD auch dort schreiben", False)]),
          it("G6D-03", "ENTRY RECORD `type` in Quellreihenfolge", "default", "Opus (GREEN slice6d)",
             "Ein RESPONSE RECORD sortiert die Felder, ein ENTRY RECORD nicht. Der Fingerprint sortiert in beiden.", "", [],
             [("A", "Quellreihenfolge", True), ("B", "sortiert wie RESPONSE RECORD", False)]),
          it("G6D-12", "Literal-Enum im Eingabe-TYPE braucht eine Keep-Value-Variante", "default", "Opus (GREEN slice6d)",
             "Wie `Unknown(String)` bei `Channel`. Kein Test pinnt das.", "", [beaml('''
enum Channel { Web = "web"  App = "app"  Unknown(String) }
''')], [("A", "wie gebaut", True)]),
          it("Q5-9", "Die Listenseite lädt über eine zweite ENTRY LINE aus `mount`", "default", "Opus (PLAN exp0005)",
             "Kein neuer Transport `ui.mount`. `mount/3` ruft `Orders.ui_orders(%{})`.", "", [beaml('''
effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") |> list_orders
''')], [("A", "zweite ENTRY LINE aus `mount`", True), ("B", "neuer Transport `ui.mount`", False)]),
          it("NOTES", "Eine Seite /notes mit Formular und Liste", "default", "Opus (GREEN exp0005)",
             "Anders als /orders/new und /orders. Nach dem Absenden `push_navigate` auf dieselbe Seite.", "", [],
             [("A", "eine Seite", True), ("B", "`/notes/new` und `/notes`", False)]),
      ])

# ---------------------------------------------------------------- 9
group("09-syntax", "Syntax-Regeln",
      "Regeln, die in der Sprache sichtbar sind. Sie sind am teuersten zu ändern.",
      [
          it("COMMENT", "Kommentare nur mit `//`", "decided", "13ue (DL-132)", "", "", [beaml('''// so, und nur so''')], [], dl="DL-132"),
          it("Q5-3", "Listen als Feldform `[Order]`", "default", "Opus (PLAN exp0005)",
             "Kein eigenes `list`-Schlüsselwort. Die Grammatik kennt `[T]`.", "", [beaml('''
type OrderList { items: [Order] }
''')], [("A", "`items: [Order]`", True), ("B", "ein `list`-Schlüsselwort", False)]),
          it("CTOR-ROW", "Konstruktor-Feld in einer Zeile: erste Signatur nimmt genau die String-Felder", "default", "Opus (GREEN db-transport)",
             "Der Encoder schreibt die Struct-Felder, der Decoder liest die erste passende Signatur. Jede andere erste Signatur wäre nicht rücklesbar: Build-Fehler.", "", [beaml('''
type Amount { value: String currency: String }
fn Amount value: String, currency: String -> Amount ! BadAmount
// Die erste Signatur muss genau value und currency nehmen.
''')], [("A", "diese Regel", True), ("B", "nach Signaturnamen kodieren", False), ("C", "erlauben und Zeilen verlieren", False)]),
          it("ROW-FIELDS", "Zeilen-Felder: String, Literal-Enum mit Keep-Variante, Konstruktor-Records", "default", "Opus (GREEN db-transport)",
             "Int und verschachtelte Records sind in einer Zeile ein Build-Fehler („slice 1 decodes String fields only“).", "", [],
             [("A", "wie gebaut", True)]),
          it("Q6E-4", "Ein EFFECT pro Flow", "default", "Opus (PLAN multi-effect)",
             "`place` kann nicht zahlen und speichern in einem Flow.", "", [],
             [("A", "einer", True), ("B", "mehrere, Records nach operation gewählt", False)]),
          it("Q6E-3", "`Replay.run(operation, …)` bei mehreren EFFECTS", "default", "Opus (PLAN multi-effect)",
             "Der Replay wählt den EFFECT über das erste Argument.", "", [], [("A", "wie gebaut", True)]),
          it("D025", "Alternative Form mit `=` und `|` für enum und type", "open", "13ue (notiert)",
             "Du wolltest später prüfen, ob `enum X = A | B` und `type X = { … }` auch erlaubt sein sollen. Nur notiert, nicht geplant.", "", [], []),
          it("TEXTS", "Zwei Fehlertexte sind als Default gepinnt", "default", "Opus (RED db-transport)",
             "`order_v2` nennt `orders.save` und `Order.amount` (D6B-39). N25b nennt `TYPE Order v1` und das Feld `channel` (DL-122).", "", [], [("A", "wie gebaut", True)]),
      ])

# ---------------------------------------------------------------- 10
group("10-misc", "Kleines",
      "Defaults ohne Sprach- oder Formatwirkung.",
      [
          it("Q5-5", "Erzeugter Code liegt in git", "default", "Opus (PLAN exp0005)",
             "`app/lib/generated/orders.ex` ist eingecheckt, kein Mix-Compiler nach `_build`.", "", [],
             [("A", "in git", True), ("B", "Mix-Compiler", False)]),
          it("TEST-O1", "`run.py run` setzt `proto_dev` zurück", "default", "Opus (TEST exp0005)",
             "Der Lauf leert die Datenbank und prüft `orders.ex` gegen 0 Zeilen. Das README sagt es. Siehe A3.", "", [],
             [("A", "Reset behalten", True), ("B", "eigener Build-Schritt mit Dev-Zeilen", False)]),
          it("DL-147", "Eine RED-Datei kommt erst mit ihrem GREEN in `run.py`", "decided", "Fable",
             "Sonst fällt der Gesamtlauf, solange RED offen ist.", "", [], [], dl="DL-147"),
      ])

# ---------------------------------------------------------------- 11
group("11-parked", "Geparkt (D036)",
      "Von dir am 2026-11-07 geparkt. Hier nur, damit die Liste vollständig ist; M4 steht auf seiner eigenen Seite.",
      [
          it("M3", "Fate-Formen und DL-116", "parked", "OWNER", "Braucht zuerst eine frische Erklärung. Ohne M3 kein Ausweg aus einem Block außer SQL.", "", [], []),
          it("M5", "Was `retire` bedeutet, auch für Zeilen", "parked", "OWNER", "N28b pinnt den heutigen Stand; die Orphan-Hilfe druckt `retire <op> keep <n> days`.", "", [], []),
          it("M8", "Failure-Struct am Host", "parked", "OWNER", "P2 hat es vermieden (P5-18).", "", [], []),
          it("M9", "Record-Zeilen in einem Blocktext", "parked", "OWNER", "P2 hat es vermieden.", "", [], []),
      ])

# ---------------------------------------------------------------- 12
group("12-decided", "Schon entschieden",
      "Zum Nachschlagen. Alles von dir (13ue), außer wo markiert.",
      [
          it("DL-126", "Deklarativ für Form und Policy", "decided", "13ue", "", dl="DL-126"),
          it("DL-127..129", "Eine JSONB-Tabelle, UI-Eingang als EFFECT, drei db-Transporte", "decided", "13ue", "", dl="DL-127"),
          it("DL-130..134", "ENTRY LINE, `ui_<event>/1`, `//`, `Rejected`, `--stored` über entries", "decided", "13ue", "", dl="DL-130"),
          it("DL-135..136", "DRIFT pinnt Klassen; `--stored` prüft nur replayable Records", "decided", "13ue", "", dl="DL-135"),
          it("DL-137", "Ein `migrate`-Block für Records und Zeilen", "decided", "13ue", "", dl="DL-137"),
          it("DL-139", "Slice baut Defaults, außer Syntax, Record-Format, Host-Namen; explizit präsentieren bis abgenommen", "decided", "13ue", "", dl="DL-139"),
          it("DL-140", "Literal-Tausch bekannt→bekannt blockt; `map` MIGRATE STEP erzwungen (nicht gebaut)", "decided", "13ue", "", dl="DL-140"),
          it("DL-141..143", "ENTRY RECORD outcome/reason, beide unknown-Listen, ein Record-Format", "decided", "13ue", "", dl="DL-141"),
          it("DL-144", "Freier Lauf für 0005, Walk-through am Tag danach", "decided", "13ue", "", dl="DL-144"),
          it("DL-138", "ENTRY RECORD trägt outcome/reason", "decided", "Fable (Repair)", "", dl="DL-138"),
          it("DL-147", "RED-Datei erst mit GREEN in run.py", "decided", "Fable", "", dl="DL-147"),
          it("QDB-6", "zurückgezogen: `accepted`/`rejected` und die P2-Gründe gelten", "decided", "Fable (Repair)", "", dl=""),
      ])

# ---------------------------------------------------------------- render
JS = r'''
<script>
(() => {
const $ = (s, r=document) => r.querySelector(s), $$ = (s, r=document) => [...r.querySelectorAll(s)];
const post = (u, b) => fetch(u, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(b)}).then(r => r.json());
const act = (action, target, result, source='mouse') => post('/api/act', {source, action, target, result}).catch(()=>{});
const fmtT = ts => { try { return new Date(ts).toLocaleTimeString('de-DE', {hour:'2-digit', minute:'2-digit'}); } catch { return ts; } };
function paint(id, a) {
  const sec = document.getElementById(id); if (!sec) return;
  $$('ol.opts li', sec).forEach(li => li.classList.toggle('chosen', !!a && li.dataset.choice === a.choice));
  const box = $('.ans', sec); box.innerHTML = '';
  if (a && a.choice) box.insertAdjacentHTML('beforeend', `<div class=a><time>${fmtT(a.ts)}</time>Deine Wahl: <b>${a.choice}</b></div>`);
  if (a && a.note) box.insertAdjacentHTML('beforeend', `<div class=a><time>${fmtT(a.ts)}</time>${a.note.replace(/</g,'&lt;')}</div>`);
}
async function load() { try { const all = await (await fetch('/api/answers')).json(); $$('section.card').forEach(s => paint(s.id, all[s.id])); } catch {} }
$$('section.card').forEach(sec => {
  const id = sec.id;
  $$('ol.opts li', sec).forEach(li => { const pick = async () => { await post('/api/answer', {id, choice: li.dataset.choice}); act('choose', id, li.dataset.choice); load(); };
    li.addEventListener('click', pick); li.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(); } }); });
  const ta = $('.fbt', sec), st = $('.fbs', sec), mic = $('.mic', sec);
  const save = async () => { const note = ta.value.trim(); if (!note) return; await post('/api/answer', {id, note}); act('note', id, note.length + ' chars', 'key'); ta.value = ''; st.textContent = 'gespeichert'; load(); };
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); save(); } });
  // push-to-talk: hold the button or the key M while the pointer is over the card
  let rec = null, stream = null, chunks = [], t0 = 0;
  async function down() {
    if (rec) return; st.textContent = 'Mikro…'; fetch('/api/stt/warm', {method:'POST'}).catch(()=>{});
    try { stream = await navigator.mediaDevices.getUserMedia({audio: true}); } catch (e) { st.textContent = 'kein Mikrofon: ' + e.message; return; }
    const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'].find(t => MediaRecorder.isTypeSupported(t)) || '';
    rec = new MediaRecorder(stream, mime ? {mimeType: mime} : {}); chunks = []; t0 = performance.now();
    rec.ondataavailable = e => e.data.size && chunks.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach(t => t.stop()); const blob = new Blob(chunks, {type: rec.mimeType || mime || 'audio/webm'}); rec = null;
      mic.classList.remove('on'); mic.classList.add('busy'); st.textContent = 'schreibe ab…';
      try { const r = await fetch('/api/stt?id=' + encodeURIComponent(id), {method:'POST', headers:{'Content-Type': blob.type}, body: blob}); const j = await r.json();
        st.textContent = r.ok ? (j.text ? 'notiert' : 'nichts gehört') : ('Fehler: ' + (j.error || r.status)); if (!r.ok) ta.focus(); }
      catch (e) { st.textContent = 'Fehler: ' + e.message; }
      mic.classList.remove('busy'); act('voice', id, Math.round((performance.now() - t0) / 100) / 10 + ' s', 'voice'); load();
    };
    rec.start(); mic.classList.add('on'); st.textContent = 'aufnahme… loslassen zum Senden';
  }
  function up() { if (rec && rec.state === 'recording') rec.stop(); }
  mic.addEventListener('pointerdown', e => { e.preventDefault(); mic.setPointerCapture?.(e.pointerId); down(); });
  mic.addEventListener('pointerup', up); mic.addEventListener('pointercancel', up);
  sec.addEventListener('pointerenter', () => window.__hot = sec); 
  document.addEventListener('keydown', e => { if (e.key.toLowerCase() === 'm' && !e.repeat && window.__hot === sec && !e.target.matches('input, textarea')) down(); });
  document.addEventListener('keyup', e => { if (e.key.toLowerCase() === 'm' && window.__hot === sec) up(); });
});
load();
$$('a[href]').forEach(a => a.addEventListener('click', () => act('nav', a.getAttribute('href'))));
})();
</script>'''

CSS = """
:root{color-scheme:light dark;--bg:#fafafa;--fg:#383a42;--mut:#8a8f98;--bd:#d9dce2;--card:#fff;
--k:#a626a4;--t:#c18401;--f:#4078f2;--p:#e45649;--s:#50a14f;--c:#0184bc;--o:#383a42;--m:#9a9fa8;
--ok:#2e8b57;--open:#c0392b;--def:#b7791f;--park:#6c757d}
@media (prefers-color-scheme:dark){:root{--bg:#1e2127;--fg:#abb2bf;--mut:#7f848e;--bd:#3a3f4b;--card:#262a31;
--k:#c678dd;--t:#e5c07b;--f:#61afef;--p:#e06c75;--s:#98c379;--c:#56b6c2;--o:#abb2bf;--m:#7f848e;
--ok:#98c379;--open:#e06c75;--def:#e5c07b;--park:#7f848e}}
*{box-sizing:border-box}body{margin:0;padding:20px 16px 60px;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,-apple-system,sans-serif;max-width:860px;margin-inline:auto}
a{color:var(--f);text-decoration:none}a:hover{text-decoration:underline}
h1{font-size:24px;margin:8px 0 6px}h2{font-size:17px;margin:28px 0 8px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.lead{color:var(--mut);margin:0 0 18px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:10px 12px;border:1px solid var(--bd);border-radius:8px;margin:10px 0;background:var(--card);font:13px/1.55 ui-monospace,Menlo,monospace}
code{font:0.92em ui-monospace,Menlo,monospace;background:var(--card);border:1px solid var(--bd);border-radius:4px;padding:0 4px}
i{font-style:normal}.k{color:var(--k)}.t{color:var(--t)}.f{color:var(--f)}.p{color:var(--p)}.s{color:var(--s)}.c{color:var(--c)}.o,.b{color:var(--o)}.m{color:var(--m);font-style:italic}
.card{border:1px solid var(--bd);border-radius:10px;padding:14px 16px;margin:14px 0;background:var(--card)}
.badge{font:600 11px/1 system-ui;letter-spacing:.3px;text-transform:uppercase;padding:4px 7px;border-radius:999px;border:1px solid currentColor}
.decided{color:var(--ok)}.open{color:var(--open)}.default{color:var(--def)}.parked{color:var(--park)}
.id{font:600 12px ui-monospace,Menlo,monospace;color:var(--mut)}
.why{border-left:3px solid var(--def);padding:2px 10px;color:var(--fg);margin:8px 0}
ol.opts{padding-left:0;list-style:none;margin:10px 0 4px}ol.opts li{padding:6px 10px;border:1px solid var(--bd);border-radius:8px;margin:5px 0;display:flex;gap:10px}
ol.opts li.built{border-color:var(--def)}ol.opts .L{font-weight:700;min-width:1.4em}ol.opts .tag{margin-left:auto;color:var(--def);font-size:12px;white-space:nowrap}
.by{color:var(--mut);font-size:13px;margin-top:8px}.note{color:var(--mut);font-size:13px}
nav{display:flex;justify-content:space-between;gap:12px;margin:24px 0 0;padding-top:14px;border-top:1px solid var(--bd);font-size:14px}
table{border-collapse:collapse;width:100%;margin:14px 0}td,th{border-bottom:1px solid var(--bd);padding:8px 6px;text-align:left;vertical-align:top}th{color:var(--mut);font-weight:600;font-size:13px}
td.n{text-align:right;white-space:nowrap}
ol.opts li{cursor:pointer}ol.opts li:hover{background:var(--bg)}ol.opts li.chosen{outline:2px solid var(--ok);outline-offset:-1px}
.fb{display:flex;gap:8px;align-items:flex-start;margin-top:10px}.mic{font:600 13px system-ui;padding:8px 12px;border-radius:999px;border:1px solid var(--bd);background:var(--card);color:var(--fg);cursor:pointer;white-space:nowrap;user-select:none;-webkit-user-select:none}
.mic.on{background:var(--open);color:#fff;border-color:var(--open)}.mic.busy{opacity:.6}
.fbt{flex:1;font:14px/1.4 system-ui;padding:8px 10px;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--fg);resize:vertical;min-height:36px}
.fbs{font-size:12px;color:var(--mut);align-self:center;white-space:nowrap}
.ans{font-size:13px;margin-top:8px}.ans .a{border-left:3px solid var(--ok);padding:2px 10px;margin:4px 0}.ans .a time{color:var(--mut);margin-right:6px}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--mut);margin:12px 0}
"""
LABEL = dict(decided="entschieden", open="offen", default="Default, gebaut", parked="geparkt")


def page(title, body, prev=None, nxt=None):
    nav = '<nav><span>' + (f'<a href="{prev[0]}.html">← {html.escape(prev[1])}</a>' if prev else "") + \
          '</span><a href="index.html">Übersicht</a><span>' + (f'<a href="{nxt[0]}.html">{html.escape(nxt[1])} →</a>' if nxt else "") + '</span></nav>' + JS
    return f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}</title><style>{CSS}</style></head><body>{body}{nav}</body></html>'


def render_item(x):
    st = x["status"]
    h = [f'<section class="card" id="{html.escape(x["id"])}"><h2><span class="id">{html.escape(x["id"])}</span> {text(x["title"])} <span class="badge {st}">{LABEL[st]}{(" · " + x["dl"]) if x["dl"] else ""}</span></h2>']
    if x["what"]:
        h.append(f'<p>{text(x["what"])}</p>')
    if x["why"]:
        h.append(f'<p class="why">{text(x["why"])}</p>')
    h += x["code"]
    if x["options"]:
        h.append('<ol class="opts">')
        for L, t, built in x["options"]:
            h.append(f'<li class="{"built" if built else ""}" data-choice="{html.escape(L)}" role="button" tabindex="0"><span class="L">{html.escape(L)}</span><span>{text(t)}</span>{"<span class=tag>gebaut</span>" if built else ""}</li>')
        h.append('</ol>')
    if x["note"]:
        h.append(f'<p class="note">{text(x["note"])}</p>')
    h.append(f'<p class="by">By: {text(x["by"])}</p>')
    h.append('<div class="fb"><button class="mic" type="button" title="Halten und sprechen (oder Taste M)">🎤 Sprechen</button>'
             '<textarea class="fbt" rows="1" placeholder="Anmerkung (Enter speichert)"></textarea><span class="fbs"></span></div>'
             '<div class="ans"></div></section>')
    return "".join(h)


def main():
    for i, g in enumerate(G):
        prev = (G[i - 1]["slug"], G[i - 1]["title"]) if i else None
        nxt = (G[i + 1]["slug"], G[i + 1]["title"]) if i + 1 < len(G) else None
        body = f'<p class="id"><a href="index.html">Übersicht</a> · Seite {i + 1} von {len(G)}</p><h1>{text(g["title"])}</h1><p class="lead">{text(g["lead"])}</p>' + "".join(render_item(x) for x in g["items"])
        with open(os.path.join(HERE, g["slug"] + ".html"), "w") as f:
            f.write(page(g["title"], body, prev, nxt))
    rows = []
    tot = dict(decided=0, open=0, default=0, parked=0)
    for i, g in enumerate(G):
        c = dict(decided=0, open=0, default=0, parked=0)
        for x in g["items"]:
            c[x["status"]] += 1
            tot[x["status"]] += 1
        cells = "".join(f'<td class="n {k}">{c[k] or ""}</td>' for k in ("open", "default", "parked", "decided"))
        rows.append(f'<tr><td>{i + 1}</td><td><a href="{g["slug"]}.html">{text(g["title"])}</a><br><span class="note">{text(g["lead"])}</span></td>{cells}</tr>')
    body = f'''<h1>Walk-through: gebaute Defaults und offene Fragen</h1>
<p class="lead">Stand 2026-11-08 nach dem Nachtlauf (DL-144). Groß zuerst. Jede Seite ist eine Gruppe; jeder Kasten eine Frage. Quelle: <code>owner-review.md</code>, Register D037.</p>
<div class="legend"><span class="badge open">offen</span> braucht deine Antwort, nichts gebaut oder Einwand <span class="badge default">Default, gebaut</span> gebaut, gilt erst nach deiner Abnahme (DL-139) <span class="badge parked">geparkt</span> D036 <span class="badge decided">entschieden</span> DL-Eintrag vorhanden</div>
<table><thead><tr><th>#</th><th>Gruppe</th><th class="open">offen</th><th class="default">Default</th><th class="parked">geparkt</th><th class="decided">entschieden</th></tr></thead><tbody>{"".join(rows)}</tbody>
<tfoot><tr><th></th><th>Summe</th>{"".join(f'<td class="n {k}">{tot[k]}</td>' for k in ("open", "default", "parked", "decided"))}</tr></tfoot></table>
<p class="note">Reihenfolge für das Gespräch: 1 → 2 → 3 → 4, dann 5 bis 10 als Sammelfragen, 11 nur zur Kenntnis.</p>'''
    with open(os.path.join(HERE, "index.html"), "w") as f:
        f.write(page("Walk-through D037", body, None, (G[0]["slug"], G[0]["title"])))
    print(f"{len(G)} pages, {sum(tot.values())} items", tot)


if __name__ == "__main__":
    main()
