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
    out = []
    for line in html.escape(code.strip("\n")).split("\n"):
        s, hash_, comment = line.partition("#")  # ponytail: a "#" inside a string would start a comment; none in the snippets
        s = re.sub(r"(&quot;[^&]*?&quot;)", r"<i class=s>\1</i>", s)
        s = re.sub(r"(?<![\w:])(:[a-z_]+)", r"<i class=c>\1</i>", s)
        s = re.sub(r"\b(def|defmodule|do|end|case|fn|when)\b", r"<i class=k>\1</i>", s)
        s = re.sub(r"\b([A-Z][A-Za-z]+(?:\.[A-Z][A-Za-z]+)*)\b", r"<i class=t>\1</i>", s)
        out.append(s + (f"<i class=m>#{comment}</i>" if hash_ else ""))
    return "<pre>" + "\n".join(out) + "</pre>"


def text(s):
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


# status: decided | default | open | parked
# An item: dict(id, title, status, by, what, why, code=[html], options=[(letter, text, built?)], ref)
G = []


def group(slug, title, lead, items):
    G.append(dict(slug=slug, title=title, lead=lead, items=items))


S = "\u2800\u2800↳ "  # prefix of a real sub-point in a `what` list


def it(id, title, status, by, what, why="", code=(), options=(), note="", dl=""):
    """`what`: a list of short bullets (rendered as → lines), or one plain string."""
    return dict(id=id, title=title, status=status, by=by, what=what, why=why, code=list(code), options=list(options), note=note, dl=dl)


# ---------------------------------------------------------------- 1
group("01-review", "Schlussreview Slice 6: drei hohe Einwände",
      "Am Ende von Slice 6 hat der Devil's Advocate (ein Gegen-Prüfer) drei Einwände gefunden. Alle drei sind hoch eingestuft. Zwei hast du entschieden, einer ist offen.",
      [
          it("A1", "Der PASS beweist weniger als die These", "decided", "Opus (Schlussreview); entschieden 13ue: B",
             ["These: BEAML trägt die ganze Kette.",
              "Kette = Formular → BEAML → Zeile in Postgres.",
              "Gebaut und grün: nur die Kette für `Note`.",
              "`Note` hat nur Text-Felder (String).",
              "`Order` mit `Amount` und `Channel` wartet auf M4.",
              "Vertauschte `Channel`-Werte bauen noch durch.",
              S + "DL-140 beschlossen, nicht gebaut",
              "Block = der Build bricht mit Fehler ab.",
              "Aus einem Block hilft nur SQL-Delete.",
              "Fate-Form = Zeile im `migrate`: was mit alten Daten passiert.",
              "Fate-Formen gibt es noch nicht.",
              "Umstellung v2 → v3 lief per Python-Skript."],
             "Sagt das README weiter „PASS“, liest man mehr hinein als gezeigt.",
             [beaml('''
// Läuft heute durch die ganze Kette:

type Note { text: String }

// Wartet auf M4 (Konstruktor- und Enum-Feld):

type Order {
  order_id: String
  amount: Amount
  channel: Channel
}
''')],
             [("A", "Wort „PASS“ so lassen", False),
              ("B", "Anspruch enger fassen: „nur String-Kette, Blocks bewiesen, noch keine Fate-Form“ in README, Register und Seiten", False)], dl="DL-149"),
          it("A2", "Eine nicht dekodierbare Zeile bricht die Listenseite", "decided", "Opus (Schlussreview); entschieden 13ue: A",
             ["STORED ROW = gespeicherte Zeile in der Tabelle `records`.",
              "Nicht dekodierbar = BEAML kann die Zeile nicht lesen.",
              S + "z. B. falscher Digest (Prüfsumme)",
              S + "z. B. SQL-`UPDATE` von Hand",
              "Der Build zählt so eine Zeile nur.",
              "Der Build bleibt grün.",
              "`db.list` = lädt alle Zeilen für eine Liste.",
              "Zur Laufzeit scheitert `db.list` dann ganz (QDB-4).",
              "Folge: Seite /orders leer oder rot."],
             "Genau diesen Fall soll BEAML verhindern.",
             [],
             [("A", "Build bricht ab bei einer nicht dekodierbaren Zeile", False),
              ("B", "`db.list` lässt die Zeile weg und meldet sie", False),
              ("C", "Ausfall hinnehmen (so gebaut)", True)],
             note="Hängt mit QDB-4 und P4c zusammen (Seite „Zeilen“).", dl="DL-150"),
          it("A3", "Der Compiler prüft nicht, woher der Zeilen-Snapshot kommt", "decided", "Opus (Schlussreview); entschieden 13ue: B",
             ["`--stored` = Build-Prüfung gegen gespeicherte Daten.",
              "ROW SNAPSHOT = Kopie der Zeilen als Datei `rows.jsonl`.",
              "Daneben liegt `snapshot-meta.json`.",
              "Fehlt diese Datei: trotzdem grün (exit 0).",
              "Gelesen wird nur `row_count` (Zahl der Zeilen).",
              "`run.py run` leert vorher die Datenbank.",
              S + "geprüft wird gegen 0 Zeilen"],
             "Ein Build gegen leere Daten sieht aus wie gegen echte.",
             [],
             [("A", "Compiler verlangt die Meta-Datei und prüft Datenbankname und Abfragezeit", False),
              ("B", "`--stored` fragt die Tabelle selbst ab (so steht es in DL-127)", False),
              ("C", "so lassen, nur die Prüfung im Host (N8c)", True)], dl="DL-151"),
      ])

