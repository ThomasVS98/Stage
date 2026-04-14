from stores.session_store import SessionStore

def test_session_create_and_get():
    store = SessionStore()
    store.create("session1")

    session = store.get("session1")

    assert session is not None
    assert session["step"] == 0
    assert session["data"] == {}

def test_session_update_and_increment():
    from stores.session_store import SessionStore

    store = SessionStore()
    store.create("session2")

    store.update("session2", "key", "value")
    store.increment_step("session2")

    session = store.get("session2")

    assert session["data"]["key"] == "value"
    assert session["step"] == 1

def test_session_update_nonexistent():
    from stores.session_store import SessionStore

    store = SessionStore()

    store.update("unknown", "key", "value")
    store.increment_step("unknown")

    assert store.get("unknown") is None

