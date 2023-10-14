import io

import cv2
# from darkflow.net.build import TFNet
from google.cloud import vision


# 画像に含まれる物体を検出する
def detect_objects(image_path, mode='gcp'):

    detected_objects = []

    if mode == 'gcp':
        client = vision.ImageAnnotatorClient()
        with io.open(image_path, 'rb') as f:
            content = f.read()
        image = vision.Image(content=content)
        objects = client.object_localization(image=image).localized_object_annotations
        print('Number of objects found: {}'.format(len(objects)))

        pers_img = cv2.imread(image_path)
        pers_img_h, pers_img_w = pers_img.shape[:2]

        for object_ in objects:
            if object_.score > 0.5:
                label = object_.name
                tlx = int(object_.bounding_poly.normalized_vertices[0].x * pers_img_w)
                tly = int(object_.bounding_poly.normalized_vertices[0].y * pers_img_h)
                brx = int(object_.bounding_poly.normalized_vertices[2].x * pers_img_w)
                bry = int(object_.bounding_poly.normalized_vertices[2].y * pers_img_h)
                detected_objects.append({'label': label, 'tlx': tlx, 'tly': tly, 'brx': brx, 'bry': bry})

    elif mode == 'darkflow':
        pers_img = cv2.imread(image_path)
        options = {'model': 'cfg/yolo.cfg', 'load': 'yolo.weights', 'threshold': 0.1, 'GPU': 1.0}
        tfnet = TFNet(options)
        result = tfnet.return_predict(pers_img)

        for item in result:
            if item['confidence'] > 0.5:
                label = item['label']
                tlx = item['topleft']['x']
                tly = item['topleft']['y']
                brx = item['bottomright']['x']
                bry = item['bottomright']['y']
                detected_objects.append({'label': label, 'tlx': tlx, 'tly': tly, 'brx': brx, 'bry': bry})

    else:
        print('unknown mode')

    return detected_objects
