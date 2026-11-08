#!/usr/bin/env python3
"""Build the OWNER decision site (D037, site v2) from the item list below. See README.md for the rules.

Run from the repo root: python3 experiments/0005-prototype-fullstack/workflow/2026-11-08/review-site/build.py
Writes index.html, next.html, eingang.html, entschieden.html, aenderungen.html and one page per group; keeps
items.json (snapshot of the last build) and appends to changelog.jsonl. Reads feedback/answers.jsonl, never writes it.
BEAML snippets are colored with integrations/zed-beaml/preview.py --chat. Source: ../../2026-11-07/owner-review.md.
"""
import datetime as dt, html, json, os, re, subprocess, sys, tempfile

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


def group(slug, title, lead, items, added, source):
    """`added`/`source` stamp every item of the group that has none of its own."""
    for x in items:
        x["added"] = x["added"] or added
        x["source"] = x["source"] or source
        x["group"] = slug
    G.append(dict(slug=slug, title=title, lead=lead, items=items))


S = "\u2800\u2800↳ "  # prefix of a real sub-point in a `what` list


def it(id, title, status, by, what, why="", code=(), options=(), note="", dl="",
       added=None, source=None, decided=None, gate=False, later=False):
    """`what`: a list of short bullets (rendered as → lines), or one plain string.
    added: ISO date or UTC time the card first went on the site; source: where it came from.
    decided: UTC time of an OWNER decision taken outside the site (chat walk-through).
    gate: a Migrate question that gates the next slice (stack "Blockt Arbeit").
    later: an open card that blocks nothing (stack "Ideen für später")."""
    return dict(id=id, title=title, status=status, by=by, what=what, why=why, code=list(code), options=list(options), note=note, dl=dl,
                added=added, source=source, decided=decided, gate=gate, later=later)


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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
enum Channel {
  Web = "web"
  App = "app"
  Unknown(String)
}
'''), beaml('''
// Heute ein Build-Fehler, sobald migrate dranhängt.

// amount ist ein Konstruktor-Feld, channel ein Enum-Feld.

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
          it("QM4-1", "Fehlertext: Schritt auf Enum- oder Konstruktor-Feld", "default", "Opus (PLAN m4-lift, Default, offen)",
             ["Ein `rename` auf so ein Feld ist heute ein Compile-Fehler", "Der Text nennt M3 und DL-152 als Grund", "Gebaut: A"],
             "", [], [("A", "Text am EFFECT, nennt M3 und DL-152", True), ("B", "Text am Schritt, wie in Slice 3", False)], added="2026-11-08T09:19:32Z", source="m4-plan"),
          it("QM4-2", "Kein Versions-Mark an `Order` in 0005", "default", "Opus (PLAN m4-lift, Default, offen)",
             ["`type Order v2` steht nicht im Kopf; die Kette zeigt die Version", "fmt streicht ein Mark ohnehin (DL-104)", "Mit DL-155 wird das Mark bei betroffenen Daten Pflicht; dann Frage neu"],
             "", [], [("A", "`type Order v2 {`", False), ("B", "kein Mark", True)], added="2026-11-08T09:19:32Z", source="m4-plan"),
          it("QM4-3", "DL-122-Hilfe nennt weiter D6B-39", "default", "Opus (PLAN m4-lift, Default, offen)",
             ["Vier Tests pinnen den Text", "Mit DL-155 sollte die Hilfe die Versions-Form nennen; Docs-Frage für den Fate-Slice"],
             "", [], [("A", "Text behalten", True), ("B", "M3 und DL-140 nennen", False)], added="2026-11-08T09:19:32Z", source="m4-plan"),
          it("QM4-4", "`rename` eines Enum-Felds bleibt Fehler", "default", "Opus (PLAN m4-lift, Default, offen)",
             ["Ein `rename` bewegt nur den Schlüssel", "Trotzdem Fehler, bis der Fate-Slice die Formen hat"],
             "", [], [("A", "Fehler", True), ("B", "jetzt erlauben", False)], added="2026-11-08T09:19:32Z", source="m4-plan"),
          it("N9", "Der strengere Amount braucht eine Fate-Form", "parked", "OWNER geparkt (über M3, M4, M5)",
             ["Variante `stricter`: `Amount` wird strenger.",
              "Neu: der Betrag `\"0\"` wird abgelehnt.",
              "Alte Zeilen mit `\"0\"` blocken dann den Build.",
              "Das ist so gewollt.",
              "Kleinster Ausweg: `quarantine value` im migrate-Block von `Amount v2`.",
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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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

// f = Feldname. Die Fate-Zeile steht im migrate-Block des TYPE, dem das Feld gehört.
// Beispiel: value darf nicht mehr "0" sein, 2 Zeilen sind betroffen (DL-155).

type Amount v2 {
  value: String
  currency: String
}

migrate Amount v1 -> v2 {
  quarantine value
}

fn Amount value: String, currency: String -> Amount ! BadAmount
fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
fn Amount "0",           _                -> Amount ! BadAmount = BadAmount {}
fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
''')],
             [], note="Form A, wie im unterschriebenen Bild vom 2026-11-08 (DL-155). Für ein Enum: `enum Channel v2 { … }` plus `migrate Channel v1 -> v2 { map \"app\" -> Mobile }`.", dl="DL-125"),
          it("VERSION-RULE", "Versionsregel: Änderung plus betroffene Werte = neue Version", "decided", "13ue (2026-11-08, nach drei Beispielen)",
             ["Build prüft live: fällt ein gespeicherter Wert anders?",
              "Nein: Änderung frei, keine neue Version",
              "Ja: `type Amount v2` oder `enum Channel v2` plus `migrate v1 -> v2` mit Fate oder `map`",
              "v1 steht von Anfang an; alte Version lebt, bis Production leer ist, dann SQUASH",
              "Gilt für Konstruktor-TYPES und Enums",
              "Nummern in Records werden nie neu vergeben"],
             "", [], [], dl="DL-155", added="2026-11-08T09:06:08Z", source="walk-through 2026-11-08", decided="2026-11-08T09:06:08Z"),
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

type BadAmount {}

type Amount {
  value: String
  currency: String
}

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

type Order {
  order_id: String
  amount: Amount
  channel: Channel
}

migrate Order v1 -> v2 { redact amount }
''')],
             [("A", "DL-116 verlässt die Liste; neue Frage: wie läuft eine Regel über einen fehlenden Wert", False),
              ("B", "`redact` überspringt die Regel, DL-116 B kommt zurück", False)], gate=True),
          it("FATE-NEXT", "Reihenfolge: wann bauen wir die Fate-Formen?", "decided", "Fable (Vorschlag); entschieden 13ue: A",
             ["Mit DL-152 brauchen Schritte auf Enum- und Konstruktor-Feldern diese Formen.",
              "Vorschlag: nach M4 Schritt 1 (erst migrieren, dann prüfen) kommt der Fate-Slice.",
              S + "Grammatik für die vier Zeilen",
              S + "`--stored` löst DL-102/DL-122/DL-140, wenn eine Fate-Zeile das Feld nennt",
              S + "REPLAY RUN überspringt Werte in `quarantine`",
              S + "Use Case: 0005 N9 mit `quarantine value` (Amount v2)",
              "Alternative: erst `--stored` live aus der Datenbank (DL-151)."],
             "",
             [],
             [("A", "Fate-Slice direkt nach M4 Schritt 1", False),
              ("B", "erst live `--stored` (DL-151), dann Fate-Slice", False)], dl="DL-156", decided="2026-11-08T09:19:32Z"),
      ], added="2026-11-08T07:26:11Z", source="m3-page 2026-11-08")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
              "Nur notiert, nicht geplant."], "", [], [], later=True),
          it("TEXTS", "Zwei Fehlertexte sind als Default gepinnt", "default", "Opus (RED db-transport)",
             ["Zwei Fehlertexte sind als Default festgehalten:",
              "`order_v2` nennt `orders.save` und `Order.amount` (D6B-39).",
              "N25b nennt `TYPE Order v1` und das Feld `channel` (DL-122)."], "", [], [("A", "so gebaut", True)]),
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

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
              "Die Orphan-Hilfe druckt `retire <op> keep <n> days`."], "", [], [], gate=True),
          it("M8", "Failure-Struct am Host", "parked", "OWNER",
             ["Frage: ein eigenes Failure-Struct am Host.",
              "P2 hat das umgangen (P5-18)."], "", [], []),
          it("M9", "Record-Zeilen in einem Blocktext", "parked", "OWNER",
             ["Frage: Record-Zeilen im Text eines Blocks.",
              "P2 hat das umgangen."], "", [], []),
      ], added="2026-11-07", source="owner-review 2026-11-07")

