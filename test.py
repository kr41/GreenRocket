import gc

try:
    import asyncio
except ImportError:
    asyncio = None

from nose import tools

from greenrocket import Signal, Watchman


def signal_test():
    signal = Signal(a=1, b=2)
    tools.eq_(signal.a, 1)
    tools.eq_(signal.b, 2)


def subscribtion_test():
    log = []

    @Signal.subscribe
    def handler(signal):
        log.append('processed: ' + repr(signal))

    Signal(value='Test').fire()
    tools.eq_(log, ["processed: Signal(value='Test')"])

    Signal.unsubscribe(handler)
    Signal(value='Test 2').fire()
    tools.eq_(log, ["processed: Signal(value='Test')"])


def double_subscribtion_test():
    log = []

    def handler(signal):
        log.append('processed: ' + repr(signal))
    Signal.subscribe(handler)
    Signal.subscribe(handler)

    Signal().fire()
    tools.eq_(log, ["processed: Signal()"])

    Signal.unsubscribe(handler)
    Signal.unsubscribe(handler)  # Should raise no error


def error_swallow_test():
    @Signal.subscribe
    def handler(signal):
        raise Exception('Test')

    Signal().fire()
    Signal.unsubscribe(handler)


def propagation_test():
    log = []

    class MySignal(Signal):
        pass

    @Signal.subscribe
    def handler(signal):
        log.append('processed by handler: ' + repr(signal))

    @MySignal.subscribe
    def my_handler(signal):
        log.append('processed by my_handler: ' + repr(signal))

    MySignal().fire()
    tools.eq_(log, ["processed by my_handler: MySignal()",
                    "processed by handler: MySignal()"])
    Signal.unsubscribe(handler)


def weakref_handler_test():
    log = []

    def subscribe():
        @Signal.subscribe
        def handler(signal):
            log.append('processed: ' + repr(signal))
        Signal().fire()

    subscribe()
    gc.collect()            # PyPy fails the test without this explicit call
    Signal().fire()
    tools.eq_(log, ["processed: Signal()"])


def watchman_test():
    watchman = Watchman(Signal)
    tools.eq_(len(watchman.log), 0)

    Signal(x=1, y=2).fire()
    tools.eq_(len(watchman.log), 1)
    tools.eq_(watchman.log[0].x, 1)
    tools.eq_(watchman.log[0].y, 2)
    watchman.assert_fired_with(x=1, y=2)

    Signal(z=3).fire()
    tools.eq_(len(watchman.log), 2)
    tools.eq_(watchman.log[1].z, 3)
    watchman.assert_fired_with(z=3)

    watchman.assert_fired_with(-2, x=1, y=2)

    assert_error_raised = True
    try:
        watchman.assert_fired_with(-3)
        assert_error_raised = False
    except AssertionError as e:
        tools.eq_(e.args[0], 'There is no Signal in the log at index -3')
    tools.ok_(assert_error_raised)

    assert_error_raised = True
    try:
        watchman.assert_fired_with(x=1)
        assert_error_raised = False
    except AssertionError as e:
        tools.eq_(e.args[0], 'Signal has no attribute x')
    tools.ok_(assert_error_raised)

    assert_error_raised = True
    try:
        watchman.assert_fired_with(z=4)
        assert_error_raised = False
    except AssertionError as e:
        tools.eq_(e.args[0], 'Failed assertion on Signal.z: 3 != 4')
    tools.ok_(assert_error_raised)


if asyncio is not None:
    def afire_test():

        log = []

        @Signal.subscribe
        @asyncio.coroutine
        def handler(signal):
            log.append('processed by handler: ' + repr(signal))

        @Signal.subscribe
        @asyncio.coroutine
        def error_handler(signal):
            log.append('processed by error_handler: ' + repr(signal))
            raise Exception('Test')

        signal = Signal()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(signal.afire())

        log.sort()
        tools.eq_(log, ['processed by error_handler: Signal()',
                        'processed by handler: Signal()'])
