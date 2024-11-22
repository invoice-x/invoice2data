"""Google Cloud Vision input module for invoice2data."""

import logging
import os


logger = logging.getLogger(__name__)


def have_google_cloud():
    try:
        from google.cloud import storage  # noqa: F401
        from google.cloud import vision  # noqa: F401
    except ImportError:
        return False
    return True


def to_text(
    path: str, bucket_name: str = "cloud-vision-84893", language: str = "en"
) -> str:
    """Sends PDF files to Google Cloud Vision for OCR.

    Before using invoice2data, make sure you have the auth JSON path set as
    the environment variable GOOGLE_APPLICATION_CREDENTIALS.

    Args:
        path (str): Path of the electronic invoice in JPG or PNG format.
        bucket_name (str, optional): Name of the bucket to use for file storage
                                     and results cache. Defaults to "cloud-vision-84893".
        language (str, optional): Language to use for OCR. Defaults to "en".

    Returns:
        str: Extracted text from the image in JPG or PNG format.
    """
    if not have_google_cloud():
        logger.warning(
            "Google Cloud Vision API not available. "
            "Install with 'pip install google-cloud-vision' to enable."
        )
        return ""
    else:
        from google.cloud import storage
        from google.cloud import vision
    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "application/pdf"

    path_dir, filename = os.path.split(path)
    result_blob_basename = filename.replace(".pdf", "").replace(".PDF", "")
    result_blob_name = f"{result_blob_basename}/output-1-to-1.json"
    result_blob_uri = f"gs://{bucket_name}/{result_blob_basename}/"
    input_blob_uri = f"gs://{bucket_name}/{filename}"

    # Upload file to Google Cloud Storage if it doesn't exist yet
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    if not bucket.exists(filename):
        blob = bucket.blob(filename)
        blob.upload_from_filename(path)

    # See if the result already exists
    # TODO: upload as hash, not filename
    result_blob = bucket.get_blob(result_blob_name)
    if result_blob is None:
        # How many pages should be grouped into each JSON output file.
        batch_size = 10

        client = vision.ImageAnnotatorClient()

        feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

        gcs_source = vision.GcsSource(uri=input_blob_uri)
        input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

        gcs_destination = vision.GcsDestination(uri=result_blob_uri)
        output_config = vision.OutputConfig(
            gcs_destination=gcs_destination, batch_size=batch_size
        )

        async_request = vision.AsyncAnnotateFileRequest(
            features=[feature], input_config=input_config, output_config=output_config
        )

        operation = client.async_batch_annotate_files(requests=[async_request])

        print("Waiting for the operation to finish.")
        operation.result(timeout=180)

    # Get result after OCR is completed
    result_blob = bucket.get_blob(result_blob_name)

    json_string = result_blob.download_as_string()
    response = vision.AnnotateFileResponse.from_json(json_string)

    # The actual response for the first page of the input file.
    first_page_response = response.responses[0]
    annotation = first_page_response.full_text_annotation

    return annotation.text