# ---------------------------------------------------------------- 12b
group("12b-register", "Neue Fragen aus dem Walk-through",
      "Ideen, die heute dazukamen. Noch nichts entschieden; jede hat einen Register-Eintrag.",
      [
          it("D038", "Zeilenlänge und Umbrüche in einer Klausel", "open", "13ue (Idee)",
             ["Maximale Länge, z. B. 120, oder Umbruch-Regel in der CLAUSE TABLE", "Spalten zählen heute Bytes; ein langer Name verbreitert den Block", "Erst bei längeren Funktionen"], "", [], []),
          it("D039", "Wie ein geschwärztes Feld in Records gespeichert wird", "open", "13ue (Idee)",
             ["Default: Hash (prüfbar, nicht lesbar); braucht Schlüssel oder Salz", "Explizit: verschlüsselt mit Server-Secret, für den Notfall lesbar", "Einstellung mit sicherem Default"], "", [],
             [("A", "Hash als Default", False), ("B", "verschlüsselt, nur als Opt-in", False)]),
          it("D040", "Sichtbarkeit: was ein Modul vor dem Host verbirgt", "open", "13ue (Idee)",
             ["Etwas als intern markieren, damit es nie nach außen gerät", "Ebene offen: Modul, TYPE oder Feld", "Team-Vorschlag: Oberfläche aus den ENTRY LINES ableiten, kein neues Wort"], "", [],
             [("A", "abgeleitet, Build listet die Oberfläche", False), ("B", "explizites Opt-in pro TYPE", False), ("C", "abgeleitet plus Opt-out-Wort", False)]),
          it("D041", "Enum-Konstruktor entfernen", "open", "Sprach-Team (Kandidat 2)",
             ["Heute bildet eine `fn Channel …` fremde Strings mit Logik auf Varianten ab", "Vorschlag: nur die Literal-Tabelle; `fn Großname` ist immer Record-Konstruktor", "Verlust: Logik und Int → Variante; 9 Enums in Fixtures, keins in 0005"], "", [],
             [("A", "nur Literale", False), ("B", "Literale plus `\"web\" | \"WEB\"`", False), ("C", "wie heute", False)], source="lang-team"),
          it("D042", "Lazy-Nachprüfung geschwärzter Regeln", "open", "13ue (Idee)",
             ["Prüfung dort, wo der Wert ist: in der App beim Lesen oder Neueingeben", "Compiler listet jede Stelle, die das Ergebnis erreicht (Totalität)", "Form offen: Zustand im TYPE oder Fehlergrund im `! StoreError`", "M3 (`redact` überspringt Regel?): Neigung A, noch zu bestätigen"], "", [],
             [("A", "Zustand im TYPE (`T v1 | T v2`)", False), ("B", "Fehlergrund pro Aufruf", False)]),
      ], added="2026-11-08T09:19:32Z", source="walk-through 2026-11-08")

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
      ], added="2026-11-07", source="owner-review 2026-11-07")

# ---------------------------------------------------------------- model
FB = os.path.join(HERE, "feedback")
SNAP = os.path.join(HERE, "items.json")
LOG = os.path.join(HERE, "changelog.jsonl")
INBOX = "eingang"
STACKS = [("block", "Blockt Arbeit", "Offene Fragen und Migrate-Fragen, die den nächsten Slice aufhalten."),
          ("defaults", "Gebaute Defaults", "Gebaut nach DL-139. Gilt erst, wenn du es abnimmst."),
          ("ideas", "Ideen für später", "Notiert oder geparkt. Blockt nichts.")]
ICON = dict(decided="✓", open="?", default="◆", parked="‖")
LABEL = dict(decided="entschieden", open="offen", default="Default, gebaut", parked="geparkt")
CHANGE = {"added": "neu", "status decided": "entschieden", "moved to Eingang": "in den Eingang verschoben", "removed": "entfernt"}


def ts(s):
    """ISO date or UTC time -> aware datetime (a bare date counts as its first second, UTC)."""
    d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)


def fmt(s):
    if not s:
        return ""
    if len(s) == 10:
        return ts(s).strftime("%d.%m.%Y")
    return ts(s).astimezone().strftime("%d.%m.%Y, %H:%M")


def read_answers():
    """feedback/answers.jsonl, read only. Latest choice and latest note per id win; choice "" means cleared."""
    d = {}
    try:
        lines = open(os.path.join(FB, "answers.jsonl")).read().splitlines()
    except FileNotFoundError:
        return d
    for line in lines:
        r = json.loads(line)
        a = d.setdefault(r["id"], dict(first=r["ts"]))
        if r.get("choice") is not None:
            a["choice"], a["choice_ts"] = r["choice"], r["ts"]
        if r.get("note") is not None:
            a["note"], a["note_ts"] = r["note"], r["ts"]
    return d


def owner_time(x, ans):
    """When the OWNER first answered this card: a site answer, or an OWNER decision shown on the card from its start."""
    t = [ans[x["id"]]["first"]] if x["id"] in ans else []
    if x["decided"]:
        t.append(x["decided"])
    if not t and x["status"] == "decided" and "13ue" in x["by"]:
        t.append(x["added"])  # decided by the OWNER before the card went on the site
    return min(t, key=ts) if t else None


def place(ans):
    """Eingefroren: once a page holds an OWNER answer, a card added later goes to the Eingang."""
    for g in G:
        F = None
        for x in sorted(g["items"], key=lambda x: ts(x["added"])):
            if F is not None and ts(x["added"]) > ts(F):
                x["page"] = INBOX
                continue
            x["page"] = g["slug"]
            t = owner_time(x, ans)
            if t and (F is None or ts(t) < ts(F)):
                F = t
        g["frozen"] = F


