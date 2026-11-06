defmodule ProbeSupport.Capture do
  use GenServer

  def child_spec(arg),
    do: %{id: __MODULE__, start: {__MODULE__, :start_link, [arg]}, restart: :temporary}

  def start_link(_), do: GenServer.start_link(__MODULE__, nil, name: __MODULE__)
  def init(_), do: {:ok, %{bytes: %{}, loss: []}}

  def write(kind, record) do
    GenServer.call(__MODULE__, {:write, kind, record}, 2000)
  catch
    _, _ -> :error
  end

  def status, do: GenServer.call(__MODULE__, :status, 2000)
  def handle_call(:status, _, state), do: {:reply, state, state}

  def handle_call({:write, kind, record}, _, state) do
    bytes = ProbeSupport.json(record) <> "\n"
    count = Map.get(state.bytes, kind, 0) + byte_size(bytes)

    result =
      if count <= 1_048_576,
        do:
          File.write(Path.join(ProbeSupport.config(:output), kind <> ".jsonl"), bytes, [:append]),
        else: {:error, :overflow}

    state =
      case result do
        :ok -> %{state | bytes: Map.put(state.bytes, kind, count)}
        _ -> %{state | loss: Enum.uniq([kind | state.loss])}
      end

    {:reply, result, state}
  end
end
