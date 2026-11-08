defmodule Proto.Prototype.BuildTest do
  # EXPERIMENT 0005 N1 and N10 (plan.md; corrections 2026-11-07, N10 control). Each case generates one source over
  # a live, empty ROW SNAPSHOT (mix beaml.stored, Q5-4 B) and builds a copy of the host with
  # `mix compile --warnings-as-errors`. The checked-in lib/generated/orders.ex is not touched.
  use Proto.DataCase, async: false
  import Proto.Prototype

  @moduletag committed: :truncate

  @tag use_case: "N1"
  test "N1 orders.beaml generates the module Orders and the host builds without a warning" do
    {exit, output, generated} = host_build(nil, "n1")

    for marker <- [
          "defmodule Orders do",
          "def ui_place(",
          "def ui_orders(",
          "def ui_note(",
          "def ui_notes("
        ],
        do: assert(generated =~ marker, "N1: the generated module lacks #{marker}")

    assert {exit, output =~ "Generated proto app"} == {0, true}, output
  end

  @tag use_case: "N10"
  test "N10 a removed ui.place line stops the host build at Orders.ui_place/1" do
    {exit, output, generated} = host_build("no_place", "n10")

    assert generated =~ "defmodule Orders do"
    refute generated =~ "def ui_place("
    assert exit != 0
    assert output =~ "Orders.ui_place/1"
    refute output =~ "Orders.ui_orders/1"
    refute output =~ "BeamlDb"
  end
end
