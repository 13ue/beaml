sorted = fn
  map, encode when is_map(map) -> :json.encode_key_value_list(Enum.sort(Map.to_list(map)), encode)
  other, encode -> :json.encode_value(other, encode)
end
IO.read(:stdio, :eof) |> String.split("\n", trim: true) |> Enum.each(fn line ->
  r = :json.decode(line)
  text = :json.encode(%{"redacted" => r["redacted"], "unknown_keys" => r["unknown_keys"], "value" => r["value"]}, sorted)
  IO.puts(Base.encode16(:crypto.hash(:sha256, text), case: :lower))
end)
