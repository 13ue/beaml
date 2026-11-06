ExUnit.start()

defmodule FixtureTest do
  use ExUnit.Case

  test "compiled exact interfaces and host value checks" do
    order = %{"order_id" => "order-1"}
    payment = %{"order_id" => "order-1", "status" => "authorized"}

    module =
      if Code.ensure_loaded?(OrdersBeamlSpike), do: OrdersBeamlSpike, else: PaymentsBeamlSpike

    function = if module == OrdersBeamlSpike, do: :prepare, else: :authorize
    assert apply(module, function, [order]) == if(function == :prepare, do: order, else: payment)

    for value <- [
          %{},
          Map.put(order, "extra", "x"),
          %{"order_id" => 42},
          %{"order_id" => <<255>>}
        ] do
      assert_raise ArgumentError, fn -> apply(module, function, [value]) end
    end

    if module == OrdersBeamlSpike do
      assert apply(module, :finish, [payment]) == payment

      for value <- [order, Map.put(payment, "extra", "x"), Map.put(payment, "status", 42)] do
        assert_raise ArgumentError, fn -> apply(module, :finish, [value]) end
      end
    end

    for value <- [Map.put(payment, "order_id", "other"), Map.put(payment, "status", "declined")] do
      assert_raise ArgumentError, fn -> ProbeSupport.valid_payment!(value, order) end
    end
  end
end
