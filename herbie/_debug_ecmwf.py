## Brian Blaylock
## January 27, 2022

from herbie.archive import Herbie

H = Herbie("2022-01-26 12:00", model="ecmwf")

H.download(":10u:")

idx = H.read_idx()

idx


