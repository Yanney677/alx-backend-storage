#!/usr/bin/env python3
"""Import the ncessary modules and libraries"""
import uuid
from functools import wraps
from typing import Callable, Union

import redis


def count_calls(method: Callable) -> Callable:
    """Decorator to count method calls"""
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Increment the call counter with key/value anytime it is called and returns the value"""
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """Create keys to stores the history of inputs and outputs
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Stores the input and output in redis
        """
        input_key = method.__qualname__ + ":inputs"
        output_key = method.__qualname__ + ":outputs"

        output = method(self, *args, **kwargs)

        self._redis.rpush(input_key, str(args))
        self._redis.rpush(output_key, str(output))

        return output

    return wrapper


def replay(fn: Callable):
    """Display the call history"""
    w = redis.Redis()
    fxn_name = fn.__qualname__
    n_calls = w.get(fxn_name)
    try:
        n_calls = n_calls.decode('utf-8')
    except Exception:
        n_calls = 0
    print(f'{fxn_name} was called {n_calls} times:')

    inp = w.lrange(fxn_name + ":inputs", 0, -1)
    outp = w.lrange(fxn_name + ":outputs", 0, -1)

    for x, y in zip(inp, outp):
        try:
            x = x.decode('utf-8')
        except Exception:
            x = ""
        try:
            y = y.decode('utf-8')
        except Exception:
            y = ""

        print(f'{fxn_name}(*{x}) -> {y}')


class Cache():
    """Cache class with redis"""

    def __init__(self) -> None:
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """Store method in Redis

        Args:
            data (Union[str, bytes, int, float]): Data to be stored

        Returns:
            str: string
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Callable = None)\
            -> Union[str, bytes, int, float]:
        """ Get data from redis and transform it to its python type """
        data = self._redis.get(key)
        if fn:
            return fn(data)
        return data

    def get_str(self, key: str) -> str:
        """ Transform a redis type value to python string """
        v = self._redis.get(key)
        return v.decode("UTF-8")

    def get_int(self, key: str) -> int:
        """ Transform a redis type vale to python string """
        v = self._redis.get(key)
        try:
            v = int(v.decode("UTF-8"))
        except Exception:
            v = 0
        return v
