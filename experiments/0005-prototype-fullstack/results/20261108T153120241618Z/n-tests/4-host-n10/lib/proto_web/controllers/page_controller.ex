defmodule ProtoWeb.PageController do
  use ProtoWeb, :controller

  def home(conn, _params) do
    render(conn, :home)
  end
end
