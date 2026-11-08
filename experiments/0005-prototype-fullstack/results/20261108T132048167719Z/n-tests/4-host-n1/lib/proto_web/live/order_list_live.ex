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
    <Layouts.app flash={@flash}>
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-semibold">Orders</h1>
        <.link navigate={~p"/orders/new"} class="btn btn-primary btn-sm">New order</.link>
      </div>
      <div :if={@items == []} class="alert">No orders yet.</div>
      <table :if={@items != []} class="table table-zebra">
        <thead>
          <tr>
            <th>Order id</th>
            <th>Amount</th>
            <th>Currency</th>
            <th>Channel</th>
          </tr>
        </thead>
        <tbody>
          <tr :for={o <- @items} data-order>
            <td>{o["order_id"]}</td>
            <td>{o["amount"]["value"]}</td>
            <td>{o["amount"]["currency"]}</td>
            <td>{o["channel"]}</td>
          </tr>
        </tbody>
      </table>
    </Layouts.app>
    """
  end
end
