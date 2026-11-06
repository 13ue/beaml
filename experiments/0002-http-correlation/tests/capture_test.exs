ExUnit.start()

defmodule CaptureTest do
  use ExUnit.Case

  test "capture cap and write loss are sticky and do not raise" do
    directory =
      Path.join(System.tmp_dir!(), "beaml-capture-#{System.unique_integer([:positive])}")

    File.mkdir_p!(directory)
    Application.put_env(:probe_support, :output, directory)
    {:ok, pid} = ProbeSupport.Capture.start_link([])

    try do
      assert ProbeSupport.Capture.write("spans", %{synthetic: String.duplicate("x", 1_048_576)}) ==
               {:error, :overflow}

      assert ProbeSupport.Capture.status().loss == ["spans"]
      assert ProbeSupport.Capture.write("spans", %{synthetic: "small"}) == :ok
      assert ProbeSupport.Capture.status().loss == ["spans"]
      File.rm_rf!(directory)
      assert {:error, _} = ProbeSupport.Capture.write("logs", %{synthetic: "write failure"})
      assert "logs" in ProbeSupport.Capture.status().loss
    after
      GenServer.stop(pid)
      File.rm_rf!(directory)
    end
  end
end
