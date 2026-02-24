from heidi_engine.teacher.openhei_teacher import _AssistantTextCollector


def test_assistant_text_collector_nested_props_completion():
    c = _AssistantTextCollector(session_id="sess1")

    # Simulate streamed delta events (nested `properties` shape)
    c.feed({
        "type": "message.part.delta",
        "properties": {
            "sessionID": "sess1",
            "messageID": "mid1",
            "partID": "p1",
            "field": "text",
            "delta": "Hello ",
        },
    })

    c.feed({
        "type": "message.part.delta",
        "properties": {
            "sessionID": "sess1",
            "messageID": "mid1",
            "partID": "p1",
            "field": "text",
            "delta": "world",
        },
    })

    # Finalize via message.part.updated with time.end
    c.feed({
        "type": "message.part.updated",
        "properties": {
            "part": {
                "id": "p1",
                "sessionID": "sess1",
                "messageID": "mid1",
                "type": "text",
                "text": "Hello world",
                "time": {"end": "t"},
            }
        },
    })

    assert c.completed
    assert c.text() == "Hello world"


def test_assistant_text_collector_flat_event_shape():
    c = _AssistantTextCollector(session_id="sess2")

    # Simulate events using a flat/top-level event shape (no `properties`)
    c.feed({
        "type": "message.part.delta",
        "sessionID": "sess2",
        "messageID": "mid2",
        "partID": "p2",
        "field": "text",
        "delta": "A",
    })

    c.feed({
        "type": "message.part.delta",
        "sessionID": "sess2",
        "messageID": "mid2",
        "partID": "p2",
        "field": "text",
        "delta": "B",
    })

    c.feed({
        "type": "message.part.updated",
        "part": {
            "id": "p2",
            "sessionID": "sess2",
            "messageID": "mid2",
            "type": "text",
            "text": "AB",
            "time": {"end": "t"},
        },
    })

    assert c.completed
    assert c.text() == "AB"
