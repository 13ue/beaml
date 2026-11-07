"""EXPERIMENT 0005 prerequisite P4a: the DB TRANSPORTS db.put, db.get, db.list (DL-127, DL-129, DL-143, 0005 Q5-1 to Q5-10).

Ledger: experiments/0004-generated-replay/workflow/2026-11-07/db-transport/ (plan.md with "Plan repair" and "Plan repair 2",
decisions.md PDB-01 to PDB-36 and QDB-1 to QDB-8, plan-review.md, red-plan.md, red-output.md). P4b (`--stored` over
rows.jsonl, N17 to N27) is a later RED; only N25b (the list-item literal check, M-a) stands here.
Defaults pinned here (all open for the OWNER): QDB-1 A (the db.get key is the one String field of the key TYPE), QDB-2 A
with PDB-30 (BeamlDb.put/3 with `{type, version}` and one JSON encoder: JSON binaries both ways), QDB-3 A (newest row
wins), QDB-4 A (one bad row fails the list), QDB-5 A (db call records in "responses"), QDB-6b (v3 words: `accepted`, or
`rejected` with `transport | decode | constructor | not_found`), PDB-18 (`items.<i>.<field>`), PDB-20 (no Http module).
Expected values come from the plan, DL-143 and this file's own digest and fingerprint code (`stored_types_test`),
never from the new compiler. The fake BeamlDb (PDB-10, PDB-30) stores and returns the JSON binary as given.
Not here: the host-side `jsonb_typeof(value->'reason') = 'null'` tie (0005 N2c, Postgres only).

Byte guard (N13). Five pin sites hold the bytes of every existing source; P4 moves none of them (plan "Byte changes"):
  1. tests/slice5_syntax_test.py PIN
  2. tests/slice6_pipe_test.py EFFECT_OUTPUTS (also read by slice6_struct_order_test.py)
  3. tests/slice6_host_struct_test.py BYTE_GUARD
  4. slice6/effect-reach/byte-guard.json (the (71, 40) setup invariant)
  5. tests/slice6_entry_test.py BASE (N13 of slice 6d)
A GREEN that must change an existing byte stops and reports a blocker; a re-pin moves all five together.
N13 here compares every tracked source without a db EFFECT against P4_BASE. P4_BASE is the HEAD at this RED; P2 and P3
GREEN change bytes first, so the P4 GREEN worker sets P4_BASE to the commit it starts from (after P2 and P3 TEST).

Depends on P2 (v3 key names, `accepted`/`rejected`, the v3 `--stored` reader) and P3/P5 (several EFFECTS per source,
`Replay.run(operation, a0, trace_id, records)`, module `Orders` from the stem): see red-plan.md, "Dependencies".
Run: python3 -B experiments/0004-generated-replay/tests/slice6_db_test.py [-k NAME]
Scratch compiler: BEAML_SPIKE=<git archive HEAD build>/target/debug/beaml-spike (other workers write main.rs).
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from arm_tree import EXPERIMENT, REPO  # noqa: E402
import slice5_syntax_test as s5  # noqa: E402
import slice6_entry_test as se  # noqa: E402
import slice6_record_test as sr  # noqa: E402
import stored_types_test as st  # noqa: E402

P4_BASE = "ce190054"  # the multi-effect GREEN commit; P4a GREEN moves it to its own commit (see the docstring)
FIX = EXPERIMENT / "slice6" / "db"
ORDERS = FIX / "orders.beaml"
PLAIN, PLAIN_V2, TWO_ROWS = FIX / "plain" / "orders.beaml", FIX / "plain_v2" / "orders.beaml", FIX / "two_rows" / "orders.beaml"
ORDER_V2, NO_APP = FIX / "order_v2" / "orders.beaml", FIX / "no_app" / "orders.beaml"
BAD = FIX / "bad"
STORED = ["--stored", str(FIX / "stored" / "responses.jsonl")]  # empty, with an empty rows.jsonl beside it (PDB-23)
EMPTY = ["--stored", str(EXPERIMENT / "stored" / "empty.jsonl")]
GRAMMAR = REPO / "integrations" / "zed-beaml"
TREE_SITTER = os.environ.get("TREE_SITTER", "/private/tmp/beaml-zed-highlighting/tools/tree-sitter")
ex, b = sr.ex, sr.b

# DL-143 core (the P2 names, PDB-01): 14 keys in every ROW CORE; a db call record adds `request` (PDB-17).
CORE = sorted(["version", "trace_id", "span_id", "artifact_id", "operation", "attempt", "type", "value", "value_sha256",
               "redacted", "unknown_keys", "unknown_fields", "outcome", "reason"])
DB_RECORD = sorted(CORE + ["request"])


def type_of(name, version, fields):
    """The `type` of a record: fields in source order, fingerprint over the sorted fields (as the ENTRY RECORD)."""
    text = json.dumps(sorted(fields), separators=(",", ":"))
    return {"name": name, "version": version, "fields": fields, "fingerprint": hashlib.sha256(text.encode()).hexdigest()}


ORDER_TYPE = type_of("Order", 1, [["order_id", "String"], ["amount", "Amount"], ["channel", "Channel"]])
LIST_TYPE = type_of("OrderList", 1, [["items", "[Order]"]])  # PDB-08: the field TYPE text is [Order]
PLAIN_V1 = type_of("Order", 1, [["order_id", "String"], ["label", "String"]])
PLAIN_V2_TYPE = type_of("Order", 2, [["order_id", "String"], ["label", "String"], ["note", "String"]])
EUR = {"value": "12.50", "currency": "EUR"}
WIRE1 = {"order_id": "order-1", "amount": EUR, "channel": "web"}
WIRE2 = dict(WIRE1, order_id="order-2")
TV_WIRE = {"order_id": "order-tv", "amount": EUR, "channel": "tv"}


def core(value, type_=ORDER_TYPE, unknown_fields=(), operation="orders.save"):
    """A ROW CORE as PDB-14 with the v3 words (O1): written on success only, so `accepted` with reason null."""
    return {"version": 3, "trace_id": "", "span_id": "", "artifact_id": "", "operation": operation, "attempt": 1,
            "type": type_, "value": value, "value_sha256": st.value_sha256(value), "redacted": [], "unknown_keys": [],
            "unknown_fields": list(unknown_fields), "outcome": "accepted", "reason": None}


def jb(term):
    """A JSON term as the Elixir binary that BeamlDb holds (PDB-30)."""
    return b(json.dumps(term, separators=(",", ":")).encode())


def changed(path, value, rehash=False):
    """GOOD_CORE with one key set; `rehash` recomputes the digest so only the named fault stays."""
    out = copy.deepcopy(GOOD_CORE)
    node = out
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    if rehash:
        out["value_sha256"] = st.value_sha256(out["value"])
    return out


GOOD_CORE = core(WIRE1)
# N6 (PDB-15): each fault alone. The digest fault keeps order_id, so db.get still finds the row by its key.
FAULTS = {
    "digest": (changed(["value", "amount", "value"], "99.00"), "decode"),
    "type_name": (changed(["type", "name"], "Payment"), "decode"),
    "type_version": (changed(["type", "version"], 7), "decode"),
    "fingerprint": (changed(["type", "fingerprint"], "0" * 64), "decode"),
    "constructor": (changed(["value", "amount", "currency"], "", rehash=True), "constructor"),
}

# The fake host store (PDB-10, PDB-30): rows newest first; the JSON binary is stored and returned as given. Every call
# is logged before its mode decides the result. Modes: :ok, :down, :raise, :exit, :junk, :okjunk, :forbid (N11).
BEAMLDB = r'''
defmodule BeamlDb do
  def start, do: Agent.start_link(fn -> {[], []} end, name: __MODULE__)
  def reset, do: Agent.update(__MODULE__, fn _ -> {[], []} end)
  def rows, do: Agent.get(__MODULE__, &elem(&1, 0))
  def calls, do: Agent.get(__MODULE__, &elem(&1, 1))
  def mode(m), do: :persistent_term.put(:beaml_db_mode, m)

  def seed(type, version, value) do
    Agent.update(__MODULE__, fn {rows, log} ->
      {[%{"id" => length(rows) + 1, "type" => type, "version" => version, "value" => value} | rows], log}
    end)
  end

  defp call(row, ok) do
    Agent.update(__MODULE__, fn {rows, log} -> {rows, log ++ [row]} end)

    case :persistent_term.get(:beaml_db_mode, :ok) do
      :ok -> ok.()
      :down -> {:error, "down"}
      :raise -> raise "db down"
      :exit -> exit(:noproc)
      :junk -> :what
      :okjunk -> {:ok, :what}
      :forbid -> raise "BeamlDb called in a REPLAY RUN"
    end
  end

  defp out(row), do: Map.take(row, ["id", "version", "value"])

  defp field(row, key) do
    try do
      get_in(:json.decode(row["value"]), ["value", key])
    rescue
      _ -> nil
    end
  end

  def put(table, {type, version} = head, json) do
    call({:db, :put, table, head, json}, fn ->
      seed(type, version, json)
      {:ok, length(rows())}
    end)
  end

  def get(table, type, key) do
    call({:db, :get, table, type, key}, fn ->
      found = Enum.find(rows(), fn r -> r["type"] == type and Enum.all?(key, fn {k, v} -> field(r, k) == v end) end)
      {:ok, found && out(found)}
    end)
  end

  def list(table, type, query) do
    call({:db, :list, table, type, query}, fn -> {:ok, for(r <- rows(), r["type"] == type, do: out(r))} end)
  end
end
'''
# Structs through struct/2 at run time: a missing module fails its case, not the whole script.
HELPERS = r'''
{:ok, _} = BeamlDb.start()
rt = fn term -> term |> :json.encode() |> IO.iodata_to_binary() |> :json.decode() end
fresh = fn ->
  BeamlDb.mode(:ok)
  BeamlDb.reset()
  Process.put(:log, [])
  Process.put(:captures, [])
end
log = fn -> Process.get(:log, []) end
resp = fn -> for {"responses", r} <- Process.get(:captures, []), do: rt.(r) end
puts = fn -> for {:db, :put, t, h, j} <- BeamlDb.calls(), do: {t, h, j} end
last_core = fn -> {_, _, j} = List.last(puts.()); :json.decode(j) end
fail = fn r -> {:error, struct(Orders.StoreError, reason: r)} end
amount = fn v -> struct(Orders.Amount, value: v, currency: "EUR") end
o1 = fn -> %{"order_id" => "order-1", "amount" => amount.("12.50"), "channel" => {"Channel", "Web", []}} end
o2 = fn -> %{"order_id" => "order-2", "amount" => amount.("12.50"), "channel" => {"Channel", "Web", []}} end
tv = fn -> %{"order_id" => "order-tv", "amount" => amount.("12.50"), "channel" => {"Channel", "Unknown", ["tv"]}} end
key1 = %{"order_id" => "order-1"}
'''
TAIL = r'''
for {name, check} <- cases do
  {ok, got} =
    try do
      got = check.()
      {got == true, inspect(got)}
    rescue
      e -> {false, Exception.format_banner(:error, e) |> String.split("\n") |> hd()}
    catch
      kind, value -> {false, inspect({kind, value})}
    end

  IO.puts("#{name} #{if ok, do: "PASS", else: "FAIL"}")
  if not ok, do: IO.puts("  got #{name}: #{got}")
end
'''
TRANSPORT = 'fail.("transport")'
ORDERS_CASES = {
    # N2 (PDB-14, PDB-30): one put with the head {"Order", 1} and a JSON binary; the decoded core has the v3 core.
    "N2_save_returns_its_input": "fresh.(); Orders.save(o1.()) == {:ok, o1.()}",
    "N2_one_put_with_a_json_binary": ('fresh.(); Orders.save(o1.()); '
                                      'match?([{"records", {"Order", 1}, j}] when is_binary(j), puts.())'),
    "N2_core_key_set": "fresh.(); Orders.save(o1.()); Enum.sort(Map.keys(last_core.())) == %s" % ex(CORE),
    "N2_core_values": ("fresh.(); Orders.save(o1.()); Map.drop(last_core.(), %s) == %s"
                       % (ex(["trace_id", "span_id", "artifact_id"]),
                          ex({k: v for k, v in GOOD_CORE.items() if k not in ("trace_id", "span_id", "artifact_id")}))),
    "N2_reason_is_json_null": 'fresh.(); Orders.save(o1.()); last_core.()["reason"] == :null',
    # N3 (PDB-13): the keep-value variant is written as its String and named in unknown_fields.
    "N3_kept_value": ('fresh.(); Orders.save(tv.()); Map.take(last_core.(), ["value", "value_sha256", "unknown_fields"]) '
                      "== %s" % ex({"value": TV_WIRE, "value_sha256": st.value_sha256(TV_WIRE),
                                    "unknown_fields": ["channel"]})),
    # N4 (PDB-13 round trip): host order (newest first); Unknown("tv") comes back as the tuple.
    "N4_list_round_trip": ("fresh.(); Orders.save(o1.()); Orders.save(o2.()); Orders.save(tv.()); "
                           'Orders.list_orders(%{}) == {:ok, %{"items" => [tv.(), o2.(), o1.()]}}'),
    "N4_list_call": ('fresh.(); Orders.list_orders(%{}); '
                     'Enum.member?(BeamlDb.calls(), {:db, :list, "records", "Order", %{}})'),
    # N6 control: the test-built core decodes, so the reject cases below cannot pass by rejecting every row.
    "N6_control_built_core_lists": ('fresh.(); BeamlDb.seed("Order", 1, %s); '
                                    'Orders.list_orders(%%{}) == {:ok, %%{"items" => [o1.()]}}' % jb(GOOD_CORE)),
    "N6_control_built_core_loads": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.load(key1) == {:ok, o1.()}'
                                    % jb(GOOD_CORE)),
    # N6 (PDB-15, O2): a core that is no JSON map, or a value that is no binary, is a decode failure.
    "N6_list_core_not_a_map": 'fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}) == fail.("decode")' % b(b"[1]"),
    "N6_list_core_not_json": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}) == fail.("decode")'
                              % b(b"not json")),
    "N6_list_value_not_a_binary": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}) == fail.("decode")'
                                   % ex(GOOD_CORE)),
    # QDB-4 A: one bad row fails the whole list, also behind a good newer row.
    "QDB4_one_bad_row_fails_the_list": ('fresh.(); BeamlDb.seed("Order", 1, %s); BeamlDb.seed("Order", 1, %s); '
                                        'Orders.list_orders(%%{}) == fail.("decode")'
                                        % (jb(FAULTS["digest"][0]), jb(GOOD_CORE))),
    # N7 (QDB-1 A): the key is the one String field of OrderKey; no row is not_found.
    "N7_get": "fresh.(); Orders.save(o1.()); Orders.load(key1) == {:ok, o1.()}",
    "N7_get_call": ('fresh.(); Orders.load(key1); '
                    'Enum.member?(BeamlDb.calls(), {:db, :get, "records", "Order", %{"order_id" => "order-1"}})'),
    "N7_not_found": 'fresh.(); Orders.save(o1.()); Orders.load(%{"order_id" => "none"}) == fail.("not_found")',
    # QDB-3 A: several rows with one key, the newest wins.
    "QDB3_newest_row_wins": ('fresh.(); Orders.save(o1.()); newer = Map.put(o1.(), "amount", amount.("99.00")); '
                             "Orders.save(newer); Orders.load(key1) == {:ok, newer}"),
    # N9: client spans per call; a failure sets the attribute reason in its span.
    "N9_save_span": ('fresh.(); Orders.save(o1.()); '
                     'Enum.member?(log.(), {:span, "orders.orders.save", :client, "order-1", nil})'),
    "N9_load_span": ('fresh.(); Orders.load(key1); '
                     'Enum.member?(log.(), {:span, "orders.orders.load", :client, "order-1", nil})'),
    "N9_list_span": ('fresh.(); Orders.list_orders(%{}); '
                     'Enum.member?(log.(), {:span, "orders.orders.list", :client, nil, nil})'),
    "N9_failure_sets_reason": ('fresh.(); BeamlDb.mode(:down); Orders.save(o1.()); BeamlDb.mode(:ok); '
                               'Enum.member?(log.(), {:attr, :reason, "transport", "orders.orders.save"})'),
    # N10 (QDB-5 A, PDB-17, QDB-6b): one "responses" record per db call, the v3 core plus request.
    "N10_save_record": ('fresh.(); Orders.save(o1.()); [r] = resp.(); '
                        '{Enum.sort(Map.keys(r)), Map.take(r, ["operation", "value", "request", "outcome", "reason"]), '
                        'r["value_sha256"] == last_core.()["value_sha256"]} == {%s, %s, true}'
                        % (ex(DB_RECORD), ex({"operation": "orders.save", "value": WIRE1, "request": WIRE1,
                                              "outcome": "accepted", "reason": None}))),
    "N10_load_record": ('fresh.(); Orders.save(o1.()); Process.put(:captures, []); Orders.load(key1); [r] = resp.(); '
                        'Map.take(r, ["operation", "value", "request", "outcome"]) == %s'
                        % ex({"operation": "orders.load", "value": WIRE1, "request": {"order_id": "order-1"},
                              "outcome": "accepted"})),
    "N10_list_record": ('fresh.(); Orders.save(o1.()); Orders.save(tv.()); Process.put(:captures, []); '
                        'Orders.list_orders(%%{}); [r] = resp.(); '
                        'Map.take(r, ["operation", "value", "request", "unknown_fields", "outcome", "value_sha256"]) == %s'
                        % ex({"operation": "orders.list", "value": {"items": [TV_WIRE, WIRE1]}, "request": {},
                              "unknown_fields": ["items.0.channel"], "outcome": "accepted",
                              "value_sha256": st.value_sha256({"items": [TV_WIRE, WIRE1]})})),
    "N10_transport_record": ('fresh.(); BeamlDb.mode(:down); Orders.save(o1.()); BeamlDb.mode(:ok); [r] = resp.(); '
                             'Map.take(r, ["value", "outcome", "reason"]) == %s'
                             % ex({"value": None, "outcome": "rejected", "reason": "transport"})),
    "N10_not_found_record": ('fresh.(); Orders.load(key1); [r] = resp.(); Map.take(r, ["value", "outcome", "reason"]) '
                             "== %s" % ex({"value": None, "outcome": "rejected", "reason": "not_found"})),
    "N10_decode_record": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}); [r] = resp.(); '
                          'Map.take(r, ["value", "outcome", "reason"]) == %s'
                          % (jb(FAULTS["digest"][0]), ex({"value": None, "outcome": "rejected", "reason": "decode"}))),
    # N11 (PDB-19, PDB-29): the REPLAY RUN reads the records through JSON and never calls BeamlDb.
    "N11_replay_save": ('fresh.(); live = Orders.save(o1.()); recs = resp.(); BeamlDb.reset(); BeamlDb.mode(:forbid); '
                        'r = Orders.Replay.run("orders.save", o1.(), hd(recs)["trace_id"], recs); BeamlDb.mode(:ok); '
                        "{r, BeamlDb.calls(), live} == {live, [], {:ok, o1.()}}"),
    "N11_replay_list": ('fresh.(); Orders.save(o1.()); Orders.save(tv.()); Process.put(:captures, []); '
                        "live = Orders.list_orders(%{}); recs = resp.(); BeamlDb.reset(); BeamlDb.mode(:forbid); "
                        'r = Orders.Replay.run("orders.list", %{}, hd(recs)["trace_id"], recs); BeamlDb.mode(:ok); '
                        '{r, BeamlDb.calls(), live} == {live, [], {:ok, %{"items" => [tv.(), o1.()]}}}'),
    "N11_replay_load": ('fresh.(); Orders.save(o1.()); Process.put(:captures, []); Orders.load(key1); recs = resp.(); '
                        'BeamlDb.reset(); BeamlDb.mode(:forbid); '
                        'r = Orders.Replay.run("orders.load", key1, hd(recs)["trace_id"], recs); BeamlDb.mode(:ok); '
                        "{r, BeamlDb.calls()} == {{:ok, o1.()}, []}"),
    "N11_rejected_record_replays_its_reason": (
        'fresh.(); BeamlDb.mode(:down); Orders.save(o1.()); recs = resp.(); BeamlDb.mode(:forbid); '
        'r = Orders.Replay.run("orders.save", o1.(), hd(recs)["trace_id"], recs); BeamlDb.mode(:ok); '
        "r == %s" % TRANSPORT),
    "N11_operation_mismatch": ('fresh.(); Orders.save(o1.()); recs = resp.(); '
                               'Orders.Replay.run("orders.load", o1.(), hd(recs)["trace_id"], recs) == '
                               "{:error, :operation_mismatch}"),
}
for _name, (_core, _reason) in FAULTS.items():
    ORDERS_CASES["N6_list_%s" % _name] = ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}) == fail.(%s)'
                                          % (jb(_core), ex(_reason)))
    ORDERS_CASES["N6_load_%s" % _name] = ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.load(key1) == fail.(%s)'
                                          % (jb(_core), ex(_reason)))
# N8 (PDB-12): every host error, other shape, raise and exit is reason "transport"; the process lives; no row is added.
for _mode in ("down", "raise", "exit", "junk", "okjunk"):
    ORDERS_CASES["N8_%s_is_transport" % _mode] = (
        "fresh.(); BeamlDb.mode(:%s); r = [Orders.save(o1.()), Orders.load(key1), Orders.list_orders(%%{})]; "
        "BeamlDb.mode(:ok); {r, BeamlDb.rows(), Process.alive?(self())} == {List.duplicate(%s, 3), [], true}"
        % (_mode, TRANSPORT))

PLAIN_ROW = {"order_id": "order-1", "label": "first"}
PLAIN_CASES = {
    # N5 control: the v1 writer gives the TYPE and digest that the test builds for its v1 row.
    "N5_control_v1_writes_the_built_type": ('fresh.(); Orders.save(%s); Map.take(last_core.(), ["type", "value", '
                                            '"value_sha256"]) == %s'
                                            % (ex(PLAIN_ROW), ex({k: v for k, v in core(PLAIN_ROW, PLAIN_V1).items()
                                                                  if k in ("type", "value", "value_sha256")}))),
}
V1_ROW = core(PLAIN_ROW, PLAIN_V1)
V3_ROW = {"order_id": "order-3", "label": "third", "note": ""}
MIGRATED = {"order_id": "order-1", "label": "first", "note": ""}
PLAIN_V2_CASES = {
    # N5 (DL-127 lazy read): a v1 row decodes through the MIGRATE CHAIN; the stored row keeps version 1 and its core.
    "N5_v1_row_migrates_on_read": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}) == '
                                   '{:ok, %%{"items" => [%s]}}' % (jb(V1_ROW), ex(MIGRATED))),
    "N5_row_stays_v1": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.list_orders(%%{}); '
                        'BeamlDb.rows() == [%%{"id" => 1, "type" => "Order", "version" => 1, "value" => %s}]'
                        % (jb(V1_ROW), jb(V1_ROW))),
    "N5_save_writes_v2": ('fresh.(); Orders.save(%s); [{_, head, _}] = puts.(); '
                          '{head, Map.take(last_core.(), ["type", "value"])} == {{"Order", 2}, %s}'
                          % (ex(V3_ROW), ex({"type": PLAIN_V2_TYPE, "value": V3_ROW}))),
    "N5_list_holds_both_versions": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.save(%s); '
                                    'Orders.list_orders(%%{}) == {:ok, %%{"items" => [%s, %s]}}'
                                    % (jb(V1_ROW), ex(V3_ROW), ex(V3_ROW), ex(MIGRATED))),
    "N5_load_migrates": ('fresh.(); BeamlDb.seed("Order", 1, %s); Orders.load(%%{"order_id" => "order-1"}) == {:ok, %s}'
                         % (jb(V1_ROW), ex(MIGRATED))),
}


def fourth_kind():
    return ("unsupported effect kind: db.query in effect orders.save (supported: http.post, db.put, db.get, db.list)\n"
            '  help: write http.post("path"), db.put("records"), db.get("records") or db.list("records")')


def d6b_39(kind, owner, field, help_tail=""):
    """The built D6B-39 texts (main.rs HEAD effects(), PDB-31), with the db EFFECT as owner."""
    return ("error: effect orders.save: the %s field %s.%s cannot stand in a TYPE with a MIGRATE CHAIN or a VERSION MARK "
            "in slice 6b (D6B-39)\n  help: remove the MIGRATE CHAIN and the VERSION MARK of %s%s"
            % (kind, owner, field, owner, help_tail))


# N12: the Checks table of plan.md (after "Plan repair": the D6B-39 texts replace the MIGRATE CHANGE row).
BAD_CASES = {
    "fourth_kind": fourth_kind(),
    "table": 'error: effect orders.save: db.put uses the table "records" only (DL-127)',
    "put_head": "error: effect orders.save: db.put returns its input TYPE; write Order -> Order",
    "get_key": "error: effect orders.load: db.get takes a key TYPE with one String field (QDB-1)",
    "get_key_field": "error: effect orders.load: the key field name of ByName is not a String field of Order (QDB-1)",
    "list_query": "error: effect orders.list: db.list takes a query TYPE with no fields (Q5-2)",
    "list_output": ("error: effect orders.list: db.list returns a TYPE with one field of a LIST TYPE, for example "
                    "type OrderList { items: [Order] } (Q5-3)"),
    "list_elsewhere": "error: the LIST TYPE [Order] of Basket.items stands only as the field of a db.list output TYPE (Q5-3)",
    "list_element": "error: the LIST TYPE [String] needs a record TYPE inside the brackets",
    "row_constructor": ("error: effect tickets.save: the ROW TYPE Ticket has a constructor; a row holds a plain record "
                        "(PDB-06)"),
    "row_redacted": ("error: effect orders.save: the ROW TYPE Order has the redacted field card_holder; rows hold no "
                     "redacted field yet (M3, DL-116)"),
    "row_enum_no_keep": ("error: effect orders.save: the enum Channel of Order.channel has no keep-value variant (DL-065)\n"
                         "  help: add the variant Unknown(String) to enum Channel"),
    "row_enum_no_literals": ("error: effect orders.save: the enum Channel of Order.channel has no ENUM LITERALS; a row "
                             "stores an enum by its literal (PDB-07)"),
    "row_enum_chain": d6b_39("enum", "Order", "channel", ", or make channel a String field"),
    "row_constructor_chain": d6b_39("constructor", "Order", "amount"),
}
# S13 of slice6_pipe_test.py changes with P4 (plan "Existing assertions that change"): db.get is a KIND now.
S13 = (EXPERIMENT / "bad" / "unsupported_effect_kind.beaml",
       'error: effect payments.authorize: db.get uses the table "records" only (DL-127)')

# N25b (M-a, PDB-18, PDB-33): a stored orders.list record; item 0 holds the literal "app" that no_app/ lost.
LITERAL_BLOCK = ("error: TYPE Order v1: 1 stored RESPONSE RECORD of operation orders.list has a value of field channel "
                 "that is no ENUM LITERAL of Channel now (DL-122)\n"
                 "  record source: %s:1 (line 1)\n"
                 "  help: declare the fate in a MIGRATE STEP (DL-122); slice 6b has no MIGRATE STEP form for an enum field "
                 "(D6B-39), so restore the removed or changed ENUM LITERAL of Channel")


def list_record(channel, unknown_fields=()):
    items = {"items": [{"order_id": "order-app", "amount": EUR, "channel": channel}]}
    return dict(core(items, LIST_TYPE, unknown_fields, "orders.list"), request={})


class Slice6Db(unittest.TestCase):
    maxDiff = None
    setUp = se.Slice6Entry.setUp

    def compile(self, source, extra=STORED, binary=None):
        """N14: events hold no path, no source text, no stored value (the 6d check) and no transport call."""
        code, stdout, stderr = se.Slice6Entry.compile(self, source, extra, binary)
        log = self.work / "cwd" / ".beaml" / "actions.jsonl"
        if log.is_file():
            self.assertNotIn("db.put(", log.read_text(), "action events must not record source text")
        return code, stdout, stderr

    def built(self, source, extra=STORED):
        code, stdout, stderr = self.compile(source, extra)
        self.assertEqual((0, True), (code, "defmodule Orders do" in stdout),
                         "expected exit 0 and the module Orders on stdout; stderr: " + stderr)
        return stdout

    def runtime(self, source, cases):
        stdout = self.built(source)
        out, beam = se.Slice6Entry.elixirc(self, stdout, ("beamldb.ex", BEAMLDB))
        self.assertEqual(0, beam.returncode, "setup: elixirc failed:\n" + beam.stdout + beam.stderr)
        listed = ",\n".join('  {"%s", fn -> %s end}' % (name, check) for name, check in cases.items())
        (out / "checks.exs").write_text(HELPERS + "\ncases = [\n" + listed + "\n]\n" + TAIL)
        run = subprocess.run(["elixir", "-pa", str(out), str(out / "checks.exs")], capture_output=True, text=True,
                             timeout=180)
        self.assertEqual(0, run.returncode, "setup: checks.exs did not run:\n" + run.stdout + run.stderr)
        results = dict(line.rsplit(" ", 1) for line in run.stdout.splitlines() if line.endswith((" PASS", " FAIL")))
        for name in cases:
            with self.subTest(name):
                self.assertEqual("PASS", results.get(name), run.stdout)

    # N1 (first RED): the three transports and the LIST TYPE build; no Http module (PDB-20).

    def test_N1_db_source_builds(self):
        stdout = self.built(ORDERS)
        for want in ("def orders_save(", "def orders_load(", "def orders_list(", "def ui_orders(",
                     "defmodule Replay do"):
            with self.subTest(want):
                self.assertIn(want, stdout)
        with self.subTest("PDB-20 no Http module"):
            self.assertEqual((False, False), ("defmodule Http do" in stdout, "BeamlSpike" in stdout))

    def test_N1b_variants_build(self):
        for source in (PLAIN, PLAIN_V2, TWO_ROWS, NO_APP):
            with self.subTest(str(source.relative_to(FIX))):
                self.built(source)

    # N2 to N4, N6 to N11: the runtime over the fake BeamlDb.

    def test_N2_to_N11_orders_runtime(self):
        self.runtime(ORDERS, ORDERS_CASES)

    def test_N5_control_plain_v1_writer(self):
        self.runtime(PLAIN, PLAIN_CASES)

    def test_N5_migrate_chain_on_read(self):
        self.runtime(PLAIN_V2, PLAIN_V2_CASES)

    # N12: compile rejects, exact texts (plan Checks table, Plan repair O3).

    def assert_rejected(self, source, message):
        code, stdout, stderr = self.compile(source)
        self.assertEqual((1, "", message), (code, stdout, stderr.strip()), "expected exit 1, no stdout, the exact text")

    def test_N12_rejects(self):
        self.assertEqual(sorted(BAD_CASES), sorted(p.stem for p in BAD.glob("*.beaml")), "setup: bad/ and the table differ")
        for name, message in BAD_CASES.items():
            with self.subTest(name):
                self.assert_rejected(BAD / ("%s.beaml" % name), message)

    def test_N12_order_v2_chain_with_constructor_and_enum_fields(self):
        # PDB-31: D6B-39 holds for ROW TYPES. Default: the first db EFFECT in source order, first field (amount).
        self.assert_rejected(ORDER_V2, d6b_39("constructor", "Order", "amount"))

    def test_N12_s13_db_get_is_a_kind_now(self):
        self.assert_rejected(*S13)

    # N13 (guard, passes before and after): every tracked source without a db EFFECT keeps exit, stdout and stderr.

    def test_N13_sources_without_a_db_effect_keep_their_bytes(self):
        listed = subprocess.run(["git", "-C", str(REPO), "ls-files", "experiments/0001-syntax-to-beam/*.beaml",
                                 "experiments/0002-http-correlation/apps/*.beaml",
                                 "experiments/0004-generated-replay/arms/*.beaml",
                                 "experiments/0004-generated-replay/slice*/*.beaml",
                                 "experiments/0004-generated-replay/drift/*.beaml",
                                 "experiments/0004-generated-replay/bad/*.beaml"],
                                capture_output=True, text=True, check=True).stdout.split()
        sources = [REPO / p for p in listed if not re.search(r"= *db\.\w+\(|: *\[", (REPO / p).read_text())]
        self.assertGreater(len(sources), 100, "setup: too few tracked sources")
        base = s5.compiler_at(P4_BASE)
        for path in sources:
            with self.subTest(str(path.relative_to(REPO))):
                self.assertEqual(self.compile(path, EMPTY, base), self.compile(path, EMPTY))

    # N15: fmt keeps the fixtures; [Order] keeps its bytes; the db EFFECT lines align as one group.

    def fmt(self, data):
        path = self.work / "fmt" / "orders.beaml"
        path.parent.mkdir(exist_ok=True)
        path.write_text(data)
        result = subprocess.run([st.compiler(), "fmt", str(path)], cwd=self.work / "cwd", capture_output=True,
                                text=True, timeout=se.TIMEOUT)
        return result.returncode, path.read_text(), result.stderr

    def test_N15_fmt_keeps_the_fixtures(self):
        for source in (ORDERS, PLAIN, PLAIN_V2, TWO_ROWS, NO_APP):
            with self.subTest(str(source.relative_to(FIX))):
                code, after, stderr = self.fmt(source.read_text())
                self.assertEqual((0, source.read_text()), (code, after), stderr)

    def test_N15b_fmt_aligns_the_db_effect_lines(self):
        text = ORDERS.read_text()
        spaced = re.sub(r"^(effect orders\.\w+) +(\w+) +-> +(\w+) +! +StoreError +=", r"\1 \2 -> \3 ! StoreError =",
                        text, flags=re.M)
        self.assertNotEqual(text, spaced, "setup: the fixture lost its aligned db EFFECT lines")
        code, after, stderr = self.fmt(spaced)
        self.assertEqual((0, text), (code, after), stderr)

    # N16: the grammar has a list_type rule, a corpus case and a highlight for the brackets.

    def test_N16_grammar_list_type(self):
        grammar = (GRAMMAR / "grammar.js").read_text()
        highlights = (GRAMMAR / "languages" / "beaml" / "highlights.scm").read_text()
        with self.subTest("grammar.js"):
            self.assertRegex(grammar, r'list_type: \(\$\) => seq\("\[", \$\.type, "\]"\)')
        with self.subTest("corpus"):
            self.assertTrue((GRAMMAR / "test" / "corpus" / "list_type.txt").is_file())
        with self.subTest("highlights"):
            self.assertRegex(highlights, r'"\["[^\n]*"\]"[^\n]*@punctuation\.bracket')
        if not os.access(TREE_SITTER, os.X_OK):
            self.skipTest("tree-sitter not found at %s (set TREE_SITTER)" % TREE_SITTER)
        for source in (ORDERS, PLAIN_V2, TWO_ROWS):
            with self.subTest("parse " + str(source.relative_to(FIX))):
                run = subprocess.run([TREE_SITTER, "parse", "-q", str(source)], cwd=GRAMMAR, capture_output=True,
                                     text=True, timeout=120)
                self.assertEqual((0, False), (run.returncode, "ERROR" in run.stdout), run.stdout + run.stderr)

    # N25b (P4b reader, M-a): a lost literal in a stored orders.list item blocks; a kept value does not.

    def stored_list(self, record):
        holder = self.work / "stored"
        holder.mkdir(exist_ok=True)
        (holder / "rows.jsonl").write_text("")  # PDB-23: the ROW SNAPSHOT is known and empty
        path = holder / "responses.jsonl"
        path.write_text(json.dumps(record, separators=(",", ":")) + "\n")
        return path

    def test_N25b_lost_literal_in_a_list_item_blocks(self):
        stored = self.stored_list(list_record("app"))
        code, stdout, stderr = self.compile(NO_APP, ["--stored", str(stored)])
        self.assertEqual((1, "", LITERAL_BLOCK % stored), (code, stdout, stderr.strip()))

    def test_N25b_control_kept_value_builds(self):
        stored = self.stored_list(list_record("tv", ["items.0.channel"]))
        code, stdout, stderr = self.compile(NO_APP, ["--stored", str(stored)])
        self.assertEqual((0, True, False), (code, "defmodule Orders do" in stdout, "error" in stderr), stderr)

    def test_N25b_control_the_record_builds_where_the_literal_stands(self):
        # The same "app" record under orders.beaml (App = "app" stands): exit 0, so N25b fails for the literal only.
        stored = self.stored_list(list_record("app"))
        code, stdout, stderr = self.compile(ORDERS, ["--stored", str(stored)])
        self.assertEqual((0, True, False), (code, "defmodule Orders do" in stdout, "error" in stderr), stderr)

    @unittest.skip("0005 only: jsonb_typeof(value->'reason') = 'null' needs Postgres (0005 N2c, PDB-30)")
    def test_N2c_jsonb_typeof_reason_is_null(self):
        pass


if __name__ == "__main__":
    if not __debug__:
        raise SystemExit("Run without Python optimization.")
    unittest.main(verbosity=2)
