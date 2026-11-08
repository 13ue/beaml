defmodule Proto.Prototype.StoredTest do
  # EXPERIMENT 0005 N8, N8b, N8c, N11, N15 (plan.md, "Plan repair" O2). Phase n8: run.py runs it under the generated
  # orders.beaml with committed rows: mix test --only phase:n8 --seed 0. Every build reads a fresh live ROW
  # SNAPSHOT through mix beaml.stored; snapshot! checks its provenance (N8c) each time.
  use ProtoWeb.ConnCase, async: false
  import Phoenix.LiveViewTest
  import Proto.Prototype

  @moduletag phase: :n8
  @moduletag committed: :truncate

  # The built P4 text (0004 slice6_db_stored_test N18), M4: the help line is not asserted.
  @blocked "error: TYPE Order: 1 stored ROW of table records fails the constructor of Amount for field amount with BadAmount"

  defp place(conn, order) do
    {:ok, view, _} = live(conn, "/orders/new")

    assert {:error, {:live_redirect, %{to: "/orders"}}} =
             view |> form("#place", order: order) |> render_submit()
  end

  defp zero(conn) do
    place(conn, %{
      good()
      | "order_id" => "order-zero",
        "amount" => %{"value" => "0", "currency" => "EUR"}
    })

    assert [{id, "Order", 1, core}] = rows()
    {id, core}
  end

  @tag use_case: "N8"
  test "N8 a stricter Amount blocks the build against the live row and prints no stored value", %{
    conn: conn
  } do
    {_id, core} = zero(conn)
    {code, out, lines, _dir} = live_build("stricter", "n8")

    assert {code, out, Enum.reject(lines, &String.starts_with?(&1, "rows: ")) |> List.first()} ==
             {1, "", @blocked}

    text = Enum.join(lines, "\n")
    for secret <- ["order-zero", core["trace_id"], core["span_id"]], do: refute(text =~ secret)
    assert_no_ddl!()
  end

  @tag use_case: "N8"
  test "N8 control: the same live row builds under orders.beaml", %{conn: conn} do
    zero(conn)
    assert {0, _, [line], _} = live_build(nil, "n8-control")
    assert line == counted(1, 1, 0)
  end

  @tag use_case: "N8b"
  test "N8b the stricter build passes after the row is deleted by SQL", %{conn: conn} do
    {id, _} = zero(conn)
    assert {1, _, _, _} = live_build("stricter", "n8b-blocked")
    Proto.Repo.query!("DELETE FROM records WHERE id = $1", [id])
    assert {0, out, [line], _} = live_build("stricter", "n8b")
    assert {line, out =~ "defmodule Orders do"} == {counted(0, 0, 0), true}
  end

  @tag use_case: "N15"
  test "N15 an SQL edit of a row value without a new digest blocks the build", %{conn: conn} do
    # P2b (DL-164, DL-158): the D035 site example. The build stops; the text names no value and no id.
    place(conn, good())
    assert [{id, "Order", 1, core}] = rows()

    Proto.Repo.query!(
      "UPDATE records SET value = jsonb_set(value, '{value,amount,value}', '\"99.00\"') WHERE id = $1",
      [id]
    )

    {code, out, lines, _dir} = live_build(nil, "n15")

    assert {code, out, Enum.reject(lines, &String.starts_with?(&1, "rows: ")) |> List.first()} ==
             {1, "",
              "error: TYPE Order: 1 stored ROW of table records has a wrong digest: value_sha256 does not match " <>
                "value, unknown_keys and redacted (DL-164)"}

    text = Enum.join(lines, "\n")

    for secret <- ["99.00", "order-1", core["trace_id"], core["span_id"]],
        do: refute(text =~ secret)

    assert_no_ddl!()
    # Control: the row is gone, the same build passes.
    Proto.Repo.query!("DELETE FROM records WHERE id = $1", [id])
    assert {0, _, [line], _} = live_build(nil, "n15-control")
    assert line == counted(0, 0, 0)
  end

  @tag use_case: "N8c"
  test "N8c the snapshot holds exactly the live row ids of this instant", %{conn: conn} do
    place(conn, good())
    place(conn, Map.put(good(), "order_id", "order-2"))
    dir = snapshot!("n8c")
    assert length(psql_ids()) == 2

    assert dir
           |> Path.join("snapshot-meta.json")
           |> File.read!()
           |> Jason.decode!()
           |> Map.fetch!("row_count") == 2
  end
end
