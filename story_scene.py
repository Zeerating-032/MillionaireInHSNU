# 故事場景，得到script後執行，初設用set_script，考慮檔案過長狀況，有extend_script功能
# script格式可參考/script/Talkyourself.txt
# script分背景、人物引入(用到storydata.py，這部分很爛)，
# 接下來才是主腳本
# "$"表人物或背景指令，"#"表控制畫面指令，如等待動畫結束、紀錄加分
# 包含":"的語句為文字框顯示，";"開頭是註解，中間也可以插空行
# 問題格式：
# %{QuestionName} Chooser={Host、Guest}%
# {Option1} >> {part1}
# {Option2} >> {part2}
# > {part1}
# //內容
# > {part2}
# //另一段內容
# %--End{QuestionName}%

from VARIBLE import *
import re
from functools import partial
from collections import deque

from button import keybtnlist, mousebtnlist
from storydata import *
from story_ele import *
from ani_normal import *
from ani_story import *
from waitfunc import waitfunc_manager


class story_main(waitfunc_manager):
    
    def __init__(self):
        '''
        Layer安排:
        背景 -1 人物 0 文字框 1
        問題 2 轉場 5
        '''

        #一般
        waitfunc_manager.__init__(self)
        self.name = "Story_scene"
        self.GPblit = pg.sprite.LayeredUpdates()
        self.Mousebtnlist = mousebtnlist()
        self.Keybtnlist = keybtnlist()
        self.send_admin = []

        self.Surface = pg.Surface(SCREEN_SIZE, SRCALPHA, 32)
        self.chara_name = [] #紀錄故事中用到的角色名
        self.player = {"Host":None, "Guest":None} #mono中的玩家名, Host是當前回合的人
        self.record = {"Host": 0, "Guest": 0} #得分紀錄
        self.onQueChoose = 0

        #背景
        self.Bkg = figure("Bkg", [])
        self.Bkg.appear_at((0, 0))
        self.GPblit.add(self.Bkg, layer = -1)
        #文字框
        self.TextBox = textbox()
        self.GPblit.add(self.TextBox, layer = 1)
        #問題
        self.Question = question()
        self.GPblit.add(self.Question, layer = 2)
        #空劇本
        self.Script = deque()
        #轉場
        self.Cover = transition() #name是Transition
        self.GPblit.add(self.Cover, layer = 5)

        for i in iter(self.GPblit):
            i.admin = self

        #設定按鈕
        self.set_btn()
    
    def set_script(self, path = "", script = []):
        self.Script.clear()
        self.Script = readscript(self, path, script)
        print("檔案讀入完成")

    def set_btn(self):
        #獲取下一指令
        def run_scr(self = self):
            if not self.TextBox.allshow:
                self.TextBox.quick_end_text()
            else:
                self.Keybtnlist.turn_off("Get_next")
                fini = self.get_next()
                if fini:
                    self.Keybtnlist.turn_on("Get_next")
            return
        self.Keybtnlist.add(K_SPACE , "Get_next", {"press_func": partial(run_scr)})
        #自動運行
        self.Keybtnlist.add(K_c, "Auto_get_next", {"press_func": partial(self.ani, auto_get_text)})
        #關閉文字框
        def cls_txbox(self = self):
            alp = 0 if self.TextBox.alpha else 255
            self.TextBox.ani(direct_fade, endalpha = alp)
        self.Keybtnlist.add(K_m, "Close_textbox", {"press_func": partial(cls_txbox)})

    def set_player(self, Host, Guest):
        self.player = {"Host":Host, "Guest":Guest}

    def set_bkg(self, bkg_name_list): #str list
        for i in bkg_name_list:
            self.Bkg.img_modify_data("Add", bkgdata.get(i))

    def set_figure(self, figure_list): #str list
        for i in figure_list:
            attrname, fig = map(lambda x: x.strip(), i.split(":"))
            setattr(self, attrname, figure(attrname, figuredata.get(fig)))
            self.GPblit.add(getattr(self, attrname), layer = 0)
            getattr(self, attrname).admin = self
            self.chara_name.append(attrname)

    def set_send_admin(self, typ, *args, **kwargs):
        '''
        設定要回傳給admin的值, 會在get_messenge的時候回傳
        '''
        d = {"Author": self.name}
        if typ == "QuitGame":
            d["Title"] = "Quit"
        elif typ == "ResizeScreen":
            d["Title"] = "ResizeScreen"
        elif typ == "Mono": #轉換畫面至Mono
            d["Title"] = "TransScene"
            d["NextScene"] = "Mono"
            d["Record"] = self.record
        else:
            raise ValueError(f"MonoScene的set_send_admin不支援typ='{typ}'")

        self.send_admin.append(d)

    def checkEvent(self):
        for event in pg.event.get():
            if event.type == QUIT:
                self.set_send_admin("QuitGame")
            
            elif event.type == WINDOWSIZECHANGED:
                self.set_send_admin("ResizeScreen")
            
            if event.type == MOUSEMOTION:
                mx, my = pg.mouse.get_pos()
                self.Mousebtnlist.check_focus(mx, my)

            if event.type == MOUSEBUTTONDOWN:
                self.Mousebtnlist.check_click()
            
            if event.type == MOUSEBUTTONUP:
                self.Mousebtnlist.check_up()
            
            if event.type == KEYDOWN:
                self.Keybtnlist.check_press(event.key)
            
            if event.type == KEYUP:
                self.Keybtnlist.check_up(event.key)

    def appear(self, arg = ""):
        #獲取資料
        self.get_next()
        for i in ("Get_next", "Auto_get_next", "Close_textbox"):
            self.Keybtnlist.turn_on(i)
        self.TextBox.ani(direct_fade, endalpha = 255)
    
    def clear(self):
        self.Cover.fade_in()

    def extend_script(self, nfile_path = "", ndeq = deque(), left = False):
        if len(ndeq) == 0:
            ndeq = readscript(nfile_path)
        if not left:
            self.Script.extend(ndeq)
        else:
            ndeq.reverse()
            self.Script.extendleft(ndeq)
    
    def get_next(self):
        if self.onQueChoose:
            return
        
        leave = 0 #leave條件:遇見文句、要等待動畫結束時、問題
        finish = 1 #是否有因指令語句導致進入timer延遲執行
        while not leave:
            try:
                a = self.Script.popleft()
            except IndexError: #Script用完了
                self.story_end()
                return
            
            if type(a) == type(tuple()): #文句
                self.TextBox.set_content(*a)
                self.TextBox.show_up()
                leave = 1
            elif isinstance(a, partial): #指令
                a.__call__()
            elif isinstance(a, que_saver): #開啟問題
                self.Question.set_content(a)
                self.Question.show_up()
                self.TextBox.ani(direct_fade, endalpha = 0)
                self.onQueChoose = 1
                leave = 1
            else:
                print(f"{a}無法辨識與執行")
        return finish

    def add_score(self, who, num):
        self.record[who] += num #目前沒有用typ

    def story_end(self):
        self.clear()
        self.create_timer(self.set_send_admin, 2, [], "Mono")

    def draw(self):
        self.checkEvent()
        self.run_wfm("PRE") #通常不用執行POST
        #製作Surface
        self.Surface.fill((0, 0, 0, 0))
        #self.GPblit.update()
        for i in iter(self.GPblit):
            i.update()
        #rect_list = self.GPblit.draw(self.Surface)
        rect_list = []
        for i in iter(self.GPblit):
            if i.has_image():
                r = self.Surface.blit(i.image, i.rect)
                rect_list.append(r)
        
        s = self.send_admin.copy()
        self.send_admin.clear()
        
        return self.Surface, rect_list, s

    def reset(self):
        for i in self.chara_name:
            delattr(self, i)
        self.__init__()
	
    def ani_static(self):
        for i in iter(self.GPblit):
            if not i.ani_static():
                return 0
        return 1
	
    def is_static(self):
        for i in self.GPblit:
            if not i.is_static():
                return 0
        return 1
    

