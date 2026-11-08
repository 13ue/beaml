defmodule ProtoWeb.NotesLive do
  # /notes: the list through Orders.ui_notes/1, the submit through Orders.ui_note/1 (plan repair 2, QDB-8 B).
  use ProtoWeb, :live_view
  alias ProtoWeb.ActionLog

  def mount(_params, _session, socket) do
    result = Orders.ui_notes(%{})
    ActionLog.log("notes", "/notes", ActionLog.result(result))

    case result do
      {:ok, %{"items" => items}} ->
        {:ok, assign(socket, items: items)}

      {:error, error} ->
        {:ok, socket |> assign(items: []) |> put_flash(:error, ActionLog.message(error))}
    end
  end

  # R2: navigate after the submit, so the submit runs one ENTRY LINE only (no re-list in this event).
  def handle_event("note", %{"note" => params}, socket) do
    result = Orders.ui_note(params)
    ActionLog.log("note", "/notes", ActionLog.result(result), params)

    case result do
      {:ok, _note} -> {:noreply, push_navigate(socket, to: ~p"/notes")}
      {:error, error} -> {:noreply, put_flash(socket, :error, ActionLog.message(error))}
    end
  end

  def render(assigns) do
    ~H"""
    <Layouts.app flash={@flash}>
      <h1 class="text-xl font-semibold">Notes</h1>
      <div class="card bg-base-100 shadow-sm border border-base-300">
        <form id="note" phx-submit="note" class="card-body">
          <.input name="note[text]" value="" label="Note" />
          <div class="card-actions justify-end">
            <.button variant="primary">Save</.button>
          </div>
        </form>
      </div>
      <div :if={@items == []} class="alert">No notes yet.</div>
      <ul :if={@items != []} class="list bg-base-100 rounded-box border border-base-300">
        <li :for={n <- @items} data-note data-tag={n["tag"]} class="list-row">{n["text"]}</li>
      </ul>
    </Layouts.app>
    """
  end
end
