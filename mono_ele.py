from pygame.locals import *
from pygame.math import Vector2 as Vec2
import pygame as pg

from element import basic_element
from ani_normal import *


pg.init()
pg.font.init()


class cover(basic_element):
	'''
	覆蓋整個畫面, 轉場或突顯重點
	'''
	def __init__(self):
		super().__init__("Cover", [], (0, 0))

	def cover_color(self, color, t, alpha):
		self.image = pg.Surface(SCREEN_SIZE, SRCALPHA, 32).convert_alpha()
		self.image.fill(color)
		self.image.set_alpha(alpha[0])
		id = self.ani(const_fade, t = t, endalpha = alpha[1])
		return id
	
	def cover_white(self):
		return self.cover_color((255, 255, 255), t = 0.2, alpha = (0, 204))
	
	def cover_black(self):
		return self.cover_color((0, 0, 0), t = 0.2, alpha = (0, 204))
	
	def fade_out(self):
		'''
		轉場用, 黑色, 1s
		'''
		return self.cover_color((0, 0, 0), t = 1, alpha = (0, 255))
	
	def rm_cover(self, t = 0.2):
		'''
		預設0.2s後消失
		'''
		id = self.ani(const_fade, t = t, endalpha = 0)
		self.create_timer(self.reset, tr_statement = [lambda: self.ani_in(id = id) == 0])

	def reset(self):
		self.__init__()


class dice(basic_element):
	def __init__(self, name, img_data, pos):
		super().__init__(name, img_data, pos)
		self.result = 0
		self.preset = [5] #作弊，骰子會由前向後用這些值，用完後隨機


class board(basic_element):
	'''
	底圖是所有Board共用的, 盡量不要更改
	'''
	Rhombic_bkg = pg.image.load("./img/mono/board_rh.png")
	Cylindrical_bkg = pg.image.load("./img/mono/board_cy.png")
	optimization = 0
	#如果加了convert_alpha會報錯, 在optimize_bkg執行
	
	def __init__(self, name, pos, step_on_pos, bkg_img):
		if self.optimization == 0:
			raise ValueError("需先執行optimize_bkg才可以定義board物件")
		if bkg_img == "Rhombic":
			super().__init__(name, [{"Key":"board", "Surface":self.Rhombic_bkg}], pos)
		elif bkg_img == "Cylindrical":
			super().__init__(name, [{"Key":"board", "Surface":self.Cylindrical_bkg}], pos)
		self.step_on_pos = Vec2(step_on_pos)
	
	@classmethod
	def optimize_bkg(cls):
		'''
		必先於定義物件前執行
		'''
		cls.Rhombic_bkg = cls.Rhombic_bkg.convert_alpha()
		cls.Cylindrical_bkg = cls.Cylindrical_bkg.convert_alpha()
		cls.optimization = 1


class piece(basic_element):
	
	def __init__(self, name, img_data, pos, path_list):
		super().__init__(name, img_data, pos)
		self.pos = 0 #物件所在的格子編號
		self.path_list = path_list #地圖上格子的中心點座標list
		self.freezed_round = 0 #被暫停的回合數
		self.next = None #下一順位
		self.profile = None #連結到的profile物件


class popup(basic_element):
	
	def __init__(self, bkg):
		'''
		onfocus_black位置:(177.5, 289)
		sfield掃瞄範圍:(120, 60)
		'''
		self.title_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 40)
		self.notice_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 28)
		self.result_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 20)
		
		#btn black製作
		blk = pg.Surface((120, 60), SRCALPHA, 32).convert_alpha()
		blk.fill((0, 0, 0, 51))
		
		a = [
			{"Key":"bkg", "Path":bkg, "Pos":(0, 0)},
			{"Key":"Onfocus", "Surface":blk, "Pos":(177.5, 289), "Alpha":255}
		]
		super().__init__("Popup", a, (320, 100))
		self.no_content = True
	
	def set_content(self, title, notice_word, result): #set title and notice_word, then show
		title = self.title_font.render(title, True, (0, 0, 0)).convert_alpha()
		notice_word = self.notice_font.render(notice_word, True, (0, 0, 0)).convert_alpha()
		result = self.result_font.render(result, True, (0, 0, 0)).convert_alpha()
		x = lambda a: (self.get_img_data("bkg")["Size"].ext[0] - a.get_size()[0]) / 2 #置中文字用
		self.img_modify_data("Add", {"Key":"title", "Surface":title, "Pos":(x(title), 12)})
		self.img_modify_data("Add", {"Key":"notice_word", "Surface":notice_word, "Pos":(x(notice_word), 100)})
		self.img_modify_data("Add", {"Key":"result", "Surface":result, "Pos":(x(result), 228)})
		self.no_content = False
		
	def show_up(self):
		self.admin.Cover.cover_white()
		self.order_change("Apply", ["bkg", "title", "notice_word", "result"])
		self.ani(const_zoom_image, t = 0.4, fixed = (0.5, 0.5))
		self.ani(const_fade, t = 0.4, endalpha = 255)
		self.admin.create_timer(self.admin.Mousebtnlist.turn_on, 0.35, [], "Popup_confirm")
	
	def close(self):
		self.admin.Cover.rm_cover()
		self.ani(const_zoom_image, t = 0.4, fixed = (0.5, 0.5), reverse = 1)
		self.create_timer(self.ani, 0.2, [], const_fade, t = 0.2, endalpha = 0)
		self.create_timer(self.ani, 0, [self.ani_static], direct_move, endpos = (320, 100)) #zoom會改變最後的rect
		self.create_timer(self.reset, 0, [self.ani_static, lambda: len(self.timer_list) == 1])

	def update(self):
		if self.no_content:
			self.run_wfm("PRE")
			return
		super().update()
	
	def reset(self):
		self.ani_list.clear()
		self.timer_list.clear()
		self.image = None
		self.size = (0, 0)
		self.pic_print_order.clear()
		for i in ("title", "notice_word", "result"):
			self.img_modify_data("Del", i)
		self.no_content = True