def readscript(admin, path = "", scripts = []): #story_scene, str, list
    if scripts == []:
        scripts = open(path, "r", encoding = "utf8").readlines()
    else:
        pass
    scripts = list(map(lambda x: x.strip(), scripts[::-1])) #O(pop()) < O(pop(0))
    
    retn = deque()
    
    while len(scripts) > 0:
        s = scripts.pop()
        if s in ("BKG", "FIGURE"): #設定屬性
            onset = s
            print(f"設定{onset}中")
            l = []
            while 1:
                s = scripts.pop()
                if s != "--"+onset:
                    l.append(s)
                else:
                    if onset == "BKG":
                        admin.set_bkg(l)
                    elif onset == "FIGURE":
                        admin.set_figure(l)
                    print(f"設定{onset}完成, length: {len(l)}")
                    break
        
        elif s.startswith(";") or s == "": #註解、空行
            continue

        elif s.startswith("$"): #畫面上的物件指令
            '''
            規則:
            {obj}.{func}({Arg1}, {Arg2})
            一行一個指令
            '''
            #分離目標、函數、參數
            reg = re.compile(r"\$([\w\d]+)\.([\w\d]+)\(([\s\S]{0,})\)")
            a = re.match(reg, s)
            if a is None:
                raise ValueError(f"{s}語句無法解析")
            obj, func, args = a.group(1), a.group(2), a.group(3)
            #檢查
            if not hasattr(admin, obj):
                raise ValueError(f"找不到{obj}物件")
            if not hasattr(getattr(admin, obj), func):
                raise ValueError(f"{obj}物件無{func}屬性")
            #包裝
            p = partial(exec, "self."+s[1:]) #s要去除前綴$
            retn.append(p)

        elif s.startswith("#"): #對self的指令
            p = partial(exec, "self."+s[1:]) #s要去除前綴#
            retn.append(p)
        
        elif s[0] == s[-1] == "%": #選擇問題
            reg = re.compile(r"%([\S]+)[ ]*Chooser=([\S]+)%")
            a = re.match(reg, s)
            if a is None:
                raise ValueError(f"{s}語句無法解析")
            que_name, chooser = a.group(1), a.group(2)
            
            para = []
            while 1:
                s = scripts.pop()
                if s != f"%--End{que_name}%":
                    para.append(s)
                else:
                    break
            divide_ind = list(filter(lambda i: para[i].startswith(">"), range(len(para))))
            '''
            para:
            n行Option
            {divi-1}
            opt1結果
            {divi-2}
            opt2結果
            ...
            {divi-n}
            optn結果

            整個問題會分為n+1個section
            '''
            #檢查
            if not divide_ind[0] == len(divide_ind):
                raise ValueError(f"問題{que_name}的格式不合")

            #整理 opt -> para_name
            opt_res = {}
            for i in para[0:divide_ind[0]]:
                reg = re.compile(r"([\w]+)[* ]>>[* ]([\w]+)")
                a = re.match(reg, i)
                if a is None:
                    raise ValueError(f"{i}語句無法解析")
                opt_res[a.group(1).strip()] = a.group(2).strip()
            #將各section轉為Queue替代para_name
            divide_ind.append(len(para)) #這樣取i+1不會出錯
            for i in range(divide_ind[0]):
                reg = re.compile(r">[ ]*([\w]+)")
                res_name = re.match(reg, para[divide_ind[i]]).group(1)
                que = readscript(admin, scripts = para[divide_ind[i]+1:divide_ind[i+1]])
                for j in opt_res.keys():
                    if opt_res[j] == res_name:
                        opt_res[j] = que
                        break
                else:
                    raise ValueError(f"{res_name}找不到目的")
            
            p = que_saver(que_name, chooser, opt_res)
            retn.append(p)
        
        elif ":" in s: #文字
            speaker, content = map(lambda x: x.strip(), s.split(":"))
            retn.append((speaker, content))
        
        else:
            print(f"忽略句子'{s}', 未找到處理方式。")

    return retn
