from datetime import datetime

import pytest
from starlette.websockets import WebSocketDisconnect
from app.auth import create_access_token
from app.core.websocket_manager import manager
from app.models import models


def room(client):
    response = client.post("/rooms/", json={"name": "Test room", "host_nickname": "Host"})
    assert response.status_code == 200, response.text
    return response.json()


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_delete_populated_room(service):
    client, sessions = service
    info = room(client)
    guest = client.post("/rooms/join", json={"room_code": info["room_code"], "nickname": "Guest"}).json()
    with sessions() as db:
        db.add(models.ChatMessage(room_id=info["id"], user_id=guest["user_id"], message="hello"))
        db.add(models.QueueItem(room_id=info["id"], user_id=info["host_id"], title="Song"))
        db.commit()
    response = client.delete(f'/rooms/{info["room_code"]}', headers=headers(info["token"]))
    assert response.status_code == 200, response.text
    with sessions() as db:
        for model in (models.Room, models.RoomParticipant, models.ChatMessage, models.QueueItem):
            assert db.query(model).count() == 0
        assert [u.id for u in db.query(models.User).all()] == [0]


def test_jump_and_previous_with_equal_timestamps(service):
    client, sessions = service
    info = room(client)
    with sessions() as db:
        songs = [models.QueueItem(room_id=info["id"], user_id=info["host_id"],
                 title=f"Song {i}", artist="Artist", music_url=f"https://youtu.be/{i}",
                 platform="Youtube", created_at=datetime(2026, 1, 1), is_played=False)
                 for i in range(4)]
        db.add_all(songs)
        db.commit()
        ids = [song.id for song in songs]
    base = f'/rooms/{info["room_code"]}'
    for target, expected in [(2, [True, True, False, False]), (1, [True, False, False, False])]:
        response = client.post(f"{base}/player/jump/{ids[target]}", headers=headers(info["token"]))
        assert response.status_code == 200, response.text
        assert [s["is_played"] for s in client.get(f"{base}/queue_list").json()] == expected
    client.post(f"{base}/player/jump/{ids[3]}", headers=headers(info["token"]))
    assert client.post(f"{base}/player/prev", headers=headers(info["token"])).json()["song"] == "Song 2"


def test_host_nickname_cannot_be_reused(service):
    client, _ = service
    info = room(client)
    assert client.post("/rooms/join", json={"room_code": info["room_code"], "nickname": "Host"}).status_code == 409


@pytest.mark.parametrize("invalid", [[], None, 123, "text", {"message": ["hello"]}, {"message": 123}])
def test_malformed_chat_does_not_kill_connection(service, invalid):
    client, _ = service
    info = room(client)
    with client.websocket_connect(f'/ws/{info["room_code"]}?token={info["token"]}') as ws:
        assert ws.receive_json()["type"] == "system"
        assert ws.receive_json()["type"] == "chat"
        ws.send_json(invalid)
        if not isinstance(invalid, dict):
            assert ws.receive_json()["type"] == "error"
        ws.send_json({"type": "chat", "message": "still connected"})
        assert ws.receive_json()["message"] == "still connected"
    assert info["id"] not in manager.active_connections


def test_nonmember_rejected_before_initial_sync(service):
    client, sessions = service
    info = room(client)
    with sessions() as db:
        outsider = models.User(username="Outsider")
        db.add(outsider)
        db.commit()
        token = create_access_token({"user_id": outsider.id, "room_id": info["id"]})
    manager.update_room_state(info["id"], {"type": "sync", "private": True})
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(f'/ws/{info["room_code"]}?token={token}'):
            pytest.fail("nonmember was accepted")
    assert error.value.code == 4003


def test_failed_welcome_transaction_recovers(service):
    client, sessions = service
    info = room(client)
    # Missing bot forces the welcome INSERT to violate a real FK constraint.
    with sessions() as db:
        db.delete(db.get(models.User, 0))
        db.commit()
    with client.websocket_connect(f'/ws/{info["room_code"]}?token={info["token"]}') as ws:
        assert ws.receive_json()["type"] == "system"
        ws.send_json({"type": "chat", "message": "after rollback"})
        assert ws.receive_json()["message"] == "after rollback"


def test_request_sync_returns_saved_state(service):
    client, _ = service
    info = room(client)
    with client.websocket_connect(f'/ws/{info["room_code"]}?token={info["token"]}') as ws:
        ws.receive_json()
        ws.receive_json()
        ws.send_json({"type": "sync", "currentTime": 42})
        state = ws.receive_json()
        ws.send_json({"type": "request_sync"})
        assert ws.receive_json() == state
