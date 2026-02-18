import unittest
from unittest.mock import patch, MagicMock
from heidi_engine.telemetry import start_http_server

class TestHTTPHostBinding(unittest.TestCase):
    @patch('http.server.HTTPServer')
    @patch('threading.Thread')
    def test_start_http_server_binds_to_correct_host(self, mock_thread, mock_httpserver):
        # Test default host
        start_http_server(port=7780)
        # The inner function run_server is where HTTPServer is called.
        # It's called in a thread, so we need to trigger it.

        target_func = mock_thread.call_args[1]['target']
        target_func() # This calls run_server()

        mock_httpserver.assert_called_once()
        args, kwargs = mock_httpserver.call_args
        self.assertEqual(args[0], ("127.0.0.1", 7780))

    @patch('http.server.HTTPServer')
    @patch('threading.Thread')
    def test_start_http_server_binds_to_custom_host(self, mock_thread, mock_httpserver):
        # Test custom host
        start_http_server(port=7781, host="0.0.0.0")

        target_func = mock_thread.call_args[1]['target']
        target_func() # This calls run_server()

        mock_httpserver.assert_called_once()
        args, kwargs = mock_httpserver.call_args
        self.assertEqual(args[0], ("0.0.0.0", 7781))

if __name__ == '__main__':
    unittest.main()
