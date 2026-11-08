defmodule ProtoWeb.OrderListLive do
  # /orders: the list comes only from Orders.ui_orders/1 (Q5-9 A); the page renders the BEAML value.
  use ProtoWeb, :live_view
  alias ProtoWeb.ActionLog

  def mount(_params, _session, socket) do
    result = Orders.ui_orders(%{})
    ActionLog.log("orders", "/orders", ActionLog.result(result))

    case result do
      # The generated encoder gives the DL-105 projection: the channel as its literal text.
      {:ok, %{"items" => items}} ->
        {:ok, assign(socket, items: Enum.map(items, &Orders.__beaml_encode_order/1))}

      {:error, error} ->
        {:ok, socket |> assign(items: []) |> put_flash(:error, ActionLog.message(error))}
    end
  end

  def render(assigns) do
    ~H"""
    <.flash kind={:error} flash={@flash} />
    <ul>
      <li :for={o <- @items} data-order>
        {o["order_id"]} {o["amount"]["value"]} {o["amount"]["currency"]} {o["channel"]}
      </li>
    </ul>
    <.link navigate={~p"/orders/new"}>New order</.link>
    """
  end
end
