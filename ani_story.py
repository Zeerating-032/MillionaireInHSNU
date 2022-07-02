from VARIBLE import *
from pygame.locals import *
import pygame as pg
from tools import get_from_kws
from ani_normal import *
from waitfunc import ANI_END


def run_text(**kwargs): #img_df
    '''
    obj : 目標物件 (textbox)

    1幀多一個字
    顯示範圍定義在obj.word_field
    文字顯示完隔20frame再出現箭頭
    '''

    obj = get_from_kws(kwargs, "obj")

    #set info
    INFO = dict()
    INFO["Func"] = "run_text"
    INFO["Type"] = ["img_df"]
    INFO["Flag"] = []
    yield INFO

    nline_ind = obj.newline_index
    words = obj.text
    previous_lines_sur = pg.Surface(obj.word_field, SRCALPHA, 32).convert_alpha()
    rd_text = ""
    show_pos_y = 0
    ind = 0

    while ind < len(words):        
        rd_text += words[ind]
        rd_sur = obj.word_font.render(rd_text, True, obj.word_color).convert_alpha()
        s = previous_lines_sur.copy()
        s.blit(rd_sur, (0, show_pos_y))

        #換行更新
        if ind in nline_ind:
            previous_lines_sur.blit(rd_sur, (0, show_pos_y))
            show_pos_y += obj.line_space
            rd_text = ""
        
        yield lambda: obj.img_modify_values("Text", "Surface", s)
        for _ in range(0):
            yield
        ind += 1
    
    else:
        yield lambda: setattr(obj, "allshow", True)
        for _ in range(60):
            yield
        yield lambda: obj.ani(twinkle, sub = "Arrow", alp1 = 0, alp2 = 255, cycle = 1)
    
    yield ANI_END()

def auto_get_text(**kwargs): #trigger
    '''
    obj : 故事場景 (story_scene)

    兩句話中間停0.5s, 即30 frame
    可 a -> b, b -> a
    '''

    admin = get_from_kws(kwargs, "obj")

    #set info
    INFO = dict()
    INFO["Func"] = "auto_get_text"
    INFO["Type"] = ["trigger"]
    INFO["Flag"] = []
    yield INFO

    if len(admin.search_ani(func_name = "auto_get_text")) > 1:
        admin.kill_ani(func_name = "auto_get_text")
        admin.Keybtnlist.turn_on("Get_next")
        yield ANI_END()
    
    admin.Keybtnlist.turn_off("Get_next")
    while 1: #Script用完之後的處理在get_next
        if admin.TextBox.allshow and len(admin.timer_list) == 0:
            for _ in range(30):
                yield
            admin.get_next()
        else:
            yield
