import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from heidi_engine.telemetry import estimate_cost, load_pricing_config, DEFAULT_PRICING

class TestCostEstimation:
    """Test suite for cost estimation logic in telemetry.py."""

    def test_estimate_cost_gpt4o_mini(self):
        """Test cost estimation for gpt-4o-mini (default model)."""
        pricing = DEFAULT_PRICING["gpt-4o-mini"]
        # 1M input, 1M output should be input_price + output_price
        cost = estimate_cost(1_000_000, 1_000_000, "gpt-4o-mini")
        assert cost == pytest.approx(pricing["input"] + pricing["output"])

    def test_estimate_cost_gpt4o(self):
        """Test cost estimation for gpt-4o (default model)."""
        pricing = DEFAULT_PRICING["gpt-4o"]
        # 2M input, 0.5M output
        cost = estimate_cost(2_000_000, 500_000, "gpt-4o")
        expected = (2 * pricing["input"]) + (0.5 * pricing["output"])
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model(self):
        """Test that unknown models return 0.0 cost."""
        cost = estimate_cost(1000, 1000, "non-existent-model")
        assert cost == 0.0

    def test_estimate_cost_zero_tokens(self):
        """Test cost estimation with zero tokens."""
        cost = estimate_cost(0, 0, "gpt-4o")
        assert cost == 0.0

    def test_estimate_cost_custom_pricing(self):
        """Test cost estimation with mocked custom pricing."""
        custom_pricing = {"custom-model": {"input": 1.0, "output": 2.0}}
        with patch("heidi_engine.telemetry.load_pricing_config", return_value=custom_pricing):
            # 1M tokens each
            cost = estimate_cost(1_000_000, 1_000_000, "custom-model")
            assert cost == pytest.approx(3.0)

    def test_estimate_cost_partial_pricing(self):
        """Test cost estimation when pricing config is missing fields."""
        custom_pricing = {"partial-model": {"input": 1.0}}  # output missing
        with patch("heidi_engine.telemetry.load_pricing_config", return_value=custom_pricing):
            cost = estimate_cost(1_000_000, 1_000_000, "partial-model")
            # output price should default to 0
            assert cost == pytest.approx(1.0)

    def test_load_pricing_config_defaults(self):
        """Test that load_pricing_config returns defaults when no file exists."""
        with patch("heidi_engine.telemetry.get_run_dir") as mock_get_run_dir:
            # Point to a non-existent directory
            mock_get_run_dir.return_value = Path("/non/existent/path/that/definitely/does/not/exist")
            with patch("heidi_engine.telemetry.PRICING_CONFIG_PATH", ""):
                pricing = load_pricing_config()
                assert pricing == DEFAULT_PRICING

    def test_load_pricing_config_custom_file(self, tmp_path):
        """Test that load_pricing_config correctly loads and merges custom pricing."""
        custom_pricing = {"new-model": {"input": 5.0, "output": 10.0}}
        pricing_file = tmp_path / "pricing.json"
        with open(pricing_file, "w") as f:
            json.dump(custom_pricing, f)

        with patch("heidi_engine.telemetry.get_run_dir", return_value=tmp_path):
            with patch("heidi_engine.telemetry.PRICING_CONFIG_PATH", ""):
                pricing = load_pricing_config()
                assert "new-model" in pricing
                assert pricing["new-model"] == custom_pricing["new-model"]
                # Should still have default models
                assert "gpt-4o-mini" in pricing
