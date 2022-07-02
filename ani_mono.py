from VARIBLE import *
from tools import get_from_kws
from ani_normal import *
from waitfunc import ANI_END
import random
import pygame as pg


def to_dice(**kwargs): #order, alpha, trigger
	'''
	參數:
	obj : 目標物件 (dice)
	t : 時間 (float)
	流程:
	骰子按鈕消失 -> 作骰子動畫1秒 -> 骰子靜止後向admin觸發走路 -> 骰子淡出 -> 結束

	骰子圖片大小: 83*83
	'''
	obj, t, trf_obj = get_from_kws(kwargs, "obj", "t", "trf_obj")
	allpic = obj.get_img_data("All")["Surface"]
	pics = {}
	
	#set info
	INFO = dict()
	INFO["Func"] = "to_dice"
	INFO["Type"] = ["order", "alpha", "trigger"]
	INFO["Flag"] = ["Post_edit"]
	yield INFO
	
	#run
	#設定結果
	if len(obj.preset) > 0: #preset就是個作弊
		obj.result = obj.preset.pop(0)
	else:
		obj.result = random.randint(1, 6)
	#骰子出現、關閉按鈕、白幕出現
	yield [
		lambda: obj.ani(direct_fade, endalpha = 255),
		lambda: trf_obj.ani(direct_fade, endalpha = 0),
		lambda: obj.admin.Mousebtnlist.turn_off("Dice"),
		lambda: obj.admin.Cover.cover_white()
	]

	#換圖片， 4 frames一張
	i = 0
	while i < t*FPS//2-1:
		rnd = random.randint(1, 6)
		if pics.get(rnd, None) is None:
			pics[rnd] = pg.Surface.subsurface(allpic, pg.Rect((83*(rnd-1), 0), (83, 83)))
		yield pics[rnd]
		for _ in range(3):
			yield
		i += 1
	if pics.get(obj.result, None) is None:
		yield pg.Surface.subsurface(allpic, pg.Rect((83*(obj.result-1), 0), (83, 83)))
	else:
		yield pics[obj.result]

	#骰子消失、白幕消失
	for _ in range(20):
		yield
	yield [
		lambda: obj.ani(const_fade, t = 0.3, endalpha = 0),
		lambda: obj.admin.Cover.rm_cover()
	]
	
	#移動棋子動畫
	yield lambda: obj.admin.create_timer(
		obj.admin.pieces[obj.admin.now_turn].ani,
		0, [obj.is_static, obj.admin.Cover.is_static],
		move_piece,
		steps = obj.result,
		trigger = 1
		)
	yield ANI_END()

def move_piece(**kwargs): #pos, trigger
	'''
	參數:
	obj : 目標物件 (piece)
	steps : 步數
	trigger : 是否觸發事件 (bool)

	說明:
	1.一個格子140*80
	2.預設移動速度為 360 pixel/s, 即6 pixel/frame
	3. 走一格, 停0.15s, 即9幀
	
	流程:
	加入新的位置 -> 設定動畫 -> 物件靜止後等待8幀 -> 加入下一終點 -> 物件靜止後向admin觸發trigger
	'''
	obj, steps, trigger = get_from_kws(kwargs, "obj", "steps", "trigger")

	# set INFO
	INFO = dict()
	INFO["Func"] = "move_piece"
	INFO["Type"] = ["pos", "trigger"]
	INFO["Flag"] = []
	yield INFO
	
	backward = 1 if steps > 0 else -1
	for _ in range(abs(steps)):
		obj.pos = (obj.pos + 1*backward) % len(obj.path_list)
		endpos = obj.path_list[obj.pos] - Vec2(obj.size[0]//2, obj.size[1])
		id = obj.ani(const_move, v0 = 20, endpos = tuple(endpos))
		while obj.ani_in(id = id):
			yield
		for _ in range(8):
			yield
	
	if trigger:
		yield lambda: obj.admin.get_board_action(obj.pos)
	
	yield ANI_END()

def add_score(**kwargs): #img_df, trigger
	'''
	obj : 目標物件 (profile)
	num : 增加數 (int)
	typ : 增加的種類, 與物件的titles對應 (str)
	
	三幀分數加一, 加分時分數為紅色
	'''
	cRed = (255, 0, 0)

	obj, num, typ = get_from_kws(kwargs, "obj", "num", "typ")
	target_ind = obj.titles.index(typ)
	target = f"val{target_ind}"
	init_score = obj.values[target_ind]
	previous_pos = obj.get_img_data(target)["Pos"].ext
	
	#set INFO
	INFO = dict()
	INFO["Func"] = "add_score"
	INFO["Type"] = ["img_df"]
	INFO["Flag"] = []
	yield INFO
	
	#run
	for d in range(init_score, init_score+num+1):
		obj.values[target_ind] = d
		sur = obj.value_font.render(str(d), True, cRed)

		sur_lam = lambda: obj.img_modify_values(target, "Surface", sur)
		n_pos = (206-sur.get_size()[0], previous_pos.y)
		pos_lam = lambda: obj.img_modify_values(target, "Pos", n_pos)
		yield [sur_lam, pos_lam]

		if d == obj.max_value:
			print("已滿分")
			#可能有滿分動畫
			break
		
		for _ in range(2):
			yield
	sur = obj.value_font.render(str(init_score+num), True, obj.value_color)
	yield lambda: obj.img_modify_values(target, "Surface", sur)

	yield ANI_END()
