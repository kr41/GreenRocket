"""
Green Rocket is a simple implementation of Observer (or Publish/Subscribe)
design pattern using Signals.

Create specific signal from base class::

    >>> from greenrocket import Signal
    >>> class MySignal(Signal):
    ...     pass
    ...

Subscribe handler::

    >>> @MySignal.subscribe
    ... def handler(signal):
    ...     print('handler: ' + repr(signal))
    ...

Fire signal::

    >>> MySignal().fire()
    handler: MySignal()

Note, that signal propagates over inheritance, i.e. all subscribes of base
signal will be called when child signal fired::

    >>> @Signal.subscribe
    ... def base_hadler(signal):
    ...     print('base_handler: ' + repr(signal))
    ...
    >>> MySignal().fire()
    handler: MySignal()
    base_handler: MySignal()

Unsubscribe handler::

    >>> MySignal.unsubscribe(handler)
    >>> MySignal().fire()
    base_handler: MySignal()

Any keyword argument passed to signal constructor becomes its attribute::

    >>> s = Signal(a=1, b=2)
    >>> s.a
    1
    >>> s.b
    2

"""

from logging import getLogger
try:
    from weakref import WeakSet
except ImportError:
    # Python 2.6
    # TODO: Add to dependecies into setup.py
    from weakrefset import WeakSet


__all__ = ['Signal']
__version__ = '0.2'
__author__ = 'Dmitry Vakhrushev <self@kr41.net>'
__license__ = 'BSD'


class SignalMeta(type):
    """ Signal Meta Class """

    def __init__(cls, class_name, bases, attrs):
        cls.__handlers__ = WeakSet()


# For compatibility between Python 2.x and Python 3.x
BaseSignal = SignalMeta('BaseSignal', (object,), {})


class Signal(BaseSignal):
    """ Base Signal Class """

    logger = getLogger(__name__)

    @classmethod
    def subscribe(cls, handler):
        """ Subscribe handler to signal.  May be used as decorator """
        cls.logger.debug('Subscribe %r on %r', handler, cls)
        cls.__handlers__.add(handler)
        return handler

    @classmethod
    def unsubscribe(cls, handler):
        """ Unsubscribe handler from signal """
        cls.logger.debug('Unsubscribe %r from %r', handler, cls)
        cls.__handlers__.discard(handler)

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        params = []
        for k, v in self.__dict__.items():
            params.append('{0}={1!r}'.format(k, v))
        params = ', '.join(params)
        return '{0}({1})'.format(self.__class__.__name__, params)

    def fire(self):
        """ Fire signal """
        self.logger.debug('Fired %r', self)
        for cls in self.__class__.__mro__:
            if hasattr(cls, '__handlers__'):
                self.logger.debug('Propagate on %r', cls)
                for handler in cls.__handlers__:
                    try:
                        self.logger.debug('Call %r', handler)
                        handler(self)
                    except:
                        self.logger.error('Failed on processing %r by %r',
                                          self, handler, exc_info=True)