def stack(x):
    if x["status"] == "decided":
        return "done"
    if x["gate"] or (x["status"] == "open" and not x["later"] and x["group"] != "12b-register"):
        return "block"
    return "defaults" if x["status"] == "default" else "ideas"


def built(x):
    return next((L for L, _, b in x["options"] if b), "")


def decided_at(x, ans):
    a = ans.get(x["id"], {})
    return x["decided"] or (a.get("choice_ts") if a.get("choice") else None)


def changelog(ans, now):
    """Append one line per change against items.json (the last build) to changelog.jsonl; then refresh items.json."""
    old = {}
    if os.path.exists(SNAP):
        old = {(r["group"], r["id"]): r for r in json.load(open(SNAP))}
    seed = not old  # first build: rebuild the history from the `added` and decision times
    cur, ev = [], []
    for g in G:
        for x in g["items"]:
            r = dict(group=g["slug"], id=x["id"], status=x["status"], page=x["page"], added=x["added"], source=x["source"], by=x["by"])
            cur.append(r)
            o = old.get((r["group"], r["id"]))
            if o is None:
                ev.append(dict(ts=x["added"] if seed else now, id=x["id"], page=x["page"], change="added", by=x["source"]))
                if seed and x["status"] == "decided":
                    ev.append(dict(ts=decided_at(x, ans) or x["added"], id=x["id"], page=x["page"], change="status decided", by=x["by"]))
                if x["page"] == INBOX:
                    ev.append(dict(ts=now, id=x["id"], page=x["page"], change="moved to Eingang", by="build.py (eingefroren)"))
                continue
            if o["status"] != r["status"]:
                ev.append(dict(ts=now, id=x["id"], page=x["page"], change="status decided" if r["status"] == "decided" else "status " + r["status"], by=x["by"]))
            if o["page"] != r["page"] and r["page"] == INBOX:
                ev.append(dict(ts=now, id=x["id"], page=x["page"], change="moved to Eingang", by="build.py (eingefroren)"))
    keys = {(r["group"], r["id"]) for r in cur}
    ev += [dict(ts=now, id=k[1], page=old[k]["page"], change="removed", by="build.py") for k in old if k not in keys]
    if ev:
        with open(LOG, "a") as f:
            for e in sorted(ev, key=lambda e: ts(e["ts"])):
                f.write(json.dumps(dict(e, seed=True) if seed else e, ensure_ascii=False) + "\n")
    with open(SNAP, "w") as f:
        json.dump(cur, f, ensure_ascii=False, indent=1)
    return ev


