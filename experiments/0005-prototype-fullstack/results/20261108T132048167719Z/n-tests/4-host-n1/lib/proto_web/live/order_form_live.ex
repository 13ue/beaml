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
    <Layouts.app flash={@flash}>
      <div class="card bg-base-100 shadow-sm border border-base-300">
        <form id="place" phx-submit="place" class="card-body">
          <h1 class="card-title">New order</h1>
          <.input name="order[order_id]" value="" label="Order id" />
          <.input name="order[amount][value]" value="" label="Amount" inputmode="decimal" />
          <.input name="order[amount][currency]" value="" label="Currency" />
          <.input name="order[channel]" value="" label="Channel" />
          <div class="card-actions justify-end">
            <.button variant="primary">Place</.button>
          </div>
        </form>
      </div>
    </Layouts.app>
    """
  end
end
