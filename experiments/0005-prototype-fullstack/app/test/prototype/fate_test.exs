defmodule Proto.Prototype.FateTest do
  # EXPERIMENT 0005 N9 (P5-15): a MIGRATE STEP that frees the stricter Amount, smallest form
  # `migrate Order v1 -> v2 { quarantine amount }` (DL-125). Needs the fate slice P6; D036 parks M3, M4, M5 first.
  use ExUnit.Case, async: true

  @tag use_case: "N9"
  @tag skip: "blocked: fate slice (D036)"
  test "N9 quarantine amount frees the stricter build and the list omits order-zero" do
    flunk("N9 is blocked until the fate slice (P6, D036)")
  end
end
