from scripts.view_server import VIEW_APPS


def test_view_server_manages_replay_app():
    assert VIEW_APPS["replay"].module == "olden.battlefield_view.replay_app"
    assert VIEW_APPS["replay"].url == "http://localhost:8081"
