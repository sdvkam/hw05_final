from django.core.paginator import Paginator


def page_from_paginator(post_list, page_number, nums_on_page=10):
    paginator = Paginator(post_list, nums_on_page)
    return paginator.get_page(page_number)
