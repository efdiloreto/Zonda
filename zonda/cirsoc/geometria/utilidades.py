# Copyright (c) 2019, Eduardo Di Loreto <efdiloreto@gmail.com>

# This file is part of Zonda.

# Zonda is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Zonda is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Zonda.  If not, see <https://www.gnu.org/licenses/>.

import math
import numpy as np


def array_alturas(altura_inferior, altura_superior, alturas_personalizadas=None,
                  *otras_alturas):
    """Crea un array de alturas desde :attr:`elevacion` a
    :attr:`altura_cumbrera`.

    :returns: Un array de alturas ordenada.
    :rtype: :class:`~numpy:numpy.ndarray`
    """

    if alturas_personalizadas is not None:
        array_alturas = [
            altura for altura in alturas_personalizadas if
            altura_inferior <= altura <= altura_superior
        ]
    else:
        array_alturas = list(
            range(math.ceil(altura_inferior), math.ceil(altura_superior) + 1, 1)
        )
    # Se añaden valores representativos en el array si no se encuentran.
    alturas_caracteristicas = (altura_inferior, altura_superior, *otras_alturas)
    for altura in alturas_caracteristicas:
        if altura not in array_alturas:
            array_alturas.append(altura)
    array_alturas.sort()
    return np.array(array_alturas)