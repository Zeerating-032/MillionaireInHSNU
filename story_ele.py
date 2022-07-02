from VARIBLE import *
from pygame.locals import *
import pygame as pg
from functools import partial
import re

from element import basic_element
from ani_story import *
from ani_normal import *
from btn_func import *

pg.init()
pg.font.init()

'''
bug:
question的answer_reaction最後的get_next會導致自動模式時
連續執行兩次get_next，跳過一句話
'''

# 其實就是把一些動畫包起來，寫腳本方便
class figure(basic_element):
	def __init__(self, name, img_data):
		super().__init__(name, img_data, (-9999, -9999))

	#Animation
	def appear_at(self, endpos = (-9999, -9999)):
		self.ani(const_fade, t = 0.3, endalpha = 255)
		if endpos != (-9999, -9999):
			self.ani(direct_move, endpos = endpos)
	
	def disappear(self):
		self.ani(const_fade, t = 0.3, endalpha = 0)
	
	def swift(self, endpos):
		self.ani(const_move, v0 = 30, endpos = endpos)
	
	#Pic order
	def add_pic(self, key):
		self.order_change("Add", key)
	
	def rm_pic(self, key):
		self.order_change("Del", key)
	
	def apply_odr(self, key_list):
		self.order_change("Apply", key_list)


class textbox(basic_element):

	def __init__(self):
		a = [
			{"Key": "Bkg", "Path": "./img/story/textbox.png"},
			{"Key": "Arrow", "Path": "./img/story/next_arrow.png", "Pos": (840, 135), "Alpha": 0},
			{"Key": "Speaker", "Surface": pg.Surface((0, 0)), "Pos": (50, 70)},
			{"Key": "Text", "Surface": pg.Surface((0, 0)), "Pos": (180, 30)}
		]
		super().__init__("TextBox", a, (100, 410))
		self.speaker_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 28)
		self.word_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 28)
		self.speaker_color = (0, 0, 0)
		self.word_color = (0, 0, 0)

		self.speaker = None
		self.text = None

		self.word_field = (710, 120) #文字可在之範圍
		self.newline_index = [] #在ind後須加換行符
		self.lines = 0 #文句行數

		self.line_space = 32 #兩行間空白，由左上點計算
		
		self.allshow = False #文字是否已全部出現
	
	def set_content(self, speaker, words):
		self.reset()
		self.speaker = speaker
		self.text = words

		#紀錄不可切分點 : 英文單字、數字、標點符號不可在句首
		reg = re.compile(r"[a-zA-Z0-9_]+") ##破折號、刪節號也不能切斷，目前未檢查
		eng_and_int = list(map(lambda x: x.span(), re.finditer(reg, words)))
		reg = re.compile(r"[，,。．.：:；;！!？?]")
		punc_mk = list(map(lambda x: x.start(), re.finditer(reg, words)))

		#計算換行點
		start_ind = 0
		while len(words) > 0:
			length = len(words)
			size = self.word_font.size(words)
			if size[0] > self.word_field[0]:
				short = 0
				long = len(words)
				# 用比例搜尋最佳長度
				while long - short > 1:
					length = int(length * self.word_field[0] / size[0])
					if length == short:
						length += 1
					elif length == long:
						length -= 1
					size = self.word_font.size(words[0:length])
					if size[0] < self.word_field[0]:
						short = length
					elif size[0] > self.word_field[0]:
						long = length
					else: #剛好等長
						short = length
						break
				#short是最佳長度
				#檢查是否切斷字詞
				while 1:
					if (short+start_ind-1) in punc_mk:
						short -= 1
					else:
						break
				for i in eng_and_int:
					if (short+start_ind-1) in range(*i):
						short = i[0] - start_ind -1
						break
				#更改words
				self.newline_index.append(short+start_ind-1)
				start_ind += short
				words = words[short:]
			else:
				words = words[length:]
		#更新資訊
		self.lines = len(self.newline_index) + 1		

	def show_up(self):
		sur_spek = self.speaker_font.render(self.speaker, True, self.speaker_color).convert_alpha()
		self.img_modify_values("Speaker", "Surface", sur_spek)
		self.kill_ani(sub = "Arrow")
		self.img_modify_values("Arrow", "Alpha", 0)
		self.ani(run_text, words = self.text)
		self.order_change("Apply", ["Bkg", "Speaker", "Text", "Arrow"])
	
	def quick_end_text(self):
		self.admin.Keybtnlist.turn_off("Get_next")

		sur = pg.Surface(self.word_field, SRCALPHA, 32).convert_alpha()
		#停止動畫
		self.kill_ani(func_name = "run_text")
		#分段blit文字
		slice = [0] + self.newline_index + [len(self.text)]
		for i in range(len(slice)-1):
			s = self.word_font.render(self.text[slice[i]:slice[i+1]+1], True, self.word_color).convert_alpha()
			sur.blit(s, (0, 0+self.line_space*i))
		self.img_modify_values("Text", "Surface", sur)
		self.allshow = True
		self.ani(twinkle, sub = "Arrow", alp1 = 0, alp2 = 255, cycle = 1)
		
		self.admin.Keybtnlist.turn_on("Get_next")
			
	def reset(self):
		self.speaker = None
		self.text = None
		self.newline_index = []
		self.lines = 0
		self.img_modify_values("Speaker", "Surface", pg.Surface((0, 0)))
		self.img_modify_values("Text", "Surface", pg.Surface((0, 0)))
		self.allshow = False


