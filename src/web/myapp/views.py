from django.db.models import Count, Exists, OuterRef, Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.timezone import localtime
from django.views import generic

from .models import Photo
from .utils import detect_objects, translate_to_japanese
from .utils.photo import crop_image

from datetime import datetime
import json
import os

import cv2
import numpy as np


class IndexView(generic.TemplateView):
    template_name = 'index.html'


class PhotoListView(generic.ListView):
    model = Photo
    ordering = '-created_at'
    template_name = 'photo_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        photo_list = list(context['photo_list'].values())
        photo_info = []

        for idx, photo in enumerate(photo_list):
            json_path = os.path.join('/media', photo['user_name'], photo['title'], 'objects.json')

            if os.path.exists(json_path):
                with open(json_path, mode='r', encoding='utf-8') as f:
                    json_dict = json.load(f)

                obj_counts = {}

                for k, v in json_dict['detection'].items():
                    for obj in v['objects']:
                        if obj['label'] in obj_counts.keys():
                            obj_counts[obj['label']]['count'] += 1
                        else:
                            if 'label_japanese' in obj.keys():
                                # obj_counts[obj['label']] = {'label_japanese': obj['label_japanese'], 'count': 1}
                                # 下は英語版
                                obj_counts[obj['label']] = {'label_japanese': obj['label'], 'count': 1}
                            else:
                                obj_counts[obj['label']] = {'label_japanese': obj['label'], 'count': 1}

                detection_summary = ''

                for obj in obj_counts.values():
                    detection_summary += '{} ({}) '.format(obj['label_japanese'], str(obj['count']))

                # 切り取り結果に含まれる物体
                with open(os.path.join('/media', photo['user_name'], photo['title'], 'results', photo['result_name'], 'log.json'), mode='r', encoding='utf-8') as log_file:
                    log_dict = json.load(log_file)

                # gcp_result = ', '.join(log_dict['gcp_list_jp'])
                # 下は英語版
                gcp_result = ', '.join(log_dict['gcp_list_en'])

                photo_info.append({
                    'index': idx + 1,
                    'detection_summary': detection_summary,
                    'voice_memo': json_dict['transcript'],
                    'gcp_result': gcp_result
                })

        context['photo_list'] = zip(photo_list, photo_info)

        return context

    def get(self, request, *args, **kwargs):
        request.session['datetime_start'] = localtime(timezone.now()).strftime('%Y-%m-%d--%H-%M-%S %z')
        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)


class PhotoDetailView(generic.DetailView):
    model = Photo
    template_name = 'photo_detail.html'

    def get_json_dict(self, photo):
        json_path = os.path.join('/media', photo.user_name, photo.title, 'objects.json')

        if os.path.exists(json_path):
            with open(json_path, mode='r', encoding='utf-8') as f:
                json_dict = json.load(f)
        else:
            json_dict = {}

        return json_dict

    def get_object_list(self, json_dict):
        obj_list = {}
        idx = 0

        for k, v in json_dict['detection'].items():
            clock = v['clock']
            obj_list[k] = {'clock': clock, 'objects': []}
            for obj in v['objects']:
                # obj_list[k]['objects'].append({'index': idx, 'class': obj['label_japanese']})
                # 下は英語版
                obj_list[k]['objects'].append({'index': idx, 'class': obj['label']})
                idx += 1

        count = idx

        return (count, obj_list)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo = self.get_object()
        json_dict = self.get_json_dict(photo)
        count, obj_list = self.get_object_list(json_dict)

        context['num_obj'] = count
        context['objects'] = obj_list

        return context

    def get(self, request, *args, **kwargs):
        request.session['datetime_accessed_object_selection'] = localtime(timezone.now()).strftime('%Y-%m-%d--%H-%M-%S %z')
        self.object = super().get_object()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context=context)

    def post(self, request, *args, **kwargs):
        for item in request.POST:
            print(item, request.POST[item])

        photo = self.get_object()
        json_dict = self.get_json_dict(photo)

        now = localtime(timezone.now()).strftime('%Y-%m-%d--%H-%M-%S %z')
        result_dir = os.path.join('/media', photo.user_name, photo.title, 'results', now)
        os.makedirs(result_dir)

        erp_img = cv2.imread(os.path.join('/media', photo.user_name, photo.title, 'theta.JPG'))
        obj_list = crop_image(erp_img, json_dict['detection'], request.POST, result_dir)
        # print(obj_list)

        # 切り取り結果に物体検出を適用
        gcp_objects = detect_objects(os.path.join(result_dir, 'result.jpg'))
        gcp_list_en = list(set([object['label'] for object in gcp_objects]))
        gcp_list_jp = [translate_to_japanese(label) for label in gcp_list_en]

        datetime_start = timezone.datetime.strptime(request.session['datetime_start'], '%Y-%m-%d--%H-%M-%S %z')
        datetime_finish = localtime(timezone.now())

        log_dict = {
          'objects': obj_list,
          'gcp_list_en': gcp_list_en,
          'gcp_list_jp': gcp_list_jp,
          'datetime_start': request.session['datetime_start'],
          'datetime_accessed_object_selection': request.session['datetime_accessed_object_selection'],
          'datetime_finish': datetime_finish.strftime('%Y-%m-%d--%H-%M-%S %z'),
          'time': (datetime_finish - datetime_start).total_seconds()
        }

        with open(os.path.join(result_dir, 'log.json'), mode='w', encoding='utf-8') as f:
            json.dump(log_dict, f, indent=2, ensure_ascii=False)

        # update result_name
        photo.result_name = now
        photo.save()

        return redirect('/photos/' + str(photo.id) + '/result/')


class ResultView(generic.DetailView):
    model = Photo
    template_name = 'photo_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo = self.get_object()

        result_dir = os.path.join('/media', photo.user_name, photo.title, 'results', photo.result_name)

        with open(os.path.join(result_dir, 'log.json'), mode='r', encoding='utf-8') as f:
            log_dict = json.load(f)

        # context['gcp_result'] = ', '.join(log_dict['gcp_list_jp']
        # 下は英語版
        context['gcp_result'] = ', '.join(log_dict['gcp_list_en'])
        context['image_url'] = '/media/{}/{}/results/{}/result.jpg'.format(photo.user_name, photo.title, photo.result_name)

        return context
