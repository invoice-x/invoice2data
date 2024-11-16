import os
import unittest
from unittest.mock import patch, MagicMock

from invoice2data.input import gvision


class TestGvisionToText(unittest.TestCase):

    @patch('google.cloud.storage.Client')
    @patch('google.cloud.vision.ImageAnnotatorClient')
    def test_to_text(self, mock_vision_client, mock_storage_client):
        # Set up mock objects
        mock_bucket = MagicMock()
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_bucket.exists.return_value = False  # Simulate file not existing

        mock_result_blob = MagicMock()
        mock_result_blob.download_as_string.return_value = b'{"responses": [{"full_text_annotation": {"text": "test text"}}]}'
        mock_bucket.get_blob.return_value = mock_result_blob

        mock_async_response = MagicMock()
        mock_vision_client.return_value.async_batch_annotate_files.return_value = mock_async_response
        mock_async_response.result.return_value = None

        # Call the function
        path = 'test.pdf'
        extracted_text = gvision.to_text(path)

        # Assertions
        mock_storage_client.return_value.get_bucket.assert_called_once_with('cloud-vision-84893')
        mock_bucket.exists.assert_called_once_with('test.pdf')
        mock_blob.upload_from_filename.assert_called_once_with('test.pdf')
        mock_vision_client.return_value.async_batch_annotate_files.assert_called_once()
        mock_async_response.result.assert_called_once_with(timeout=180)
        mock_result_blob.download_as_string.assert_called_once()
        self.assertEqual(extracted_text, 'test text')

    @patch('google.cloud.storage.Client')
    def test_to_text_existing_result(self, mock_storage_client):
        # Set up mock objects
        mock_bucket = MagicMock()
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket
        mock_result_blob = MagicMock()
        mock_result_blob.download_as_string.return_value = b'{"responses": [{"full_text_annotation": {"text": "cached text"}}]}'
        mock_bucket.get_blob.return_value = mock_result_blob

        # Call the function
        path = 'test.pdf'
        extracted_text = gvision.to_text(path)

        # Assertions
        mock_storage_client.return_value.get_bucket.assert_called_once_with('cloud-vision-84893')
        mock_bucket.get_blob.assert_called_once()
        self.assertEqual(extracted_text, 'cached text')

if __name__ == '__main__':
    unittest.main()
