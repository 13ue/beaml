defmodule Proto.Repo.Migrations.CreateRecords do
  use Ecto.Migration

  # The one host migration (DL-127, P5-07). A TYPE change never changes it.
  def change do
    create table(:records, primary_key: false) do
      add :id, :identity, primary_key: true
      add :type, :text, null: false
      add :version, :integer, null: false
      add :value, :map, null: false

      add :inserted_at, :utc_datetime_usec,
        null: false,
        default: fragment("timezone('utc', now())")
    end

    create index(:records, [:type, :inserted_at])
  end
end
