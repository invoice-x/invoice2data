# -*- coding: utf-8 -*-
def to_text(path, bucket_name="cloud-vision-84893", language="en"):
    """Sends PDF files to Google Cloud Vision for OCR.

    Before using invoice2data, make sure you have the auth json path set as
    env var GOOGLE_APPLICATION_CREDENTIALS

    Parameters
    ----------
    path : str
        path of electronic invoice in JPG or PNG format
    bucket_name : str
        name of bucket to use for file storage and results cache.

    Returns
    -------
    extracted_str : str
        returns extracted text from image in JPG or PNG format

    """

    """OCR with PDF/TIFF as source files on GCS"""
    import os
    from google.cloud import vision
    from google.cloud import storage
    from google.protobuf import json_format

    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "application/pdf"

    path_dir, filename = os.path.split(path)
    result_blob_basename = filename.replace(".pdf", "").replace(".PDF", "")
    result_blob_name = result_blob_basename + "/output-1-to-1.json"
    result_blob_uri = "gs://{}/{}/".format(bucket_name, result_blob_basename)
    input_blob_uri = "gs://{}/{}".format(bucket_name, filename)

    # Upload file to gcloud if it doesn't exist yet
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    if bucket.get_blob(filename) is None:
        blob = bucket.blob(filename)
        blob.upload_from_filename(path)

    # See if result already exists
    # TODO: upload as hash, not filename
    result_blob = bucket.get_blob(result_blob_name)
    if result_blob is None:

        # How many pages should be grouped into each json output file.
        batch_size = 10

        client = vision.ImageAnnotatorClient()

        feature = vision.types.Feature(
            type=vision.enums.Feature.Type.DOCUMENT_TEXT_DETECTION
        )

        gcs_source = vision.types.GcsSource(uri=input_blob_uri)
        input_config = vision.types.InputConfig(
            gcs_source=gcs_source, mime_type=mime_type
        )

        gcs_destination = vision.types.GcsDestination(uri=result_blob_uri)
        output_config = vision.types.OutputConfig(
            gcs_destination=gcs_destination, batch_size=batch_size
        )

        async_request = vision.types.AsyncAnnotateFileRequest(
            features=[feature], input_config=input_config, output_config=output_config
        )

        operation = client.async_batch_annotate_files(requests=[async_request])

        print("Waiting for the operation to finish.")
        operation.result(timeout=180)

    # Get result after OCR is completed
    result_blob = bucket.get_blob(result_blob_name)

    json_string = result_blob.download_as_string()
    response = json_format.Parse(json_string, vision.types.AnnotateFileResponse())

    # The actual response for the first page of the input file.
    first_page_response = response.responses[0]
    annotation = first_page_response.full_text_annotation

    return annotation.text.encode("utf-8")
