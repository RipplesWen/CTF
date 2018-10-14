#!/usr/bin/env python
# coding:utf-8

import base64
import struct
import collections

def _lb_wrapper(func):
    endian = func.__name__[0] == 'l' and '<' or '>'
    bits = int(func.__name__[1:])
    pfs = {8: 'B', 16: 'H', 32: 'I', 64: 'Q'}
    def wrapper(*args):
        ret = []
        join = False
        for i in args:
            if isinstance(i, int):
                join = True
                v = struct.pack(endian + pfs[bits], i % (1 << bits))
                ret.append(v)
            else:
                if not i:
                    ret.append(None)
                else:
                    v = struct.unpack(endian + pfs[bits] * (len(i) * 8/bits), i)
                    ret += v
        if join:
            return ''.join(ret)
        elif len(ret) == 1:
            return ret[0]
        elif len(ret) == 0:     # all of the input are empty strings
            return None
        else:
            return ret
    wrapper.__name__ = func.__name__
    return wrapper

@_lb_wrapper
def l8 (*args): pass
@_lb_wrapper
def b8 (*args): pass
@_lb_wrapper
def l16(*args): pass
@_lb_wrapper
def b16(*args): pass
@_lb_wrapper
def l32(*args): pass
@_lb_wrapper
def b32(*args): pass
@_lb_wrapper
def l64(*args): pass
@_lb_wrapper
def b64(*args): pass


def flat(*args, **kwargs):
    s = ''
    for x in args:
        s += struct.pack('<Q', x)
    return s

def b64e(s):
    return base64.b64encode(s)


def partition(lst, f, save_keys = False):
    """partition(lst, f, save_keys = False) -> list

    Partitions an iterable into sublists using a function to specify which
    group they belong to.

    It works by calling `f` on every element and saving the results into
    an :class:`collections.OrderedDict`.

    Arguments:
      lst: The iterable to partition
      f(function): The function to use as the partitioner.
      save_keys(bool): Set this to True, if you want the OrderedDict
                       returned instead of just the values

    Example:
      >>> partition([1,2,3,4,5], lambda x: x&1)
      [[1, 3, 5], [2, 4]]
    """
    d = collections.OrderedDict()

    for l in lst:
        c = f(l)
        s = d.setdefault(c, [])
        s.append(l)
    if save_keys:
        return d
    else:
        return d.values()

def group(n, lst, underfull_action = 'ignore', fill_value = None):
    """group(n, lst, underfull_action = 'ignore', fill_value = None) -> list

    Split sequence into subsequences of given size. If the values cannot be
    evenly distributed among into groups, then the last group will either be
    returned as is, thrown out or padded with the value specified in fill_value.

    Arguments:
      n (int): The size of resulting groups
      lst: The list, tuple or string to group
      underfull_action (str): The action to take in case of an underfull group at the end. Possible values are 'ignore', 'drop' or 'fill'.
      fill_value: The value to fill into an underfull remaining group.

    Returns:
      A list containing the grouped values.

    Example:
      >>> group(3, "ABCDEFG")
      ['ABC', 'DEF', 'G']
      >>> group(3, 'ABCDEFG', 'drop')
      ['ABC', 'DEF']
      >>> group(3, 'ABCDEFG', 'fill', 'Z')
      ['ABC', 'DEF', 'GZZ']
      >>> group(3, list('ABCDEFG'), 'fill')
      [['A', 'B', 'C'], ['D', 'E', 'F'], ['G', None, None]]
    """

    if underfull_action not in ['ignore', 'drop', 'fill']:
        raise ValueError("group(): underfull_action must be either 'ignore', 'drop' or 'fill'")

    if underfull_action == 'fill':
        if isinstance(lst, tuple):
            fill_value = (fill_value,)
        elif isinstance(lst, list):
            fill_value = [fill_value]
        elif isinstance(lst, (str, unicode)):
            if not isinstance(fill_value, (str, unicode)):
                raise ValueError("group(): cannot fill a string with a non-string")
        else:
            raise ValueError("group(): 'lst' must be either a tuple, list or string")

    out = []
    for i in range(0, len(lst), n):
        out.append(lst[i:i+n])

    if out and len(out[-1]) < n:
        if underfull_action == 'ignore':
            pass
        elif underfull_action == 'drop':
            out.pop()
        else:
            out[-1] = out[-1] + fill_value * (n - len(out[-1]))

    return out

def concat(l):
    """concat(l) -> list

    Concats a list of lists into a list.

    Example:

      >>> concat([[1, 2], [3]])
      [1, 2, 3]

    """

    res = []
    for k in l:
        res.extend(k)

    return res

def concat_all(*args):
    """concat_all(*args) -> list

    Concats all the arguments together.

    Example:
       >>> concat_all(0, [1, (2, 3)], [([[4, 5, 6]])])
       [0, 1, 2, 3, 4, 5, 6]
    """

    if len(args) != 1:
        return concat_all(list(args))

    if not isinstance(args[0], (tuple, list)):
        return [args[0]]

    res = []
    for k in args[0]:
        res.extend(concat_all(k))

    return res

def ordlist(s):
    """ordlist(s) -> list

    Turns a string into a list of the corresponding ascii values.

    Example:
      >>> ordlist("hello")
      [104, 101, 108, 108, 111]
    """
    return map(ord, s)

def unordlist(cs):
    """unordlist(cs) -> str

    Takes a list of ascii values and returns the corresponding string.

    Example:
      >>> unordlist([104, 101, 108, 108, 111])
      'hello'
    """
    return ''.join(chr(c) for c in cs)

def findall(haystack, needle):
    """findall(l, e) -> l

    Generate all indices of needle in haystack, using the
    Knuth-Morris-Pratt algorithm.

    Example:
      >>> foo = findall([1,2,3,4,4,3,4,2,1], 4)
      >>> foo.next()
      3
      >>> foo.next()
      4
      >>> foo.next()
      6
    """
    def __kmp_table(W):
        pos = 1
        cnd = 0
        T = []
        T.append(-1)
        T.append(0)
        while pos < len(W):
            if W[pos] == W[cnd]:
                cnd += 1
                pos += 1
                T.append(cnd)
            elif cnd > 0:
                cnd = T[cnd]
            else:
                pos += 1
                T.append(0)
        return T

    def __kmp_search(S, W):
        m = 0
        i = 0
        T = __kmp_table(W)
        while m + i < len(S):
            if S[m + i] == W[i]:
                i += 1
                if i == len(W):
                    yield m
                    m += i - T[i]
                    i = max(T[i], 0)
            else:
                m += i - T[i]
                i = max(T[i], 0)

    def __single_search(S, w):
        for i in xrange(len(S)):
            if S[i] == w:
                yield i


    if type(haystack) != type(needle):
        needle = [needle]
    if len(needle) == 1:
        return __single_search(haystack, needle[0])
    else:
        return __kmp_search(haystack, needle)


