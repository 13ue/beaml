defmodule Proto.UseCaseFormatter do
  @moduledoc """
  Writes the use-case events of the EXPERIMENT 0005 N-TESTS to `<repo>/.beaml/actions.jsonl` (AGENTS rule) and,
  when `BEAML_RUN_DIR` is set, to `<run>/use-cases.jsonl` for run.py. One start and one finish per test.
  The reason of a failure is the error kind only: an assertion diff can hold a form value, so it is never logged.
  Logging never raises.
  """
  use GenServer

  def init(_opts), do: {:ok, %{}}

  # ExUnit also starts excluded tests: hold the start event until the test finishes and is not excluded.
  def handle_cast({:test_started, %ExUnit.Test{} = test}, state),
    do: {:noreply, Map.put(state, {test.module, test.name}, now())}

  def handle_cast({:test_finished, %ExUnit.Test{} = test}, state) do
    result =
      case test.state do
        nil -> "pass"
        {:skipped, reason} -> to_string(reason)
        {:excluded, _} -> nil
        {:invalid, _} -> "fail: invalid (setup_all failed)"
        {:failed, [{kind, error, _} | _]} -> "fail: " <> kind_of(kind, error)
        {:failed, _} -> "fail"
      end

    {started, state} = Map.pop(state, {test.module, test.name}, now())

    if result do
      write(test, started, "start", "running")
      write(test, now(), "finish", result)
    end

    {:noreply, state}
  end

  def handle_cast(_event, state), do: {:noreply, state}

  defp kind_of(:error, %{__struct__: module}), do: inspect(module)
  defp kind_of(kind, _), do: to_string(kind)

  defp now, do: DateTime.utc_now() |> DateTime.to_iso8601()

  defp write(test, ts, action, result) do
    if id = test.tags[:use_case] do
      line =
        Jason.encode!(%{
          ts: ts,
          source: "test",
          use_case: "exp0005-" <> id,
          action: action,
          target: to_string(test.name),
          result: result
        }) <> "\n"

      append(Proto.Prototype.actions_file(), line)

      if dir = System.get_env("BEAML_RUN_DIR"),
        do: append(Path.join(dir, "use-cases.jsonl"), line)
    end
  rescue
    _ -> :ok
  end

  defp append(path, line) do
    File.mkdir_p(Path.dirname(path))
    File.write(path, line, [:append])
  end
end
