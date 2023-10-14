import cv2
import numpy as np
# from scipy.optimize import minimize
# import tensorflow as tf

# from .vfn.prediction import evaluate_aesthetic_score


# 長方形を広げる
def expand_rect(x1, y1, x2, y2, w, h, r):
    dw = int(r * w)
    dh = int(r * h)
    #print([x1 - dw, y1 - dh, x2 + dw, y2 + dh])
    return [max(0, x1 - dw), max(0, y1 - dh), min(w, x2 + dw), min(h, y2 + dh)]


# 現在の長方形の座標を返す
def get_current_rect(ix1, iy1, ix2, aspect_ratio, width, height):
    iy2 = int((ix2 - ix1) * aspect_ratio + iy1)

    if ix1 < 0 or iy1 < 0:
        ix1 = max(ix1, 0)
        iy1 = max(iy1, 0)
        dw = ix2 - ix1
        dh = iy2 - iy1
        if dw * aspect_ratio < dh:
            iy2 = dw * aspect_ratio + iy1
            print('exception case 1')
        else:
            ix2 = dh / aspect_ratio + ix1
            print('exception case 2')

    if ix2 >= width or iy2 >= height:
        ix2 = min(ix2, width - 1)
        iy2 = min(iy2, height - 1)
        dw = ix2 - ix1
        dh = iy2 - iy1
        if dw * aspect_ratio < dh:
            iy1 = iy2 - dw * aspect_ratio
            print('exception case 3')
        else:
            ix1 = ix2 - dh / aspect_ratio
            print('exception case 4')
    ix1 = int(ix1)
    iy1 = int(iy1)
    ix2 = int(ix2)
    iy2 = int(iy2)
    print(ix1, iy1, ix2, iy2)
    print((iy2 - iy1) / (ix2 - ix1))
    return([ix1, iy1, ix2, iy2])


# 二つの長方形の重なり具合を返す
def R_IN(rect_x1, rect_y1, rect_x2, rect_y2, obj_x1, obj_y1, obj_x2, obj_y2):
    sx = max([rect_x1, obj_x1])
    sy = max([rect_y1, obj_y1])
    ex = min([rect_x2, obj_x2])
    ey = min([rect_y2, obj_y2])
    w = ex - sx
    h = ey - sy

    if w > 0 and h > 0:
        return (w * h) / ((obj_x2 - obj_x1) * (obj_y2 - obj_y1))
    else:
        return 0


# 切り取り領域を最適化する (アスペクト比は制約あり)
def optimize_crop_region(img, objects, vfn=True, aspect_ratio=0.75):
    # aspect_ratio = 0.75
    pers_size = 800
    width = pers_size
    height = pers_size

    selected = [obj for obj in objects if obj['choice'] == '0']
    # print('selected', selected)

    if len(selected) == 0:
        xx = [0, 0, pers_size]
        rect = get_current_rect(xx[0], xx[1], xx[2], aspect_ratio, pers_size, pers_size)
        return rect
    else:
        x1_init = min([obj['tlx'] for obj in selected])
        y1_init = min([obj['tly'] for obj in selected])
        x2_init = max([obj['brx'] for obj in selected])
        y2_init = max([obj['bry'] for obj in selected])

        x = [0, 0, pers_size]

        # if (x2_init - x1_init) * aspect_ratio > y2_init - y1_init:
        #     dw = x2_init - x1_init
        #     dh = y2_init - y1_init
        #     th = dw * aspect_ratio
        #     diff = th - dh
        #     #t = (x2_init - x1_init) * aspect_ratio + y1_init
        #     print('before', x1_init, y1_init, x2_init, y2_init)
        #     x = expand_rect(x1_init, y1_init - diff / 2, x2_init, y2_init + diff / 2, width, height, 0.1)[:3]
        #     print('after', expand_rect(x1_init, y1_init - diff / 2, x2_init, y2_init + diff / 2, width, height, 0.1))
        #     print('expand_rect case 1')
        # else:
        #     dw = x2_init - x1_init
        #     dh = y2_init - y1_init
        #     tw = dh / aspect_ratio
        #     diff = tw - dw
        #     #t = (y2_init - y1_init) / aspect_ratio + x1_init
        #     print('before', x1_init, y1_init, x2_init, y2_init)
        #     x = expand_rect(x1_init - diff / 2, y1_init, x2_init + diff / 2, y2_init, width, height, 0.1)[:3]
        #     print('after', expand_rect(x1_init, y1_init - diff / 2, x2_init, y2_init + diff / 2, width, height, 0.1))
        #     print('expand_rect case 2')

        x = [0, 0, pers_size]

        # 目的関数
        def RR(x):
            ans = 0
            rect = get_current_rect(x[0], x[1], x[2], aspect_ratio, pers_size, pers_size)
            for obj in objects:
                if obj['choice'] == '0':
                    ans += 1 - R_IN(rect[0], rect[1], rect[2], rect[3], obj['tlx'], obj['tly'], obj['brx'], obj['bry'])
                elif obj['choice'] == '1':
                    ans += 0
                elif obj['choice'] == '2':
                    ans += R_IN(rect[0], rect[1], rect[2], rect[3], obj['tlx'], obj['tly'], obj['brx'], obj['bry'])

            if vfn == True:
                score = evaluate_aesthetic_score(img[rect[1]:rect[3], rect[0]:rect[2], :])
            else:
                score = 1

            print('R_sum', ans)
            print('score', score)
            ans = (ans + 1) / score
            print(ans)
            return ans

        result = minimize(RR, x0=x, method='Nelder-Mead')
        xx = [int(i) for i in result.x]
        print(result.x)

        rect = get_current_rect(xx[0], xx[1], xx[2], aspect_ratio, pers_size, pers_size)
        return rect