# ---------------------------------------------------------------- 2
group("02-order-chain", "M4: die echte Order-Kette",
      "Hier bremst eine Regel alles: D6B-39. Sie verbietet bestimmte Felder in einem TYPE mit `migrate`. Darum läuft `Order` noch nicht über gespeicherte Zeilen.",
      [
          it("M4", "Darf eine verkettete Zeile Amount und Channel tragen?", "decided", "OWNER geparkt (D036); gebauter Stand Fable (Repair); entschieden 13ue: B voll",
             ["TYPE = Bauplan eines Werts, z. B. `Order`.",
              "TYPE VERSION = Stand eines TYPE beim Speichern (v1, v2 …).",
              "MIGRATE CHAIN = die `migrate`-Schritte eines TYPE.",
              S + "liest alte Zeilen in die neue Form",
              "Regel D6B-39: in so einer Kette kein Konstruktor-Feld, kein Enum-Feld.",
              "Konstruktor-Feld = Feld mit eigener Prüf-`fn`, z. B. `amount: Amount`.",
              "Enum-Feld = Feld mit festen Werten, z. B. `channel: Channel`.",
              "`Order` hat beide: also Build-Fehler.",
              "Gebaut: nichts geändert, D6B-39 gilt.",
              "Test N18 hält den heutigen Hilfetext fest.",
              "FATE OPERATION = Zeile im `migrate`: was mit alten Daten passiert."],
             "Ohne M4 keine `Order`-Kette; mit M3 und M5 auch keine Fate-Formen (N9).",
             [beaml('''
type Amount {
  value: String
  currency: String
}

enum Channel {
  Web = "web"
  App = "app"
  Unknown(String)
}

// Heute ein Build-Fehler, sobald migrate dranhängt:

type Order {
  order_id: String
  amount: Amount
  channel: Channel
  note: String
}

migrate Order v1 -> v2 { add note: String = "" }
''')],
             [("A", "D6B-39 bleibt. Der Hilfetext (DL-102) sagt: „stelle die vorige Klausel oder das Literal wieder her“", False),
              ("B", "D6B-39 aufheben, noch vor der ersten FATE OPERATION", False)], dl="DL-152"),
          it("QDB-8", "Der verkettete Lesepfad läuft solange auf Note", "decided", "Fable (Default, offen); entschieden 13ue: C",
             ["`Order` darf heute keine Kette haben (M4).",
              "Also prüfen die Tests N7/N7b die MIGRATE CHAIN an `Note`.",
              "`Note` hat nur String-Felder.",
              "Gebaut und grün (Variante `note_v2`).",
              "Alte v1-Zeilen werden beim Lesen zu v2.",
              "Keine Änderung an der Tabelle nötig (keine DDL)."],
             "",
             [beaml('''
type Note {
  text: String
  tag: String
}

migrate Note v1 -> v2 { add tag: String = "" }
''')],
             [("A", "Tests N7/N7b warten auf M4", False),
              ("B", "eigener String-TYPE `Note` mit eigener Kette", True),
              ("C", "M4 jetzt beantworten", False)], dl="DL-153"),
          it("N9", "Der strengere Amount braucht eine Fate-Form", "parked", "OWNER geparkt (über M3, M4, M5)",
             ["Variante `stricter`: `Amount` wird strenger.",
              "Neu: der Betrag `\"0\"` wird abgelehnt.",
              "Alte Zeilen mit `\"0\"` blocken dann den Build.",
              "Das ist so gewollt.",
              "Kleinster Ausweg: `quarantine amount`.",
              S + "alte Werte beiseite stellen, mit Grund",
              "Diese Form gibt es noch nicht."],
             "Heute hilft nur ein SQL-Delete.",
             [beaml('''
type BadAmount {}

type Amount {
  value: String
  currency: String
}

// Variante stricter: die Zeile mit "0" ist neu.

fn Amount value: String, currency: String -> Amount ! BadAmount
fn Amount "0",           _                -> Amount ! BadAmount = BadAmount {}
fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
''')],
             []),
      ])

# ---------------------------------------------------------------- 2b
group("02b-fates", "M3: Fate-Formen",
      "Gestern geparkt, weil die Erklärung unklar war. Mit DL-152 (D6B-39 ganz aufgehoben, jede Migration muss gehen) sind die Fate-Formen jetzt die nächste kritische Frage.",
      [
          it("FATE", "Was eine Fate-Form ist", "decided", "13ue",
             ["Gespeicherter Wert = eine Zeile oder ein RESPONSE RECORD.",
              S + "RESPONSE RECORD = gespeicherte Zeile eines ausgehenden EFFECT-Aufrufs",
              "Er wurde unter dem TYPE von gestern geschrieben.",
              "Der TYPE von heute liest ihn anders oder lehnt ihn ab.",
              "`--stored` merkt das und bricht den Build ab.",
              "Fate-Form = eine Zeile in `migrate T v1 -> v2 { … }`.",
              S + "sagt, was mit solchen Werten passiert",
              "`quarantine f`: Wert wird beiseite gestellt.",
              S + "aufgelistet, nie wieder abgespielt (kein REPLAY RUN)",
              "`retire f keep N days`: Wert fällt nach N Tagen raus.",
              "`map f \"old\" -> Variant`: verlorenes oder vertauschtes Literal bekommt ein Ziel (DL-140).",
              S + "Literal = fester Text-Wert eines Enum, z. B. `\"web\"`",
              "`redact f`: das Feld wird geleert.",
              "Deklarativ: jede Zeile sagt was, nie wie.",
              "Noch nicht in der Grammatik, noch nicht gebaut."],
             "",
             [beaml('''
// Form aus DL-125, noch nicht gebaut

// f = Feldname, hier amount und channel.

migrate Order v2 -> v3 {
  quarantine amount
  map channel "mobile" -> App
}
''')],
             [], note="Feldwert `\"mobile\"` ist erfunden, nur zur Anschauung.", dl="DL-125"),
          it("VERSION-RULE", "Versionsregel: Änderung plus betroffene Werte = neue Version", "decided", "13ue (2026-11-08, nach drei Beispielen)",
             ["Build prüft live: fällt ein gespeicherter Wert anders?",
              "Nein: Änderung frei, keine neue Version",
              "Ja: `type Amount v2` oder `enum Channel v2` plus `migrate v1 -> v2` mit Fate oder `map`",
              "v1 steht von Anfang an; alte Version lebt, bis Production leer ist, dann SQUASH",
              "Gilt für Konstruktor-TYPES und Enums",
              "Nummern in Records werden nie neu vergeben"],
             "", [], [], dl="DL-155"),
          it("BLOCKS", "Die drei Sperren, die heute nur SQL löst", "default", "Fable (Stand)",
             ["Sperre = `--stored` bricht den Build ab.",
              "DL-102: ein gespeicherter Wert fällt durch eine neue Regel.",
              S + "z. B. der strengere `Amount` in 0005 (N9)",
              "DL-122: ein gespeichertes Enum-Literal gibt es nicht mehr.",
              "DL-140: ein Literal wurde zwischen zwei Varianten getauscht.",
              S + "beschlossen, noch nicht gebaut",
              "Heute einziger Ausweg: Zeilen von Hand löschen (SQL)."],
             "Genau diese drei Sperren soll eine Fate-Zeile lösen.",
             [beaml('''
// Variante stricter, echte Klauseln.

// Eine gespeicherte Zeile mit Betrag "0" blockt den Build.

fn Amount value: String, currency: String -> Amount ! BadAmount
fn Amount "0",           _                -> Amount ! BadAmount = BadAmount {}
fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
''')],
             []),
          it("M3", "M3: Darf `redact` eine Regel überspringen?", "parked", "OWNER geparkt (D036); Einwand D3 von Opus (RED TEAM)",
             ["REDACTED FIELD = Feld, dessen Wert nicht gespeichert wird.",
              "DL-116: so ein Feld darf nur ein einfaches String- oder Int-Feld sein.",
              S + "ohne Konstruktor (eigene Prüf-`fn`)",
              "Grund: eine Regel kann nicht über einen Wert laufen, der fehlt.",
              "Du hast abgelehnt: „Replay überspringt die Regel still“ (DL-116, Option B).",
              "DL-125 zählt DL-116 aber zu den Sperren, die eine Fate-Zeile löst.",
              "Einwand D3: dann baut `redact` genau dieses stille Überspringen."],
             "Ein Agent, der DL-125 wörtlich baut, baut, was du abgelehnt hast.",
             [beaml('''
// Form aus DL-125, noch nicht gebaut

// Amount hat einen Konstruktor. Was tut seine Regel ohne Wert?

migrate Order v3 -> v4 { redact amount }
''')],
             [("A", "DL-116 verlässt die Liste; neue Frage: wie läuft eine Regel über einen fehlenden Wert", False),
              ("B", "`redact` überspringt die Regel, DL-116 B kommt zurück", False)]),
          it("FATE-NEXT", "Reihenfolge: wann bauen wir die Fate-Formen?", "open", "Fable (Vorschlag)",
             ["Mit DL-152 brauchen Schritte auf Enum- und Konstruktor-Feldern diese Formen.",
              "Vorschlag: nach M4 Schritt 1 (erst migrieren, dann prüfen) kommt der Fate-Slice.",
              S + "Grammatik für die vier Zeilen",
              S + "`--stored` löst DL-102/DL-122/DL-140, wenn eine Fate-Zeile das Feld nennt",
              S + "REPLAY RUN überspringt Werte in `quarantine`",
              S + "Use Case: 0005 N9 mit `quarantine amount`",
              "Alternative: erst `--stored` live aus der Datenbank (DL-151)."],
             "",
             [],
             [("A", "Fate-Slice direkt nach M4 Schritt 1", False),
              ("B", "erst live `--stored` (DL-151), dann Fate-Slice", False)]),
      ])