def read_log():
    try:
        return [json.loads(l) for l in open(LOG).read().splitlines() if l.strip()]
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------- style and behavior
CSS = """
:root{color-scheme:light dark;--bg:#f6f7f9;--fg:#24272e;--mut:#555b66;--bd:#c9ced6;--card:#fff;--soft:#eef0f4;
--acc:#1f5fbf;--acc-fg:#fff;--focus:#1f5fbf;
--k:#a626a4;--t:#8a5d00;--f:#2c5ccf;--p:#c2392c;--s:#3a7a39;--c:#016a96;--o:#383a42;--m:#636975;
--ok:#1d6b3f;--open:#b02a1f;--def:#80530a;--park:#555b66;--new:#6b3fa0}
@media (prefers-color-scheme:dark){:root{--bg:#17191e;--fg:#d5d9e0;--mut:#a3aab6;--bd:#424854;--card:#21252c;--soft:#2a2f37;
--acc:#7fb0ff;--acc-fg:#10141a;--focus:#9cc2ff;
--k:#d38ae6;--t:#e5c07b;--f:#7ab8f5;--p:#f08a92;--s:#a5cf88;--c:#6cc6d1;--o:#c8ced8;--m:#9aa1ad;
--ok:#8fd19e;--open:#ff9a8f;--def:#f0c674;--park:#b4bac4;--new:#c9a6f2}}
*{box-sizing:border-box}[hidden]{display:none!important}
html{scroll-behavior:smooth}
body{margin:0 auto;max-width:880px;padding:0 16px 64px;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
a{color:var(--acc);text-underline-offset:2px}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px;border-radius:4px}
main:focus,.card:focus,.done:focus{outline:none}
.skip{position:absolute;left:8px;top:-60px;background:var(--acc);color:var(--acc-fg);padding:8px 12px;border-radius:6px;z-index:10}
.skip:focus{top:8px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.top nav{display:flex;flex-wrap:wrap;gap:4px 18px;padding:14px 0 10px;border-bottom:1px solid var(--bd);margin-bottom:8px;font-size:15px}
.top a{text-decoration:none;padding:4px 0}.top a:hover{text-decoration:underline}
.top a[aria-current]{color:var(--fg);font-weight:700;border-bottom:3px solid var(--acc)}
.count{display:inline-block;min-width:1.6em;padding:0 6px;border-radius:999px;background:var(--new);color:var(--card);font-size:12px;font-weight:700;text-align:center}
h1{font-size:28px;line-height:1.2;margin:18px 0 6px}
.sec{font-size:19px;margin:28px 0 8px}
.lead{color:var(--mut);margin:0 0 16px}.mut{color:var(--mut)}
.crumb{font-size:14px;color:var(--mut);margin:14px 0 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:14px 16px;border:1px solid var(--bd);border-radius:8px;margin:12px 0;background:var(--soft);font:13.5px/1.7 ui-monospace,Menlo,monospace}
code{font:0.9em ui-monospace,Menlo,monospace;background:var(--soft);border:1px solid var(--bd);border-radius:4px;padding:0 4px;overflow-wrap:anywhere}
i{font-style:normal}.k{color:var(--k)}.t{color:var(--t)}.f{color:var(--f)}.p{color:var(--p)}.s{color:var(--s)}.c{color:var(--c)}.o,.b{color:var(--o)}.m{color:var(--m);font-style:italic}
.ico{width:1em;height:1em;vertical-align:-0.12em}
.btn{font:600 15px/1.2 system-ui,sans-serif;padding:10px 14px;min-height:44px;border-radius:8px;border:1px solid var(--bd);background:var(--card);color:var(--fg);cursor:pointer;display:inline-flex;gap:6px;align-items:center;text-decoration:none}
.btn:hover{border-color:var(--acc)}
.btn.primary{background:var(--acc);border-color:var(--acc);color:var(--acc-fg)}
.btn.big{font-size:17px;padding:14px 20px}
.btn.link{border:0;background:none;color:var(--acc);padding:2px 4px;min-height:0;text-decoration:underline;font-weight:600}
.pill{display:inline-flex;gap:4px;align-items:center;font:600 12.5px/1 system-ui,sans-serif;padding:5px 9px;border-radius:999px;border:1px solid currentColor;color:var(--mut);white-space:nowrap}
.st-decided{color:var(--ok)}.st-open{color:var(--open)}.st-default{color:var(--def)}.st-parked{color:var(--park)}.st-new{color:var(--new)}
.card{border:1px solid var(--bd);border-radius:12px;padding:16px 18px;margin:16px 0;background:var(--card)}
.card.answered{border-left:5px solid var(--ok)}
.card-top{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.card-id{font:700 13px ui-monospace,Menlo,monospace;color:var(--mut)}
.card-title{font-size:19px;line-height:1.3;margin:8px 0 4px}
.meta{display:flex;flex-wrap:wrap;gap:2px 16px;font-size:13.5px;color:var(--mut);margin:0 0 8px}
.why{border-left:3px solid var(--def);padding:2px 12px;margin:10px 0}
.note{color:var(--mut);font-size:14px}
ul.arrows{list-style:none;padding-left:0;margin:8px 0}ul.arrows li{margin:3px 0;padding-left:1.4em;text-indent:-1.4em}ul.arrows li::before{content:"→ ";color:var(--mut)}
ul.arrows li.sub{padding-left:0;text-indent:0}ul.arrows li.sub::before{content:none}
.opts{display:grid;gap:8px;margin:14px 0 6px}
.opt{display:grid;grid-template-columns:2em 1fr;gap:4px 10px;align-items:start;text-align:left;width:100%;font:15px/1.45 system-ui,sans-serif;color:var(--fg);background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:10px 12px;min-height:44px;cursor:pointer}
.opt:hover{border-color:var(--acc);background:var(--soft)}
.opt.built{border-style:dashed;border-color:var(--def)}
.opt[aria-pressed=true]{border:2px solid var(--ok);background:var(--soft)}
.opt-l{font-weight:800;font-size:16px}
.opt-tags{grid-column:2;display:flex;flex-wrap:wrap;gap:6px}.opt-tags:empty{display:none}
.tag{font:600 12.5px/1 system-ui;padding:4px 8px;border-radius:999px;border:1px solid currentColor}
.tag-built{color:var(--def)}.tag-mine{color:var(--ok);display:none}.opt[aria-pressed=true] .tag-mine{display:inline-block}
.ans{font-size:14.5px}.ans-row{border-left:3px solid var(--ok);padding:4px 12px;margin:8px 0;background:var(--soft);border-radius:0 6px 6px 0}
.ans time{color:var(--mut);margin:0 4px}
.fb{margin-top:12px}.fbt{width:100%;font:15px/1.45 system-ui,sans-serif;padding:8px 10px;border:1px solid var(--bd);border-radius:8px;background:var(--card);color:var(--fg);resize:vertical;min-height:44px}
.fb-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:8px}
.mic{user-select:none;-webkit-user-select:none;touch-action:none}.mic.on{background:var(--open);border-color:var(--open);color:var(--card)}.mic.busy{opacity:.7}
.fbs{font-size:13.5px;color:var(--mut)}
.prog{display:flex;align-items:center;gap:10px;margin:10px 0;font-size:14px;color:var(--mut)}
progress{flex:0 1 220px;height:10px;accent-color:var(--ok)}
.frozen,.hint{background:var(--soft);border:1px solid var(--bd);border-radius:8px;padding:8px 12px;font-size:14.5px}
.bulk{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:12px 0}
.empty{color:var(--mut);font-style:italic;border:1px dashed var(--bd);border-radius:8px;padding:12px}
dialog{border:1px solid var(--bd);border-radius:12px;background:var(--card);color:var(--fg);max-width:min(560px,calc(100vw - 32px));padding:18px 20px}
dialog::backdrop{background:rgba(0,0,0,.45)}dialog h2{margin-top:0;font-size:19px}
.dlg-actions{display:flex;flex-wrap:wrap;gap:10px;justify-content:flex-end;margin-top:14px}
ul.plain{list-style:none;padding-left:0;margin:8px 0}ul.list li{padding:6px 0;border-bottom:1px solid var(--bd)}
#bulk-list{max-height:40vh;overflow:auto}
.news time{color:var(--mut);font-size:13.5px;margin-right:6px}
#toast{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:var(--fg);color:var(--bg);padding:10px 14px;border-radius:10px;max-width:calc(100vw - 32px);z-index:20}
#toast .btn.link{color:var(--bg)}
.hero{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;margin:16px 0 8px}
.stacks{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:16px 0}
.stack{border:1px solid var(--bd);border-radius:12px;padding:14px 16px;background:var(--card)}
.stack h2{font-size:18px;margin:0 0 4px}.stack-n{font-size:26px;font-weight:800;margin-right:4px}
.stack .mut{font-size:14px;margin:0}
.duo{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:0 24px}
.tablewrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;margin:10px 0;font-size:14.5px}
td,th{border-bottom:1px solid var(--bd);padding:8px 6px;text-align:left;vertical-align:top}thead th{color:var(--mut);font-weight:600}
td.n,th.n{text-align:right;white-space:nowrap}td.nw{white-space:nowrap}
th.n .pill{font-size:11.5px;padding:3px 6px}
.pager{display:flex;justify-content:space-between;gap:16px;margin-top:28px;padding-top:14px;border-top:1px solid var(--bd);font-size:15px}
.pager span:last-child{text-align:right}
.qbar{position:sticky;top:0;z-index:5;background:var(--bg);padding:6px 0;border-bottom:1px solid var(--bd)}
.qpos{margin:0;font-size:15px}
.keys{font-size:13.5px;color:var(--mut)}kbd{font:600 12px ui-monospace,Menlo,monospace;border:1px solid var(--bd);border-bottom-width:2px;border-radius:4px;padding:1px 5px;background:var(--card);color:var(--fg)}
.qnav{display:flex;justify-content:flex-end;margin:8px 0}
.done{border:2px solid var(--ok);border-radius:12px;padding:16px 18px;background:var(--card);margin:16px 0}.done h2{margin-top:0;color:var(--ok)}
.new-tag{margin:22px 0 -8px;font-size:14px;color:var(--mut)}
@media (max-width:560px){h1{font-size:24px}.card{padding:14px}.btn{width:auto}th.n .lbl{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}th.n .pill{padding:4px 7px}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*{transition:none!important;animation:none!important}}
"""

