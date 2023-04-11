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

import functools
from cached_property import cached_property
import numpy as np


class PresionesBase:
    """Clase que contiene métodos comunes para determinar las presiones sobre
    diferentes tipos de estructuras.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Puede ser un único valor númerico o de tipo
        :class:`~numpy:numpy.ndarray`.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param rafaga: Una instancia de :class:`Rafaga`.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Puede ser un único valor númerico o de tipo
        :class:`~numpy:numpy.ndarray`.
    :param float factor_direccionalidad: El factor de direccionalidad
        correspondiente para el tipo de estructura.
    """
    def __init__(self, alturas, categoria, velocidad, rafaga, factor_topografico,
                 factor_direccionalidad):
        self.alturas = alturas
        self.categoria = categoria
        self.velocidad = velocidad
        self.rafaga = rafaga
        self.factor_topografico = factor_topografico
        self.factor_direccionalidad = factor_direccionalidad

    @cached_property
    def factor_importancia(self):
        """Calcula el factor de importancia de acuerdo a la categoría de la
        estructura.

        :rtype: float o int
        """
        factores = {'I': 0.87, 'II': 1, 'III': 1.15, 'IV': 1.15}
        return factores[self.categoria]

    @cached_property
    def coeficientes_exposicion(self):
        """Coeficiente de exposición para la presión dinámica.

        Este método calcula el coeficiente de exposición kz para cada altura.

        :returns: Un array si hay varias alturas sobre las cuales hay que calcular
            el coeficiente de exposicion. En caso de que haya una única altura
            retorna un float.
        :rtype: :class:`~numpy:numpy.ndarray` o float
        """
        kz_parcial_func = functools.partial(
            self._kz, alfa=self.rafaga.constantes_exp_terreno.alfa,
            zg=self.rafaga.constantes_exp_terreno.zg
        )
        try:
            zg_iter = (kz_parcial_func(height) for height in self.alturas)
            return np.fromiter(zg_iter, float)
        except TypeError:
            return kz_parcial_func(self.alturas)

    @cached_property
    def presiones_velocidad(self):
        """Presiones de velocidad.

        :returns: Un array con los valores de presiones de velocidad.
        :rtype: :class:`~numpy:numpy.ndarray`
        """
        presiones_velocidad = 0.613 * self.factor_direccionalidad * \
            self.coeficientes_exposicion * self.factor_topografico * \
            self.factor_importancia * self.velocidad ** 2
        return presiones_velocidad

    @staticmethod
    def _kz(altura, alfa, zg):
        """Calcula el coeficiente de exposición.

        :param float altura: La altura a la que se calcula el coeficiente de
            exposición.
        :param float alfa: La constante "alfa" de exposición de terreno.
        :param float zg: La constante "zg" de exposición de terreno.

        :returns: El valor del coeficiente de exposición.
        :rtype: float
        """
        return 2.01 * (max(altura, 5) / zg) ** (2 / alfa)
