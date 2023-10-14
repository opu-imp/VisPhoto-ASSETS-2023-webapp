import io
import os
import json
from datetime import datetime

import numpy as np
import cv2
# import tensorflow as tf

# from darkflow.net.build import TFNet
from google.cloud import vision

from . import eq2cm
from .nelder_mead import optimize_crop_region, optimize_crop_region_free, optimize_crop_region_simple


# 全方位画像上の座標を透視投影画像の座標に変換
def convert_equi_pos_to_pers_pos(X, Y, angle_u, angle_v, pers_size_w, pers_size_h, erp_w, erp_h):
    u = X / erp_w * 2 * np.pi - np.pi
    v = Y / erp_h * np.pi - np.pi / 2

    Rx = np.array([[1, 0, 0], [0, np.cos(v), -np.sin(v)], [0, np.sin(v), np.cos(v)]])
    Ry = np.array([[np.cos(u), 0, np.sin(u)], [0, 1, 0], [-np.sin(u), 0, np.cos(u)]])
    R = np.dot(Ry, Rx)

    xyz = np.dot(R, np.array([0, 0, 1]))
    x, y, z = xyz.tolist()

    Rx = np.array([[1, 0, 0], [0, np.cos(angle_v), -np.sin(angle_v)], [0, np.sin(angle_v), np.cos(angle_v)]])
    Ry = np.array([[np.cos(angle_u), 0, np.sin(angle_u)], [0, 1, 0], [-np.sin(angle_u), 0, np.cos(angle_u)]])
    R = np.dot(Ry, Rx)

    cxyz = np.dot(np.linalg.inv(R), np.array([x, y, z]))
    cx, cy, cz = (cxyz / cxyz[2]).tolist()

    fov = np.pi/2
    px = (cx + np.tan(fov / 2)) / (np.tan(fov / 2) * 2 / (pers_size_w - 1))
    py = (-cy + np.tan(fov / 2)) / (np.tan(fov / 2) * 2 / (pers_size_h - 1))

    return [px, py]


# ユーザーの選択結果をリストに入れる
def apply_selection_level(obj_list, nouns):
    # for idx, obj in enumerate(obj_list):
    #     obj['choice'] = selection['object' + str(idx)]

    for obj in obj_list:
        if obj['label_japanese'] in nouns:
            obj['choice'] = '0'
        else:
            obj['choice'] = '1'


# 写真として適切な領域を切り取る
# def crop_image(usr_name, img_name, objects, selection, now):
def crop_image(erp_img, objects, nouns, result_dir):
    obj_list = []
    for clock, ll in objects.items():
        for obj in ll['objects']:
            obj_list.append({
              'label': obj['label'],
              'label_japanese': obj['label_japanese'],
              'clock': clock,
              'x': obj['x'],
              'y': obj['y'],
              'x_min': obj['x_min'],
              'y_min': obj['y_min'],
              'x_max': obj['x_max'],
              'y_max': obj['y_max'],
              'choice': None
            })

    apply_selection_level(obj_list, nouns)
    selected = [obj for obj in obj_list if obj['choice'] == '0']
    erp_h, erp_w = erp_img.shape[:2]

    if len(selected) > 0:
        x_mean = sum([item['x'] for item in selected]) / len(selected)
        y_mean = sum([item['y'] for item in selected]) / len(selected)
    else:
        x_mean = erp_w / 2
        y_mean = erp_h / 2

    print(x_mean, y_mean)

    angle_u = x_mean / erp_w * 2 * np.pi - np.pi
    angle_v = y_mean / erp_h * np.pi - np.pi / 2
    print('angle_u', angle_u)
    print('angle_v', angle_v)

    # 選択された物体の平均位置を中央とする画像を生成する
    pers_size = 1600
    # output = eq2cm.eq_to_pers(erp_img, np.pi/2, angle_u, angle_v, pers_size, pers_size)
    output = eq2cm.eq_to_pers(erp_img, np.pi/2, np.pi/2, angle_u, angle_v, pers_size, pers_size)
    cv2.imwrite(os.path.join(result_dir, 'target.jpg'), output)

    # 透視投影上の画像に変換する
    for obj in obj_list:
        cx_min, cy_min = convert_equi_pos_to_pers_pos(obj['x_min'], obj['y_min'], angle_u, angle_v, pers_size, pers_size, erp_w, erp_h)
        cx_max, cy_max = convert_equi_pos_to_pers_pos(obj['x_max'], obj['y_max'], angle_u, angle_v, pers_size, pers_size, erp_w, erp_h)
        obj['tlx'] = cx_min
        obj['tly'] = cy_min
        obj['brx'] = cx_max
        obj['bry'] = cy_max

    # 切り取り位置の最適化する
    # rect1 = optimize_crop_region(output, obj_list, vfn=True)
    # rect2 = optimize_crop_region(output, obj_list, vfn=False)
    # rect3 = optimize_crop_region_free(output, obj_list, vfn=True)
    # rect4 = optimize_crop_region_free(output, obj_list, vfn=False)
    rect5 = optimize_crop_region_simple(output, obj_list)

    # 画像を保存する
    # cv2.imwrite(os.path.join(result_dir, 'result.jpg'), output[rect1[1]:rect1[3], rect1[0]:rect1[2]])
    # cv2.imwrite(os.path.join(result_dir, 'result_without_vfn.jpg'), output[rect2[1]:rect2[3], rect2[0]:rect2[2]])
    # cv2.imwrite(os.path.join(result_dir, 'result_free.jpg'), output[rect3[1]:rect3[3], rect3[0]:rect3[2]])
    # cv2.imwrite(os.path.join(result_dir, 'result_free_without_vfn.jpg'), output[rect4[1]:rect4[3], rect4[0]:rect4[2]])
    cv2.imwrite(os.path.join(result_dir, 'result.jpg'), output[rect5[1]:rect5[3], rect5[0]:rect5[2]])

    return obj_list