JS = r'''<script>
(() => {
const $ = (s, r=document) => r.querySelector(s), $$ = (s, r=document) => [...r.querySelectorAll(s)];
const PAGE = document.body.dataset.page;
const post = (u, b) => fetch(u, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(b)}).then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
const act = (action, target, result, source='mouse') => post('/api/act', {source, action, target, result}).catch(()=>{});
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmtT = t => { try { return new Date(t).toLocaleString('de-DE', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'}); } catch { return t; } };
let A = {}, offline = false;
const has = id => { const a = A[id]; return !!a && (!!a.choice || !!a.note); };  // choice "" = cleared (Rückgängig)

function toast(msg, undo) {
  const t = $('#toast'); $('.toast-t', t).textContent = msg; const b = $('.toast-undo', t);
  b.hidden = !undo; b.onclick = async () => { t.hidden = true; await undo(); };
  t.hidden = false; clearTimeout(toast.h); toast.h = setTimeout(() => t.hidden = true, 10000);
}
function paint(card) {
  const id = card.dataset.id, a = A[id] || {}, ch = a.choice || '';
  $$('.opt', card).forEach(b => b.setAttribute('aria-pressed', String(!!ch && b.dataset.choice === ch)));
  let h = '';
  if (ch) h += `<p class="ans-row"><span aria-hidden="true">✓</span> Deine Wahl: <b>${esc(ch)}</b> <time>${fmtT(a.choice_ts || a.ts)}</time> <button type="button" class="btn link undo">Rückgängig</button></p>`;
  if (a.note) h += `<p class="ans-row"><span aria-hidden="true">✎</span> Deine Notiz <time>${fmtT(a.note_ts || a.ts)}</time>: ${esc(a.note)}</p>`;
  const box = $('.ans', card); box.innerHTML = h; card.classList.toggle('answered', has(id));
  const u = $('.undo', box); if (u) u.onclick = async () => { try { await post('/api/answer', {id, choice: ''}); act('undo', id, ch); await load(); toast(`Wahl ${ch} zu ${id} zurückgenommen.`); } catch (e) { toast('Nicht gespeichert: ' + e.message); } };
}
function summary() {
  $$('.prog').forEach(p => { const ids = p.dataset.ids.split(' ').filter(Boolean), n = ids.filter(has).length;
    $('progress', p).value = n; $('.prog-t', p).textContent = `${n} von ${ids.length} ${p.dataset.label}`; });
  $$('[data-left]').forEach(el => el.textContent = el.dataset.left.split(' ').filter(i => i && !has(i)).length);
  const mine = $('#mine');
  if (mine) { const idx = JSON.parse($('#idx').textContent);
    const rows = Object.entries(A).filter(([id, a]) => (a.choice || a.note) && idx[id] && idx[id][2] !== 'decided').sort((x, y) => (y[1].ts > x[1].ts) - (y[1].ts < x[1].ts));
    mine.innerHTML = rows.length ? rows.map(([id, a]) => `<li><a href="${idx[id][1]}"><b>${esc(id)}</b> ${esc(idx[id][0])}</a> · ${a.choice ? 'deine Wahl <b>' + esc(a.choice) + '</b>' : 'nur Notiz'} <time class="mut">${fmtT(a.choice_ts || a.ts)}</time></li>`).join('')
      : '<li class="empty">Noch keine Antworten auf offene Karten.</li>'; }
}
async function load() {
  try { A = await (await fetch('/api/answers', {cache: 'no-store'})).json(); offline = false; }
  catch { offline = true; }
  $$('section.card').forEach(paint); summary();
}
async function choose(card, L, source) {
  const id = card.dataset.id, st = $('.fbs', card);
  try { await post('/api/answer', {id, choice: L}); act('choose', id, L, source); st.textContent = `Wahl ${L} gespeichert`; await load(); card.dispatchEvent(new Event('chosen')); }
  catch (e) { st.textContent = 'Nicht gespeichert: ' + e.message; }
}
let hot = null;
$$('section.card').forEach(card => {
  const id = card.dataset.id, ta = $('.fbt', card), st = $('.fbs', card), mic = $('.mic', card);
  $$('.opt', card).forEach(b => b.addEventListener('click', ev => choose(card, b.dataset.choice, ev.detail === 0 ? 'key' : 'mouse')));
  const save = async () => { const note = ta.value.trim(); if (!note) { st.textContent = 'Notiz ist leer'; return; }
    try { await post('/api/answer', {id, note}); act('note', id, note.length + ' chars', 'key'); ta.value = ''; st.textContent = 'Notiz gespeichert'; await load(); }
    catch (e) { st.textContent = 'Nicht gespeichert: ' + e.message; } };
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); save(); } });
  $('.save', card).addEventListener('click', save);
  // push-to-talk: hold the button, or hold M while the card has the pointer or the focus
  let rec = null, stream = null, chunks = [], t0 = 0;
  card._down = async () => {
    if (rec) return; st.textContent = 'Mikrofon…'; fetch('/api/stt/warm', {method:'POST'}).catch(()=>{});
    try { stream = await navigator.mediaDevices.getUserMedia({audio: true}); } catch (e) { st.textContent = 'Kein Mikrofon: ' + e.message + '. Tippe die Notiz.'; return; }
    const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'].find(t => MediaRecorder.isTypeSupported(t)) || '';
    rec = new MediaRecorder(stream, mime ? {mimeType: mime} : {}); chunks = []; t0 = performance.now();
    rec.ondataavailable = e => e.data.size && chunks.push(e.data);
    rec.onstop = async () => {
      stream.getTracks().forEach(t => t.stop()); const blob = new Blob(chunks, {type: rec.mimeType || mime || 'audio/webm'}); rec = null;
      mic.classList.remove('on'); mic.classList.add('busy'); st.textContent = 'Schreibe ab…';
      try { const r = await fetch('/api/stt?id=' + encodeURIComponent(id), {method:'POST', headers:{'Content-Type': blob.type}, body: blob}); const j = await r.json();
        st.textContent = r.ok ? (j.text ? 'Sprachnotiz gespeichert' : 'Nichts gehört') : ('Fehler: ' + (j.error || r.status) + '. Tippe die Notiz.'); if (!r.ok) ta.focus(); }
      catch (e) { st.textContent = 'Fehler: ' + e.message; }
      mic.classList.remove('busy'); act('voice', id, Math.round((performance.now() - t0) / 100) / 10 + ' s', 'voice'); load();
    };
    rec.start(); mic.classList.add('on'); st.textContent = 'Aufnahme läuft. Loslassen zum Senden.';
  };
  card._up = () => { if (rec && rec.state === 'recording') rec.stop(); };
  mic.addEventListener('pointerdown', e => { e.preventDefault(); mic.setPointerCapture?.(e.pointerId); card._down(); });
  mic.addEventListener('pointerup', card._up); mic.addEventListener('pointercancel', card._up);
  mic.addEventListener('keydown', e => { if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) { e.preventDefault(); card._down(); } });
  mic.addEventListener('keyup', e => { if (e.key === ' ' || e.key === 'Enter') card._up(); });
  card.addEventListener('pointerenter', () => hot = card); card.addEventListener('focusin', () => hot = card);
});
const typing = e => e.target.matches?.('input, textarea, select') || e.metaKey || e.ctrlKey || e.altKey;
document.addEventListener('keydown', e => { if (e.key.toLowerCase() === 'm' && !e.repeat && hot && !hot.hidden && !typing(e)) hot._down(); });
document.addEventListener('keyup', e => { if (e.key.toLowerCase() === 'm' && hot) hot._up(); });

// Gruppenweise abnicken
const bulk = $('#bulk');
if (bulk) {
  const dlg = $('#bulk-dlg'); let todo = [];
  bulk.addEventListener('click', () => {
    todo = $$('section.card[data-stack="defaults"]').filter(c => c.dataset.built && !has(c.dataset.id)).map(c => [c.dataset.id, c.dataset.built, $('.card-title', c).textContent]);
    if (!todo.length) { $('#bulk-st').textContent = 'Nichts zu tun: jede Default-Karte hier hat schon eine Antwort oder Notiz.'; return; }
    $('#bulk-n').textContent = todo.length;
    $('#bulk-list').innerHTML = todo.map(([id, b, t]) => `<li><b>${esc(id)}</b> → ${esc(b)} <span class="mut">${esc(t)}</span></li>`).join('');
    dlg.showModal();
  });
  $('#bulk-cancel').addEventListener('click', () => dlg.close());
  $('#bulk-ok').addEventListener('click', async () => {
    dlg.close(); const done = [];
    for (const [id, b] of todo) { try { await post('/api/answer', {id, choice: b, note: 'Gruppe abgenickt'}); done.push(id); } catch {} }
    act('bulk-accept', PAGE, done.length + ' ids: ' + done.join(' ')); await load();
    $('#bulk-st').textContent = `${done.length} von ${todo.length} gespeichert.`;
    toast(`${done.length} Defaults abgenickt.`, async () => {
      for (const id of done) { try { await post('/api/answer', {id, choice: '', note: ''}); } catch {} }
      act('bulk-undo', PAGE, done.length + ' ids'); await load(); $('#bulk-st').textContent = 'Zurückgenommen.';
    });
  });
}

// Eine Frage auf einmal
let start = () => {};
if (PAGE === 'next') {
  const cards = $$('#queue section.card'), nx = $('#qnext'); let q = [], i = 0;
  const show = () => {
    cards.forEach(c => c.hidden = true);
    const end = i >= q.length; $('#done').hidden = !end; $('#qbar').hidden = end; nx.hidden = end; $('.keys').hidden = end;
    if (end) { const left = cards.filter(c => !has(c.dataset.id)).length; $('#again-p').hidden = !left; $('#again-n').textContent = left; $('#done').focus(); act('focus-done', 'next', left + ' left'); return; }
    const c = q[i]; c.hidden = false; hot = c; $('#qpos').textContent = `${i + 1} von ${q.length}`;
    nx.textContent = has(c.dataset.id) ? 'Weiter (N)' : 'Überspringen (N)'; c.focus({preventScroll: true}); window.scrollTo(0, 0);
  };
  start = () => { q = cards.filter(c => !has(c.dataset.id)); i = 0; show(); };
  nx.addEventListener('click', ev => { const c = q[i]; if (c) act(has(c.dataset.id) ? 'next' : 'skip', c.dataset.id, null, ev.detail === 0 ? 'key' : 'mouse'); i++; show(); });
  cards.forEach(c => c.addEventListener('chosen', () => { nx.textContent = 'Weiter (N)'; nx.focus(); }));
  $('#again').addEventListener('click', start);
  document.addEventListener('keydown', e => {
    if (typing(e) || e.repeat) return; const k = e.key.toUpperCase(), c = q[i];
    if (k === 'N' && c) { e.preventDefault(); nx.click(); return; }
    const b = c && $$('.opt', c).find(b => b.dataset.choice === k);
    if (b) { e.preventDefault(); choose(c, k, 'key'); }
  });
}
load().then(() => { if (offline) toast('Server nicht erreichbar: Antworten werden nicht gespeichert.'); start(); });
$$('a[href]').forEach(a => a.addEventListener('click', () => act('nav', a.getAttribute('href'))));
})();
</script>'''


