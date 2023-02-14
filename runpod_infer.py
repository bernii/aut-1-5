''' infer.py for runpod worker '''

import os
import requests
import uuid
import base64
from io import BytesIO

import runpod
from runpod.serverless.utils import upload, validator, download, rp_cleanup

from utils import parallel_upload


INPUT_VALIDATIONS = {
    'prompt': {
        'type': str,
        'required': True
    },
    'negative_prompt': {
        'type': str,
        'required': False
    },
    # 'width': {
    #     'type': int,
    #     'required': True
    # },
    # 'height': {
    #     'type': int,
    #     'required': True
    # },
    'image': {
        'type': str,
        'required': True
    },
    'mask': {
        'type': str,
        'required': False
    },
    'num_outputs': {
        'type': int,
        'required': False
    },
    'num_inference_steps': {
        'type': int,
        'required': False
    },
    'guidance_scale': {
        'type': float,
        'required': False
    },
    'scheduler': {
        'type': str,
        'required': False
    },
    'seed': {
        'type': int,
        'required': False
    },
    'nsfw': {
        'type': bool,
        'required': False
    },
    'group_id': {
        'type': str,
        'required': True
    },
}

def get_results(
    prompt,
    negative_prompt,
    # width=job_input.get('width', 512),
    # height=job_input.get('height', 512),
    image,
    mask,
    # prompt_strength=job_input.get('prompt_strength', 0.8),
    num_outputs,
    num_inference_steps,
    # guidance_scale,
    scheduler,
    seed):


    with open(image, "rb") as img_file:
        init_image = base64.b64encode(img_file.read()).decode('utf-8')

    with open(mask, "rb") as img_file:
        mask = base64.b64encode(img_file.read()).decode('utf-8')

    print("What is it?", type(init_image))

    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "sampler_index": scheduler,
        "denoising_strength": 0.75,
        "init_images": [init_image],
        "mask": mask,
        "include_init_images": True,
        "batch_size": num_outputs,
        "steps": num_inference_steps,

        # "script_name": "SD upscale",
        # "script_args": ["", 64, "ESRGAN_4x", 3],
        # "batch_size": 1,
        # "denoising_strength": 0.12,
        # "steps": 20, 
        # quick testing only ^ should be ~100 and EULER a maybe?
    }


    resp = requests.post(url="http://localhost:7860/sdapi/v1/img2img/", json=params).json()

    print("RESP IS ", resp.keys())
    print("LETS SEE", resp.get('detail', ""))

    img_paths = []
    for i in resp['images']:
        # TODO: change to file
        bytesio = BytesIO(base64.b64decode(i))
        # save to disk
        file_extension = ".png"
        filename = f'/output/{str(uuid.uuid4()).replace("-", "")}{file_extension}'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'wb') as output_file:
            output_file.write(bytesio.getbuffer())
        # img.show()
        print("Writing to file", filename)
        img_paths.append(filename)

    return img_paths


def run(job):
    '''
    Run inference on the model.
    Returns output path, width the seed used to generate the image.
    '''
    job_input = job['input']


    input_errors = validator.validate(job_input, INPUT_VALIDATIONS)
    if input_errors:
        return {"error": input_errors}

    job_input['seed'] = job_input.get('seed', int.from_bytes(os.urandom(2), "big"))

    # MODEL.NSFW = job_input.get('nsfw', True)

    # Download input objects
    # or change to base64 ? 
    job_input['image'], job_input['mask'] = download.download_input_objects(
        [job_input.get('image', None), job_input.get('mask', None)]
    )  # pylint: disable=unbalanced-tuple-unpacking


    img_paths = get_results(
        prompt=job_input["prompt"],
        negative_prompt=job_input.get("negative_prompt", None),
        # width=job_input.get('width', 512),
        # height=job_input.get('height', 512),
        image=job_input['image'],
        mask=job_input['mask'],
        # prompt_strength=job_input.get('prompt_strength', 0.8),
        num_outputs=job_input.get('num_outputs', 1),
        num_inference_steps=job_input.get('num_inference_steps', 50),
        # guidance_scale=job_input.get('guidance_scale', 7.5),
        scheduler=job_input.get('scheduler', "DDIM"),
        seed=job_input.get('seed', None)
    )

    job_output = parallel_upload(job_input['group_id'], img_paths)
    rp_cleanup.clean(['input_objects'])

    return job_output

runpod.serverless.start({"handler": run})
