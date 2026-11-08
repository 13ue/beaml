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

  # GREEN repair 2026-11-08: a String-only TYPE is a map, not a struct (no Orders.Note module). The Note v2 encoder
  # of the generated module carries the field `tag`; the v1 encoder does not.
  defp v2_module! do
    assert Map.has_key?(Orders.__beaml_encode_note(%{}), "tag"), "the host runs no Note v2 module"
  end

  defp notes(rows), do: for({id, "Note", version, core} <- rows, do: {id, version, core["value"]})

  @tag use_case: "N7"
  test "N7 the v1 row lists through the MIGRATE CHAIN with tag empty and stays version 1", %{
    conn: conn
  } do
    v2_module!()
    marks = marks()
    {:ok, view, _} = live(conn, "/notes")
    assert has_element?(view, ~s([data-note][data-tag=""]), "note-1")

    # RED repair O1: the v1 row came through Orders.ui_notes/1, db.list and the chain default tag "".
    for db <- through_beaml!("ui.notes", "notes.list", marks),
        do: assert(db["value"] == %{"items" => [%{"text" => "note-1", "tag" => ""}]})

    assert [{_, 1, %{"text" => "note-1"}}] = notes(rows())
  end

  @tag use_case: "N7b"
  test "N7b a submit under v2 writes a version 2 row and the list shows v1 and v2", %{conn: conn} do
    v2_module!()
    marks = marks()
    {:ok, view, _} = live(conn, "/notes")
    through_beaml!("ui.notes", "notes.list", marks)
    marks = marks()
    view |> form("#note", note: %{"text" => "note-2"}) |> render_submit()
    # RED repair O1: one submit, one ENTRY RECORD and one notes.save record with one trace.
    assert [_] = through_beaml!("ui.note", "notes.save", marks)

    assert [{_, 1, %{"text" => "note-1"}}, {_, 2, %{"text" => "note-2", "tag" => ""}}] =
             notes(rows())

    marks = marks()
    {:ok, view, _} = live(conn, "/notes")

    for db <- through_beaml!("ui.notes", "notes.list", marks),
        do:
          assert(
            Enum.sort(db["value"]["items"]) ==
              [%{"text" => "note-1", "tag" => ""}, %{"text" => "note-2", "tag" => ""}]
          )

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
