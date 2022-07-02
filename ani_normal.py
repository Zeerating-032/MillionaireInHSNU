from VARIBLE import *
from pygame.math import Vector2 as Vec2
import pygame as pg
from tools import OverCheck, get_from_kws
from waitfunc import ANI_END

'''
這邊的函數都應支援sub
'''

def direct_move(**kwargs): #pos
	'''
	endpos : 終點 (tuple)
	'''
	endpos = get_from_kws(kwargs, "endpos")

	#set info
	INFO = dict()
	INFO["Func"] = "direct_move"
	INFO["Type"] = ["pos"]
	INFO["Flag"] = []
	yield INFO
	
	#run
	yield endpos
	yield ANI_END()

def const_move(**kwargs): #pos
	'''
	obj : 目標物件
	init_pos : 初始位置，優先使用 (tuple)
	endpos : 終點(tuple)
	t : 時間 (float)
	v0 : 初速, 單位pixel per frame (float)
	'''
	
	#set info
	INFO = dict()
	INFO["Func"] = "const_move"
	INFO["Type"] = ["pos"]
	INFO["Flag"] = []
	yield INFO
	
	init_pos = get_from_kws(kwargs, "init_pos")
	if init_pos is None:
		obj, sub = get_from_kws(kwargs, "obj", "sub")
		if sub is not None:
			init_pos = obj.get_img_data(sub)["Pos"]
		else:
			init_pos = obj.rect
	t, v0, endpos = get_from_kws(kwargs, "t", "v0", "endpos")
	
	#run
	init_pos, endpos = Vec2(init_pos), Vec2(endpos)
	if t is not None and endpos is not None: #固定時間
		mrate = (endpos - init_pos) / (t*FPS)
		while init_pos != endpos:
			init_pos = OverCheck(init_pos, init_pos+mrate, endpos)
			yield tuple(init_pos)
		
	elif v0 is not None and endpos is not None: #固定初速
		delta_s = endpos - init_pos
		v0 = v0 * delta_s.normalize()
		while init_pos != endpos:
			init_pos = OverCheck(init_pos, init_pos+v0, endpos)
			yield tuple(init_pos)
	
	yield ANI_END()

def direct_fade(**kwargs): #alpha
	'''
	endalpha = 最後不透明度 (int)
	'''
	endalpha = get_from_kws(kwargs, "endalpha")

	#set info
	INFO = dict()
	INFO["Func"] = "direct_fade"
	INFO["Type"] = ["alpha"]
	INFO["Flag"] = []
	yield INFO
	
	#run
	yield endalpha
	yield ANI_END()

def const_fade(**kwargs): #alpha
	'''
	obj : 目標物件
	init_alpha : 初始透明度，優先使用 (int)
	t : 時間 (float)
	endalpha : 最後不透明度 (int)
	v0 : 初速, 單位1/frame (float)
	'''

	#set info
	INFO = dict()
	INFO["Func"] = "const_fade"
	INFO["Type"] = ["alpha"]
	INFO["Flag"] = []
	yield INFO
	
	init_alpha = get_from_kws(kwargs, "init_alpha")
	if init_alpha is None:
		obj, sub = get_from_kws(kwargs, "obj", "sub")
		if sub is not None:
			init_alpha = obj.get_img_data(sub)["Alpha"]
		else:
			init_alpha = obj.alpha
	t, v0, endalpha = get_from_kws(kwargs, "t", "v0", "endalpha")
	#run
	if t is not None and endalpha is not None: #固定時間
		v0 = (endalpha - init_alpha) / (t*FPS)

	if v0 is not None and endalpha is not None: #固定初速或初速已計算
		while init_alpha != endalpha:
			init_alpha = OverCheck([init_alpha], [init_alpha+v0], [endalpha])
			yield int(init_alpha)
	yield ANI_END()

def const_zoom_image(**kwargs): #post_edit # img, pos
	'''
	等速縮放obj.image
	
	obj : 目標物件
	fixed : 固定點相對圖片大小的值，即(fixed[0]/size[0], fixed[1]/size[1]) (float tuple)
	t : 時間 (float)
	before : 初始大小，預設(0, 0) (tuple)
	after : 目標大小，預設為原圖大小 (tuple)
	reverse : 把before和after對調 (bool)
	'''

	#set info
	INFO = dict()
	INFO["Func"] = "const_zoom_image"
	INFO["Type"] = ["pos", "image"]
	INFO["Flag"] = ["Post_edit"]
	yield INFO

	obj, sub = get_from_kws(kwargs, "obj", "sub")
	fixed, t = get_from_kws(kwargs, "fixed", "t")
	def get_img_and_rect(o = obj, s = sub):
		if s is not None:
			a = obj.get_img_data(s)
			return (a["Surface"], a["Pos"])
		else:
			return (o.image, o.rect)
	
	origin_image, o_rect = get_img_and_rect()
	s = origin_image.get_size()
	o_fixed_pos = Vec2(s[0]*fixed[0], s[1]*fixed[1])
	
	before, after, reverse = get_from_kws(kwargs, "before", "after", "reverse")
	before = Vec2(before) if before is not None else Vec2(0, 0)
	after = Vec2(after) if after is not None else Vec2(origin_image.get_size())
	if reverse:
		before, after = after, before
	size_rate = (after - before) / (t*FPS)

	#run
	while before != after:
		#縮放圖片
		n_size = OverCheck(before, before+size_rate, after)
		n_image = pg.transform.scale(origin_image, tuple(map(int, n_size))) #need some time
		#新固定點
		n_fixed_pos = Vec2(int(n_size[0])*fixed[0], int(n_size[1])*fixed[1])
		#新位置
		n_rect = o_rect + o_fixed_pos - n_fixed_pos
		
		reblit = yield [n_image, tuple(n_rect)]
		
		#更新
		before = Vec2(n_size[0], n_size[1])
		if not reblit:
			o_fixed_pos = Vec2(n_fixed_pos[0], n_fixed_pos[1])
			o_rect = Vec2(n_rect[0], n_rect[1])
		else:
			origin_image, o_rect = get_img_and_rect()
			s = origin_image.get_size()
			o_fixed_pos = Vec2(s[0]*fixed[0], s[1]*fixed[1])

	yield ANI_END()

def twinkle(**kwargs): #endless #alpha
	'''
	obj : 目標物件 (basic_element)
	alp1 : 起始alpha值 (int)
	alp2 : 終點alpha值 (int)
	cycle : 週期 (float)

	無止盡的讓alpha值來回等速變動
	'''

	#set info
	INFO = dict()
	INFO["Func"] = "twinkle"
	INFO["Type"] = ["alpha"]
	INFO["Flag"] = ["Endless"]
	yield INFO

	obj, sub, alp1, alp2, cycle = get_from_kws(kwargs, "obj", "sub", "alp1", "alp2", "cycle")

	def detect_alpha(obj = obj, sub = sub):
		if sub is not None:
			return obj.get_img_data(sub)["Alpha"]
		else:
			return obj.alpha

	#run
	#first time
	yield lambda: obj.ani(const_fade, sub = sub, t = cycle/2, endalpha = alp2)

	#loop
	while 1:
		while detect_alpha() != alp2:
			yield
		else:
			yield lambda: obj.ani(const_fade, sub = sub, t = cycle/2, endalpha = alp1)
		while detect_alpha() != alp1:
			yield
		else:
			yield lambda: obj.ani(const_fade, sub = sub, t = cycle/2, endalpha = alp2)
