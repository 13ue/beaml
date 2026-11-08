defmodule Proto.Prototype.OrderPagesTest do
  # EXPERIMENT 0005 N2 to N6 and N12 (plan.md "N-tests", corrections 2026-11-07). SQL sandbox, LiveViewTest.
  # The host pages call only Orders.ui_place/1 and Orders.ui_orders/1 (DL-131, Q5-9 A).
  use ProtoWeb.ConnCase, async: false
  import Phoenix.LiveViewTest
  import Proto.Prototype

  @values ["order-1", "12.50", "EUR"]

  defp place(conn, order) do
    {:ok, view, _html} = live(conn, "/orders/new")
    view |> form("#place", order: order) |> render_submit()
  end

  defp without(map, keys), do: map |> Map.drop(keys) |> Jason.encode!()

  @tag use_case: "N2"
  test "N2 a form submit writes one Order row through db.put", %{conn: conn} do
    assert {:error, {:live_redirect, %{to: "/orders"}}} = place(conn, good())
    assert [{_id, "Order", 1, core}] = rows()

    # Q5-10 B: the row value is the record format v3 core; the DL-105 projection sits under its `value` key.
    assert {core["version"], core["operation"], core["value"], core["outcome"], core["reason"]} ==
             {3, "orders.save", good(), "accepted", nil}

    assert core["value_sha256"] =~ ~r/\A[0-9a-f]{64}\z/
    assert core["type"]["name"] == "Order" and core["type"]["version"] == 1
  end

  @tag use_case: "N2c"
  test "N2c the reason of the row is a JSON null", %{conn: conn} do
    assert {:error, {:live_redirect, _}} = place(conn, good())

    assert %{rows: [["null"]]} =
             Proto.Repo.query!("SELECT jsonb_typeof(value->'reason') FROM records")
  end

  @tag use_case: "N3"
  test "N3 the submit writes one ENTRY RECORD and one db record with one trace", %{conn: conn} do
    entries = mark(capture_file("entries"))
    responses = mark(capture_file("responses"))
    assert {:error, {:live_redirect, _}} = place(conn, good())

    assert [entry] = records_since("entries", entries)
    assert [db] = records_since("responses", responses)

    assert {entry["version"], entry["operation"], entry["outcome"], entry["reason"],
            entry["unknown_keys"]} ==
             {3, "ui.place", "accepted", nil, []}

    assert {db["version"], db["operation"], db["outcome"], db["reason"]} ==
             {3, "orders.save", "accepted", nil}

    assert entry["trace_id"] == db["trace_id"] and entry["trace_id"] =~ ~r/\A[0-9a-f]{32}\z/
    # No form value outside `value` (and the db record's `request`, QDB-5 A).
    for v <- @values do
      refute without(entry, ["value"]) =~ v
      refute without(db, ["value", "request"]) =~ v
    end
  end

  @tag use_case: "N4"
  test "N4 a constructor reject writes no row and no db record", %{conn: conn} do
    entries = mark(capture_file("entries"))
    responses = mark(capture_file("responses"))
    html = place(conn, put_in(good(), ["amount", "currency"], ""))

    assert is_binary(html) and html =~ "form rejected: constructor"
    assert rows() == []
    assert [entry] = records_since("entries", entries)

    assert {entry["operation"], entry["outcome"], entry["reason"]} ==
             {"ui.place", "rejected", "constructor"}

    refute Enum.any?(records_since("responses", responses), &(&1["operation"] == "orders.save"))
  end

  @tag use_case: "N4"
  test "N4 an unknown channel is accepted and stored as its text", %{conn: conn} do
    assert {:error, {:live_redirect, %{to: "/orders"}}} =
             place(conn, Map.put(good(), "channel", "tv"))

    assert [{_, "Order", 1, %{"value" => %{"channel" => "tv"}}}] = rows()
  end

  @tag use_case: "N5"
  test "N5 the list page shows both orders through db.list, newest first", %{conn: conn} do
    assert {:error, {:live_redirect, _}} = place(conn, good())
    assert {:error, {:live_redirect, _}} = place(conn, Map.put(good(), "order_id", "order-2"))

    {:ok, _view, html} = live(conn, "/orders")
    assert {first, _} = :binary.match(html, "order-2")
    assert {second, _} = :binary.match(html, "order-1")
    assert first < second
  end

  @tag use_case: "N6"
  test "N6 an Unknown channel lists as its text", %{conn: conn} do
    assert {:error, {:live_redirect, _}} = place(conn, Map.put(good(), "channel", "tv"))
    {:ok, view, _html} = live(conn, "/orders")
    assert has_element?(view, "[data-order]", "tv")
  end

  @tag use_case: "N12"
  test "N12 the host writes one action event per action and no value", %{conn: conn} do
    offset = mark(actions_file())
    assert {:error, {:live_redirect, _}} = place(conn, good())
    place(conn, put_in(good(), ["amount", "currency"], ""))

    lines = lines_since(actions_file(), offset)
    ui = lines |> Enum.map(&Jason.decode!/1) |> Enum.filter(&(&1["source"] == "ui"))

    assert ui |> Enum.filter(&(&1["action"] == "place")) |> Enum.map(& &1["result"]) ==
             ["ok", "rejected:constructor"]

    for e <- ui,
        do:
          assert(Enum.all?(["ts", "source", "action", "target", "result"], &Map.has_key?(e, &1)))

    for line <- lines, bad <- @values ++ [app(), "effect ", "ui.event("] do
      refute line =~ bad
    end
  end
end
