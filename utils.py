import os
import time
from boto3 import session
from botocore.config import Config
from io import BytesIO
import concurrent.futures
from PIL import Image
import uuid

bucket_session = session.Session()

boto_config = Config(
    signature_version='s3v4',
    retries={
        'max_attempts': 3,
        'mode': 'standard'
    }
)

boto_client = bucket_session.client(
    's3',
    endpoint_url=os.environ.get('BUCKET_ENDPOINT_URL', None),
    aws_access_key_id=os.environ.get('BUCKET_ACCESS_KEY_ID', None),
    aws_secret_access_key=os.environ.get('BUCKET_SECRET_ACCESS_KEY', None),
    config=boto_config
)


def parallel_upload(group_id, file_list):
    '''
    Uploads a list of files in parallel.
    Once all files are uploaded, the function returns the presigned URLs list.
    '''
    print("starting parallel upload for group_id", )

    file_urls = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(__upload_image, group_id, f, 1): f for f in file_list}
        for future in concurrent.futures.as_completed(futures):
            file_urls.append(future.result())

    return file_urls


def __upload_image(group_id, image_location, result_index=0):
    '''
    Upload image to bucket storage.
    '''
    if boto_client is None:
        # Save the output to a file
        print("No bucket endpoint, saving to disk folder 'simulated_uploaded'")

        output = BytesIO()
        img = Image.open(image_location)
        img.save(output, format=img.format)

        os.makedirs("simulated_uploaded", exist_ok=True)
        with open(f"simulated_uploaded/{result_index}.png", "wb") as file_output:
            file_output.write(output.getvalue())

        # if results_list is not None:
        #     results_list[result_index] = f"simulated_uploaded/{result_index}.png"

        return f"simulated_uploaded/{result_index}.png"

    output = BytesIO()
    img = Image.open(image_location)
    img.save(output, format=img.format)

    # bucket = time.strftime('%m-%y')
    bucket = "results"

    # use random str for filenames
    result_index = str(uuid.uuid4()).replace("-", "")

    # Upload to S3
    boto_client.put_object(
        Bucket=f'{bucket}',
        Key=f'{group_id}/{result_index}.png',
        Body=output.getvalue(),
        ContentType="image/png",
        ACL='public-read',
    )

    output.close()


    return f"https://aishoot.fra1.digitaloceanspaces.com/{bucket}/{group_id}/{result_index}.png"

    # presigned_url = boto_client.generate_presigned_url(
    #     'get_object',
    #     Params={
    #         'Bucket': f'{bucket}',
    #         'Key': f'{group_id}/{result_index}.png'
    #     }, ExpiresIn=604800)

    # if results_list is not None:
    #     results_list[result_index] = presigned_url

    # return presigned_url
