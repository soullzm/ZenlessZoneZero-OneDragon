from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List

from one_dragon.utils.log_utils import log

_od_event_bus_executor = ThreadPoolExecutor(thread_name_prefix='od_event_bus', max_workers=8)


class ContextEventBus:

    def __init__(self):
        self.callbacks: dict[str, List[Callable[[Any], None]]] = {}

    def dispatch_event(self, event_id: str, event_obj: Any = None):
        """
        下发事件
        :param event_id: 事件ID
        :param event_obj: 事件体
        :return:
        """
        log.debug("事件触发 %s", event_id)
        if event_id not in self.callbacks:
            pass
        future_list: List[Future] = []
        for callback in self.callbacks[event_id]:
            future_list.append(_od_event_bus_executor.submit(callback, event_obj))

        for future in future_list:
            future.result()

    def listen_event(self, event_id: str, callback: Callable[[Any], None]):
        """
        新增监听事件
        监听的回调，如果耗时过长，应该在自己的线程池的工作，避免阻塞
        :param event_id:
        :param callback:
        :return:
        """
        if event_id not in self.callbacks:
            self.callbacks[event_id] = []
        existed_callbacks = self.callbacks[event_id]
        if callback not in existed_callbacks:
            existed_callbacks.append(callback)

    def unlisten_event(self, event_id: str, callback: Callable[[Any], None]):
        """
        解除一个事件的监听
        :param event_id:
        :param callback:
        :return:
        """
        if event_id not in self.callbacks:
            return
        self.callbacks[event_id].remove(callback)

    def unlisten_all_event(self, obj: Any):
        """
        解除一个对象的所有监听
        :param obj:
        :return:
        """
        to_remove = {}
        for key, existed_callbacks in self.callbacks.items():
            to_remove[key] = []
            for existed in existed_callbacks:
                if id(existed.__self__) == id(obj):
                    to_remove[key].append(existed)

        for key, removes in to_remove.items():
            for remove in removes:
                self.callbacks[key].remove(remove)