# ---------------------------------------------------------------- 3
group("03-encoder", "Wie eine Seite einen BEAML-Wert anzeigt",
      "Die Seite /orders zeigt gespeicherte Bestellungen. Die Vorlage (HEEx) braucht dafür einfache Werte. Frage: welche Funktion ruft der Host dafür?",
      [
          it("ENC", "Der Host ruft `Orders.__beaml_encode_order/1`", "decided", "Opus (GREEN exp0005); C konkretisiert von Opus (TEST); entschieden 13ue: C",
             ["Host = die Phoenix-App um den erzeugten Code.",
              "Encoder = macht aus `Order` eine einfache Map.",
              "Heute ruft /orders `Orders.__beaml_encode_order/1`.",
              "Zwei Unterstriche = intern im Compiler.",
              "Vorteil: keine Compiler-Änderung.",
              "Vorteil: das Literal `\"web\"` bleibt in BEAML.",
              "Nachteil: diesen Namen haben wir nie versprochen."],
             "Benennt der Compiler ihn um, bricht die App still.",
             [ex('''
# order_list_live.ex, in mount/3

{:ok, assign(socket, items: Enum.map(items, &Orders.__beaml_encode_order/1))}
'''), beaml('''
// Option C: der Compiler erzeugt pro TYPE eine öffentliche Funktion.

// Name noch offen, z. B. project_order/1. Kein neues Schlüsselwort.

type Order {
  order_id: String
  amount: Amount
  channel: Channel
}
''')],
             [("A", "Host ruft den erzeugten internen Encoder", True),
              ("B", "Host zerlegt den Enum-Wert selbst", False),
              ("C", "Compiler erzeugt eine öffentliche `project_<type>/1`", False)], dl="DL-154"),
      ])

# ---------------------------------------------------------------- 4
group("04-rows", "Zeilen: Inhalt und Form-Prüfung",
      "Eine Zeile ist ein gespeicherter Wert in Postgres. Hier: was in ihr steht. Und was der Build an ihr prüft.",
      [
          it("Q5-10", "Was steht im `value` einer Zeile?", "default", "Fable (Default, offen)",
             ["STORED ROW = eine Zeile der Tabelle `records`.",
              "`db.put` schreibt sie.",
              "Frage: was steht in der Spalte `value`?",
              "RECORD CORE = die 14 festen Schlüssel jedes Records.",
              S + "z. B. `version`, `type`, `value`",
              "Gebaut: der ganze RECORD CORE, Version 3.",
              "RESPONSE RECORD = aufgezeichnete Antwort eines Aufrufs.",
              "So ist eine Zeile wie ein RESPONSE RECORD.",
              "`--stored` liest beide mit einem Leser (DL-127, DL-143)."],
             "",
             [],
             [("A", "nur der Wert selbst (nackte Projektion)", False), ("B", "RECORD CORE v3 in der Zeile", True)]),
          it("P4c", "Fehlendes oder falsch getyptes String-Feld in einer Zeile", "default", "Fable (Default, offen)",
             ["Fall: einer Zeile fehlt ein String-Feld.",
              S + "oder der Wert ist kein String",
              "Vorher: Build grün, `db.list` scheitert später.",
              "Block = der Build bricht mit Fehler ab.",
              "Jetzt: der Build blockt mit dem DL-102-Text.",
              "TYPE VERSION = Stand des TYPE beim Speichern.",
              "Geprüft wird gegen die TYPE VERSION der Zeile."],
             "",
             [],
             [("A", "Build blockt mit DL-102-Text", True),
              ("B", "als nicht dekodierbar zählen (BEAML kann sie nicht lesen)", False)]),
          it("P4c-http", "Dieselbe Lücke bei http RESPONSE RECORDS", "default", "Opus (GREEN P4c); auf Migrate gehoben vom TEST-Review",
             ["Gleiche Lücke bei http RESPONSE RECORDS.",
              "Dort fehlt die Prüfung noch.",
              "Ein Record ohne String-Feld geht durch.",
              "Test N32e hält diesen Stand fest."],
             "",
             [],
             [("A", "Lücke so lassen", True), ("B", "http mitprüfen, nach dem Versions-Fix", False)]),
          it("P4c-text", "Ein Fehlertext für beide Fälle", "default", "Opus (RED P4c)",
             ["Zwei Fehler, ein Text:",
              S + "Schlüssel fehlt",
              S + "Wert ist kein String",
              "Text: `TYPE <T>: 1 stored ROW of table <t> has no String value for field <f>`",
              "Dazu: Quelle und DL-102-Hilfezeile."],
             "", [], [("A", "ein Text", True), ("B", "zwei Texte", False)]),
          it("QDB-4", "Eine schlechte Zeile lässt den ganzen `db.list` fallen", "default", "Opus (PLAN db-transport)",
             ["`db.list` = lädt viele Zeilen auf einmal.",
              "Ist eine davon nicht lesbar: Fehler für alle.",
              "Rückgabe dann `{:error, decode}`.",
              "Das ist die Laufzeit-Hälfte von A2."],
             "", [], [("A", "so gebaut", True)]),
          it("QDB-3", "Neueste Zeile gewinnt bei `db.get`", "default", "Opus (PLAN db-transport)",
             ["`db.get` = lädt eine Zeile über einen Schlüssel.",
              "Mehrere Zeilen mit gleichem Schlüssel?",
              "Die zuletzt geschriebene gewinnt."],
             "", [], [("A", "so gebaut", True)]),
      ])

