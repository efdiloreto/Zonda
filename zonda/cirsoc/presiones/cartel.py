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

from .base import PresionesBase


class Cartel(PresionesBase):
    """Hereda de :class:`PresionesBase` y calcula las presiones de cartel.

    :param alturas: Las alturas donde calcular las presiones sobre el cartel.
        Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param tuple areas_parciales: Las areas entre las alturas consideradas.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param rafaga: Una instancia de :class:`Rafaga`.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param cf: Una instancia de :class:`cp.Cartel`.
    """
    def __init__(self, alturas, areas_parciales, categoria, velocidad, rafaga,
                 factor_topografico, cf):
        super().__init__(alturas, categoria, velocidad, rafaga,
                         factor_topografico, 0.85)
        self.areas_parciales = areas_parciales
        self.cf = cf
        self.factor_rafaga = rafaga.factor

    def valores(self):
        """Calcula los valores de presión para el cartel para cada altura.

        :rtype: :class:`~numpy:numpy.ndarray`.
        """
        return self.presiones_velocidad * self.factor_rafaga * self.cf()

    def fuerzas_parciales(self):
        return self.valores()[1:] * self.areas_parciales

    def fuerza_total(self):
        return sum(self.fuerzas_parciales())

    @classmethod
    def desde_cartel(cls, cartel, categoria, velocidad, rafaga,
                     factor_topografico, cf):
        """Crea una instancia a partir de un cartel.

        :param cartel: Una instancia de :class:`geometria.Cartel`.
        :param str categoria: La categoría de la estructura. Valores aceptados =
            (I, II, III, IV)
        :param float velocidad: La velocidad del viento en m/s.
        :param rafaga: Una instancia de :class:`Rafaga`.
        :param factor_topografico: Los factores topográficos correspondientes a cada
            altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
        :param cf: Una instancia de :class:`cp.Cartel`.
        """
        return cls(cartel.alturas, cartel.areas_parciales, categoria, velocidad,
                   rafaga, factor_topografico, cf)

    def __call__(self):
        return self.valores()
