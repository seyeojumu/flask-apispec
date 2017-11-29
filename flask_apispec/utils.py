# -*- coding: utf-8 -*-

import functools

import six

def resolve_instance(schema, **kwargs):
    kwargs = kwargs or {}
    resource_class_args = kwargs.get('resource_class_args') or ()
    resource_class_kwargs = kwargs.get('resource_class_kwargs') or {}
    if isinstance(schema, type):
        return schema(*resource_class_args, **resource_class_kwargs)
    return schema

class Ref(object):

    def __init__(self, key):
        self.key = key

    def resolve(self, obj):
        return getattr(obj, self.key, None)

def resolve_refs(obj, attr):
    if isinstance(attr, dict):
        return {
            key: resolve_refs(obj, value)
            for key, value in six.iteritems(attr)
        }
    if isinstance(attr, list):
        return [resolve_refs(obj, value) for value in attr]
    if isinstance(attr, Ref):
        return attr.resolve(obj)
    return attr

def match_status_code(status_code):
    def wrapped(req, res):
        return res.status_code == status_code
    return wrapped

class Annotation(object):

    def __init__(self, options=None, inherit=None, apply=None):
        self.options = options or []
        for opt in self.options:
            if '_apply' not in opt and apply:  # is not False:
                opt['_apply'] = apply
        self.inherit = inherit
        self.apply = apply

    def set_apply(self, new_apply):
        assert new_apply, 'clearing apply not supported'
        for opt in self.options:
            opt['_apply'] = new_apply

    def __eq__(self, other):
        if isinstance(other, Annotation):
            return (
                self.options == other.options and
                self.inherit == other.inherit and
                self.apply == other.apply
            )
        return NotImplemented

    def __ne__(self, other):
        ret = self.__eq__(other)
        return ret if ret is NotImplemented else not ret

    def resolve(self, obj):
        return self.__class__(
            resolve_refs(obj, self.options),
            inherit=self.inherit,
            apply=self.apply,
        )

    def merge(self, other):
        if self.inherit is False:
            return self
        return self.__class__(
            self.options + other.options,
            inherit=other.inherit,
            apply=self.apply if self.apply is not None else other.apply,
        )

def is_callable(thing):
    try:
        return callable(thing)
    except NameError:
        return hasattr(thing, '__call__')

def resolve_annotations(func, key, parent=None):
    annotations = (
        getattr(func, '__apispec__', {}).get(key, []) +
        getattr(parent, '__apispec__', {}).get(key, [])
    )
    return functools.reduce(
        lambda first, second: first.merge(second),
        [annotation.resolve(parent) for annotation in annotations],
        Annotation(),
    )

def merge_recursive(values):
    return functools.reduce(_merge_recursive, values, {})

def _merge_recursive(child, parent):
    if isinstance(child, dict) or isinstance(parent, dict):
        child = child or {}
        parent = parent or {}
        keys = set(child.keys()).union(parent.keys())
        return {
            key: _merge_recursive(child.get(key), parent.get(key))
            for key in keys
        }
    return child if child is not None else parent
