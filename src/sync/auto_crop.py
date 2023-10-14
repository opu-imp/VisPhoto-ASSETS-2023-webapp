from datetime import datetime, timedelta, timezone
import json
import os
import sys

import cv2

from utils import detect_objects, translate_to_japanese
from utils.photo import crop_image


if __name__ == '__main__':
    args = sys.argv
    input_path = args[1]
    output_dir = args[2]

    with open(os.path.join(output_dir, 'objects.json'), mode='r') as f:
        json_dict = json.load(f)

    now = datetime.now(timezone(timedelta(hours=9), 'JST')).strftime('%Y-%m-%d--%H-%M-%S %z')
    result_dir = os.path.join(output_dir, 'results', now)
    os.makedirs(result_dir)

    erp_img = cv2.imread(input_path)
    obj_list = crop_image(erp_img, json_dict['detection'], json_dict['nouns'], result_dir)

    gcp_objects = detect_objects(os.path.join(result_dir, 'result.jpg'))

    gcp_list_en = list(set([object['label'] for object in gcp_objects]))
    gcp_list_jp = [translate_to_japanese(label) for label in gcp_list_en]

    log_dict = {}
    log_dict['objects'] = obj_list
    log_dict['gcp_list_en'] = gcp_list_en
    log_dict['gcp_list_jp'] = gcp_list_jp

    with open(os.path.join(result_dir, 'log.json'), mode='w', encoding='utf-8') as f:
        json.dump(log_dict, f, indent=2, ensure_ascii=False)