# ---------------------------------------------------------------- 5
group("05-names", "Namen: Modul, Rejected, reservierte Namen",
      "Der Compiler erzeugt Elixir-Module. Hier: wie sie heißen. Und welche Namen gesperrt sind.",
      [
          it("Q6E-1", "Welche Quellen heißen nach dem Dateinamen?", "default", "Opus (PLAN multi-effect)",
             ["ENTRY LINE = Zeile, über die eine Seite BEAML ruft.",
              "`orders.beaml` wird zu `defmodule Orders`.",
              "Aber nur, wenn die Datei eine ENTRY LINE hat.",
              "Andere Quellen heißen weiter `BeamlSpike`.",
              "Byte-Pin = Test, der erzeugte Bytes festhält.",
              "Grund: sonst ändern sich alle sechs Byte-Pins."],
             "Zwei Regeln für einen Namen sind schwer zu erklären.",
             [beaml('''
// orders.beaml wird defmodule Orders, denn hier steht eine ENTRY LINE:

effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
''')],
             [("A", "jede Quelle (alle Byte-Pins ändern sich)", False), ("C", "nur eine Quelle mit ENTRY LINE", True)]),
          it("Q6E-2", "Wo wohnt das `Rejected`-Struct?", "default", "Opus (PLAN multi-effect)",
             ["`Rejected` = Fehlerwert bei abgelehnter Eingabe.",
              "Gebaut: `Orders.Rejected{reason: \"decode\"}`.",
              "DL-133 nannte die Form `BeamlSpike.Rejected`.",
              "Die Docs merken den Unterschied an."],
             "", [ex('''
# Rückgabe, wenn BEAML die Eingabe nicht lesen kann:

{:error, %Orders.Rejected{reason: "decode"}}
''')],
             [("A", "`<Modul>.Rejected`, also `Orders.Rejected`", True), ("B", "immer `BeamlSpike.Rejected`", False)]),
          it("Q5-6", "Modulname aus dem Dateinamen, keine `module`-Zeile", "default", "Opus (PLAN exp0005)",
             ["Der Modulname kommt aus dem Dateinamen.",
              "`orders.beaml` → `Orders`.",
              "Kein neues Schlüsselwort `module`."], "", [],
             [("A", "aus dem Dateinamen", True), ("B", "eigene `module`-Zeile", False)]),
          it("RESV", "`BeamlDb` und `System` sind als Modulname gesperrt", "default", "Opus (GREEN db-transport)",
             ["Datei `beaml_db.beaml` gäbe Modul `BeamlDb`.",
              "Den Namen ruft der erzeugte Code selbst.",
              "Darum: Build-Fehler.",
              "Gleiche Regel wie D6B-203.",
              "`System` ist auch gesperrt."], "", [],
             [("A", "so gebaut", True)]),
      ])

