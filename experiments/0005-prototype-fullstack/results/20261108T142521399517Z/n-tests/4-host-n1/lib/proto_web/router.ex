defmodule ProtoWeb.Router do
  use ProtoWeb, :router

  pipeline :browser do
    plug :accepts, ["html"]
    plug :fetch_session
    plug :fetch_live_flash
    plug :put_root_layout, html: {ProtoWeb.Layouts, :root}
    plug :protect_from_forgery
    plug :put_secure_browser_headers
  end

  pipeline :api do
    plug :accepts, ["json"]
  end

  scope "/", ProtoWeb do
    pipe_through :browser

    get "/", PageController, :home
    live "/orders/new", OrderFormLive
    live "/orders", OrderListLive
    live "/notes", NotesLive
  end

  # Other scopes may use custom stacks.
  # scope "/api", ProtoWeb do
  #   pipe_through :api
  # end
end