# ---------------------------------------------------------------- render
LOCK = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M4 7V5a4 4 0 0 1 8 0v2h1v8H3V7h1zm2 0h4V5a2 2 0 1 0-4 0v2z"/></svg>'
MIC = '<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 1a2.5 2.5 0 0 0-2.5 2.5v4a2.5 2.5 0 0 0 5 0v-4A2.5 2.5 0 0 0 8 1zM3.5 7.5h1a3.5 3.5 0 0 0 7 0h1a4.5 4.5 0 0 1-4 4.47V14h2v1h-5v-1h2v-2.03a4.5 4.5 0 0 1-4-4.47z"/></svg>'


def e(s):
    return html.escape(str(s), quote=True)


def pill(status):
    return f'<span class="pill st-{status}"><span aria-hidden="true">{ICON[status]}</span> <span class="lbl">{LABEL[status]}</span></span>'


def href(x):
    return f'{x["page"]}.html#{x["id"]}'


TITLES = {}


def render_item(x, ans, home=False):
    st, sid, b = x["status"], x["id"], built(x)
    h = [f'<section class="card" id="{e(sid)}" data-id="{e(sid)}" data-status="{st}" data-stack="{stack(x)}" data-built="{e(b)}" tabindex="-1" aria-labelledby="t-{e(sid)}">',
         f'<div class="card-top"><span class="card-id">{e(sid)}</span>{pill(st)}'
         + (f'<span class="pill">{e(x["dl"])}</span>' if x["dl"] else "") + '</div>',
         f'<h2 class="card-title" id="t-{e(sid)}">{text(x["title"])}</h2>']
    meta = [f'<span>Von: {text(x["by"])}</span>', f'<span>Neu am {fmt(x["added"])} · {e(x["source"])}</span>']
    d = decided_at(x, ans) if st == "decided" else None
    if d:
        meta.append(f'<span>Entschieden am {fmt(d)}</span>')
    if home:
        meta.append(f'<span>Gehört zu: <a href="{x["group"]}.html">{text(TITLES[x["group"]])}</a></span>')
    h.append('<p class="meta">' + "".join(meta) + '</p>')
    if isinstance(x["what"], str) and x["what"]:
        h.append(f'<p>{text(x["what"])}</p>')
    elif x["what"]:
        h.append('<ul class="arrows">' + "".join(f'<li class="sub">{text(w)}</li>' if w.startswith(S) else f'<li>{text(w)}</li>' for w in x["what"]) + '</ul>')
    if x["why"]:
        h.append(f'<p class="why">{text(x["why"])}</p>')
    h += x["code"]
    if x["options"]:
        h.append(f'<div class="opts" role="group" aria-label="Optionen zu {e(sid)}">')
        for L, t, bl in x["options"]:
            h.append(f'<button type="button" class="opt{" built" if bl else ""}" data-choice="{e(L)}" aria-pressed="false">'
                     f'<span class="opt-l">{e(L)}</span><span class="opt-t">{text(t)}</span><span class="opt-tags">'
                     + ('<span class="tag tag-built"><span aria-hidden="true">◆</span> gebaut</span>' if bl else "")
                     + '<span class="tag tag-mine"><span aria-hidden="true">✓</span> deine Wahl</span></span></button>')
        h.append('</div>')
    if x["note"]:
        h.append(f'<p class="note">{text(x["note"])}</p>')
    h.append('<div class="ans" aria-live="polite"></div>'
             f'<div class="fb"><label class="sr" for="n-{e(sid)}">Notiz zu {e(sid)}</label>'
             f'<textarea id="n-{e(sid)}" class="fbt" rows="2" placeholder="Notiz (Enter speichert, Umschalt+Enter neue Zeile)"></textarea>'
             '<div class="fb-row"><button type="button" class="btn save">Notiz speichern</button>'
             f'<button type="button" class="btn mic" aria-label="Halten und sprechen (Taste M)">{MIC} Halten und sprechen</button>'
             '<span class="fbs" role="status"></span></div></div></section>')
    return "".join(h)


def progress(ids, label="beantwortet"):
    return (f'<div class="prog" data-ids="{e(" ".join(ids))}" data-label="{e(label)}"><progress max="{len(ids) or 1}" value="0"></progress>'
            f'<span class="prog-t">0 von {len(ids)} {label}</span></div>')


NAV = [("index", "Übersicht"), ("next", "Nächste Frage"), (INBOX, "Eingang"), ("entschieden", "Entschieden"), ("aenderungen", "Änderungen")]


