# Phase tests (committed rows, one generated variant each) run only from run.py: mix test --only phase:<name>.
ExUnit.start(exclude: [:phase], formatters: [ExUnit.CLIFormatter, Proto.UseCaseFormatter])
Ecto.Adapters.SQL.Sandbox.mode(Proto.Repo, :manual)
