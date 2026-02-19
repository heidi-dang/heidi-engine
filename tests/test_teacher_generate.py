import asyncio
import os
import sys
import pytest
import time
import importlib.util
from unittest.mock import AsyncMock, MagicMock, patch

# Import the script with numeric filename
spec = importlib.util.spec_from_file_location("teacher_generate", os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts/01_teacher_generate.py')))
teacher_generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(teacher_generate)

call_teacher_model_async = teacher_generate.call_teacher_model_async
generate_sample_async = teacher_generate.generate_sample_async
generate_dataset_async = teacher_generate.generate_dataset_async

@pytest.fixture
def mock_openai_client():
    with patch('openai.AsyncOpenAI') as mock_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock()
        mock_client.close = AsyncMock()
        mock_class.return_value = mock_client
        yield mock_client

@pytest.mark.asyncio
async def test_concurrency_benefit(mock_openai_client):
    """Verify that concurrent execution is faster than sequential."""
    with patch.object(teacher_generate, 'PROMPT_TEMPLATES', [{'template': 'test', 'task_type': 'test', 'instruction': 'test'}]), \
         patch.object(teacher_generate, 'SYNTHETIC_CODE_SAMPLES', ['sample']), \
         patch('asyncio.sleep', return_value=None):

        async def delayed_response(*args, **kwargs):
            # Real sleep to measure time
            await asyncio.get_event_loop().run_in_executor(None, time.sleep, 0.1)
            mock_res = MagicMock()
            mock_res.choices = [MagicMock()]
            mock_res.choices[0].message.content = "mocked response"
            return mock_res

        mock_openai_client.chat.completions.create.side_effect = delayed_response

        # Test with concurrency 1
        os.environ["HEIDI_CONCURRENCY"] = "1"
        start_time = time.time()
        await generate_dataset_async(4, 1, "gpt-4o", "fake-key", 100, 42, "python")
        duration_seq = time.time() - start_time

        # Test with concurrency 4
        os.environ["HEIDI_CONCURRENCY"] = "4"
        start_time = time.time()
        await generate_dataset_async(4, 1, "gpt-4o", "fake-key", 100, 42, "python")
        duration_conc = time.time() - start_time

        print(f"Sequential duration: {duration_seq:.4f}s")
        print(f"Concurrent duration: {duration_conc:.4f}s")

        assert duration_conc < duration_seq
        assert duration_conc < 0.3

@pytest.mark.asyncio
async def test_stable_output_order(mock_openai_client):
    """Verify that output ordering remains stable by sample index."""
    with patch.object(teacher_generate, 'PROMPT_TEMPLATES', [{'template': 'test', 'task_type': 'test', 'instruction': 'test'}]), \
         patch.object(teacher_generate, 'SYNTHETIC_CODE_SAMPLES', ['sample']):

        mock_openai_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="response"))]
        )

        samples = await generate_dataset_async(5, 1, "gpt-4o", "fake-key", 100, 42, "python")

        ids = [s["id"] for s in samples]
        expected_ids = [f"round_1_{i:04d}" for i in range(5)]
        assert ids == expected_ids

@pytest.mark.asyncio
async def test_retry_logic():
    """Verify that retry logic works for API failures."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.side_effect = [
        Exception("Error 1"),
        Exception("Error 2"),
        MagicMock(choices=[MagicMock(message=MagicMock(content="success"))])
    ]

    os.environ["HEIDI_MAX_RETRIES"] = "2"
    with patch('asyncio.sleep', return_value=None):
        result = await call_teacher_model_async("prompt", "gpt-4o", mock_client, 100, "python")

    assert result == "success"
    assert mock_client.chat.completions.create.call_count == 3

@pytest.mark.asyncio
async def test_fallback_on_total_failure():
    """Verify fallback to synthetic response after max retries."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock()
    mock_client.chat.completions.create.side_effect = Exception("Permanent failure")

    os.environ["HEIDI_MAX_RETRIES"] = "1"
    with patch('asyncio.sleep', return_value=None):
        result = await call_teacher_model_async("prompt", "gpt-4o", mock_client, 100, "python")

    result_lower = result.lower()
    keywords = ["implementation", "logic", "analyzed", "sure", "task complete"]
    assert any(k in result_lower for k in keywords)
    assert mock_client.chat.completions.create.call_count == 2
