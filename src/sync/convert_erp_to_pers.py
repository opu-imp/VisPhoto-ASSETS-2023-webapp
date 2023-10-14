import os
import sys
import cv2
import numpy as np

import erp2pers_vfov180


if __name__ == '__main__':
    args = sys.argv
    input_path = args[1]
    output_dir = args[2]

    erp_img = cv2.imread(input_path)
    erp_h, erp_w = erp_img.shape[:2]
    print('width: ' + str(erp_w) + ', height: ' + str(erp_h))

    pers_img_w = 1200
    pers_img_h = 2400

    dst_dir = os.path.join(output_dir, 'pers_img')
    os.makedirs(dst_dir)

    for u in [-4, -3, -2, -1, 0, 1, 2, 3]:
        pers_img = erp2pers_vfov180.erp_to_pers(erp_img, np.pi/1.3, u*np.pi/4, 0, pers_img_w, pers_img_h)
        cv2.imwrite(os.path.join(dst_dir, str(u+4) + '.jpg'), pers_img)
