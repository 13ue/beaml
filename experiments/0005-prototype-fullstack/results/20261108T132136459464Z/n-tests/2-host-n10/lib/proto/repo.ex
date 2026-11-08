defmodule Proto.Repo do
  use Ecto.Repo,
    otp_app: :proto,
    adapter: Ecto.Adapters.Postgres
end