# ---------------------------------------------------------------- 6
group("06-db", "Datenbank-Transporte",
      "BEAML spricht über drei Aufrufe mit der Datenbank: `db.put`, `db.get`, `db.list`. Hier: wie der Host sie liefert. Was dabei aufgezeichnet wird. Und wie `--stored` an die Zeilen kommt.",
      [
          it("QDB-2", "Die Host-Signaturen", "default", "Opus (PLAN db-transport); JSON von Fable (Repair)",
             ["Host = die Phoenix-App um den erzeugten Code.",
              "Er liefert das Modul `BeamlDb`.",
              "Drei Funktionen: `put/3`, `get/3`, `list/3`.",
              "BEAML schickt JSON (OTP `:json`).",
              "`get` und `list` geben JSON zurück.",
              "Fester Modulname, kein Behaviour.",
              S + "Behaviour = Elixir-Vertrag für ein Modul"],
             "Der Host muss genau diese drei Funktionen liefern.",
             [beaml('''
effect orders.save Order -> Order ! StoreError = db.put("records")

effect orders.list OrderQuery -> OrderList ! StoreError = db.list("records")
'''), ex('''
# app/lib/proto/beaml_db.ex (Köpfe, ohne Rumpf)

defmodule BeamlDb do
  def put("records", {type, version}, json), do: ...

  def get("records", type, key), do: ...

  def list("records", type, _query), do: ...
end
''')],
             [("A", "fest: `BeamlDb.put/3`, `get/3`, `list/3`", True),
              ("B", "eigenes Modul per Konfiguration, mit Behaviour (Q5-8 B), oder `put/4` (QDB-2 B)", False)]),
          it("QDB-6b", "Ein gescheiterter db-Aufruf schreibt ein rejected-Record", "default", "Fable (Default, offen)",
             ["Record = eine aufgezeichnete Zeile pro Aufruf.",
              "http, Transportfehler: kein Record.",
              "db, Fehler: ein Record mit `outcome: rejected`.",
              S + "dazu `reason: transport`",
              "Zwei Ströme, zwei Regeln."], "", [],
             [("A", "ja, ein rejected-Record", True), ("B", "kein Record, wie bei http", False)]),
          it("QDB-1", "Der Schlüssel von `db.get` ist ein String-Feld des Key-TYPE", "default", "Opus (PLAN db-transport)",
             ["`db.get` = lädt eine Zeile über einen Schlüssel.",
              "Key-TYPE = TYPE mit genau einem String-Feld.",
              "Der Name dieses Felds ist der Schlüssel.",
              "Damit ist Q5-1 entschieden: B (TYPE-Feld, nicht Zeilen-`id`).",
              "In 0005 nicht benutzt."], "",
             [beaml('''
type OrderKey { order_id: String }

effect orders.get OrderKey -> Order ! StoreError = db.get("records")
''')],
             [("A", "ein String-Feld im Key-TYPE", True), ("B", "Schlüssel im Aufruf, oder Zeilen-`id`", False)]),
          it("GET", "`BeamlDb.get/3` sucht mit `@>` Containment", "default", "Opus (GREEN exp0005)",
             ["So sucht der Host bei `db.get`.",
              "Der Schlüssel kommt als Map.",
              "Postgres-Suche: `value->'value' @> key`.",
              S + "`@>` heißt „enthält“",
              "Neueste Zeile gewinnt.",
              "Keine Zeile: `{:ok, nil}`.",
              "Gebaut, aber nicht benutzt.",
              "TEST O2 fand zwei Lücken:",
              S + "migrierte Felder findet er nicht",
              S + "leerer Schlüssel trifft jede Zeile"],
             "", [], [("A", "„enthält“-Suche, neueste Zeile", True), ("B", "ein Feld pro Aufruf, mit eindeutigem Index", False)]),
          it("QDB-5", "db-Aufrufe landen im Strom `responses`", "default", "Opus (PLAN db-transport)",
             ["Jeder db-Aufruf wird aufgezeichnet.",
              "Strom = eine Datei mit Records, eine Zeile je Record.",
              "Ziel: der Strom `responses`, wie bei http.",
              "Inhalt: RECORD CORE v3 plus `request`."], "", [],
             [("A", "Strom `responses`", True), ("B", "eigener Strom mit Verweisen auf Zeilen", False)]),
          it("QDB-7", "Der ROW SNAPSHOT: `rows.jsonl` plus `snapshot-meta.json`", "default", "Opus (PLAN db-transport)",
             ["ROW SNAPSHOT = Kopie der Zeilen als Datei.",
              "`mix beaml.stored DIR` schreibt `rows.jsonl`.",
              "Daneben: `snapshot-meta.json` mit `row_count`.",
              "`row_count` muss zur Zahl der Zeilen passen.",
              "Siehe A3."], "", [],
             [("A", "`rows.jsonl` daneben, Meta geprüft", True), ("B", "alles in einer gemischten Datei", False)]),
          it("Q5-4", "`--stored` über Postgres läuft über eine Host-Task", "default", "Opus (PLAN exp0005)",
             ["`--stored` = Build-Prüfung gegen gespeicherte Daten.",
              "Der Compiler ruft kein `psql`.",
              "Der Host schreibt den Snapshot.",
              "Der Compiler liest nur Dateien."], "", [],
             [("A", "Compiler ruft `psql`", False), ("B", "Host-Task `mix beaml.stored` schreibt den Snapshot", True)]),
          it("STORED-ARG", "`mix beaml.stored DIR` nimmt das Snapshot-Verzeichnis", "default", "Opus (RED exp0005)",
             ["Die Task `mix beaml.stored` nimmt ein Argument.",
              "Das Argument: das Snapshot-Verzeichnis.",
              "Danach ruft `run.py` den Compiler."], "", [],
             [("A", "Verzeichnis; `run.py` ruft den Compiler", True), ("B", "BEAML-Quelle; die Task ruft den Compiler", False)]),
          it("SNAP-SET", "`--stored` liest nur die Zeilen, keine alten Capture-Records", "default", "Opus (RED exp0005)",
             ["`--stored` liest nur STORED ROWS.",
              "`mix beaml.stored` schreibt ein leeres `responses.jsonl`.",
              "Aufzeichnungen früherer Läufe zählen nicht.",
              "Grund: sie sind kein Speicher (Q5-7 A)."], "", [],
             [("A", "nur STORED ROWS", True), ("B", "auch Aufzeichnungen früherer Läufe", False)]),
          it("Q5-7", "Capture-Ströme als JSONL pro Lauf", "default", "Opus (PLAN exp0005)",
             ["Aufzeichnung pro Lauf als JSONL-Dateien.",
              "JSONL = eine JSON-Zeile pro Record.",
              "Keine Tabelle `records` dafür."], "", [],
             [("A", "JSONL pro Lauf", True), ("B", "Zeilen in der Tabelle `records`", False)]),
          it("Q5-2", "`db.list`: neueste zuerst, 100, fest im Host", "default", "Opus (PLAN exp0005)",
             ["`db.list` liefert die neuesten 100 zuerst.",
              "Das steht fest im Host.",
              "`OrderQuery {}` hat keine Felder."], "", [],
             [("A", "fest im Host", True), ("B", "Felder in `OrderQuery`", False)]),
          it("ORPHAN", "Verwaiste Zeilen blocken wie verwaiste Records", "default", "Opus (RED db-stored)",
             ["EFFECT = eine `effect`-Zeile, z. B. `orders.save`.",
              "Verwaiste Zeile = ihre `operation` hat keinen EFFECT mehr.",
              S + "und keine RETIRE LINE",
              "RETIRE LINE = `retire <op> keep <n> days`.",
              S + "absichtlich stillgelegt, Daten n Tage halten",
              "Verwaiste Zeile: der Build blockt (DL-040-Text).",
              "Hilfe: `declare: retire <op> keep <n> days`.",
              "Mit RETIRE LINE: Zeilen gezählt, nicht geprüft.",
              "Was `retire` für Zeilen heißt: offen (M5)."], "", [],
             [("A", "blocken mit DL-040-Text", True), ("B", "nur nach `operation` blocken", False),
              ("C", "nur zählen, als „nicht dekodierbar“", False)]),
          it("OFFCHAIN", "Eine Zeile einer TYPE VERSION ohne Kette blockt", "default", "Opus (RED db-stored)",
             ["Beispiel: eine angenommene Zeile `Note v3`.",
              "Es gibt aber nur `migrate Note v1 -> v2`.",
              "Kein Weg von v3 zur heutigen Form.",
              "Der Build blockt mit dem Pfad-Text."], "", [],
             [("A", "blocken mit Pfad-Text", True), ("B", "nur zählen, als „nicht dekodierbar“", False)]),
      ])

