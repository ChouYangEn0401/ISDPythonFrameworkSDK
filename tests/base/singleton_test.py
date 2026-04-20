from hyper_framework.base import SingletonMetaclass

class MyManager(metaclass=SingletonMetaclass):
    def _initialize_manager(self):
        # 單例首次建立時執行一次
        self.data = []

a = MyManager()
b = MyManager()
print(a)
print(b)
assert a is b  # True