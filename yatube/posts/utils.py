from django.core.paginator import Paginator


def make_paginator(object, request, value):
    """Функция пагинации"""
    paginator = Paginator(object, value)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