# ---------------------------------------------------------------- 7
group("07-record-v3", "Record-Format v3",
      "Ein Record ist eine aufgezeichnete Zeile pro Aufruf. Seit DL-143 haben alle Ströme ein Format: Version 3. Hier: die acht Default-Fragen dazu.",
      [
          it("CORE", "Der Kern: 14 Schlüssel", "decided", "13ue (DL-141 bis DL-143)",
             ["RECORD CORE = 14 Schlüssel in jedem Record:",
              S + "`version` (3), `trace_id`, `span_id`",
              S + "`artifact_id`, `operation`, `attempt`",
              S + "`type`, `value`, `value_sha256`",
              S + "`redacted`, `unknown_keys`",
              S + "`unknown_fields`, `outcome`, `reason`",
              "http hängt `request` und `status` an."], "", [], [], dl="DL-143"),
          it("QV3-1", "Marker `version: 3`", "default", "Opus (PLAN record-v3)",
             ["Woran erkennt man Version 3?",
              "Am Schlüssel `version: 3`.",
              "Kein `format`-Schlüssel, nicht am Dateinamen."], "", [],
             [("A", "`version: 3`", True), ("B", "eigener Schlüssel `format`", False), ("C", "am Dateinamen", False)]),
          it("QV3-2", "Ein `span_id`", "default", "Opus (PLAN record-v3)",
             ["Trace = Spur eines Aufrufs durch das System.",
              "Span = ein Abschnitt dieser Spur.",
              "Jeder Record hat genau ein `span_id`.",
              "Keine Trennung Client / Server, kein `span_kind`."], "", [],
             [("A", "ein `span_id`", True), ("B", "je ein Span für Client und Server, als Zusatz", False), ("C", "`span_id` plus `span_kind`", False)]),
          it("QV3-3", "Transport-Extras flach", "default", "Opus (PLAN record-v3)",
             ["Zusatz-Schlüssel bei http: `status`, `request`.",
              "Sie stehen oben, neben dem Kern.",
              "Nicht verschachtelt unter `transport: {}`."], "", [],
             [("A", "flach, oben", True), ("B", "verschachtelt unter `transport`", False)]),
          it("QV3-4", "`outcome`/`reason`: erst Status, dann Decode", "default", "Opus (PLAN record-v3)",
             ["`outcome` = angenommen oder abgelehnt.",
              "`reason` = warum abgelehnt.",
              "Decode = Antwort in einen BEAML-Wert lesen.",
              "Werte: `status`, `decode` oder `constructor`.",
              "Erst zählt der Status, dann der Decode.",
              "Gleich wie der Fehlergrund zur Laufzeit.",
              "Das geht weiter als der Text von DL-136."], "", [],
             [("A", "erst Status, dann Decode", True), ("B", "nur Status", False)]),
          it("QV3-5", "Alte v2-Dateien einmal umgeschrieben", "default", "Opus (PLAN record-v3)",
             ["Alte Dateien im Format v2: 15 Test-Dateien.",
              "Einmal umgeschrieben mit `convert_v3.py`.",
              "Der Leser kennt nur noch v3."], "", [],
             [("A", "einmal umschreiben, Leser nur v3", True), ("B", "Leser nimmt v2 und v3", False)]),
          it("QV3-6", "Der Digest deckt `redacted`, `unknown_keys`, `value`", "default", "Opus (PLAN record-v3)",
             ["Digest = Prüfsumme (`value_sha256`).",
              "Sie deckt `redacted`, `unknown_keys`, `value`.",
              "Nicht: `unknown_fields`, `outcome`, `reason`.",
              "So wie bisher (D6B-58)."], "", [],
             [("A", "drei Schlüssel", True), ("B", "auch `outcome`, `reason`, `unknown_fields`", False)]),
          it("QV3-8", "Ein rejected RESPONSE RECORD überspringt auch Pfad- und Versionszählung", "default", "Opus (PLAN-Repair record-v3); groß durch Fable",
             ["RESPONSE RECORD = aufgezeichnete Antwort eines Aufrufs.",
              "rejected = der Aufruf schlug fehl.",
              S + "kein Status 200, oder abgelehnt",
              "`--stored` überspringt dann die Wertprüfungen.",
              "Gebaut: auch TYPE-Pfad und Versionszählung.",
              "Grund: ein Ausfall ändert keinen TYPE (DL-136).",
              "Verwaist- und Held-Prüfungen lesen trotzdem jedes Record."], "", [],
             [("A", "nur die Wertprüfungen überspringen", False), ("B", "auch TYPE-Pfad und Versionszählung (W2)", True)]),
          it("COUNT", "Die Zählzeilen-Regel: wann drucken?", "default", "Fable (zusammengelegt); Zeilen-Zeile Opus (RED db-stored)",
             ["Zählzeile = Zeile mit Zahlen nach `--stored`.",
              "RESPONSE RECORDS: nur wenn M > 0.",
              S + "`N records, K checked, M rejected at capture`",
              "ROW SNAPSHOT: immer.",
              S + "`rows: N rows, K checked, M not decodable`",
              "Zwei Regeln für dieselbe Frage:",
              "Beweist eine Zahl, dass geprüft wurde?",
              "Oder ist Stille der Normalfall?"],
             "Bei A verliert Test N20b seinen Beweis „3 checked“.", [],
             [("A", "Stille ist normal: beide nur bei M > 0", False), ("B", "Zahl beweist die Prüfung: beide immer", False), ("—", "gebaut: geteilt, A für Records, B für Zeilen", True)]),
          it("D035", "Digest-Hälfte von DL-136 (P2b)", "open", "Fable (Ruling O3 unter DL-144)",
             ["Digest = Prüfsumme `value_sha256`.",
              "DL-136 hat eine Digest-Hälfte.",
              "Falscher Digest: nur gezählt, nicht geprüft.",
              "P2 druckt `digest not verified (P2b)`.",
              "Frage: in Schritt P2b bauen oder offen lassen?"], "", [],
             [("A", "in Schritt P2b bauen", False), ("B", "offen lassen", False)]),
          it("PDB-18", "`unknown_fields` einer Liste heißen `items.<i>.<feld>`", "default", "Fable (Flag)",
             ["Gilt für Records von `db.list`.",
              "Ein Eintrag in `unknown_fields` nennt den Pfad.",
              "Form: `items.<i>.<feld>`.",
              S + "`<i>` = Platz in der Liste"], "", [], [("A", "so gebaut", True)]),
      ])

