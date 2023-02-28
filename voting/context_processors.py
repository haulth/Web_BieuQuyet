# -*- coding: utf-8 -*-

from django.conf import settings


def ElectionTitle(request):
    context = {}
    title = "Chưa có tiêu đề"
    try:
        file = open(settings.ELECTION_TITLE_PATH, 'r', encoding='utf-8')
        title = file.read()
    except:
        pass
    context['TITLE'] = title
    return context
