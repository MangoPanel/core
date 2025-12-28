from dataclasses import replace
import functools
from typing import Callable, Type, Any
import numpy as np
import cv2
from cv2.typing import MatLike

def add_debug_field(name: str = "transformation_info", type_hint: Type = str, default: Any = ""):
    def decorator(cls: Type):
        if __debug__:
            if not hasattr(cls, "__annotations__"):
                cls.__annotations__ = {}
            cls.__annotations__[name] = type_hint
            setattr(cls, name, default)
        return cls
    return decorator


def return_debug(info_provider: Callable[[Any], str] = None):
    def actual_decorator(func):
        if not __debug__:
            return func

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)

            if info_provider:
                info = info_provider(self)
            elif hasattr(self, "get_debug_info"):
                info = self.get_debug_info()
            else:
                info = type(self).__name__

            if hasattr(result, "transformation_info"):
                try:
                    result.transformation_info += f"{info} "
                except AttributeError:
                    current = getattr(result, "transformation_info", "")
                    result = replace(result, transformation_info=current + f"{info} ")

            return result
        return wrapper
    return actual_decorator