class question(basic_element):
	'''
	選擇人提示文字: (x置中, 0)
	選項框大小: (480, 80)
	位置: 
	1st選項 (0, 50); 2nd選項 (0, 160); 3rd選項(0, 270)
	'''

	def __init__(self):
		self.opt_space = 30 #兩選項框間的間隔
		self.word_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 20)
		self.word_color = (255, 255, 255)
		a = [
			{"Key": "Bkg", "Path": "./img/story/option.png"},
			{"Key": "Arr", "Path": "./img/story/opt_arr.png"}
		]
		super().__init__("Question", a, (320, 100))
		self.opt_length = 0
	
	def set_content(self, saver): #arg : que_saver
		frame_size = self.get_img_data("Bkg")["Size"].ext

		#選擇人
		c = self.word_font.render(f"本題由{self.admin.player[saver.chooser]}選擇", True, (0, 0, 0))
		self.img_modify_data("Add", {"Key":"Chooser", "Surface":c, "Pos":(frame_size[0]/2-c.get_size()[0]/2, 0)})
		self.order_change("Add", "Chooser")

		#選項
		opt_text = list(saver.opt_res.keys())
		self.opt_length = len(opt_text)
		for i in range(self.opt_length):
			bkg = self.get_img_data("Bkg")["Surface"].copy()
			sur = self.word_font.render(opt_text[i], True, self.word_color)
			text_size = Vec2(sur.get_size())
			bkg.blit(sur, frame_size / 2 - text_size / 2) #置中
			pos = (0, 50 + (frame_size[1]+self.opt_space)*i)
			self.img_modify_data("Add",
				{"Key": f"Opt{i+1}", "Surface": bkg, "Pos": pos}
			)

			#按鈕設定
			def answer_reaction(ndeq, admin = self.admin, **kwargs):
				admin.Question.close()
				admin.TextBox.ani(direct_fade, endalpha = 255)
				admin.extend_script(ndeq = ndeq, left = True)
				admin.onQueChoose = 0
				admin.get_next()
				return
			x = lambda a: tuple(Vec2(a) + Vec2(490, 25)) #箭頭標示位置計算
			self.admin.Mousebtnlist.add(f"Opt{i+1}", self,
				{
					"detect_func" : partial(rect_detect, dpos = pos, sfield = (480, 80)),  
					"onfocus_func" : partial(add_pic_at, key = "Arr", ndata = {"Pos":x(pos)}),
					"press_func" : partial(answer_reaction, saver.opt_res[opt_text[i]])
				})

	def show_up(self):
		for i in range(self.opt_length):
			self.order_change("Add", f"Opt{i+1}")
			self.admin.Mousebtnlist.turn_on(f"Opt{i+1}")
		self.ani(direct_fade, endalpha = 255)

	def close(self):
		self.ani(direct_fade, endalpha = 0)
		self.create_timer(self.reset, 0, [lambda: not self.admin.onQueChoose])
		
	def reset(self):
		o = self.img_df[self.img_df["Key"].str.startswith("Opt")]["Key"]
		self.img_modify_data("Del", "Chooser")
		for i in o:
			self.admin.Mousebtnlist.kill(i)
			self.img_modify_data("Del", i)
		self.opt_length = 0
		self.order_change("Apply", [])

