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
import numpy as np


class Cartel:
    """Calcula los coeficientes de de fuerza para un cartel.

    :param float altura_neta: La altura de la superficie del cartel donde pega
        el viento.
    :param float ancho: El ancho del cartel.
    :param bool es_parapeto: Indica si se tiene que calcular como un parapeto
        de edificio.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, altura_inferior, altura_neta, ancho, es_parapeto=False):
        self.altura_inferior = altura_inferior
        self.altura_neta = altura_neta
        self.ancho = ancho
        self.es_parapeto = es_parapeto

    def sobre_nivel_terreno(self):
        """Determina si el cartel esta sobre o a nivel del terreno.

        :returns: `True` si esta sobre nivel de terreno.
        :rtype: bool
        """
        if self.es_parapeto:
            return False
        if self.altura_inferior < 0.25 * self.altura_neta:
            return False
        return True

    @cached_property
    def cf(self):
        """Retorna el coeficiente de fuerza para el cartel.

        :rtype: float
        """
        if self.sobre_nivel_terreno():
            return self._sobre_nivel_terreno()
        return self._a_nivel_terreno()

    def _sobre_nivel_terreno(self):
        """Retorna el factor cf para un cartel sobre de terreno.

        :rtype: float
        """
        m_n = (6, 10, 16, 20, 40, 60, 80)
        cfs = (1.2, 1.3, 1.4, 1.5, 1.75, 1.85, 2)
        m = max(self.altura_neta, self.ancho)
        n = min(self.altura_neta, self.ancho)
        return np.interp(m / n, m_n, cfs)

    def _a_nivel_terreno(self):
        """Retorna el factor cf para un cartel a nivel de terreno.

        :rtype: float
        """
        m_n = (3, 5, 8, 10, 20, 30, 40)
        cfs = (1.2, 1.3, 1.4, 1.5, 1.75, 1.85, 2)
        return np.interp(self.altura_neta / self.ancho, m_n, cfs)

    @classmethod
    def desde_cartel(cls, cartel, es_parapeto=False):
        """Crea una instancia a partir de un cartel.

        :param cartel: Una instancia de :class:`geometria.Cartel`
        :param bool es_parapeto: Indica si el cartel debe ser tratado como parapeto de edificio.
        """
        return cls(cartel.altura_inferior, cartel.altura_neta, cartel.ancho,
                   es_parapeto)

    def __call__(self):
        return self.cf
