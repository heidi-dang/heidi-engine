from unittest.mock import MagicMock, patch

from heidi_engine.utils.openai_compat import openai_chat_create


def test_openai_chat_create_v1_mock():
    # Mocking OpenAI SDK v1+
    with (
        patch("heidi_engine.utils.openai_compat.HAS_OPENAI_V1", True),
        patch("heidi_engine.utils.openai_compat.openai"),
        patch("heidi_engine.utils.openai_compat.OpenAI") as mock_openai_class,
    ):
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "v1 response"
        mock_client.chat.completions.create.return_value = mock_response

        result = openai_chat_create(
            model="gpt-4",
            messages=[{"role": "user", "content": "hi"}],
            api_key="test-key",
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "v1 response"
        mock_openai_class.assert_called_once_with(api_key="test-key")
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.7,
            max_tokens=100,
        )


def test_openai_chat_create_v0_mock():
    # Mocking OpenAI SDK v0.x
    with (
        patch("heidi_engine.utils.openai_compat.HAS_OPENAI_V1", False),
        patch("heidi_engine.utils.openai_compat.openai") as mock_openai,
    ):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "v0 response"
        mock_openai.ChatCompletion.create.return_value = mock_response

        result = openai_chat_create(
            model="gpt-4",
            messages=[{"role": "user", "content": "hi"}],
            api_key="test-key",
            temperature=0.7,
            max_tokens=100,
        )

        assert result == "v0 response"
        assert mock_openai.api_key == "test-key"
        mock_openai.ChatCompletion.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.7,
            max_tokens=100,
        )
