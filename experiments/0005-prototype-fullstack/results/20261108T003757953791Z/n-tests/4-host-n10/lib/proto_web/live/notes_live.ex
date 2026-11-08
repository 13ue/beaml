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
    <.flash kind={:error} flash={@flash} />
    <ul>
      <li :for={n <- @items} data-note data-tag={n["tag"]}>{n["text"]}</li>
    </ul>
    <form id="note" phx-submit="note">
      <label>Note <input name="note[text]" /></label>
      <button>Save</button>
    </form>
    """
  end
end
