import cv2
import numpy as np
from scipy import ndimage


def gen_xyz(hfov, vfov, u, v, out_w, out_h):
    out = np.ones((out_h, out_w, 3), np.float32)
    x_rng = np.linspace(-np.tan(hfov / 2), np.tan(hfov / 2), num=out_w, dtype=np.float32)
    y_rng = np.linspace(-np.tan(vfov / 2), np.tan(vfov / 2), num=out_h, dtype=np.float32)

    out[:, :, :2] = np.stack(np.meshgrid(x_rng, -y_rng), -1)
    Rx = np.array([[1, 0, 0], [0, np.cos(v), -np.sin(v)], [0, np.sin(v), np.cos(v)]])
    Ry = np.array([[np.cos(u), 0, np.sin(u)], [0, 1, 0], [-np.sin(u), 0, np.cos(u)]])

    R = np.dot(Ry, Rx)
    return out.dot(R.T)

def xyz_to_uv(xyz):
    x, y, z = np.split(xyz, 3, axis=-1)
    u = np.arctan2(x, z)
    c = np.sqrt(x ** 2 + z ** 2)
    v = np.arctan2(y, c)
    return np.concatenate([u, v], axis=-1)

def uv_to_XY(uv, erp_w, erp_h):
    u, v = np.split(uv, 2, axis=-1)
    X = (u / (2 * np.pi) + 0.5) * erp_w - 0.5
    Y = (-v / np.pi + 0.5) * erp_h - 0.5
    return np.concatenate([X, Y], axis=-1)

def eq_to_pers(erp_img, hfov, vfov, u, v, out_w, out_h):
    xyz = gen_xyz(hfov, vfov, u, v, out_w, out_h)
    uv  = xyz_to_uv(xyz)

    erp_h, erp_w = erp_img.shape[:2]
    XY = uv_to_XY(uv, erp_w, erp_h)

    X, Y = np.split(XY, 2, axis=-1)
    X = np.reshape(X, (out_h, out_w))
    Y = np.reshape(Y, (out_h, out_w))

    mc0 = ndimage.map_coordinates(erp_img[:, :, 0], [Y, X]) # channel: B
    mc1 = ndimage.map_coordinates(erp_img[:, :, 1], [Y, X]) # channel: G
    mc2 = ndimage.map_coordinates(erp_img[:, :, 2], [Y, X]) # channel: R

    output = np.stack([mc0, mc1, mc2], axis=-1)
    return output


# 透視投影画像上の座標を元の全方位画像上の座標に変換する
def get_original_pos(x, y, hfov, vfov, angle_u, angle_v, pers_size_w, pers_size_h, erp_w, erp_h):
    cx = (np.tan(hfov / 2) * 2 / (pers_size_w - 1)) * x - np.tan(hfov / 2)
    cy = (np.tan(vfov / 2) * 2 / (pers_size_h - 1)) * y - np.tan(vfov / 2)
    cz = 1

    Rx = np.array([[1, 0, 0], [0, np.cos(angle_v), -np.sin(angle_v)], [0, np.sin(angle_v), np.cos(angle_v)]])
    Ry = np.array([[np.cos(angle_u), 0, np.sin(angle_u)], [0, 1, 0], [-np.sin(angle_u), 0, np.cos(angle_u)]])
    R = np.dot(Ry, Rx)

    xyz = np.dot(R, np.array([cx, -cy, cz]))
    x, y, z = xyz.tolist()

    u = np.arctan2(x, z)
    c = np.sqrt(x ** 2 + z ** 2)
    v = np.arctan2(y, c)

    X = (u / (2 * np.pi) + 0.5) * erp_w - 0.5
    Y = (-v / np.pi + 0.5) * erp_h - 0.5
    return [Y, X]
