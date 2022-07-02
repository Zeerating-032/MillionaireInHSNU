import pygame as pg
import inspect
import time
from queue import Queue
from functools import partial

'''
Bug:
1. timer在執行完成後，下一幀才會刪除，所以立即檢查仍會顯示非靜止
'''

class timer:
    '''
    延遲執行函數，可設定條件或時間
    '''
    def __init__(self, func, *args, **kwargs):
        self.finish = 0
        self.wait_until = Queue(0) #儲存func，全部符合才可以run
        self.func = partial(func, *args, **kwargs)
    
    def delay(self, t):
        t = time.time() + t
        self.wait_until.put(lambda: time.time() >= t)

    def set_tr(self, func):
        self.wait_until.put(func)

    def run(self):
        # 檢查
        for _ in range(self.wait_until.qsize()):
            tr = self.wait_until.get()
            try:
                if tr.__call__() == 1:
                    pass
                else:
                    self.wait_until.put(tr)
            except:
                print(self.func.func, self.func.args, tr)
        # 執行
        if self.wait_until.empty():
            self.finish = 1
            return self.func.__call__()
        else:
            return

    def is_finish(self):
        return self.finish


class ANI_END:
    '''
    代表動畫已經完全結束了
    '''
    def __init__(self):
        pass


class animation:
    '''
    包裝generator, 儲存許多資訊方便debug與搜尋等控制
    '''
    def __init__(self, func, admin, sub, **kwargs): #func, basic_element, str, func的參數
        self.admin = admin
        self.sub = sub
        self.gener = func(obj = admin, sub = sub, **kwargs)
        
        self.finish = 0 #所有動畫皆完成，可移除此animation
        self.id = id(self)
        
        data = next(self.gener)
        self.func_name = data.get("Func", None)
        self.typ = data.get("Type", None)
        self.flag = data.get("Flag", None)

    def get_info(self):
        retn = "***Ani Info***\n"
        if hasattr(self.admin, "name"):
            retn += f"Admin: {self.admin.name}\n"
        else:
            retn += f"Admin: {self.admin}\n"
        retn += f"動畫名稱: {self.func_name}\n"
        if self.sub is not None:
            retn += f"動畫目標: {self.sub}\n"
        else:
            retn += f"動畫目標: image\n"
        retn += f"Type: {self.typ}\n"
        retn += f"Flag: {self.flag}\n"
        retn += f"ID: {self.id}\n"
        retn += f"是否完成: {bool(self.is_finish())}\n"
        retn += "**************"
        return retn
    
    def run(self):
        comm = next(self.gener)
        if type(comm) != type(list()):
            comm = [comm]
        if self.sub == None:
            self.apply_to_image(comm)
        else:
            self.apply_to_sub(comm)

    def apply_to_image(self, comm):
        for i in comm:
            if type(i) == type(tuple()) and "pos" in self.typ: #位置
                self.admin.rect = i
            elif type(i) == type(1) and "alpha" in self.typ: #透明度
                self.admin.alpha = i
            elif isinstance(i, pg.Surface): #image
                self.admin.image = i
            elif inspect.isfunction(i): #其他函數
                i.__call__()
            elif i is None:
                pass
            elif isinstance(i, ANI_END):
                self.finish = 1
            else:
                raise ValueError(f"無法辨識指令{i}, Type_i: {type(i)}, Detail: {self.get_info()}")

    def apply_to_sub(self, comm):
        for i in comm:
            if type(i) == type(tuple()) and "pos" in self.typ: #位置
                self.admin.img_modify_values(self.sub, "Pos", i)
            elif type(i) == type(1) and "alpha" in self.typ: #透明度
                self.admin.img_modify_values(self.sub, "Alpha", i)
            elif isinstance(i, pg.Surface): #image
                self.admin.img_modify_values(self.sub, "Surface", i)
            elif inspect.isfunction(i): #其他函數
                i.__call__()
            elif i is None:
                pass
            elif isinstance(i, ANI_END):
                self.finish = 1
            else:
                raise ValueError(f"無法辨識指令{i}, Type_i: {type(i)}, Detail: {self.get_info()}")

    def is_finish(self):
        return self.finish


