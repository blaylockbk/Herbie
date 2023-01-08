# MIT License
# (c) 2023 Andreas Motl <andreas.motl@panodata.org>
# https://github.com/earthobservations
from iarray_community import IArray

iarray_info_items_original = IArray.info_items


@property
def iarray_info_items(self):
    """
    Just a minor patch for ironArray to extend info output.

    TODO: Submit patch to upstream repository.
          https://github.com/ironArray/iarray-community
    """
    items = iarray_info_items_original.fget(self)
    items += [("codec", self.codec)]
    items += [("clevel", self.clevel)]
    items += [("size", self.size)]
    return items


def monkeypatch_iarray():
    IArray.info_items = iarray_info_items