"""
class question(basic_element):
	'''
	選擇人提示文字: (x置中, -40)
	選項框大小: (480, 80)
	位置: 
	1st選項 (0, 0); 2nd選項 (0+80+space, 0); 3rd選項(0+160+2*space, 0)
	'''

	def __init__(self):
		self.opt_space = 30 #兩選項框間的間隔
		self.word_font = pg.font.Font("./ttf/GenSenRounded-M.ttc", 20)
		self.word_color = (255, 255, 255)
		a = [
			{"Key": "Bkg", "Path": "./img/story/option.png"},
			{"Key": "Opt_arr", "Path": "./img/story/opt_arr.png"}
		]
		super().__init__("Question", a, (320, 140))
		self.opt_length = 0
	
	def set_content(self, saver): #arg : que_saver
		frame_size = self.get_img_data("Bkg")["Size"].ext

		#選擇人
		c = self.word_font.render(f"本題由{saver.chooser}選擇", True, (0, 0, 0))
		self.img_modify_data("Add", {"Key":"Chooser", "Surface":c, "Pos":(frame_size[0]/2-c.get_size()[0]/2, -80)})
		self.order_change("Add", "Chooser")

		#選項
		opt_text = list(saver.opt_res.keys())
		self.opt_length = len(opt_text)
		for i in range(self.opt_length):
			bkg = self.get_img_data("Bkg")["Surface"].copy()
			sur = self.word_font.render(opt_text[i], True, self.word_color)
			text_size = Vec2(sur.get_size())
			bkg.blit(sur, frame_size / 2 - text_size / 2) #置中
			pos = (0, (frame_size[1]+self.opt_space)*i)
			self.img_modify_data("Add",
				{"Key": f"Opt{i+1}", "Surface": bkg, "Pos": pos}
			)

			#按鈕設定
			def answer_reaction(ndeq, admin = self.admin, **kwargs):
				admin.Question.close()
				admin.extend_script(ndeq = ndeq, left = True)
				admin.get_next()
				admin.onQueChoose = 0
				return
			x = lambda a: tuple(Vec2(a) + Vec2(-70, 25)) #箭頭標示位置計算
			self.admin.Mousebtnlist.add(f"Opt{i+1}", self,
				{
					"detect_func" : partial(rect_detect, dpos = pos, sfield = (480, 80)),  
					"onfocus_func" : partial(add_pic_at, key = "Opt_arr", ndata = {"Pos":x(pos)}),
					"press_func" : partial(answer_reaction, saver.opt_res[opt_text[i]])
				})

	def show_up(self):
		for i in range(self.opt_length):
			self.order_change("Add", f"Opt{i+1}")
			self.admin.Mousebtnlist.turn_on(f"Opt{i+1}")
		self.ani(direct_fade, endalpha = 255)

	def close(self):
		self.ani(direct_fade, endalpha = 0)
		self.create_timer(self.reset, 0, [lambda: not self.admin.onQueChoose])
		
	def reset(self):
		o = self.img_df[self.img_df["Key"].str.startswith("Opt")]["Key"]
		self.img_modify_data("Del", "Chooser")
		for i in o:
			self.admin.Mousebtnlist.kill(i)
			self.img_modify_data("Del", i)
		self.opt_length = 0
		self.order_change("Apply", [])
"""

class que_saver:

	def __init__(self, name, chooser, data_dict):
		self.name = name
		self.chooser = chooser
		self.opt_res = data_dict
	
	def __repr__(self):
		retn = (
			"<que_saver>:\n"+
			f"名稱: {self.name}; \n"+
			f"選擇人: {self.chooser}; \n"
		)
		for i, j in self.opt_res.items():
			retn += f"敘述: {i} -> 有{len(j)}個語句;\n"
		return retn.strip()


class transition(basic_element): #跟mono_ele的cover差不多

	def __init__(self):
		super().__init__("Transition", [], (0, 0))
	
	def fade_in(self):
		'''
		淡入黑幕
		'''
		self.image = pg.Surface(SCREEN_SIZE, SRCALPHA, 32)
		self.image.fill((0, 0, 0, 255))
		self.ani(const_fade, t = 1, endalpha = 255)
	
	def fade_out(self):
		'''
		淡出黑幕
		'''
		self.image = pg.Surface(SCREEN_SIZE, SRCALPHA, 32)
		self.image.fill((0, 0, 0, 255))
		self.ani(const_fade, t = 1, endalpha = 0)
