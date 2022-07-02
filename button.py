import pygame as pg
from pygame.locals import *
from element import basic_element
from tools import nothing
import functools

pg.init()
'''
蒐集所有要監測的按鈕，開關增刪一應俱全，但是不能偵測長按
'''

class keybtnlist:
	
	def __init__(self):
		self.allkey = []
		self.allname = []
		self.data_list = []
		self.status = [] # 0:normal 1:down
		self.seen = [] # bool
		self.length = 0
	
	def search(self, x): #arg : str or k_id
		'''
		可傳入名稱或按鍵變數，回傳index
		'''
		if type(x) == type(""):
			for i in range(self.length):
				if self.allname[i] == x:
					return i
			else:
				raise ValueError(f"鍵盤:找不到'{x}'相關資料")
		elif type(x) == type(K_SPACE):
			for i in range(self.length):
				if x == self.allkey[i]:
					return i
			else:
				raise ValueError(f"鍵盤:找不到代號為'{x}'的物件")
	
	def add(self, key, name, data): #arg : pygame.local var, str, dict
		'''
		規定同mousebtnlist
		'''
		kfunc = ("down_func", "press_func")
		for i in kfunc:
			if data.get(i, 0) == 0:
				data[i] = functools.partial(nothing)
		self.allkey.append(key)
		self.allname.append(name)
		self.data_list.append(data)
		self.status.append(0)
		self.seen.append(0)
		self.length += 1

	def kill(self, x): #arg : str or k_id
		'''
		先回復原狀再刪除
		'''	
		ind = self.search(x)
		self.data_list[ind]["down_func"](**self.data_list[ind]["down_arg"], force = 0)
		del self.allkey[ind]
		del self.allname[ind]
		del self.data_list[ind]
		del self.status[ind]
		del self.seen[ind]
		self.length -= 1
		return
	
	def kill_pl(self, x_tuple):
		for i in x_tuple:
			self.kill(i)
	
	def is_open(self, x):
		ind = self.search(x)
		return self.seen[ind]
	
	def is_off(self, x):
		return not self.is_open(x)
	
	def turn_on(self, x):
		ind = self.search(x)
		self.seen[ind] = 1
		if pg.key.get_pressed()[self.allkey[ind]]:
			self.status[ind] = 1
			self.data_list[ind]["down_func"]()
	
	def turn_off(self, x):
		ind = self.search(x)
		self.data_list[ind]["down_func"](force = 0)
		self.status[ind] = 0
		self.seen[ind] = 0

	def turn_on_pl(self, x_tuple):
		for i in x_tuple:
			self.turn_on(i)
	
	def turn_off_pl(self, x_tuple):
		for i in x_tuple:
			self.turn_off(i)
	
	def check_press(self, press_id): #arg : k_id
		for i in range(self.length):
			if not self.seen[i]:
				continue
			if self.allkey[i] == press_id and self.status[i] == 0:
				self.status[i] = 1 #仿造mouse button, 彈起時才執行函式
				self.data_list[i]["down_func"]()
	
	def check_up(self, up_id): #arg : k_id
		for i in range(self.length):
			if not self.seen[i]:
				continue
			if self.allkey[i] == up_id and self.status[i] == 1:
				self.status[i] = 0
				self.data_list[i]["down_func"]()
				self.data_list[i]["press_func"]()
	
	def change_data(self, x, key, content): # arg : x, str, func or dict
		ind = self.search(x)
		self.data_list[ind][key] = content
	
	def reset(self):
		self.__init__(self)


class mousebtnlist:
	
	def __init__(self):
		self.allobj = []
		self.allname = []
		self.data_list = [] #裡面放dict，dict內皆partial
		self.status = [] # 0:Normal, 2:on focus, 1:down
		self.seen = []
		self.length = 0
	
	def search(self, x): #arg : str or obj
		'''
		可傳入名稱或物件本體，回傳index
		'''
		if type(x) == type(""):
			for i in range(self.length):
				if self.allname[i] == x:
					return i
			else:
				raise ValueError(f"按鈕:找不到'{x}'名稱")
		elif isinstance(x, basic_element):
			for i in range(self.length):
				if id(x) == id(self.allobj[i]):
					return i
			else:
				raise ValueError(f"按鈕:找不到名稱為'{x.name}'的物件")
	
	def add(self, name, obj, data):
		kfunc = ("detect_func", "onfocus_func", "press_func")
		for i in kfunc:
			if data.get(i, 0) == 0:
				data[i] = functools.partial(nothing)
		self.allobj.append(obj)
		self.allname.append(name)
		self.data_list.append(data)
		self.status.append(0)
		self.seen.append(0)
		self.length += 1
	
	def kill(self, x): #arg : str or obj
		'''
		先回復原狀再刪除
		'''	
		ind = self.search(x)
		self.data_list[ind]["onfocus_func"](force = 0, trf_obj=self.allobj[ind])
		del self.allobj[ind]
		del self.allname[ind]
		del self.data_list[ind]
		del self.status[ind]
		del self.seen[ind]
		self.length -= 1
		return
	
	def kill_pl(self, x_tuple):
		for i in x_tuple:
			self.kill(i)
	
	def is_open(self, x):
		ind = self.search(x)
		return self.seen[ind]
	
	def is_off(self, x):
		return not self.is_open(x)
	
	def turn_on(self, x):
		ind = self.search(x)
		self.seen[ind] = 1
	
	def turn_off(self, x):
		ind = self.search(x)
		self.data_list[ind]["onfocus_func"](force = 0, trf_obj=self.allobj[ind])
		self.status[ind] = 0
		self.seen[ind] = 0

	def turn_on_pl(self, x_tuple):
		for i in x_tuple:
			self.turn_on(i)
	
	def turn_off_pl(self, x_tuple):
		for i in x_tuple:
			self.turn_off(i)
	
	def check_focus(self, mx, my): #arg : int, int
		for i in range(self.length):
			if not self.seen[i]:
				continue
			previous_status = self.status[i]
			on = self.data_list[i]["detect_func"](mx=mx, my=my, trf_obj=self.allobj[i])
			if not on:
				self.status[i] = 0
			elif on and previous_status == 0: #如果status是1就不用改了
				self.status[i] = 2
			if bool(previous_status) != bool(self.status[i]): #有在上面(不論是否點擊) vs. 沒在上面
				self.data_list[i]["onfocus_func"](trf_obj=self.allobj[i])
	
	def check_click(self):
		for i in range(self.length):
			if self.seen[i] and self.status[i] == 2:
				self.status[i] = 1
	
	def check_up(self):
		for i in range(self.length):
			if self.seen[i] and self.status[i] == 1:
				self.status[i] = 0
				self.data_list[i]["press_func"](trf_obj=self.allobj[i])

	def change_data(self, x, key, content): # arg : x, str, func or dict
		ind = self.search(x)
		self.data_list[ind][key] = content
	
	def reset(self):
		self.__init__(self)
