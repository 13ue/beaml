defmodule Proto.RecordsTest do
  # Host scaffold check (EXPERIMENT 0005, setup, no BEAML): the one table takes and returns one row.
  use Proto.DataCase, async: true

  test "inserts and reads one row of records through Repo" do
    %{rows: [[id]]} =
      Repo.query!(
        "INSERT INTO records (type, version, value) VALUES ($1, $2, $3) RETURNING id",
        ["Order", 1, %{"order_id" => "order-1"}]
      )

    assert is_integer(id)

    assert %{rows: [["Order", 1, %{"order_id" => "order-1"}, %NaiveDateTime{}]]} =
             Repo.query!(
               "SELECT type, version, value, inserted_at FROM records WHERE id = $1",
               [id]
             )
  end
end
