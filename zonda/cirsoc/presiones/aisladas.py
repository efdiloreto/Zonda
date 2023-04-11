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

from collections import defaultdict
from .base import PresionesBase


class CubiertaAislada(PresionesBase):
    """Hereda de :class:`PresionesBase` y calcula las presiones de cartel.

    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param rafaga: Una instancia de :class:`Rafaga`.
    :param factor_topografico: El valor del factor topografico correspondiente
        con la altura media de la cubierta.
    :param cpn: Una instancia de :class:`cp.CubiertaDosAguasAislada` o
        :class:`cp.CubiertaUnAguaAislada`.
    """
    def __init__(self, altura_media, categoria, velocidad, rafaga,
                 factor_topografico, cpn):
        super().__init__(altura_media, categoria, velocidad, rafaga,
                         factor_topografico, 0.85)
        self.cpn = cpn
        self.factor_rafaga = 0.85

    def valores(self):
        """Calcula los valores de presión para el cartel para cada altura.

        :rtype: dict.
        """
        valores_cpn = self.cpn()
        valores = defaultdict(lambda: defaultdict(dict))
        # caso es global o local
        for caso, zonas in valores_cpn.items():
            for zona, cpn in zonas.items():
                if isinstance(cpn, dict):
                    for tipo, valor_cpn in cpn.items():
                        valores[caso][zona][tipo] = self.presiones_velocidad * \
                            self.factor_rafaga * valor_cpn
                else:
                    valores[caso][zona] = self.presiones_velocidad * \
                        self.factor_rafaga * cpn
        return valores

    @classmethod
    def desde_cubierta(cls, cubierta, categoria, velocidad, rafaga,
                       factor_topografico, cpn):
        """Crea una instancia a partir de una cubierta.

        :param cubierta: Una instancia de :class:`geometria.CubiertaDosAguas` o
            :class:`geometria.CubiertaUnAgua`.
        :param str categoria: La categoría de la estructura. Valores aceptados =
            (I, II, III, IV)
        :param float velocidad: La velocidad del viento en m/s.
        :param rafaga: Una instancia de :class:`Rafaga`.
        :param factor_topografico: Los factores topográficos correspondientes a cada
            altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
        :param cpn: Una instancia de :class:`cp.CubiertaDosAguasAislada` o
            :class:`cp.CubiertaUnAguaAislada`.
        """
        return cls(cubierta.altura_media, categoria, velocidad, rafaga,
                   factor_topografico, cpn)

    def __call__(self):
        return self.valores()
