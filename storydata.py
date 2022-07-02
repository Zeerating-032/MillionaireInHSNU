class figuredata:
    
    DATA = {
        "TestFigureA" : [{"Key":"Status1", "Path": "./img/figure/figure1.png"}],
        "TestFigureB" : [{"Key":"Status1", "Path": "./img/figure/figure2.png"}],
        "BlackFig" : [{"Key":"Status1", "Path":"./img/figure/FigureBlack.png"}],
        "BlueFig" : [{"Key":"Status1", "Path":"./img/figure/FigureBlue.png"}],
        "RedFig" : [{"Key":"Status1", "Path":"./img/figure/FigureRed.png"}],
        "YellowFig" : [{"Key":"Status1", "Path":"./img/figure/FigureYellow.png"}],
    }

    @classmethod
    def get(cls, keyword):
        retn = cls.DATA.get(keyword, None)
        if retn is not None:
            return retn
        else:
            raise ValueError(f"figuredata中找不到{keyword}")


class bkgdata:

    DATA = {
        "Bkg1" : {"Key":"Bkg1", "Path":"./img/bkg/bg_s1.png", "Pos":(0, 0)},
        "Bkg2" : {"Key":"Bkg2", "Path":"./img/bkg/bg_s2.png", "Pos":(0, 0)},
        "White" : {"Key":"White", "Path":"./img/bkg/white.png"}
    }

    @classmethod
    def get(cls, keyword):
        retn = cls.DATA.get(keyword, None)
        if retn is not None:
            return retn
        else:
            raise ValueError(f"bkgdata中找不到{keyword}")