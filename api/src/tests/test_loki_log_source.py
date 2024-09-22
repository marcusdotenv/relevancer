import os
import unittest
from unittest.mock import patch, Mock
import requests
import time
from src.infrastructure.pipeline.impl.loki_log_source import LokiLogSource 
class TestLokiLogSource(unittest.TestCase):

    def setUp(self):
        os.environ['LOG_SOURCE_URL'] = 'http://loki-example-url.com:1111'
        self.__loki_log_source = LokiLogSource()

    @patch('requests.get')
    def test_retrieve_with_success_a_few_logs(self, requests_mock):
        log_data = {
            "data": {
                "result": [
                    { "metric": {"term": "termm1"}, "value": ["an_valid_time_data", "10"] },
                    { "metric": {"term": "termm2"}, "value": ["an_valid_time_data", "5"] }
                ]
            }
        }

        requests_mock.return_value = Mock(status_code=200)
        requests_mock.return_value.json.return_value = log_data

        results = self.__loki_log_source.retrieve()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].term, "termm1")
        self.assertEqual(results[0].frequency, 10)
        self.assertEqual(results[1].term, "termm2")
        self.assertEqual(results[1].frequency, 5)

    @patch('requests.get')
    def test_receive_empty_result_from_loki(self, requests_mock):
        log_data = {"data": {"result": []}}

        requests_mock.return_value = Mock(status_code=200)
        requests_mock.return_value.json.return_value = log_data

        results = self.__loki_log_source.retrieve()
        
        self.assertEqual(results, [])

    @patch('requests.get')
    def test_return_empty_when_error(self, requests_mock):
        requests_mock.side_effect = requests.exceptions.RequestException("An request error")

        results = self.__loki_log_source.retrieve()
        
        self.assertEqual(results, [])
