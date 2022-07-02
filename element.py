from VARIBLE import *
from pandas import DataFrame
import pandas as pd
import numpy as np
from pygame.locals import *
from pygame.math import Vector2 as Vec2
import pygame as pg
from tools import tpwr
from waitfunc import waitfunc_manager

'''
Bugs與改進:
1. reblit是用大畫布繪製後裁剪，可參考手冊中的顯示方式改進
2. 原本的reblit有錯，基準點不能放在(0, 0)以外
'''


class basic_element(pg.sprite.Sprite, waitfunc_manager):
	'''
	一切圖片的ancestor
	'''
	def __init__(self, name, img_data, pos): #arg : str, dict list, tuple
		pg.sprite.Sprite.__init__(self)
		waitfunc_manager.__init__(self)
		
		# 基本屬性
		self.name = name
		self.img_df = self.set_img(img_data)
		self.pic_print_order = [] # 存img_df的key
		self.rect = pos
		self.alpha = 0
		
		# 產生self.image用
		self.surface = pg.Surface((SCREEN_SIZE[0]*3, SCREEN_SIZE[1]*3), SRCALPHA, 32).convert_alpha()
		self.origin_point = Vec2(SCREEN_SIZE)
		self.size = (0, 0) #每次update後更新
		self.image = None
		self.reblit = 1
		
		#上級
		self.admin = None #上級class
	
	def set_img(self, data): # arg : dict list
		'''
		用DataFrame儲存資料
		1. data內每個dict的keys、values須滿足: 
		   。有Key, 值type為String
		   。Path、Surface傳一個, 若都傳則優先用Path
		   。Pos值的type為tuple, 預設(0, 0)
		   。alpha的值type為int, 預設255
		   。size不可傳
		2. 回傳值為DataFrame
		3. Pos, Size類用tpwr(Vec2(a, b))的形式儲存, obj.ext調用
		'''
		lis = []
		for i in range(len(data)):
			#填充Surface行, Size行
			if "Surface" not in data[i].keys():
				try:
					path = data[i]["Path"]
					data[i]["Surface"] = pg.image.load(path).convert_alpha()
				except TypeError:
					raise TypeError(f"{self.name} can't find the pic '{path}' or it is not a path")
			data[i]["Size"] = tpwr(Vec2(data[i]["Surface"].get_size()))
			#將Pos包裝，預設(0, 0)
			data[i]["Pos"] = tpwr(Vec2(data[i].get("Pos", (0, 0))))
			#Alpha預設255
			data[i]["Alpha"] = data[i].get("Alpha", 255)
			lis.append(DataFrame(data[i], index = [0]))
		if len(lis) > 0:
			df = pd.concat(lis, axis = 0, ignore_index = True)
		else:
			df = DataFrame()
		return df
	
	def get_img_data(self, key): #arg : str
		'''
		取出img_df的單列
		'''
		s = self.img_df.loc[self.img_df["Key"] == key]
		d = dict()
		for i in s.columns:
			d[i] = s[i][s.index[0]]
		return d

	def img_modify_data(self, typ, data): #arg : str, dict or str
		'''
		typ : Add或Del
		data : Add - 一列, 格式與img_df一致, Key必傳, Path, Surface必傳一個, Size不可傳 (dict)
		       Del - key (str)
		'''
		if typ == "Add":
			df = self.set_img([data]) #原版: 0514, 確認可用
			self.img_df = pd.concat([self.img_df, df], axis = 0, ignore_index = True)
			
		elif typ == "Del":
			msk = self.img_df[self.img_df["Key"]==data]
			self.img_df.drop(msk.index, inplace = True)
		
		else:
			raise ValueError(f"typ只能是Add或Del，你傳入{typ}")
	
	def img_modify_values(self, key, row, new_value): #arg : str, str, ???
		'''
		key : 所改變列的key
		row : 要改變的值標題, 可傳Surface, Pos, Alpha
		new_value : 新值
		'''
		if row in ("Pos"):
			new_value = tpwr(Vec2(new_value))
		
		self.img_df.loc[self.img_df["Key"]==key, row] = new_value #定位錯誤會直接報錯

		if row == "Surface":
			self.img_df.loc[self.img_df["Key"]==key, "Path"] = np.nan
			self.img_df.loc[self.img_df["Key"]==key, "Size"] = tpwr(Vec2(new_value.get_size()))

		if key in self.pic_print_order:
			self.reblit = 1
	
	def order_change(self, typ, key): #arg : str, str or list
		'''
		更改pic_print_order
		'''
		if type(key) == type("String"):
			key = [key]
		if typ == "Apply":
			self.pic_print_order = key
		elif typ == "Add":
			self.pic_print_order.extend(key)
		elif typ == "Del":
			for i in key:
				self.pic_print_order.remove(i)
		else:
			raise ValueError(f"typ只可傳入Apply, Add, Del, 你傳入{typ}")
		self.reblit = 1

	def reblit_image(self):
		if len(self.pic_print_order) == 0:
			self.image = None
			self.size = (0, 0)
			return
		'''
		surface.size是SCREEN_SIZE的長寬各三倍, 想像成九宮格
		一張一張圖片blit上去, 算出左上、右下點, 切出image, 以達成size可變動
		'''
		self.surface.fill((0, 0, 0, 0))
		#leftup, rightdown是裁切時的左上、右下點
		leftup = self.origin_point
		rightdown = self.origin_point
		for i in self.pic_print_order:
			try:
				a = self.img_df.loc[self.img_df["Key"]==i, ["Surface", "Pos", "Alpha", "Size"]]
			except IndexError: #找不到
				raise IndexError(f"{self.name}找不到key'{i}'\n{self.img_df}")
			sur, pos, ap, size = tuple(a.values[0])
			pos, size = pos.ext, size.ext
			sur.set_alpha(ap)
			self.surface.blit(sur, tuple(pos+self.origin_point))
			#確認是否更新leftup, rightdown
			pos_lu = self.origin_point + pos
			pos_rd = self.origin_point + pos + size
			leftup = Vec2(min(leftup[0], pos_lu[0]), min(leftup[1], pos_lu[1]))
			rightdown = Vec2(max(rightdown[0], pos_rd[0]), max(rightdown[1], pos_rd[1]))

		#裁剪出self.image
		self.image = self.surface.subsurface(pg.Rect(tuple(leftup), tuple(rightdown-leftup))).convert_alpha()
		self.size = self.image.get_size()
		#計算移動後的rect
		self.rect = tuple(Vec2(self.rect) - self.origin_point + leftup)

	def update(self):
		self.run_wfm("PRE")
		if self.reblit:
			self.reblit_image()
			self.reblit = 0
		
		self.run_wfm("POST")
		'''
		Post_edit會直接改變圖片本體, 所以要放在reblit後
		目前僅能對image做Post_edit, 若是目標為sub, 則要重新reblit, 還沒做
		'''
		
		if self.image is not None: #如果物件已關閉image就是None
			self.size = self.image.get_size()
			self.image.set_alpha(self.alpha)

	def has_image(self): #是否可draw
		if self.image is not None and self.alpha > 0:
			return 1
		else:
			return 0
