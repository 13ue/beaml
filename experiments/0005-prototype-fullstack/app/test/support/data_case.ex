defmodule Proto.DataCase do
  @moduledoc """
  This module defines the setup for tests requiring
  access to the application's data layer.

  You may define functions here to be used as helpers in
  your tests.

  Finally, if the test case interacts with the database,
  we enable the SQL sandbox, so changes done to the database
  are reverted at the end of every test. If you are using
  PostgreSQL, you can even run database tests asynchronously
  by setting `use Proto.DataCase, async: true`, although
  this option is not recommended for other databases.
  """

  use ExUnit.CaseTemplate

  using do
    quote do
      alias Proto.Repo

      import Ecto
      import Ecto.Changeset
      import Ecto.Query
      import Proto.DataCase
    end
  end

  setup tags do
    Proto.DataCase.setup_sandbox(tags)
    :ok
  end

  @doc """
  Sets up the sandbox based on the test tags.
  """
  def setup_sandbox(tags) do
    # EXPERIMENT 0005 (P5-14): a `committed` test writes outside the sandbox transaction, so that the host task
    # `mix beaml.stored` and psql read its rows. `committed: :truncate` empties `records` first.
    pid =
      Ecto.Adapters.SQL.Sandbox.start_owner!(Proto.Repo,
        shared: not tags[:async],
        sandbox: !tags[:committed]
      )

    if tags[:committed] == :truncate, do: Proto.Repo.query!("TRUNCATE records RESTART IDENTITY")
    on_exit(fn -> Ecto.Adapters.SQL.Sandbox.stop_owner(pid) end)
  end

  @doc """
  A helper that transforms changeset errors into a map of messages.

      assert {:error, changeset} = Accounts.create_user(%{password: "short"})
      assert "password is too short" in errors_on(changeset).password
      assert %{password: ["password is too short"]} = errors_on(changeset)

  """
  def errors_on(changeset) do
    Ecto.Changeset.traverse_errors(changeset, fn {message, opts} ->
      Regex.replace(~r"%{(\w+)}", message, fn _, key ->
        opts |> Keyword.get(String.to_existing_atom(key), key) |> to_string()
      end)
    end)
  end
end
