from pygame.math import Vector2 as Vec2
from tools import get_from_kws

# detect, 只會return 1, 0
def rect_detect(**kwargs):
	'''
	trigger_from_obj : 呼叫函式的物件
	dpos : 判定點相對位移，預設(0, 0) (tuple)
	sfield : 掃描大小, 預設原Surface大小 (tuple)
	mx : 滑鼠座標x
	my : 滑鼠座標y
	'''
	trf_obj, dpos, sfield, mx, my = get_from_kws(kwargs, "trf_obj", "dpos", "sfield", "mx", "my")
	if dpos is None:
		dpos = (0, 0)
	if sfield is None:
		sfield = trf_obj.size
	
	distance = Vec2(mx, my) - (Vec2(trf_obj.rect) + Vec2(dpos))
	if 0 <= distance[0] <= sfield[0] and 0 <= distance[1] <= sfield[1]:
		return 1
	else:
		return 0

# onfocus, 第一次執行a -> b, 第二次b -> a，且參數可接收force
def cover_black(**kwargs):
	'''
	將onfocus開頭的surface加入pic_print_order
	'''
	trf_obj, force = get_from_kws(kwargs, "trf_obj", "force")
	order = trf_obj.pic_print_order
	has_onfocus = any(map(lambda x: x.startswith("Onfocus"), order))

	if not has_onfocus or force == 1: #增加
		for i in trf_obj.img_df[trf_obj.img_df["Key"].str.startswith("Onfocus")]["Key"]:
			trf_obj.order_change("Add", i)
	
	else: #刪除
		for i in order[::-1]:
			if i.startswith("Onfocus"):
				trf_obj.order_change("Del", i)
	return

def cover_pic(**kwargs):
	trf_obj, force, keys = get_from_kws(kwargs, "trf_obj", "force", "keys")
	if not all(x in trf_obj.pic_print_order for x in keys) or force:
		for i in keys:
			if i not in trf_obj:
				trf_obj.order_change("Add", i)
			else:
				pass
	else:
		for i in keys:
			trf_obj.order_change("Del", i)
	return

def add_pic_at(**kwargs):
	'''
	先修改obj中key的內容在加入pic_print_order
	'''
	trf_obj, key, ndata = get_from_kws(kwargs, "trf_obj", "key", "ndata")
	if key not in trf_obj.pic_print_order:
		for i, j in ndata.items():
			trf_obj.img_modify_values(key, i, j)
		trf_obj.order_change("Add", key)
	else:
		trf_obj.order_change("Del", key)