def page(slug, title, body, inbox_n, prev=None, nxt=None):
    links = "".join(f'<a href="{s}.html"{" aria-current=page" if s == slug else ""}>{e(t)}'
                    + (f' <span class="count">{inbox_n}</span>' if s == INBOX and inbox_n else "") + '</a>' for s, t in NAV)
    foot = ""
    if prev or nxt:
        foot = ('<nav class="pager" aria-label="Seiten blättern"><span>' + (f'<a href="{prev[0]}.html" rel="prev">← {text(prev[1])}</a>' if prev else "")
                + '</span><span>' + (f'<a href="{nxt[0]}.html" rel="next">{text(nxt[1])} →</a>' if nxt else "") + '</span></nav>')
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)} · Entscheidungen</title><style>{CSS}</style></head><body data-page="{slug}">'
            f'<a class="skip" href="#main">Zum Inhalt springen</a><header class="top"><nav aria-label="Hauptnavigation">{links}</nav></header>'
            f'<main id="main" tabindex="-1">{body}</main><footer>{foot}</footer>'
            '<div id="toast" role="status" aria-live="polite" hidden><span class="toast-t"></span> <button type="button" class="btn link toast-undo">Rückgängig</button></div>'
            f'{JS}</body></html>')


BULK = '''<dialog id="bulk-dlg" aria-labelledby="bulk-h"><h2 id="bulk-h">Alle Defaults dieser Gruppe so lassen?</h2>
<p>Für <b id="bulk-n"></b> Karten wird die gebaute Option als deine Wahl gespeichert, mit der Notiz „Gruppe abgenickt“.
Karten mit einer Antwort oder Notiz bleiben, wie sie sind.</p><ul id="bulk-list" class="plain"></ul>
<div class="dlg-actions"><button type="button" id="bulk-cancel" class="btn" autofocus>Abbrechen</button><button type="button" id="bulk-ok" class="btn primary">Ja, alle so lassen</button></div></dialog>'''


def write(name, s):
    with open(os.path.join(HERE, name + ".html"), "w") as f:
        f.write(s)