class story_reward(basic_element):

	def __init__(self, bkg):
		'''
		位置、大小同popup
		'''
		self.word_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 32)
		super().__init__("Story_reward", [{"Key":"bkg", "Path":bkg, "Pos":(0, 0)}], (320, 100))
		self.no_content = 1
	
	def set_content(self, host, guest): #arg : str, int tuple*2
		'''
		兩行, y = 70, 180
		x方向文字置中
		'''
		x = lambda a: (self.get_img_data("bkg")["Size"].ext[0] - a.get_size()[0]) / 2 #置中文字用
		sur_h = self.word_font.render(f"{host[0]}     獲得{host[1]}分", True, (0, 0, 0))
		sur_g = self.word_font.render(f"{guest[0]}     獲得{guest[1]}分", True, (0, 0, 0))
		self.img_modify_data("Add", {"Key":"Host_rwd", "Surface":sur_h, "Pos":(x(sur_h), 70)})
		self.img_modify_data("Add", {"Key":"Guest_rwd", "Surface":sur_g, "Pos":(x(sur_g), 180)})
		self.order_change("Apply", ["bkg", "Host_rwd", "Guest_rwd"])
		self.no_content = 0
	
	def show_up(self):
		'''
		畫面cover白底80% ->
		淡入0.3s ->
		暫停0.7s ->
		淡出0.3s ->
		cover消失
		'''
		id = self.admin.Cover.cover_white()
		self.create_timer(self.ani, 0, 
			[lambda: self.admin.Cover.ani_in(id = id) == 0],
			const_fade, t = 0.3, endalpha = 255
		)
		self.create_timer(self.close, 2, [self.ani_static])

	def close(self):
		'''
		淡出0.3秒, 關閉cover, reset
		'''
		self.ani(const_fade, t = 0.3, endalpha = 0)
		self.create_timer(self.admin.Cover.rm_cover, 0, [self.ani_static])
		self.create_timer(self.reset, 0, [self.ani_static])
	
	def update(self):
		if self.no_content:
			self.run_wfm("PRE")
			return
		super().update()

	def reset(self):
		self.ani_list = self.timer_list = []
		self.image = None
		self.size = (0, 0)
		self.img_modify_data("Del", "Host_rwd")
		self.img_modify_data("Del", "Guest_rwd")
		self.pic_print_order.clear()
		self.no_content = 1


class profile(basic_element):

	def __init__(self, name, bkg_img, pos):
		'''
		圖片設定:
		分數 右邊x貼齊206, y = 54

		編號從0開始
		'''
		#顏色、字型
		self.value_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 54)
		self.value_color = (0, 0, 0)
		
		#數值標題等設定
		self.titles = ["Score"]
		self.values = [0]
		self.data_length = len(self.titles)
		if len(self.titles) != len(self.values):
			raise ValueError("profile-init : titles, values需等長")
		self.max_value = 100 #分數的最高上限
		
		#圖片設定
		a = []
		a.append({"Key":"bkg", "Path":bkg_img})
		for i in range(self.data_length):
			d = dict()
			d["Key"] = f"val{i}"
			d["Surface"] = self.value_font.render(str(self.values[i]), True, self.value_color).convert_alpha()
			d["Pos"] = (206-d["Surface"].get_size()[0], 54)
			a.append(d)

		super().__init__(name, a, pos)
		self.order_change("Add", "bkg")
		for i in range(self.data_length):
			self.order_change("Add", f"val{i}")
	
	def is_win(self):
		for i in self.values:
			if i > self.max_value:
				return 1
		return 0
