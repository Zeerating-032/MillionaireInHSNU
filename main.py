# 運行此檔案啟動程式
# 1. 控制顯示的場景，處理轉場
# 2. 處理螢幕關閉事件

# 控制方式為寄「信」給另一個場景，handle_message就是透過篩選「信」的內容執行特定指令
# UPDATE_ALL_SCREEN : 若顯示大小改變時不更新整個畫面，會導致破圖，平時則更新部分位子就好，
#                     但因物件編寫關係，似乎整個畫面會因為背景重繪而沒有省時效果。


from pygame.locals import *
import pygame as pg

from mono_scene import monopoly_main
from story_scene import story_main


SCREEN_SIZE = (1120, 630)
Screen = pg.display.set_mode(SCREEN_SIZE, pg.SRCALPHA|pg.RESIZABLE|pg.SCALED) #繪圖視窗
pg.display.set_caption("附堡傳說")
Clock = pg.time.Clock()

RUNNING = 1
UPDATE_ALL_SCREEN = 0

Mono = monopoly_main()
Story = story_main()

  
def handle_message(mes_lis):
    global RUNNING, UPDATE_ALL_SCREEN, RUNSCENE
    for d in mes_lis:
        #快速處理
        if d["Title"] == "Quit":
            RUNNING = 0
            continue
        elif d["Title"] == "ResizeScreen":
            UPDATE_ALL_SCREEN = 1
            continue
        
        #一般事件
        have_not_handle = 1 #確保每個訊息都有處理
        if d["Author"] == "Mono_scene":
            if d["Title"] == "TransScene":
                if d["NextScene"] == "Story":
                    RUNSCENE = "Story"
                    Story.set_script(d["Script_path"])
                    Story.set_player(Host = d["Host"], Guest = d["Guest"])
                    Story.appear()
                    have_not_handle = 0

        elif d["Author"] == "Story_scene":
            if d["Title"] == "TransScene":
                if d["NextScene"] == "Mono":
                    Story.reset()
                    RUNSCENE = "Mono"
                    Mono.appear("quick")
                    Mono.create_timer(Mono.reward_from_story, 0, 
                    [lambda: Mono.status == "Running"], d["Record"])
                    have_not_handle = 0
        
        if have_not_handle:
            print("Main-handle_mes:", d, "未被處理")


#起始畫面1, Mono

RUNSCENE = "Mono"
Mono.appear()

#測試故事用
'''RUNSCENE = "Story"
Story.set_script("./script/que.txt")
Story.appear()'''


#循環
while RUNNING:
    #測試句
    #pg.display.set_caption(str(Clock.get_fps())[:6])
    #循環
    Clock.tick(60)
    if RUNSCENE == "Mono":
        sur, rect_lis, message = Mono.draw()
    elif RUNSCENE == "Story":
        sur, rect_lis, message = Story.draw()
    handle_message(message)
    Screen.fill((0, 0, 0, 0))
    Screen.blit(sur, (0, 0))
    if UPDATE_ALL_SCREEN:
        pg.display.flip()
        UPDATE_ALL_SCREEN = 0
    else:
        pg.display.update(rect_lis)
