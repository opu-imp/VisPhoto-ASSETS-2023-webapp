import io
import json
import os
import random
import sys

import cv2
import numpy as np
import requests
# from darkflow.net.build import TFNet
from google.cloud import vision

from utils import detect_objects, eq2cm, translate_to_japanese


# 長方形の面積を返す
def area(x1, y1, x2, y2):
    return (x2 - x1) * (y2 - y1)


# 矩形の重なっている面積を返す
def intersection_area(i_x1, i_y1, i_x2, i_y2, j_x1, j_y1, j_x2, j_y2):
    xA = max(i_x1, j_x1)
    yA = max(i_y1, j_y1)
    xB = min(i_x2, j_x2)
    yB = min(i_y2, j_y2)
    return max(0, xB - xA) * max(0, yB - yA)


# IoUを返す
def IoU(i_x1, i_y1, i_x2, i_y2, j_x1, j_y1, j_x2, j_y2):
    s = intersection_area(i_x1, i_y1, i_x2, i_y2, j_x1, j_y1, j_x2, j_y2)
    return s / float(area(i_x1, i_y1, i_x2, i_y2) + area(j_x1, j_y1, j_x2, j_y2) - s)


if __name__ == '__main__':
    args = sys.argv
    input_path = args[1]
    output_dir = args[2]

    # 全方位画像のサイズ
    erp_img = cv2.imread(input_path)
    erp_h, erp_w = erp_img.shape[:2]
    print('width: ' + str(erp_w) + ', height: ' + str(erp_h))

    pers_img_w = 800
    pers_img_h = 800

    # 出力結果を保存するディレクトリがなければ新しく作成する
    for dir_name in ['pers_img', 'bbox_img']:
        dst_dir = os.path.join(output_dir, dir_name)
        if not os.path.isdir(dst_dir):
            os.makedirs(dst_dir)

    # 歪みがない画像を生成して保存する
    for v in [-1, 0, 1]:
        for u in [-4, -3, -2, -1, 0, 1, 2, 3]:
            pers_img = eq2cm.eq_to_pers(erp_img, np.pi/2, np.pi/2, u*np.pi/4, v*np.pi/6, pers_img_w, pers_img_h)
            cv2.imwrite(os.path.join(output_dir, 'pers_img', str(v+1) + '_' + str(u+4) + '.jpg'), pers_img)


    # それぞれの画像に物体検出を行う
    predictions = []

    # それぞれのアングルの画像に物体検出を行う
    for v in [-1, 0, 1]:
        for u in [-4, -3, -2, -1, 0, 1, 2, 3]:
            file_path = os.path.join(output_dir, 'pers_img', str(v+1) + '_' + str(u+4) + '.jpg')
            pers_img = cv2.imread(file_path)

            objects = detect_objects(file_path)

            for object_ in objects:
                label = object_['label']
                if label == 'Television':
                    label = 'Computer monitor'

                label_japanese = translate_to_japanese(label)
                tlx = object_['tlx']
                tly = object_['tly']
                brx = object_['brx']
                bry = object_['bry']

                cv2.rectangle(pers_img, (tlx, tly), (brx, bry), (255, 0, 0), 2)
                cv2.rectangle(pers_img, (tlx, tly - 30), (tlx + 200, tly + 5), (255, 0, 0), -1)
                cv2.putText(pers_img, label, (tlx, tly), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 1)

                gx = int((tlx + brx) / 2)
                gy = int((tly + bry) / 2)

                ey1, ex1 = eq2cm.get_original_pos(tlx, tly, np.pi/2, np.pi/2, u*np.pi/4, v*np.pi/6, pers_img_w, pers_img_h, erp_w, erp_h)
                ey2, ex2 = eq2cm.get_original_pos(brx, tly, np.pi/2, np.pi/2, u*np.pi/4, v*np.pi/6, pers_img_w, pers_img_h, erp_w, erp_h)
                ey3, ex3 = eq2cm.get_original_pos(tlx, bry, np.pi/2, np.pi/2, u*np.pi/4, v*np.pi/6, pers_img_w, pers_img_h, erp_w, erp_h)
                ey4, ex4 = eq2cm.get_original_pos(brx, bry, np.pi/2, np.pi/2, u*np.pi/4, v*np.pi/6, pers_img_w, pers_img_h, erp_w, erp_h)

                predictions.append({
                    'label': label,
                    'label_japanese': label_japanese,
                    'p1': {'x': int(ex1), 'y': int(ey1)},
                    'p2': {'x': int(ex2), 'y': int(ey2)},
                    'p3': {'x': int(ex3), 'y': int(ey3)},
                    'p4': {'x': int(ex4), 'y': int(ey4)},
                    'members': [],
                    'group': -1
                })

            cv2.imwrite(os.path.join(output_dir, 'bbox_img', str(v+1) + '_' + str(u+4) + '.jpg'), pers_img)


    # 全方位画像上で端にある物体の座標を整理
    for idx, obj in enumerate(predictions):
        p1 = obj['p1']
        p2 = obj['p2']
        p3 = obj['p3']
        p4 = obj['p4']

        if (p1['x'] > p2['x']):
            p2['x'] += erp_w
        if (p3['x'] > p4['x']):
            p4['x'] += erp_w

        if p3['x'] - p1['x'] > erp_w / 2:
            p3['x'] -= erp_w
            p4['x'] -= erp_w
        elif p1['x'] - p3['x'] > erp_w / 2:
            p3['x'] += erp_w
            p4['x'] += erp_w

        tlx = min(p1['x'], p3['x'])
        tly = min(p1['y'], p2['y'])
        brx = max(p2['x'], p4['x'])
        bry = max(p3['y'], p4['y'])

        obj['tlx'] = tlx
        obj['tly'] = tly
        obj['brx'] = brx
        obj['bry'] = bry

    # バウンディングボックスの重なり具合で検出結果をグループ分け
    for i in range(0, len(predictions)):
        for j in range(i + 1, len(predictions)):
            if predictions[i]['label'] == predictions[j]['label']:
                i_x1 = predictions[i]['tlx']
                i_y1 = predictions[i]['tly']
                i_x2 = predictions[i]['brx']
                i_y2 = predictions[i]['bry']
                j_x1 = predictions[j]['tlx']
                j_y1 = predictions[j]['tly']
                j_x2 = predictions[j]['brx']
                j_y2 = predictions[j]['bry']

                area_i = area(i_x1, i_y1, i_x2, i_y2)
                area_j = area(j_x1, j_y1, j_x2, j_y2)
                iou = IoU(i_x1, i_y1, i_x2, i_y2, j_x1, j_y1, j_x2, j_y2)
                s = intersection_area(i_x1, i_y1, i_x2, i_y2, j_x1, j_y1, j_x2, j_y2)

                if iou > 0.5 or s / float(area_i) > 0.5 or s / float(area_j) > 0.5:
                    for m in predictions[i]['members']:
                        predictions[m]['members'].append(j)
                    predictions[i]['members'].append(j)
                    for m in predictions[j]['members']:
                        predictions[m]['members'].append(i)
                    predictions[j]['members'].append(i)

    # 同じグループに属する物体を統合
    type_num = 0
    labels = []
    for i in range(len(predictions)):
        if predictions[i]['group'] == -1:
            predictions[i]['group'] = type_num
            labels.append(predictions[i]['label'])
            for p in predictions[i]['members']:
                predictions[p]['group'] = type_num
            type_num += 1

    # for item in predictions:
    #     print(item)
    # print(type_num)

    objects_unified = []

    padding = int(erp_w * 0.1)
    result_img = np.zeros((erp_h, erp_w + 2 * padding, 3))
    result_img[:, padding:erp_w + padding, :] = erp_img

    for t in range(type_num):
        objects = [item for item in predictions if item['group'] == t]
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        # for obj in objects:
        #     cv2.rectangle(erp_img, (obj['tlx'], obj['tly']), (obj['brx'], obj['bry']), color, 12)
        x_min = min([obj['tlx'] for obj in objects])
        y_min = min([obj['tly'] for obj in objects])
        x_max = max([obj['brx'] for obj in objects])
        y_max = max([obj['bry'] for obj in objects])
        # print(t)

        objects_unified.append({
            'label': objects[0]['label'],
            'label_japanese': objects[0]['label_japanese'],
            'x': (x_min + x_max) / 2,
            'y': (y_min + y_max) / 2,
            'x_min': x_min,
            'y_min': y_min,
            'x_max': x_max,
            'y_max': y_max
        })

        cv2.rectangle(result_img, (x_min + padding, y_min), (x_max + padding, y_max), color, 20)
        cv2.rectangle(result_img, (x_min + padding, y_min - 100), (x_min + padding + 600, y_min + 5), color, -1)
        cv2.putText(result_img, objects[0]['label'], (x_min + padding, y_min), cv2.FONT_HERSHEY_DUPLEX, 4, (255, 255, 255), 8, cv2.LINE_AA)
    cv2.imwrite(os.path.join(output_dir, 'plot2.jpg'), result_img)

    # クロックポジションで物体を分ける
    clock_pos = {}

    # 何時方向か
    for i in range(11, 23):
        clock = str(i % 12 + 1)
        clock_pos['clock_' + clock.zfill(2)] = {
            'clock': clock,
            'objects': [],
        }

    # 物体の振り分け
    for obj in objects_unified:
        if erp_w * 11 / 24 <= obj['x'] < erp_w * 13 / 24:
            clock_pos['clock_12']['objects'].append(obj)
        elif erp_w * 13 / 24 <= obj['x'] < erp_w * 15 / 24:
            clock_pos['clock_01']['objects'].append(obj)
        elif erp_w * 15 / 24 <= obj['x'] < erp_w * 17 / 24:
            clock_pos['clock_02']['objects'].append(obj)
        elif erp_w * 17 / 24 <= obj['x'] < erp_w * 19 / 24:
            clock_pos['clock_03']['objects'].append(obj)
        elif erp_w * 19 / 24 <= obj['x'] < erp_w * 21 / 24:
            clock_pos['clock_04']['objects'].append(obj)
        elif erp_w * 21 / 24 <= obj['x'] < erp_w * 23 / 24:
            clock_pos['clock_05']['objects'].append(obj)
        elif erp_w * 1 / 24 <= obj['x'] < erp_w * 3 / 24:
            clock_pos['clock_07']['objects'].append(obj)
        elif erp_w * 3 / 24 <= obj['x'] < erp_w * 5 / 24:
            clock_pos['clock_08']['objects'].append(obj)
        elif erp_w * 5 / 24 <= obj['x'] < erp_w * 7 / 24:
            clock_pos['clock_09']['objects'].append(obj)
        elif erp_w * 7 / 24 <= obj['x'] < erp_w * 9 / 24:
            clock_pos['clock_10']['objects'].append(obj)
        elif erp_w * 9 / 24 <= obj['x'] < erp_w * 11 / 24:
            clock_pos['clock_11']['objects'].append(obj)
        else:
            clock_pos['clock_06']['objects'].append(obj)

    # 物体検出の結果をjsonファイルとして出力する
    with open(os.path.join(output_dir, 'objects.json'), mode='w', encoding='utf-8') as f:
        json.dump({'detection': clock_pos}, f, indent=2, ensure_ascii=False)