# ---------------------------------------------------------------- 8
group("08-entry", "ENTRY LINE und Seiten",
      "Die ENTRY LINE ist der Eingang von der Web-Seite in BEAML. Hier: was sie aufzeichnet. Und wie die drei Seiten der Demo-App sie rufen.",
      [
          it("ENTRY", "Die ENTRY LINE", "decided", "13ue (DL-130, DL-131)",
             ["ENTRY LINE = Eingang von der Web-Seite in BEAML.",
              "Sie sieht aus wie ein `effect`, nur nach innen.",
              "Pro Zeile erzeugt der Compiler `ui_<event>/1`.",
              "Die LiveView-Seite ruft diese Funktion.",
              "Kopf und Ziel-`fn` brauchen dieselben TYPES.",
              S + "sonst Compile-Fehler (Drift-Regel)"],
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
             ["ENTRY RECORD = Aufzeichnung eines Aufrufs über die ENTRY LINE.",
              "Fall: die Ziel-`fn` ruft keinen EFFECT nach außen.",
              "Die Datei hat aber andere EFFECTS.",
              "Dann: kein ENTRY RECORD, kein `Replay.entry`.",
              "REPLAY RUN = Lauf mit aufgezeichneten Antworten statt echter Aufrufe.",
              "Folge: kein `--stored`-Check, kein REPLAY RUN.",
              "Der alte Grund (kein `Replay`-Modul) gilt hier nicht."],
             "", [], [("A", "so gebaut", True), ("B", "auch dort ein ENTRY RECORD schreiben", False)]),
          it("G6D-03", "ENTRY RECORD `type` in Quellreihenfolge", "default", "Opus (GREEN slice6d)",
             ["Der Schlüssel `type` nennt die Felder.",
              "ENTRY RECORD: Felder wie in der Quelle.",
              "RESPONSE RECORD: Felder sortiert.",
              "RESPONSE RECORD = aufgezeichnete Antwort nach außen.",
              "Der Fingerprint sortiert in beiden.",
              S + "Fingerprint = Kennung der TYPE-Form"], "", [],
             [("A", "Reihenfolge wie in der Quelle", True), ("B", "sortiert, wie beim RESPONSE RECORD", False)]),
          it("G6D-12", "Literal-Enum im Eingabe-TYPE braucht eine Keep-Value-Variante", "default", "Opus (GREEN slice6d)",
             ["Literal-Enum = Enum mit festen Text-Werten.",
              "Im Eingabe-TYPE braucht es eine Auffang-Variante.",
              "Wie `Unknown(String)` bei `Channel`.",
              "Sie behält unbekannte Werte.",
              "Konstruktoren brauchen dort `name: String`-Signaturen.",
              "Kein Test hält das fest."], "", [beaml('''
enum Channel {
  Web = "web"
  App = "app"
  Unknown(String)
}
''')], [("A", "so gebaut", True)]),
          it("Q5-9", "Die Listenseite lädt über eine zweite ENTRY LINE aus `mount`", "default", "Opus (PLAN exp0005)",
             ["Die Liste /orders lädt beim Öffnen.",
              "`mount/3` ruft `Orders.ui_orders(%{})`.",
              "Dafür gibt es eine zweite ENTRY LINE `ui.orders`.",
              "Kein neuer Transport `ui.mount`."], "", [beaml('''
effect ui.orders OrderQuery -> OrderList ! StoreError = ui.event("orders") |> list_orders
''')], [("A", "zweite ENTRY LINE, aus `mount` gerufen", True), ("B", "neuer Transport `ui.mount`", False)]),
          it("NOTES", "Eine Seite /notes mit Formular und Liste", "default", "Opus (GREEN exp0005)",
             ["Eine Seite /notes: Formular und Liste.",
              "Bei Bestellungen sind es zwei Seiten.",
              S + "/orders/new und /orders",
              "Nach dem Absenden lädt /notes neu.",
              S + "per `push_navigate`"], "", [],
             [("A", "eine Seite", True), ("B", "zwei Seiten: `/notes/new` und `/notes`", False)]),
      ])