class waitfunc_manager:
    '''
    animation、timer總管
    由basic_element、各個scene繼承, 不會單獨使用
    因name會被覆蓋, 所以要優先init
    '''
    def __init__(self):
        # self.admin = admin
        self.name = None # 之後會覆蓋
        self.timer_list = [] #queue用法, 但deque功能較方便
        self.ani_list = []

    def create_timer(self, func, delay = 0, tr_statement = [], *args, **kwargs): #arg : func, float, func list
        t = timer(func, *args, **kwargs)
        t.delay(delay)
        for i in tr_statement:
            t.set_tr(i)
        self.timer_list.append(t)

    def ani(self, func, sub = None, **kwargs): #arg : str, func
        '''
        動畫是在update時執行的

        func需可回傳generator
        sub為key, 表示動畫需執行在此key上, 若為None則是代表執行在self
        warning: 若傳入sub則表示img_modify系列等不能用, 只能變更此圖外觀
        '''
        ani_obj = animation(func, admin = self, sub = sub, **kwargs)
        self.ani_list.append(ani_obj)
        return ani_obj.id

    def run_wfm(self, typ):
        if typ == "PRE":
            self.run_timer()
            self.run_ani_pre()
            a = self.is_finish_timer()
            if len(a) > 0:
                self.kill_timer(a)
            a = self.is_finish_ani()
            if len(a) > 0:
                self.kill_ani(a)
        elif typ == "POST":
            self.run_ani_post()
            a = self.is_finish_ani()
            if len(a) > 0:
                self.kill_ani(a)

    def run_timer(self):
        retn = []
        for i in self.timer_list:
            retn.append(i.run())
    def run_ani_pre(self):
        '''
        不執行post_edit
        '''
        for i in self.ani_list:
            if "Post_edit" not in i.flag:
                i.run()
    def run_ani_post(self):
        '''
        執行post_edit
        '''
        for i in self.ani_list:
            if "Post_edit" in i.flag:
                i.run()

    #timer info 開發中
    def ani_info(self):
        print(f"#{self.name}: 動畫{len(self.ani_list)}個")
        for i in self.ani_list:
            print(i.get_info())
        print("##--END", self.name, "##")

    def is_finish_timer(self):
        return list(filter(lambda x: x.is_finish(), self.timer_list))
    def is_finish_ani(self):
        return list(filter(lambda x: x.is_finish(), self.ani_list))

    def search_timer(self, **kwargs):
        print("search_timer功能開發中")
        return
    def search_ani(self, **kwargs):
        '''
        根據特徵尋找動畫
        可搜尋:
        func, sub, id
        typ, flag有包含即可
        回傳符合條件的id list或None
        '''
        #檢查
        can_contain = ("func_name", "sub", "id", "typ", "flag")
        s = map(lambda x: x in can_contain, kwargs.keys())
        if not all(s):
            raise ValueError(f"搜尋條件{kwargs}包含不可存在的key")
        #搜尋
        fit = []
        for an in self.ani_list:
            status = []
            for i, j in kwargs.items():
                if i in ("typ", "flag"): #有包含即可
                    status.append(set(getattr(an, i)).issubset(set(j)))
                else:
                    status.append(getattr(an, i) == j)
            if all(status):
                fit.append(an)
        if len(fit) >= 1:
            return fit
        else:
            return None    

    def kill_timer(self, objs = [], **kwargs):
        '''
        傳入objs : 直接刪除，優先
        傳入kwargs : 搜尋，再刪除
        '''
        if len(objs) == 0:
            objs = self.search_timer(**kwargs)
            if objs is None:
                print(f"{self.name}刪除條件{kwargs}的timer失敗: 找不到")
                return
        for i in objs:
            self.timer_list.remove(i)
    def kill_ani(self, objs = [], **kwargs):
        '''
        傳入objs : 直接刪除，優先
        傳入kwargs : 搜尋，再刪除
        '''
        if len(objs) == 0:
            objs = self.search_ani(**kwargs)
            if objs is None:
                print(f"{self.name}刪除條件{kwargs}的animation失敗: 找不到")
                return
        for i in objs:
            self.ani_list.remove(i)
        
    def timer_in(self):
        print("timer_in功能開發中")
        return       
    def ani_in(self, **kwargs):
        return self.search_ani(**kwargs) is not None

    def ani_static(self):
        return not bool(len(self.ani_list))
    def timer_static(self):
        return not(bool(len(self.timer_list)))
    def is_static(self):
        return self.ani_static() and self.timer_static()
