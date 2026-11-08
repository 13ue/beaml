defmodule Proto.Prototype.NotesSeedTest do
  # EXPERIMENT 0005 N7, first half (plan repair 2, QDB-8 B). Phase n7_seed, under the generated orders.beaml (Note
  # v1): one Order row and one Note row through the pages, then a live build of variants/note_v2 (N8c each build).
  use ProtoWeb.ConnCase, async: false
  import Phoenix.LiveViewTest
  import Proto.Prototype

  @moduletag phase: :n7_seed
  @moduletag committed: :truncate

  @tag use_case: "N7"
  test "N7 note_v2 builds against a live Note v1 row and an Order row", %{conn: conn} do
    {:ok, view, _} = live(conn, "/orders/new")

    assert {:error, {:live_redirect, _}} =
             view |> form("#place", order: good()) |> render_submit()

    {:ok, view, _} = live(conn, "/notes")
    view |> form("#note", note: %{"text" => "note-1"}) |> render_submit()

    assert [{_, "Order", 1, _}, {note_id, "Note", 1, %{"value" => %{"text" => "note-1"}}}] =
             rows()

    {code, _out, lines, dir} = live_build("note_v2", "n7")
    meta = dir |> Path.join("snapshot-meta.json") |> File.read!() |> Jason.decode!()
    assert note_id in meta["row_ids"]
    # Two ROW TYPES in one table (P4 N20b): both rows checked, none undecodable, no DEAD LINE.
    assert {code, lines} == {0, [counted(2, 2, 0)]}
  end
end

defmodule Proto.Prototype.NotesReadTest do
  # EXPERIMENT 0005 N7 second half, N7b and N11 (plan repair 2). Phase n7_read: run.py has generated
  # variants/note_v2 into lib/generated over the live rows of phase n7_seed. Rows stay (no truncate).
  use ProtoWeb.ConnCase, async: false
  import Phoenix.LiveViewTest
  import Proto.Prototype

  @moduletag phase: :n7_read
  @moduletag committed: :keep

  defp v2_module! do
    note = Module.concat(Orders, Note)

    assert Code.ensure_loaded?(note) and Map.has_key?(note.__struct__(), :tag),
           "the host runs no Note v2 module"
  end

  defp notes(rows), do: for({id, "Note", version, core} <- rows, do: {id, version, core["value"]})

  @tag use_case: "N7"
  test "N7 the v1 row lists through the MIGRATE CHAIN with tag empty and stays version 1", %{
    conn: conn
  } do
    v2_module!()
    {:ok, view, _} = live(conn, "/notes")
    assert has_element?(view, ~s([data-note][data-tag=""]), "note-1")
    assert [{_, 1, %{"text" => "note-1"}}] = notes(rows())
  end

  @tag use_case: "N7b"
  test "N7b a submit under v2 writes a version 2 row and the list shows v1 and v2", %{conn: conn} do
    v2_module!()
    {:ok, view, _} = live(conn, "/notes")
    view |> form("#note", note: %{"text" => "note-2"}) |> render_submit()

    assert [{_, 1, %{"text" => "note-1"}}, {_, 2, %{"text" => "note-2", "tag" => ""}}] =
             notes(rows())

    {:ok, view, _} = live(conn, "/notes")

    for text <- ["note-1", "note-2"],
        do: assert(has_element?(view, ~s([data-note][data-tag=""]), text))

    assert {0, _, [line], _} = live_build("note_v2", "n7b")
    assert line == counted(3, 3, 0)
  end

  @tag use_case: "N11"
  test "N11 a TYPE change reached the table and the DDL did not move" do
    # Not vacuous: the table holds a Note row of each TYPE VERSION (N7, N7b) before the DDL check.
    assert rows() |> notes() |> Enum.map(&elem(&1, 1)) |> Enum.uniq() |> Enum.sort() == [1, 2]
    assert_no_ddl!()
  end
end