# ---------------------------------------------------------------- 9
group("09-syntax", "Syntax-Regeln",
      "Regeln, die man in der Sprache sieht. Sie später zu ändern ist am teuersten.",
      [
          it("COMMENT", "Kommentare nur mit `//`", "decided", "13ue (DL-132)",
             ["Ein Kommentar beginnt mit `//`.",
              "Keine andere Form."], "", [beaml('''// so, und nur so''')], [], dl="DL-132"),
          it("Q5-3", "Listen als Feldform `[Order]`", "default", "Opus (PLAN exp0005)",
             ["Liste von Werten: Feldform `[T]`.",
              "Beispiel: `items: [Order]`.",
              "Kein eigenes Schlüsselwort `list`."], "", [beaml('''
type OrderList { items: [Order] }
''')], [("A", "`items: [Order]`", True), ("B", "Schlüsselwort `list`", False)]),
          it("CTOR-ROW", "Konstruktor-Feld in einer Zeile: erste Signatur nimmt genau die String-Felder", "default", "Opus (GREEN db-transport)",
             ["Konstruktor = `fn` mit TYPE-Namen, prüft Werte.",
              "Fall: so ein Feld steht in einer Zeile.",
              "Encoder schreibt die Felder des Structs.",
              "Decoder liest über die erste Signatur.",
              "Also muss sie genau die String-Felder nehmen.",
              "Sonst: Build-Fehler, die Zeile wäre nicht lesbar."], "", [beaml('''
type BadAmount {}

type Amount {
  value: String
  currency: String
}

// Die erste Signatur nimmt genau value und currency:

fn Amount value: String, currency: String -> Amount ! BadAmount
fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
''')], [("A", "diese Regel", True), ("B", "nach Namen der Signatur kodieren", False), ("C", "erlauben und Zeilen verlieren", False)]),
          it("ROW-FIELDS", "Zeilen-Felder: String, Literal-Enum mit Keep-Variante, Konstruktor-Records", "default", "Opus (GREEN db-transport)",
             ["Erlaubt in einer Zeile:",
              S + "String",
              S + "Literal-Enum mit Auffang-Variante",
              S + "Konstruktor-Records",
              "Int und verschachtelte Records: Build-Fehler.",
              "Text: „slice 1 decodes String fields only“."], "", [],
             [("A", "so gebaut", True)]),
          it("Q6E-4", "Ein EFFECT pro Flow", "default", "Opus (PLAN multi-effect)",
             ["EFFECT = eine `effect`-Zeile, ein Aufruf nach außen.",
              "Flow = eine `fn`, die Schritte verkettet, z. B. `place`.",
              "Pro Flow nur ein EFFECT.",
              "`place` kann nicht zahlen und speichern zugleich."], "", [],
             [("A", "einer", True), ("B", "mehrere; Records nach `operation` gewählt", False)]),
          it("Q6E-3", "`Replay.run(operation, …)` bei mehreren EFFECTS", "default", "Opus (PLAN multi-effect)",
             ["REPLAY RUN = Lauf mit aufgezeichneten Antworten.",
              "Fall: Datei mit mehreren EFFECTS.",
              "`Replay.run(operation, …)` wählt über das erste Argument."], "", [], [("A", "so gebaut", True)]),
          it("D025", "Alternative Form mit `=` und `|` für enum und type", "open", "13ue (notiert)",
             ["Idee: eine zweite Schreibweise.",
              S + "`enum X = A | B`",
              S + "`type X = { … }`",
              "Du wolltest das später prüfen.",
              "Nur notiert, nicht geplant."], "", [], []),
          it("TEXTS", "Zwei Fehlertexte sind als Default gepinnt", "default", "Opus (RED db-transport)",
             ["Zwei Fehlertexte sind als Default festgehalten:",
              "`order_v2` nennt `orders.save` und `Order.amount` (D6B-39).",
              "N25b nennt `TYPE Order v1` und das Feld `channel` (DL-122)."], "", [], [("A", "so gebaut", True)]),
      ])

# ---------------------------------------------------------------- 10
group("10-misc", "Kleines",
      "Kleine Defaults. Sie ändern weder Sprache noch Format.",
      [
          it("Q5-5", "Erzeugter Code liegt in git", "default", "Opus (PLAN exp0005)",
             ["Erzeugter Code = `app/lib/generated/orders.ex`.",
              "Die Datei liegt in git.",
              "Kein Mix-Compiler, der nach `_build` schreibt."], "", [],
             [("A", "in git", True), ("B", "Mix-Compiler", False)]),
          it("TEST-O1", "`run.py run` setzt `proto_dev` zurück", "default", "Opus (TEST exp0005)",
             ["`run.py run` leert die Datenbank `proto_dev`.",
              "Dann prüft er `orders.ex` gegen 0 Zeilen.",
              "Das README sagt das.",
              "Siehe A3."], "", [],
             [("A", "Leeren behalten", True), ("B", "eigener Build-Schritt mit Dev-Zeilen", False)]),
          it("DL-147", "Eine RED-Datei kommt erst mit ihrem GREEN in `run.py`", "decided", "Fable",
             ["RED = neuer Test, zuerst rot.",
              "GREEN = der Code, der ihn grün macht.",
              "Die RED-Datei kommt erst mit GREEN in `run.py`.",
              "Sonst fällt der Gesamtlauf, solange RED offen ist."], "", [], [], dl="DL-147"),
      ])

# ---------------------------------------------------------------- 11
group("11-parked", "Geparkt (D036)",
      "Diese Punkte hast du am 2026-11-07 geparkt. Sie stehen hier, damit die Liste vollständig ist. M4 hat eine eigene Seite.",
      [
          it("M3-parked", "Fate-Formen und DL-116", "parked", "OWNER",
             ["Fate-Form = Zeile im `migrate`: was mit alten Daten passiert.",
              S + "`redact`, `quarantine`, `retire`, `map`",
              "Braucht zuerst eine frische Erklärung.",
              "Ohne M3: aus einem Block nur per SQL.",
              "Siehe Seite M3: Fate-Formen."], "", [], []),
          it("M5", "Was `retire` bedeutet, auch für Zeilen", "parked", "OWNER",
             ["`retire` = absichtlich stilllegen, Daten eine Zeit halten.",
              "Offen: was das für Zeilen heißt.",
              "Test N28b hält den heutigen Stand fest.",
              "Die Orphan-Hilfe druckt `retire <op> keep <n> days`."], "", [], []),
          it("M8", "Failure-Struct am Host", "parked", "OWNER",
             ["Frage: ein eigenes Failure-Struct am Host.",
              "P2 hat das umgangen (P5-18)."], "", [], []),
          it("M9", "Record-Zeilen in einem Blocktext", "parked", "OWNER",
             ["Frage: Record-Zeilen im Text eines Blocks.",
              "P2 hat das umgangen."], "", [], []),
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
ul.arrows{list-style:none;padding-left:0;margin:8px 0}ul.arrows li{margin:2px 0}ul.arrows li::before{content:"→ "}ul.arrows li.sub::before{content:none}
pre{padding:14px 16px;line-height:1.7}
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
    if isinstance(x["what"], str) and x["what"]:
        h.append(f'<p>{text(x["what"])}</p>')
    elif x["what"]:
        h.append('<ul class="arrows">' + "".join(f'<li class="sub">{text(w)}</li>' if w.startswith(S) else f'<li>{text(w)}</li>' for w in x["what"]) + '</ul>')
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
<p class="note">Reihenfolge für das Gespräch: 1 → 2 → 3 → 4 → 5, dann 6 bis 11 als Sammelfragen, 12 nur zur Kenntnis.</p>'''
    with open(os.path.join(HERE, "index.html"), "w") as f:
        f.write(page("Walk-through D037", body, None, (G[0]["slug"], G[0]["title"])))
    print(f"{len(G)} pages, {sum(tot.values())} items", tot)


if __name__ == "__main__":
    main()
