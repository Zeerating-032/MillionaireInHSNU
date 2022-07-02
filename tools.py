from pygame.math import Vector2 as Vec2
import pygame as pg
import re

def OverCheck(old, new, dest): #arg : iterable, iterable, iterable
	'''
	移動動畫檢查: 確保物件可以回到終點不因小數誤差而造成些微偏差
	Retn : float or Vec2
	'''
	if len(old) != len(new) != len(dest):
		raise ValueError("The length of three arguments have to be same so that they can be check.")
	retn = []
	for o, n, d in zip(old, new, dest):
		if (o-d)*(n-d) <= 0:
			retn.append(d)
		else:
			retn.append(n)
	if len(retn) == 1:
		return float(retn[0])
	else:
		return Vec2(retn)

def set_black(sur, ope = 51): #arg : pg.Surface, int
	'''
	Mask檢測邊界 -> 製作黑色版本 -> return
	Retn : Surface
	'''
	msk = pg.mask.from_surface(sur)
	black = msk.to_surface(setcolor = (0, 0, 0, ope), unsetcolor = (0, 0, 0, 0)).convert_alpha()
	return black

def set_black_from_obj(obj, key, ope = 51): #arg : basic_element, str, int
	'''
	同set_black
	製作目標為obj的img_df中的key所代表的Surface, 位置也相同
	Retn : black, Vec2
	'''
	sur, pos = tuple(obj.img_df.loc[obj.img_df["Key"] == key, ["Surface", "Pos"]].values[0])
	blk = set_black(sur, ope)
	return blk, pos.ext

def get_from_kws(kws, *args): # arg : dict, (str)*n
	'''
	快速從dict中取出多個值
	Retn : tuple or ??
	'''
	retn = []
	for x in args:
		retn.append(kws.get(x, None))
	if len(retn) > 1:
		return tuple(retn)
	else:
		return retn[0]

def nothing(**kwargs):
	'''
	just nothing
	'''
	return

class tpwr:
    '''
    tuple wrapper:
    用於包裝tuple/vec2，方便放入Dataframe中儲存、修改
    '''
    def __init__(self, data):
        self.ext = data
    
    def __repr__(self):
        return f"{type(self.ext)}: {self.ext}"

def str2tuple(s):
	'''
	將字串轉為(float, float)
	'''
	a = re.findall("[\d.]+", s)
	f = tuple(map(float, a))
	return f
	