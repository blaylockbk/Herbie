from herbie.toolbox import EasyMap, pc, ccrs


def test_EasyMap():
    ax = EasyMap().ax
    ax = EasyMap().STATES().ax
