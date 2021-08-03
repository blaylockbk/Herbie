## Brian Blaylock
## August 3, 2021

from herbie.archive import Herbie

H = Herbie('2021-07-01 12:00', model='hrrr')

idx = H.read_idx()

idx