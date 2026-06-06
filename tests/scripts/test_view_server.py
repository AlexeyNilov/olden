from scripts.view_server import VIEW_APPS


def test_view_server_manages_static_and_replay_apps_on_separate_ports():
    assert VIEW_APPS["static"].module == "olden.battlefield_view.static"
    assert VIEW_APPS["static"].url == "http://localhost:8082"
    assert VIEW_APPS["replay"].module == "olden.battlefield_view.replay_app"
    assert VIEW_APPS["replay"].url == "http://localhost:8081"
