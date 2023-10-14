import os
import sys

import cv2
import numpy as np


if __name__ == '__main__':
    args = sys.argv

    input_path = args[1]
    output_dir = args[2]

    input_img = cv2.imread(input_path)
    img_h, img_w = input_img.shape[:2]

    thumbnail_w = int(args[3])
    thumbnail_h = int(img_h * thumbnail_w / img_w)

    thumbnail = cv2.resize(input_img, (thumbnail_w, thumbnail_h))
    cv2.imwrite(os.path.join(output_dir, 'thumbnail.jpg'), thumbnail)
