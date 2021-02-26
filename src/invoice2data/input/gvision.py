# -*- coding: utf-8 -*-
def to_text(path, bucket_name="cloud-vision-84893", language="fr"):
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
    # https://cloud.google.com/vision/docs/pdf?hl=en
    import os
    from google.cloud import vision
    from google.cloud import storage
    from google.protobuf import json_format
    import re, json
    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "application/pdf"
    path_dir, filename = os.path.split(path)
    result_blob_basename = filename.replace(".pdf", "").replace(".PDF", "")
    # TODO json output name can be changed by Gcloud
    result_blob_name = result_blob_basename + "/output-1-to-2.json"
    result_blob_uri = "gs://{}/{}/".format(bucket_name, result_blob_basename)
    input_blob_uri = "gs://{}/{}".format(bucket_name, filename)

    # Upload file to gcloud if it doesn't exist yet
    storage_client = storage.Client()
    # TODO bucket name has to be parametrizable (args?)
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

        print('Waiting for the operation to finish.')
        operation.result(timeout=420)
    # Recover JSON result file from gcloud bucket
    # TODO possible update to apiv1 that works without intermediate gcloud buckets
    storage_client = storage.Client()
    match = re.match(r'gs://([^/]+)/(.+)', result_blob_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)
    bucket = storage_client.get_bucket(bucket_name)
    blob_list = list(bucket.list_blobs(prefix=prefix))
    print('Output files:')
    for blob in blob_list:
        print(blob.name)
    output = blob_list[0]
    json_string = output.download_as_string()
    response = json.loads(json_string)
    # Each page of the pdf has different json nodes
    # concatenate all pdf text pages
    pdf_text = ''
    for response in response['responses']:
        annotation = response['fullTextAnnotation']
        pdf_text += annotation['text']
    return pdf_text.encode('utf-8')
