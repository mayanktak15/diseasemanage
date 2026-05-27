from chatbot import get_response


def test_chatbot_basic_response():
    response = get_response("What is Docify Online?")
    assert response
    assert "Docify" in response
