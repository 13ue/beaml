defmodule ProtoWeb.OrderFormLive do
  # /orders/new: the submit enters BEAML only through Orders.ui_place/1 (DL-131).
  use ProtoWeb, :live_view
  alias ProtoWeb.ActionLog

  def mount(_params, _session, socket) do
    ActionLog.log("mount", "/orders/new", "ok")
    {:ok, socket}
  end

  def handle_event("place", %{"order" => params}, socket) do
    result = Orders.ui_place(params)
    ActionLog.log("place", "/orders/new", ActionLog.result(result), params)

    case result do
      {:ok, _order} -> {:noreply, push_navigate(socket, to: ~p"/orders")}
      {:error, error} -> {:noreply, put_flash(socket, :error, ActionLog.message(error))}
    end
  end

  def render(assigns) do
    ~H"""
    <.flash kind={:error} flash={@flash} />
    <form id="place" phx-submit="place">
      <label>Order id <input name="order[order_id]" /></label>
      <label>Amount <input name="order[amount][value]" /></label>
      <label>Currency <input name="order[amount][currency]" /></label>
      <label>Channel <input name="order[channel]" /></label>
      <button>Place</button>
    </form>
    """
  end
end