def main():
    ans = read_answers()
    place(ans)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    changelog(ans, now)
    log = read_log()
    for g in G:
        TITLES[g["slug"]] = g["title"]
    items = [x for g in G for x in g["items"]]
    inbox = sorted((x for x in items if x["page"] == INBOX), key=lambda x: ts(x["added"]), reverse=True)
    n_in = len(inbox)
    uniq = list({x["id"]: x for x in items}.values())
    by_stack = {k: [x for x in uniq if stack(x) == k] for k, _, _ in STACKS}

    # group pages
    for i, g in enumerate(G):
        here = [x for x in g["items"] if x["page"] == g["slug"]]
        moved = [x for x in g["items"] if x["page"] == INBOX]
        todo = [x["id"] for x in here if stack(x) in ("block", "defaults")]
        bulk = [x for x in here if stack(x) == "defaults" and built(x)]
        head = [f'<p class="crumb"><a href="index.html">Übersicht</a> · Seite {i + 1} von {len(G)}</p><h1>{text(g["title"])}</h1>',
                f'<p class="lead">{text(g["lead"])}</p>']
        if g["frozen"]:
            head.append(f'<p class="frozen">{LOCK} <b>Eingefroren</b> seit {fmt(g["frozen"])}: '
                        'hier steht schon eine Antwort von dir, neue Karten kommen in den <a href="eingang.html">Eingang</a>.</p>')
        if moved:
            head.append(f'<p class="hint"><span aria-hidden="true">→</span> {len(moved)} neue Karten zu dieser Seite liegen im <a href="eingang.html">Eingang</a>: '
                        + ", ".join(f'<a href="{href(x)}">{e(x["id"])}</a>' for x in moved) + '.</p>')
        if todo:
            head.append(progress(todo))
        if bulk:
            head.append(f'<div class="bulk"><button type="button" id="bulk" class="btn">Alle Defaults dieser Gruppe so lassen</button>'
                        f'<span class="mut">{len(bulk)} Default-Karten; Einwände gibst du auf der einzelnen Karte.</span><span id="bulk-st" role="status"></span></div>{BULK}')
        body = "".join(head) + "".join(render_item(x, ans) for x in here)
        if not here:
            body += '<p class="empty">Auf dieser Seite liegen keine Karten.</p>'
        prev = (G[i - 1]["slug"], G[i - 1]["title"]) if i else None
        nxt = (G[i + 1]["slug"], G[i + 1]["title"]) if i + 1 < len(G) else None
        write(g["slug"], page(g["slug"], g["title"], body, n_in, prev, nxt))

    # Eingang
    body = ['<p class="crumb"><a href="index.html">Übersicht</a></p><h1>Eingang</h1>',
            '<p class="lead">Neue Karten, die auf eine eingefrorene Seite gehören. Neueste zuerst; jede mit Datum und Quelle.</p>']
    ib = [x for x in inbox if stack(x) == "defaults" and built(x)]
    if inbox:
        body.append(progress([x["id"] for x in inbox if stack(x) in ("block", "defaults")]))
    if ib:
        body.append(f'<div class="bulk"><button type="button" id="bulk" class="btn">Alle Defaults im Eingang so lassen</button>'
                    f'<span class="mut">{len(ib)} Default-Karten.</span><span id="bulk-st" role="status"></span></div>{BULK}')
    body += [f'<p class="new-tag"><span class="pill st-new"><span aria-hidden="true">★</span> Neu</span> {fmt(x["added"])} · {e(x["source"])}</p>' + render_item(x, ans, home=True) for x in inbox]
    if not inbox:
        body.append('<p class="empty">Der Eingang ist leer. Neue Karten auf eingefrorenen Seiten erscheinen hier.</p>')
    write(INBOX, page(INBOX, "Eingang", "".join(body), n_in))

    # Entschieden
    done = sorted((x for x in uniq if x["status"] == "decided"), key=lambda x: ts(decided_at(x, ans) or x["added"]), reverse=True)
    idx = {x["id"]: [x["title"].replace("`", ""), href(x), x["status"]] for x in uniq}
    body = ['<p class="crumb"><a href="index.html">Übersicht</a></p><h1>Entschieden</h1>',
            f'<p class="lead">{len(done)} Karten mit Entscheidung, neueste zuerst. Die Karten stehen auch weiter auf ihrer Seite.</p>',
            '<h2 class="sec">Deine Antworten auf offene Karten</h2><p class="mut">Noch ohne DL-Eintrag; der Hauptagent trägt sie ein.</p>'
            f'<ul id="mine" class="plain list"></ul><script type="application/json" id="idx">{json.dumps(idx, ensure_ascii=False).replace("</", "<\\/")}</script>',
            '<h2 class="sec">Entschiedene Karten</h2>'] + [render_item(x, ans, home=x["page"] == INBOX) for x in done]
    write("entschieden", page("entschieden", "Entschieden", "".join(body), n_in))

    # Änderungsprotokoll
    def link(r):
        x = next((x for x in items if x["id"] == r["id"]), None)
        return f'<a href="{href(x)}">{e(r["id"])}</a>' if x else e(r["id"])

    def row(r):
        return f'<tr><td class="nw">{fmt(r["ts"])}</td><td>{link(r)}</td><td>{e(CHANGE.get(r["change"], r["change"]))}</td><td>{text(r["by"])}</td></tr>'
    rows = sorted(log, key=lambda r: ts(r["ts"]), reverse=True)
    body = ('<p class="crumb"><a href="index.html">Übersicht</a></p><h1>Änderungsprotokoll</h1>'
            '<p class="lead">Jeder Build schreibt hier, was sich an Karten geändert hat: neu, entschieden, in den Eingang verschoben. Nur anhängen, nie umschreiben. '
            'Einträge mit Datum vor dem ersten Protokoll-Build sind aus git rekonstruiert.</p>'
            + ('<div class="tablewrap"><table><thead><tr><th scope="col">Zeit</th><th scope="col">Karte</th><th scope="col">Änderung</th><th scope="col">Von</th></tr></thead><tbody>'
               + "".join(row(r) for r in rows) + '</tbody></table></div>' if rows else '<p class="empty">Noch keine Änderungen.</p>'))
    write("aenderungen", page("aenderungen", "Änderungsprotokoll", body, n_in))

    # Eine Frage auf einmal
    queue = by_stack["block"] + by_stack["defaults"]
    body = ('<h1>Eine Frage auf einmal</h1><p class="lead">Erst was Arbeit blockt, dann die gebauten Defaults. Ideen für später sind nicht dabei.</p>'
            '<div id="qbar" class="qbar"><p class="qpos" aria-live="polite">Frage <b id="qpos">–</b> in dieser Runde</p>' + progress([x["id"] for x in queue], "insgesamt beantwortet") + '</div>'
            '<p class="keys"><kbd>A</kbd> <kbd>B</kbd> <kbd>C</kbd> wählen · <kbd>Enter</kbd> speichert die Notiz · <kbd>N</kbd> nächste · <kbd>M</kbd> halten zum Sprechen</p>'
            '<div id="queue">' + "".join(render_item(x, ans, home=True).replace('<section class="card"', '<section hidden class="card"', 1) for x in queue) + '</div>'
            '<div class="qnav"><button type="button" id="qnext" class="btn primary">Überspringen</button></div>'
            '<section id="done" class="done" hidden tabindex="-1"><h2><span aria-hidden="true">✓</span> Fertig</h2><p>Jede Karte in dieser Runde hat eine Antwort oder wurde übersprungen.</p>'
            '<p id="again-p" hidden><button type="button" id="again" class="btn primary"><span id="again-n"></span> offene Karten noch einmal ansehen</button></p>'
            '<p><a href="index.html">Zur Übersicht</a> · <a href="entschieden.html">Deine Antworten</a></p></section>')
    write("next", page("next", "Nächste Frage", body, n_in))

    # Übersicht
    stacks = []
    for k, t, lead in STACKS:
        xs = by_stack[k]
        pages = {}
        for x in xs:
            pages.setdefault(x["page"], []).append(x)
        lis = "".join(f'<li><a href="{p}.html">{text(TITLES.get(p, "Eingang"))}</a> <span class="mut">{len(v)}</span></li>' for p, v in pages.items())
        stacks.append(f'<section class="stack" aria-labelledby="s-{k}"><h2 id="s-{k}"><span class="stack-n">{len(xs)}</span> {t}</h2><p class="mut">{lead}</p>'
                      + (progress([x["id"] for x in xs]) if k != "ideas" else progress([x["id"] for x in xs], "mit Notiz oder Wahl"))
                      + (f'<ul class="plain list">{lis}</ul>' if lis else '<p class="empty">Nichts hier.</p>') + '</section>')
    news = "".join(f'<li><time>{fmt(r["ts"])}</time> {link(r)} · {e(CHANGE.get(r["change"], r["change"]))}</li>' for r in rows[:8])
    trs = []
    for i, g in enumerate(G):
        c = {s: 0 for s in LABEL}
        for x in g["items"]:
            if x["page"] == g["slug"]:
                c[x["status"]] += 1
        fz = f'<span class="mut">{LOCK} eingefroren</span>' if g["frozen"] else ""
        trs.append(f'<tr><td>{i + 1}</td><td><a href="{g["slug"]}.html">{text(g["title"])}</a> {fz}</td>' + "".join(f'<td class="n">{c[s] or ""}</td>' for s in ("open", "default", "parked", "decided")) + '</tr>')
    trs.append(f'<tr><td></td><td><a href="eingang.html">Eingang</a></td>' + "".join(f'<td class="n">{sum(1 for x in inbox if x["status"] == s) or ""}</td>' for s in ("open", "default", "parked", "decided")) + '</tr>')
    tot = {s: sum(1 for x in items if x["status"] == s) for s in LABEL}
    body = (f'<h1>Deine Entscheidungen zu BEAML</h1><p class="lead">Stand {fmt(now)}. {len(items)} Karten auf {len(G)} Seiten und im Eingang. Quelle: <code>owner-review.md</code>, Register D037.</p>'
            f'<div class="hero"><a class="btn primary big" href="next.html">Nächste Frage beantworten</a><span class="mut"><b data-left="{e(" ".join(x["id"] for x in queue))}">{len(queue)}</b> Karten warten auf dich</span></div>'
            '<div class="stacks">' + "".join(stacks) + '</div>'
            f'<div class="duo"><section aria-labelledby="h-in"><h2 id="h-in" class="sec">Eingang</h2>'
            + (f'<p><a href="eingang.html"><b>{n_in}</b> neue Karten</a> für eingefrorene Seiten.</p>' if n_in else '<p class="empty">Der Eingang ist leer.</p>')
            + f'<h2 class="sec">Entschieden</h2><p><a href="entschieden.html"><b>{len(done)}</b> Karten entschieden</a>, dazu deine Antworten.</p></section>'
            f'<section aria-labelledby="h-news"><h2 id="h-news" class="sec">Was ist neu</h2>'
            + (f'<ul class="plain list news">{news}</ul>' if news else '<p class="empty">Noch keine Änderungen.</p>')
            + '<p><a href="aenderungen.html">Ganzes Änderungsprotokoll</a></p></section></div>'
            '<h2 class="sec">Alle Seiten</h2><div class="tablewrap"><table><thead><tr><th scope="col">#</th><th scope="col">Seite</th>'
            + "".join(f'<th scope="col" class="n">{pill(s)}</th>' for s in ("open", "default", "parked", "decided")) + '</tr></thead><tbody>' + "".join(trs)
            + f'</tbody><tfoot><tr><td></td><th scope="row">Summe</th>' + "".join(f'<td class="n">{tot[s]}</td>' for s in ("open", "default", "parked", "decided")) + '</tr></tfoot></table></div>'
            '<p class="mut">Status: ' + " · ".join(pill(s) for s in LABEL) + '. <span aria-hidden="true">◆</span> gebaut = so steht es heute im Code. Eingefroren = die Seite bekommt keine neuen Karten mehr.</p>')
    write("index", page("index", "Übersicht", body, n_in, None, (G[0]["slug"], G[0]["title"])))
    counts = {k: len(v) for k, v in by_stack.items()}
    print(f"{len(G)} pages, {len(items)} items, inbox {n_in}", tot, counts, "decided", len(done))


if __name__ == "__main__":
    main()
