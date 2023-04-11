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

from cached_property import cached_property
from .utilidades import array_alturas


class Cartel:
    """Crea un cartel.

    :param float profundidad: La profundidad del cartel.
    :param float ancho: El ancho del cartel.
    :param float altura_inferior: La altura desde el suelo desde donde se consideran
        las presiones del viento sobre el cartel.
    :param float altura_superior: La altura superior del cartel.
    :param list alturas_personalizadas: (opcional) Las alturas sobre las que se
        calcularán las presiones de viento sobre paredes a barlovento. Puede ser
        ``list`` o ``tuple``.
    """
    def __init__(self, profundidad, ancho, altura_inferior, altura_superior,
                 alturas_personalizadas=None):
        self.profundidad = profundidad
        self.ancho = ancho
        self.altura_inferior = altura_inferior
        self.altura_superior = altura_superior
        self.alturas_personalizadas = alturas_personalizadas

    @cached_property
    def altura_neta(self):
        """Calcula la altura de la superficie del cartel donde pega el viento.

        :rtype: float
        """
        return self.altura_superior - self.altura_inferior

    @cached_property
    def area(self):
        """Calcula el area del cartel.

        :rtype: float
        """
        return self.ancho * self.altura_neta

    @cached_property
    def altura_media(self):
        """Calcula la altura media del cartel

        :rtype: float
        """
        return (self.altura_inferior + self.altura_superior) / 2

    @cached_property
    def alturas(self):
        """Crea un array de alturas desde :attr:`elevacion` a
        :attr:`altura_superior`.

        :returns: Un array de alturas ordenada.
        :rtype: :class:`~numpy:numpy.ndarray`
        """
        alturas = array_alturas(
            self.altura_inferior, self.altura_superior, self.alturas_personalizadas
        )
        return alturas

    @cached_property
    def areas_parciales(self):
        areas = tuple(
            self.ancho * (area_sup - area_inf) for area_inf, area_sup
            in zip(self.alturas, self.alturas[1:])
        )
        return areas

    def __repr__(self):
        return f'<{self.__name__}(profundidad={self.profundidad}, ancho={self.ancho},' \
            f' altura_inferior={self.altura_inferior},' \
            f' altura_superior={self.altura_superior}'

    def __str__(self):
        return 'Cartel'
