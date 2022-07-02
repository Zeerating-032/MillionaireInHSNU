# 大富翁場景
# 一回合的執行流程：
# 按滑鼠按鈕骰骰子 -> 骰子動畫(ani_mono中的to_dice) -> 棋子移動(ani_mono中的move_piece)
# -> 獲取該格資料(mono_main中的get_board_data，經過decode_action) -> 顯示彈出視窗並開啟其按鈕
# -> 等待直到使用者按確定 -> 關閉彈出視窗(mono_ele中的popup中的close) -> (做點事)
# -> 加分(ani_mono中的add_score，分數可能來自mono_main中的reward_from_story) 
# -> 準備下一回合(mono_main中的next_round)

from VARIBLE import *
from pygame.locals import *
import pygame as pg
from functools import partial
import csv

from element import basic_element
from mono_ele import *
from ani_mono import *
from button import keybtnlist, mousebtnlist
from btn_func import rect_detect, cover_black
from tools import nothing, set_black_from_obj, str2tuple
from waitfunc import waitfunc_manager

pg.init()

class monopoly_main(waitfunc_manager):
	'''
	Dice -> Walking -> Popup ->
	(1. Reward 2. Walking)機會 (3. Story)故事 
	-> (Reward) -> Dice (中間全為Waiting)

	status:
	None, OnlySet, Appearing, Running, Clearing, Closed
	'''
	def __init__(self):
		'''
		Layer安排:
		背景 -3 格子 -2 個人檔案 -2
		棋子 1 骰子 4 骰子按鈕 2
		popup、story_reward 4
		凸顯畫面用遮罩 3
		轉場 99
		'''
		# 一般
		waitfunc_manager.__init__(self)
		self.name = "Mono_scene"
		self.Surface = pg.Surface(SCREEN_SIZE, SRCALPHA, 32).convert_alpha()
		self.GPblit = pg.sprite.LayeredUpdates()
		self.status = "None"
		self.send_admin = []

		#背景
		self.bkg = basic_element("Bkg", [{"Key":"MonoBkg", "Path":"./img/mono/bkg.png"}], (0, 0))
		self.GPblit.add(self.bkg, layer = -3)

		#格子
		'''
		編號皆從0開始
		'''
		self.Boards = pg.sprite.Group()
		self.board_data = []
		board.optimize_bkg()
		with open("./csv/board_data.csv", newline = "", encoding = "utf-8") as f:
			alldata = list(csv.reader(f))
			alldata.pop(0) #標題行
			for i, data in enumerate(alldata):
				data[0] = str2tuple(data[0])
				data[1] = str2tuple(data[1])
				Board = board(f"Board{i}", *data[0:3])
				self.GPblit.add(Board, layer = -2)
				self.Boards.add(Board)
				self.board_data.append(data[3:])

		#個人資料
		self.Profile1 = profile("Profile1", "./img/mono/profile_green.png", (50, 470))
		self.Profile2 = profile("Profile2", "./img/mono/profile_yellow.png", (820, 470))
		self.Profiles = [self.Profile1, self.Profile2]
		self.GPblit.add(*self.Profiles, layer = -2)

		#骰子與骰子按鈕
		self.Dice = dice("Dice", [{"Key": "All", "Path": "./img/mono/dice.png"}], (615, 301))
		self.btn_dice = basic_element("btn_dice", [{"Key":"bkg", "Path":"./img/mono/btn_dice.png"}], (466, 353))		
		blk, pos = set_black_from_obj(self.btn_dice, "bkg")
		self.btn_dice.img_modify_data("Add", 
		{
			"Key":"Onfocus", "Surface":blk, 
			"Pos":pos, "Alpha":255
		})
		self.GPblit.add(self.Dice, layer = 4)
		self.GPblit.add(self.btn_dice, layer = 2)

		#棋子
		path_list = list(map(lambda x: x.step_on_pos, iter(self.Boards)))
		self.piece1 = piece("玩家1", [{"Key":"status1", "Path":"./img/mono/piece_green.png"}], (539, 417), path_list)
		self.piece2 = piece("玩家2", [{"Key":"status1", "Path":"./img/mono/piece_yellow.png"}], (520, 410), path_list)
		self.pieces = [self.piece1, self.piece2]
		self.player_num = len(self.pieces)
		
		for i in range(self.player_num):
			self.pieces[i].next = self.pieces[(i+1)%self.player_num]
			self.pieces[i].profile = self.Profiles[i]
		self.now_turn = 0
		self.GPblit.add(*self.pieces, layer = 1)

		#其他
		self.Cover = cover()
		self.Transition = cover()
		self.Popup = popup("./img/mono/popup.png")
		self.Story_reward = story_reward("./img/mono/story_reward.png")
		self.GPblit.add(self.Cover, layer = 3)
		self.GPblit.add(self.Transition, layer = 99)
		self.GPblit.add(self.Popup, layer = 4)
		self.GPblit.add(self.Story_reward, layer = 4)

		#設定所有basic_element的admin
		for i in iter(self.GPblit):
			i.admin = self
		
		#按鈕設定
		self.Keybtnlist = keybtnlist()
		self.Mousebtnlist = mousebtnlist()
		self.set_btn()

		self.status = "OnlySet"
	
	def set_btn(self):
		partial_dice = partial(self.Dice.ani, to_dice, t = 0.3)
		self.Mousebtnlist.add("Dice", self.btn_dice, 
		{
			"detect_func" : partial(rect_detect), 
			"onfocus_func" : partial(cover_black), 
			"press_func" : partial_dice
		})
		self.Mousebtnlist.add("Popup_confirm", self.Popup,
		{
			"detect_func" : partial(rect_detect, dpos = (177.5, 289), sfield = (120, 60)),
			"onfocus_func" : partial(cover_black),
			"press_func" : nothing
		}) #press func 在get_board_action中更改

	def set_send_admin(self, typ, *args, **kwargs):
		'''
		將回傳資料存在dict後加入list中
		基礎必傳值
		Author, Title
		'''
		d = {"Author": self.name}
		if typ == "QuitGame":
			d["Title"] = "Quit"

		elif typ == "ResizeScreen":
			d["Title"] = "ResizeScreen"

		elif typ == "Story": #轉換畫面至Story
			'''
			Title = TransScene, NextScene = Story
			內容:
			Script_path 以kwargs方法傳入
			Host, Guest 表本回合擲骰者、非擲骰者
			'''
			d["Title"] = "TransScene"
			d["NextScene"] = "Story"
			d["Host"] = self.pieces[self.now_turn].name
			d["Guest"] = self.pieces[(self.now_turn+1)%self.player_num].name
			for i in ("Script_path",):
				if kwargs.get(i, None) is None:
					raise ValueError(f"若要轉場至Story, kwargs必傳{i}")
				d[i] = kwargs[i]
		
		else:
			raise ValueError(f"MonoScene的set_send_admin不支援typ= '{typ}'")		
		self.send_admin.append(d)

	def checkEvent(self):
		for event in pg.event.get():
			if event.type == QUIT:
				self.set_send_admin("QuitGame")
			
			elif event.type == WINDOWSIZECHANGED:
				self.set_send_admin("ResizeScreen")

			elif event.type == MOUSEMOTION:
				mx, my = pg.mouse.get_pos()
				self.Mousebtnlist.check_focus(mx, my)

			elif event.type == MOUSEBUTTONDOWN:
				self.Mousebtnlist.check_click()
			
			elif event.type == MOUSEBUTTONUP:
				self.Mousebtnlist.check_up()
			
			elif event.type == KEYDOWN:
				k = event.key #get the id
				self.Keybtnlist.check_press(k)
			
			elif event.type == KEYUP:
				k = event.key
				self.Keybtnlist.check_up(k)

	def appear(self, arg = ""): #根據arg可能會有不同appear方式
		self.status = "Appearing"
		if arg == "": #一般
			#加圖
			self.bkg.order_change("Add", "MonoBkg")
			self.btn_dice.order_change("Add", "bkg")
			self.piece1.order_change("Add", "status1")
			self.piece2.order_change("Add", "status1")
			for i in iter(self.Boards):
				i.order_change("Add", "board")
			
			#顯示
			self.bkg.ani(direct_fade, endalpha = 255)
			for i in range(self.player_num):
				self.pieces[i].ani(direct_fade, endalpha = 255)
				self.Profiles[i].ani(direct_fade, endalpha = 255)
			for i in iter(self.Boards):
				i.ani(direct_fade, endalpha = 255)
			self.btn_dice.ani(direct_fade, endalpha = 255)
			
			#開按鈕
			self.Mousebtnlist.turn_on("Dice")
		
		elif arg == "quick": #從某場景回來，只要出現物件就好
			self.Transition.reset()
			self.bkg.ani(direct_fade, endalpha = 255)
			for i in range(self.player_num):
				self.pieces[i].ani(direct_fade, endalpha = 255)
				self.Profiles[i].ani(direct_fade, endalpha = 255)
			for i in iter(self.Boards):
				i.ani(direct_fade, endalpha = 255)
			self.btn_dice.ani(direct_fade, endalpha = 255)
		
		self.create_timer(
			setattr, 0, [self.ani_static], 
			self, "status", "Running"
		)
	
	def clear(self):
		self.status = "Clearing"
		self.Transition.fade_out()
		for i in self.GPblit:
			i.ani(direct_fade, endalpha = 0)
		
		self.create_timer(
			setattr, 0, [self.ani_static], 
			self, "status", "Closed"
		)

	def decode_action(self, Action): #next_round判定未寫
		'''
		分解Action String, act為lambda list交由popup按鈕執行, intro為popup所顯示的介紹訊息
		'''
		pieces = (self.pieces*2)[self.now_turn:self.now_turn+self.player_num]
		acts, intro = [], ""
		for tk in Action.split(";"): #分離各個事件
			typ, arg = tuple(tk.strip().split(">>")) #typ : 即將觸發的函數; arg : 傳入的參數
			if typ == "MOVE":
				target, steps = map(int, arg.split("_"))
				acts.append(partial(pieces[target].ani, move_piece, steps=steps, trigger=0))
				if steps > 0:
					intro += f"{pieces[target].name}向前{steps}步\n"
				else:
					intro += f"{pieces[target].name}後退{-1*steps}步\n"
			
			elif typ == "REWARD":
				target, add_title, score = tuple(arg.split("_"))
				target, score = int(target), int(score)
				acts.append(partial(pieces[target].profile.ani, add_score, typ=add_title, num=score))
				if score > 0:
					intro += f"{pieces[target].name}的{add_title}加{score}分\n"
				else:
					intro += f"{pieces[target].name}的{add_title}減{-1*score}分\n"
			
			elif typ == "OPEN":
				story_name, path = tuple(arg.split("_"))
				intro += f"進入故事:{story_name}"
				acts.append(lambda: self.create_timer(
					self.clear, 0,
					[self.Popup.is_static]
				)) #等Popup關閉
				acts.append(lambda: self.create_timer(
					self.set_send_admin, 0,
					[lambda: self.status == "Closed"],
					typ = "Story", Script_path = path
				))

			else:
				raise ValueError(f"decode_the_action : 傳入typ '{typ}', 無法辨識")
		
		if typ in ("MOVE", "REWARD"):
			acts.append(lambda: self.create_timer(self.next_round, tr_statement = [self.is_static]))
		
		return acts, intro

	def get_board_action(self, board_ind):
		#獲取資訊
		Title, Intro, Action = tuple(self.board_data[board_ind])
		acts, event_intro = self.decode_action(Action)
		self.Popup.set_content(Title, Intro, event_intro) #str, str, str
		self.Popup.show_up()
		#設定按鈕內容
		def run_popup(act_list, admin, **kwargs):
			#關閉Popup
			admin.Mousebtnlist.turn_off("Popup_confirm")
			admin.Popup.close()
			#執行事件
			for i in act_list:
				i.__call__()
			return
		self.Mousebtnlist.change_data("Popup_confirm", "press_func", partial(run_popup, acts, self))

	def reward_from_story(self, data):
		'''
		data = {"Host": {int}, "Guest": {int}}
		'''
		names = [self.pieces[self.now_turn].name, self.pieces[self.now_turn].next.name]
		self.Story_reward.set_content(*list(zip(names, data.values())))
		self.Story_reward.show_up()
		self.create_timer(
			self.pieces[self.now_turn].profile.ani, 0, [self.Story_reward.is_static],
			add_score, typ = "Score", num = data["Host"]
		)
		self.create_timer(
			self.pieces[self.now_turn].next.profile.ani, 0, [self.Story_reward.is_static],
			add_score, typ = "Score", num = data["Guest"]
		)
		self.create_timer(self.next_round, 0, [self.ani_static])

	def next_round(self):
		while 1:
			self.now_turn = (self.now_turn + 1) % self.player_num
			if self.pieces[self.now_turn].freezed_round > 0:
				print(self.pieces[self.now_turn].name, "被暫停")
				self.pieces[self.now_turn].freezed_round -= 1
			else:
				break
		self.Mousebtnlist.turn_on("Dice")
		self.btn_dice.ani(const_fade, t = 0.3, endalpha = 255)

	def draw(self):
		self.checkEvent()
		self.run_wfm("PRE") #通常不用跑POST
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
		
		#回傳send_admin
		s = self.send_admin.copy()
		self.send_admin.clear()
		
		#檢測輸贏
		win_index = filter(lambda x: self.Profiles[x].is_win(), range(len(self.Profiles)))
		for i in win_index:
			#獲勝動畫
			print(self.Profiles[i].name, "獲勝")
			pass
		return self.Surface, rect_list, s
		
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
