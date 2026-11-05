ExUnit.start()

defmodule BeamlSpikeTest do
  use ExUnit.Case

  defp order(country) do
    %{"id" => "order-1", "customer" => %{
      "name" => "Kunde", "address" => %{"city" => "Köln", "country" => country}
    }}
  end

  test "source call reaches compiled BEAM code" do
    assert BeamlSpike.sample() == "Kunde bestellt aus Berlin, Deutschland"
    assert BeamlSpike.send("console", "Hallo") == "console: Hallo"
  end

  test "nested literal pattern takes priority over the general record pattern" do
    assert BeamlSpike.describe({"OrderResult", "Ok", [order("DE")]}) ==
      "Kunde bestellt aus Köln, Deutschland"
    assert BeamlSpike.describe({"OrderResult", "Ok", [order("AT")]}) ==
      "Bestellung order-1 von Kunde"
  end

  test "nested error constructors retain their distinct meanings" do
    assert BeamlSpike.describe({"OrderResult", "Error", [{"OrderError", "NotFound", ["order-3"]}]}) ==
      "Bestellung order-3 wurde nicht gefunden"
    assert BeamlSpike.describe({"OrderResult", "Error", [{"OrderError", "Rejected", ["Adresse"]}]}) ==
      "Bestellung abgelehnt: Adresse"
  end

  test "partial patterns do not permit extra record fields at the public boundary" do
    extra = Map.put(order("DE"), "debug", true)
    assert_raise ArgumentError, "invalid BEAML input", fn ->
      BeamlSpike.describe({"OrderResult", "Ok", [extra]})
    end
  end

  test "omitted pattern fields are still required and typed at runtime" do
    missing = Map.delete(order("DE"), "id")
    wrong = put_in(order("DE"), ["customer", "address", "country"], 42)
    nested_extra = update_in(order("DE"), ["customer", "address"], &Map.put(&1, "zip", "1"))
    for value <- [missing, wrong, nested_extra] do
      assert_raise ArgumentError, fn -> BeamlSpike.describe({"OrderResult", "Ok", [value]}) end
    end
  end

  test "unknown constructors and invalid argument layouts fail before dispatch" do
    for value <- [
      {"OtherResult", "Ok", [order("DE")]},
      {"OrderResult", "Unknown", []},
      {"OrderResult", "Ok", []},
      {"OrderResult", "Ok", [order("DE"), order("DE")]},
      {"OrderResult", "Error", [{"OrderError", "Rejected", [42]}]},
      %{}, nil
    ] do
      assert_raise ArgumentError, fn -> BeamlSpike.describe(value) end
    end
  end

  test "String rejects invalid UTF-8 and non-string host values" do
    for value <- [42, nil, <<255>>] do
      assert_raise ArgumentError, fn -> BeamlSpike.send("console", value) end
    end
  end
end

defmodule BeamlLiteralTest do
  use ExUnit.Case

  test "source strings stay data and unused pattern variables compile without warnings" do
    assert BeamlSpike.literal() == ~S|#{raise("must stay data")}: Grüße| <> "\n"
    assert BeamlSpike.ignore("input") == "ignored"
  end
end
