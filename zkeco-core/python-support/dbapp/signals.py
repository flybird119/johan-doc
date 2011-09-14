# coding=utf-8
from django.dispatch import Signal
on_model_operation=Signal(providing_args=["request", "dataModel"])
on_object_operation=Signal(providing_args=["request", "dataModel", "objects"])
on_list_paginator=Signal(providing_args=["request", "dataModel", "querySet"])