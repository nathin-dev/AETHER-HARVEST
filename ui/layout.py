W, H = 1280, 720

PANEL_W   = 260
PANEL_X   = W - PANEL_W - 8
PANEL_Y   = 8
PANEL_H   = H - 16

PANEL_BTN_H   = 58
PANEL_BTN_GAP = 6
PANEL_BTN_X   = PANEL_X + 6
PANEL_BTN_W   = PANEL_W - 12

MM_W    = PANEL_W - 16
MM_H    = 90
MM_X    = PANEL_X + 8
MM_Y    = PANEL_Y + PANEL_H - MM_H - 8

PANEL_SCROLL_TOP = PANEL_Y + 36
PANEL_SCROLL_BOT = MM_Y - 6

LX        = 8
LW        = 280

RES_Y     = 8
HP_Y      = 58
BADGE_Y   = 88
MODE_Y    = 114

WEAPON_Y  = 513
STATS_Y   = 579
FPS_Y     = 699

XP_Y      = H - 5

CX        = W // 2

COMBO_Y      = 50
WAVETIMER_Y  = 108
TIMER_Y      = 6

AB_Y      = 620
AB_W      = 60
AB_H      = 60
AB_GAP    = 8
AB_TOTAL  = 3 * AB_W + 2 * AB_GAP
AB_X      = CX - AB_TOTAL // 2

LOOT_X    = AB_X + AB_TOTAL + 16
LOOT_Y    = AB_Y
LOOT_MAX_W= PANEL_X - LOOT_X - 4

def validate():
    regions = [
        ("Resource bar", LX,RES_Y,LW,44),
        ("HP bar",       LX,HP_Y,200,24),
        ("Danger badge", LX,BADGE_Y,200,20),
        ("Mode badge",   LX,MODE_Y,200,20),
        ("Weapon HUD",   LX,WEAPON_Y,210,60),
        ("Stats",        LX,STATS_Y,220,94),
        ("FPS",          LX,FPS_Y,50,14),
        ("XP bar",       0,XP_Y,W,5),
        ("Combo",        CX-120,COMBO_Y,240,52),
        ("WaveTimer",    CX-120,WAVETIMER_Y,240,38),
        ("Abilities",    AB_X,AB_Y,AB_TOTAL,AB_H),
        ("Loot effects", LOOT_X,LOOT_Y,LOOT_MAX_W,AB_H),
        ("Timer",        CX-80,TIMER_Y,160,36),
        ("Panel",        PANEL_X,PANEL_Y,PANEL_W,PANEL_H),
    ]
    def ov(r1,r2):
        x1,y1,w1,h1=r1; x2,y2,w2,h2=r2
        return not(x1+w1<=x2 or x2+w2<=x1 or y1+h1<=y2 or y2+h2<=y1)
    bad=[]
    for i,(n1,x1,y1,w1,h1) in enumerate(regions):
        for j,(n2,x2,y2,w2,h2) in enumerate(regions):
            if i>=j: continue
            if ov((x1,y1,w1,h1),(x2,y2,w2,h2)):
                bad.append(f"OVERLAP: {n1} ↔ {n2}")
    return bad