# 切り取り領域を最適化する (アスペクト比は制約なし)
def optimize_crop_region_free(img, objects, vfn=True):
    pers_size = 800
    width = pers_size
    height = pers_size

    selected = [obj for obj in objects if obj['choice'] == '0']

    # 目的関数
    def RR(x):
        retval = 0
        rect = [int(value) for value in x]

        for obj in objects:
            if obj['choice'] == '0':
                retval += 1 - R_IN(rect[0], rect[1], rect[2], rect[3], obj['tlx'], obj['tly'], obj['brx'], obj['bry'])
            elif obj['choice'] == '1':
                retval += 0
            elif obj['choice'] == '2':
                retval += R_IN(rect[0], rect[1], rect[2], rect[3], obj['tlx'], obj['tly'], obj['brx'], obj['bry'])

        if rect[0] < 0 or rect[1] < 0 or rect[2] > width - 1 or rect[3] > height - 1:
            retval += 1000000
            score = 0.01
        else:
            if vfn == True:
                score = evaluate_aesthetic_score(img[rect[1]:rect[3], rect[0]:rect[2], :])
            else:
                score = 1

        # print('R_sum', retval)
        # print('score', score)

        retval = (retval + 1) / score
        return retval

    if len(selected) == 0:
        x0 = [0, 0, width - 1, height - 1]
    else:
        x1_init = max(min(selected, key=lambda obj: obj['tlx'])['tlx'], 0)
        y1_init = max(min(selected, key=lambda obj: obj['tly'])['tly'], 0)
        x2_init = min(max(selected, key=lambda obj: obj['brx'])['brx'], width - 1)
        y2_init = min(max(selected, key=lambda obj: obj['bry'])['bry'], height - 1)
        x0 = expand_rect(x1_init, y1_init, x2_init, y2_init, width, height, 0.2)
        print(x0)
        cv2.imwrite('hogehoge.jpg', img[int(y1_init):int(y2_init), int(x1_init):int(x2_init), :])

        # x0 = [0, 0, width - 1, height - 1]
        # x0 = expand_rect(x0[0], x0[1], x0[2], x0[3], width, height, 0.1)
        # x0 = expand_rect(x0[0], x0[1], x0[2], x0[3], width, height, 0.2)
        # print(x0)

    result = minimize(RR, x0=x0, method='Nelder-Mead')
    x_opt = [int(i) for i in result.x]
    print(result.x)
    return x_opt


def optimize_crop_region_simple(img, objects):
    pers_size = 1600
    width = pers_size
    height = pers_size

    selected = [obj for obj in objects if obj['choice'] == '0']

    if len(selected) == 0:
        x0 = [0, 0, width - 1, height - 1]
    else:
        x1_init = max(min(selected, key=lambda obj: obj['tlx'])['tlx'], 0)
        y1_init = max(min(selected, key=lambda obj: obj['tly'])['tly'], 0)
        x2_init = min(max(selected, key=lambda obj: obj['brx'])['brx'], width - 1)
        y2_init = min(max(selected, key=lambda obj: obj['bry'])['bry'], height - 1)
        x0 = expand_rect(x1_init, y1_init, x2_init, y2_init, width, height, 0.1)
        print(x0)

    return [int(i) for i in x0]
