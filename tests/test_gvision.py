import sys
from pathlib import Path
from unittest.mock import MagicMock


# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invoice2data.input import gvision


def test_to_text(mocker: "pytest_mock.MockerFixture") -> None:  # type: ignore [name-defined] # noqa
    # Mock the specific classes within google.cloud
    mock_vision_client = mocker.patch(
        "invoice2data.input.gvision.google.cloud.vision.ImageAnnotatorClient"
    )
    mock_storage_client = mocker.patch(
        "invoice2data.input.gvision.google.cloud.storage.Client"
    )

    # Set up mock objects
    mock_bucket = MagicMock()
    mock_storage_client.return_value.get_bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob
    mock_bucket.exists.return_value = False  # Simulate file not existing in the bucket

    # Mock the async_batch_annotate_files call and its result
    mock_async_response = MagicMock()
    mock_vision_client.return_value.async_batch_annotate_files.return_value = (
        mock_async_response
    )
    mock_async_response.result.return_value = None

    # Mock the get_blob call to return a result blob after the OCR operation
    mock_result_blob = MagicMock()
    mock_result_blob.download_as_string.return_value = (
        b'{"responses": [{"full_text_annotation": {"text": "test text"}}]}'
    )
    mock_bucket.get_blob.side_effect = [None, mock_result_blob]

    # Call the function
    path = "test.pdf"
    extracted_text = gvision.to_text(path, bucket_name="cloud-vision-84893")

    # Assertions
    mock_storage_client.return_value.get_bucket.assert_called_once_with(
        "cloud-vision-84893"
    )
    mock_bucket.exists.assert_called_once_with("test.pdf")
    mock_blob.upload_from_filename.assert_called_once_with("test.pdf")
    mock_vision_client.return_value.async_batch_annotate_files.assert_called_once()
    mock_async_response.result.assert_called_once_with(timeout=180)
    mock_result_blob.download_as_string.assert_called_once()
    assert extracted_text == "test text"


def test_to_text_existing_result(mocker: "pytest_mock.MockerFixture") -> None:  # type: ignore [name-defined] # noqa
    # Mock the specific classes within google.cloud
    mock_storage_client = mocker.patch(
        "invoice2data.input.gvision.google.cloud.storage.Client"
    )

    # Set up mock objects
    mock_bucket = MagicMock()
    mock_storage_client.return_value.get_bucket.return_value = mock_bucket

    mock_result_blob = MagicMock()
    mock_result_blob.download_as_string.return_value = (
        b'{"responses": [{"full_text_annotation": {"text": "cached text"}}]}'
    )

    # Mock bucket.get_blob to return the result blob when called with the result blob name
    mock_bucket.get_blob.side_effect = (
        lambda x: mock_result_blob if "output-1-to-1.json" in x else None
    )

    # Call the function
    path = "test.pdf"
    extracted_text = gvision.to_text(path, bucket_name="cloud-vision-84893")

    # Assertions
    mock_storage_client.return_value.get_bucket.assert_called_once_with(
        "cloud-vision-84893"
    )

    # Check if get_blob was called with the expected arguments
    mock_bucket.get_blob.assert_any_call("test/output-1-to-1.json")
    assert extracted_text == "cached text"
