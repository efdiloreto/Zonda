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
from math import log10
import numpy as np
from cached_property import cached_property
from zonda.cirsoc import excepciones


def dedupe(items):
    """Remove duplicate for a sequence while maintaining order.

    This only works if the items in the sequence are hashable.

    Source:
        Python Cookbook, Third Edition.
        by David Beazley and Brian K. Jones.
        Copyright © 2013 David Beazley and Brian Jones.
    """
    seen = set()
    for item in items:
        if item not in seen:
            yield item
            seen.add(item)


def filtrar_cp_areas(cps, areas, area_componente):
    cp_areas = tuple(zip(cps, areas))
    numero_de_zonas = len(cp_areas)
    for i, (cp, area) in enumerate(cp_areas):
        if isinstance(cp, tuple) and isinstance(area, tuple):
            primer_area, ultima_area = area
            if area_componente > ultima_area:
                if i == numero_de_zonas - 1:
                    return cp, area
                continue
            return cp, area
        return cps, areas


def calcular_cp_cr(cps, areas, area_componente):
    """Calcula el valor de cp para un componente en base a su area tributaria.

    Referencia: Libro "DESIGN OF BUILDINGS FOR WIND - Second Edition" -
        Emil Simiu Pag. 96.

    :param tuple cps: ``tuple`` con dos valores de cp entre los que
        interpolar.
    :param tuple areas: ``tuple`` con dos valores de área entre los que
        interpolar.
    :param float area_componente: El valor de área a utilizar para encontrar el valor de
        cp por interpolación.

    :returns: El valor de cp.
    :rtype: float
    """
    primer_cp, ultimo_cp = cps
    primer_area, ultima_area = areas
    if area_componente <= primer_area:
        return primer_cp
    if area_componente >= ultima_area:
        return ultimo_cp
    g = (ultimo_cp - primer_cp) / log10(ultima_area / primer_area)
    return primer_cp + g * log10(area_componente / primer_area)


def distancia_a(ancho, longitud, altura_media):
    """Calcula la distancia "a" provista en las figuras para componentes
    y revestimientos.

    :param float ancho: El ancho de la estructura.
    :param float longitud: La longitud de la estructura.
    :param float altura_media: La altura media de la estructura.

    :rtype: float
    """
    menor_dimension_horizontal = min(ancho, longitud)
    valor_propuesto = min(0.1 * menor_dimension_horizontal, 0.4 * altura_media)
    limite_minimo = max(0.04 * menor_dimension_horizontal, 1)
    return max(valor_propuesto, limite_minimo)


class ParedesSprfvMetodoDireccional:
    """Esta clase utiliza para determinar los coeficientes de presión de paredes
    de edificio para SPRFV usando el método direccional.

    :param float ancho: El ancho del edificio.
    :param float longitud: El longitud del edificio.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud):
        self.ancho = ancho
        self.longitud = longitud

    @cached_property
    def valores(self):
        """Calcula los valores de coeficiente de presión para paredes para SPRFV.

        :returns: ``dict`` con los valores de coeficiente de presión para paredes.
        :rtype: dict
        """
        pared_sotavento_cp_paralelo = self._cp_pared_sotavento(
            self.longitud, self.ancho
        )
        pared_sotavento_cp_normal = self._cp_pared_sotavento(
            self.ancho, self.longitud
        )
        cp = {
            'paralelo': {
                'barlovento': 0.8,
                'lateral': -0.7,
                'sotavento': pared_sotavento_cp_paralelo
            },
            'normal': {
                'barlovento': 0.8,
                'lateral': -0.7,
                'sotavento': pared_sotavento_cp_normal
            }
        }
        return cp

    @cached_property
    def referencia(self):
        return 'Figura 3 (cont.)'

    @staticmethod
    def _cp_pared_sotavento(dimension_paralela, dimension_normal):
        """Calcula el coeficiente de presión para pared sotavento.

        :param float dimension_paralela: La dimension del edificio medida de
            forma paralela a la dirección del viento.
        :param float dimension_normal: La dimension del edificio medida de
            forma normal a la dirección del viento.

        :rtype: float
        """
        relaciones_paralelo_normal = (0, 1, 2, 4)
        valores_cp = (-0.5, -0.5, -0.3, -0.2)
        return np.interp(dimension_paralela / dimension_normal,
                         relaciones_paralelo_normal, valores_cp)

    def __call__(self):
        return self.valores


class ParedesMetodoEnvolvente:
    pass


class ParedesComponentes:
    """Esta clase utiliza para determinar los coeficientes de presión de paredes
    de edificio para Componentes y Revestimientos.

    :param float altura_media: La altura media de cubierta del edificio.
    :param float angulo_cubierta: El ángulo de cubierta del edificio.
    :param dict componentes: ``dict`` donde la "key" es el nombre del componente
        y el "value" es el area del mismo. Requerido para calcular las presiones
        sobre los componentes y revestimientos.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud, altura_media, angulo_cubierta,
                 componentes=None):
        self.ancho = ancho
        self.longitud = longitud
        self.altura_media = altura_media
        self.angulo_cubierta = angulo_cubierta
        self.componentes = componentes

    @cached_property
    def valores(self):
        """Calcula los valores de coeficiente de presión para
        Componentes y Revestimientos de paredes.

        :returns: Los valores de coeficiente de presión para cada pared y
            componente de la misma.
        :rtype: dict
        """
        if self.componentes is None:
            raise ValueError(
                'No hay componentes para determinar los coeficientes de presión'
            )
        valores_zonas_cp = {
            'A': {'4': (-1.1, -0.8), '5': (-1.4, -0.8), 'Todas': (1, 0.7)},
            'B': {'4': (-0.9, -0.7), '5': (-1.8, -1), 'Todas': (0.9, 0.6)}
        }
        caso = self._caso()
        factor_reduccion = 1
        if caso == 'B':
            area = (2, 50)
        else:
            area = (1, 50)
            if self.angulo_cubierta <= 10:
                factor_reduccion = 0.9
        caso_cp = valores_zonas_cp[caso]
        valor_cp = defaultdict(dict)
        for nombre, area_componente in self.componentes.items():
            for zona, cp in caso_cp.items():
                valor_cp[nombre][zona] = calcular_cp_cr(
                    cp, area, area_componente) * factor_reduccion
        return valor_cp

    @cached_property
    def distancia_a(self):
        return distancia_a(self.ancho, self.longitud, self.altura_media)

    @cached_property
    def referencia(self):
        ref = {'A': 'Figura 5A', 'B': 'Figura 8'}
        return ref[self._caso()]

    def _caso(self):
        """Determina el caso según el reglamento a usar para calcular los
        coeficientes de presión para componentes y revestimientos de pared.

        :returns: Una letra representando el caso según en reglamento.
        :rtype: string
        """
        if self.altura_media > 20:
            return 'B'
        return 'A'

    def __call__(self):
        return self.valores


class CubiertaMetodoDireccional:
    """Esta clase utiliza para determinar los coeficientes de presión de cubierta
    de edificio para SPRFV usando el método direccional.

    :param float ancho: El ancho de la cubierta.
    :param float longitud: La longitud de la cubierta.
    :param float altura_media: La altura media de la cubierta.
    :param float angulo: El ángulo de la cubierta.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud, altura_media, angulo):
        self.ancho = ancho
        self.longitud = longitud
        self.altura_media = altura_media
        self.angulo = angulo

    def normal_como_paralelo(self):
        """Determina si los coeficientes de presion sobre cubierta con el viento
        actuando normal a la cumbrera se deben determinar de la misma forma que
        con el viento actuando paralelo a la cumbrera.

        :rtype: bool
        """
        if self.angulo < 10:
            return True
        return False

    @cached_property
    def zonas(self):
        """Calcula las distancias en la cubierta sobre las que actua el viento,
        cuando la dirección del mismo es paralelo a a cumbrera o cuando el ángulo
        de la cubierta es menor que 10° y la dirección del viento es normal a la
        cumbrera.

        :returns: ``tuple`` que contiene ``tuple`` indicando el inicio y final
            para cada zona.
        :rtype: tuple
        """
        paralelo = self._zonas_cubierta(
            self.altura_media, self.longitud
        )
        if self.normal_como_paralelo():
            normal = self._zonas_cubierta(
                self.altura_media, self.ancho
            )
        else:
            normal = None
        return {'paralelo': paralelo, 'normal': normal}

    @cached_property
    def valores(self):
        """Calcula los valores de coeficiente de presión para cubierta para SPRFV.

        :returns: ``dict`` con los valores de cp para cubierta.
        :rtype: dict
        """
        cp_paralelo = self._cp_cubierta_angulo_menor_diez(
            self.longitud, self.ancho,
            len(self.zonas['paralelo'])
        )
        if self.normal_como_paralelo():
            cp_normal = self._cp_cubierta_angulo_menor_diez(
                self.ancho, self.longitud,
                len(self.zonas['normal'])
            )
        else:
            cp_barlovento = self._cp_cubierta_barlovento()
            cp_sotavento = self._cp_cubierta_sotavento()
            cp_normal = {'barlovento': cp_barlovento, 'sotavento': cp_sotavento}
        return {'paralelo': cp_paralelo, 'normal': cp_normal}

    @cached_property
    def referencia(self):
        return 'Figura 3 (cont.)'

    def _cp_cubierta_angulo_menor_diez(self, dimension_paralela, dimension_normal,
                                       numero_de_zonas):
        """Calcula los coeficientes de presion cuando el viento actua normal a
        la cumbrera o cuando el viento actua normal a la cumbrera y la cubierta
        tiene un angulo < 10°.

        :param float dimension_paralela: La longitud de la dimension paralela
            a la dirección del viento.
        :param float dimension_normal: La longitud de la dimension normal
            a la dirección del viento.
        :param int numero_de_zonas: El numero de zonas de aplicación del viento.
            Este valor debe estar comprendido entre 1 y 4.

        :returns: array con los coeficientes de presión.
        :rtype: :class:`~numpy:numpy.ndarray`
        """
        area = self._area_cp_cubierta(
            self.altura_media, dimension_paralela, dimension_normal
        )
        reduccion = np.interp(area, (10, 25, 100), (1, 0.9, 0.8))
        relaciones_altura_longitud = (0.5, 1)
        cp = (
            (-0.9, -1.3 * reduccion), (-0.9, -0.7), (-0.5, -0.7), (-0.3, -0.7)
        )
        cp_iter = (
            np.interp(self.altura_media / dimension_paralela,
                      relaciones_altura_longitud, cp_val)
            for cp_val in cp
        )
        valores_cp = np.fromiter(cp_iter, float)
        nombre_zonas = ('0 a h/2', 'h/2 a h', 'h a 2h', '> 2h')
        return {nombre: valor for valor, nombre in
                zip(valores_cp[:numero_de_zonas], nombre_zonas)}

    def _cp_cubierta_barlovento(self):
        """Calcula por interpolación los coeficientes de presión para la cubierta
        a barlovento.

        :returns: ``dict`` con los coeficientes de presión para los casos A y B
            (succión, presión).
        :rtype: dict
        :raises ValueError: Cuando el ángulo de cubierta es < 10°.

        .. note:: Debe ser usado cuando el ángulo de cubierta es ≥ 10°.
        """
        if self.angulo >= 10:
            area = self._area_cp_cubierta(
                self.altura_media, self.longitud, self.ancho
            )
            # Interpolate the reduction for apply on the cp value based on the area
            reduccion = np.interp(area, (10, 25, 100), (1, 0.9, 0.8))
            relaciones_altura_longitud = (0.25, 0.5, 1)
            angulos = (10, 15, 20, 25, 30, 35, 45, 60, 80)
            valores_cp_caso_a = (
                (-0.7, -0.9, -1.3 * reduccion), (-0.5, -0.7, -1),
                (-0.3, -0.4, -0.7), (-0.2, -0.3, -0.5),
                (-0.2, -0.2, -0.3), (0, -0.2, -0.2),
                (0, 0, 0), (0, 0, 0), (0, 0, 0)
            )
            valores_cp_caso_b = (
                (0, 0, 0), (0, 0, 0), (0.2, 0, 0),
                (0.3, 0.2, 0), (0.3, 0.2, 0.2), (0.4, 0.3, 0.2),
                (0.4, 0.4, 0.3), (0.6, 0.6, 0.6), (0.8, 0.8, 0.8)
            )
            iter_interp_relacion_caso_a = (np.interp(
                self.altura_media / self.ancho,
                relaciones_altura_longitud, cp_tuple)
                for cp_tuple in valores_cp_caso_a
            )
            iter_interp_relacion_caso_b = (np.interp(
                self.altura_media / self.ancho,
                relaciones_altura_longitud, cp_tuple)
                for cp_tuple in valores_cp_caso_b
            )
            interp_relacion_caso_a = np.fromiter(
                iter_interp_relacion_caso_a, float
            )
            interp_relacion_caso_b = np.fromiter(
                iter_interp_relacion_caso_b, float
            )
            cp_caso_a = np.interp(
                self.angulo, angulos, interp_relacion_caso_a
            )
            cp_caso_b = np.interp(
                self.angulo, angulos, interp_relacion_caso_b
            )
            return {'caso a': cp_caso_a, 'caso b': cp_caso_b}
        raise ValueError('No se pueden calcular los valores, el ángulo de '
                         'cubierta debe ser ≥ 10° para usar este método.')

    def _cp_cubierta_sotavento(self):
        """Calcula por interpolación el coeficiente de presión para la cubierta
        a sotavento.

        :rtype: float
        :raises ValueError: Cuando el ángulo de cubierta es < 10°.

        .. note:: Debe ser usado cuando el ángulo de cubierta es ≥ 10°.
        """
        if self.angulo >= 10:
            relaciones_altura_longitud = (0.25, 0.5, 1)
            angulos = (10, 15, 20)
            valores_cp = (
                (-0.3, -0.5, -0.7), (-0.5, -0.5, -0.6), (-0.6, -0.6, -0.6)
            )
            iter_interp_relacion = (np.interp(
                self.altura_media / self.ancho,
                relaciones_altura_longitud, cp_tuple) for cp_tuple in valores_cp
            )
            relation_interp_cp = np.fromiter(iter_interp_relacion, float)
            cp = np.interp(self.angulo, angulos, relation_interp_cp)
            return cp
        raise ValueError('No se pueden calcular los valores, el ángulo de '
                         'cubierta debe ser ≥ 10° para usar este método.')

    @staticmethod
    def _area_cp_cubierta(altura_media_cubierta, dimension_paralela,
                          dimension_normal):
        """Calcula el area correspondiente al producto entre el menor valor
        entre la mitad de la altura media de cubierta y la dimensión paralela,
        y la dimensión normal.

        :param float altura_media_cubierta: La altura media de cubierta.
        :param float dimension_paralela: La longitud de la dimension paralela
            a la dirección del viento.
        :param float dimension_normal: La longitud de la dimension normal
            a la dirección del viento.

        :rtype: float
        """
        min_dimension = min(altura_media_cubierta / 2, dimension_paralela)
        return min_dimension * dimension_normal

    @staticmethod
    def _zonas_cubierta(altura_media_cubierta, dimension_paralela):
        """Calcula las zonas de aplicación del viento sobre la cubierta.

        :param float altura_media_cubierta: La altura media de cubierta.
        :param float dimension_paralela: La longitud de la dimension paralela
            a la dirección del viento.

        :returns: ``tuple`` que contiene ``tuple`` indicando el inicio y final
            para cada zona.
        :rtype: tuple
        """
        distancia_codigo = (
            0, altura_media_cubierta / 2, altura_media_cubierta,
            2 * altura_media_cubierta, dimension_paralela
        )
        distancias_unicas = dedupe(distancia_codigo)
        distancias_filtradas = tuple(
            dist for dist in distancias_unicas if dist <= dimension_paralela
        )
        zonas = tuple(
            zona for zona in zip(distancias_filtradas, distancias_filtradas[1:])
        )
        return zonas

    def __call__(self):
        return self.valores


class CubiertaMetodoEnvolvente:
    pass


class AleroMetodoDireccional(CubiertaMetodoDireccional):
    """Esta clase utiliza para determinar los coeficientes de presión de alero de
    cubierta de edificio para SPRFV usando el método direccional.
    """

    @cached_property
    def valores(self):
        valores = super().valores
        if self.normal_como_paralelo():
            cps = tuple(cp for cp in valores['normal'].values())
            cp_barlovento = cps[0] - 0.8
            cp_sotavento = cps[-1]
        else:
            cp_barlovento = {
                key: valor - 0.8 for key, valor in valores['normal']['barlovento'].items()
            }
            cp_sotavento = valores['normal']['sotavento']
        valores['normal'] = {'barlovento': cp_barlovento, 'sotavento': cp_sotavento}
        return valores


class AleroMetodoEnvolvente:
    pass


class CubiertaDosAguasPlanaComponentes:
    """Esta clase utiliza para determinar los coeficientes de presión de cubierta
    a dos aguas y plana de edificio para Componentes y Revestimientos.

    :param float ancho: El ancho de la cubierta.
    :param float longitud: La longitud de la cubierta.
    :param float altura_media: La altura media de la cubierta.
    :param float angulo: El ángulo de la cubierta.
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param dict componentes: ``dict`` donde la "key" es el nombre del componente
        y el "value" es el area del mismo. Requerido para calcular las presiones
        sobre los componentes y revestimientos.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud, altura_media, angulo, parapeto=0, alero=0,
                 componentes=None):
        self.ancho = ancho
        self.longitud = longitud
        self.altura_media = altura_media
        self.angulo = angulo
        self.parapeto = parapeto
        self.alero = alero
        self.componentes = componentes

    @cached_property
    def distancia_a(self):
        return distancia_a(self.ancho, self.longitud, self.altura_media)

    @cached_property
    def valores(self):
        """Calcula los valores de coeficiente de presión para componentes y
        revestimientos de cubierta a dos aguas.

        :returns: Los valores de coeficiente de presión para cada componente y zona.
        :rtype: dict
        """
        if self.componentes is None:
            raise ValueError(
                'No hay componentes para determinar los coeficientes de presión'
            )
        caso = self._caso()
        casos = {
            'A': {'1': {'cp': (-1, -0.9)}, '2': {'cp': (-1.8, -1.1)},
                  '3': {'cp': (-2.8, -1.1)}, 'Todas': {'cp': (0.3, 0.2)}},
            'B': {'1': {'cp': (-0.9, -0.8)}, '2': {'cp': (-2.1, -1.4)},
                  '3': {'cp': (-2.1, -1.4)}, 'Todas': {'cp': (0.5, 0.3)}},
            'C': {'1': {'cp': (-1, -0.8)}, '2': {'cp': (-1.2, -1)},
                  '3': {'cp': (-1.2, -1)}, 'Todas': {'cp': (0.9, 0.8)}},
            'D': {'1': {'cp': (-1.1, -1.1)}, '2': {'cp': (-1.3, -1.2)},
                  '3': {'cp': (-1.8, -1.2)}, "2'": {'cp': (-1.6, -1.5)},
                  "3'": {'cp': (-2.6, -1.6)}, 'Todas': {'cp': (0.3, 0.2)}},
            'E': {'1': {'cp': (-1.3, -1.1)}, '2': {'cp': (-1.6, -1.2)},
                  '3': {'cp': (-2.9, -2)}, 'Todas': {'cp': (0.4, 0.3)}},
            'F': {'1': {'cp': (-1.4, -0.9)}, '2': {'cp': (-2.3, -1.6)},
                  '3': {'cp': (-3.2, -2.3)}}
        }
        if self.alero:
            casos_alero = {
                'A': {
                    '1': {'cp': ((-1.7, -1.6), (-1.6, -1.1)),
                          'area': ((1, 10), (10, 50))},
                    '2': {'cp': ((-1.7, -1.6), (-1.6, -1.1)),
                          'area': ((1, 10), (10, 50))},
                    '3': {'cp': (-2.8, -0.8)}
                },
                'B': {
                    '2': {'cp': (-2.2, -2.2)},
                    '3': {'cp': (-3.7, -2.5)}
                },
                'C': {
                    '2': {'cp': (-2.0, -1.8)},
                    '3': {'cp': (-2.0, -1.8)}
                }
            }
            for caso_alero, diccionario in casos_alero.items():
                casos[caso_alero].update(diccionario)
        caso_cp = casos[caso]
        if caso in ('A', 'F') and self.parapeto > 1:
            # CIRSOC 102 - 2005 (Fig. 5B -Nota de pie 5 y Fig. 8 Nota de pie 7)
            caso_cp['3'] = caso_cp['2']
        if caso == 'F':
            # Areas techo grandes alturas -CIRSOC 102 (2005) Fig. 8
            area = (1, 50)
        else:
            # Areas techo pequeñas alturas -CIRSOC 102 (2005) Fig. 5B)
            area = (1, 10)
        valor_cp = defaultdict(dict)
        for nombre, area_componente in self.componentes.items():
            for zona, cps in caso_cp.items():
                cp = cps['cp']
                areas = cps.get('area', area)
                cp_filtrado, area_filtrada = filtrar_cp_areas(cp, areas, area_componente)
                valor_cp[nombre][zona] = calcular_cp_cr(
                    cp_filtrado, area_filtrada, area_componente
                )
        return valor_cp

    @cached_property
    def referencia(self):
        ref = {
            'A': 'Figura 5B', 'B': 'Figura 5B (cont.) 1',
            'C': 'Figura 5B (cont.) 2', 'F': 'Figura 8'
        }
        return ref[self._caso()]

    def _caso(self):
        """Determina el caso según el reglamento a usar para calcular los
        coeficientes de presión para componentes y revestimientos de cubierta.

        :returns: Una letra representando el caso según en reglamento.
        :rtype: string
        """
        if self.angulo <= 10 and self.altura_media > 20:
            caso = 'F'
        elif self.angulo <= 10:
            caso = 'A'
        elif 10 < self.angulo <= 30:
            caso = 'B'
        elif 30 < self.angulo <= 45:
            caso = 'C'
        else:
            raise excepciones.ErrorLineamientos(
                'El Reglamento CIRSOC 102-2005 no provee lineamientos para'
                ' calcular los coeficientes de presión para componentes y'
                ' revestimientos para cubiertas a dos aguas con ángulo > 45°.'
            )
        return caso

    def __call__(self):
        return self.valores


class CubiertaUnAguaComponentes(CubiertaDosAguasPlanaComponentes):
    """Esta clase utiliza para determinar los coeficientes de presión de cubierta
    a un agua de edificio para Componentes y Revestimientos.
    """
    def _caso(self):
        """Determina el caso según el reglamento a usar para calcular los
        coeficientes de presión para componentes y revestimientos de cubierta.

        :returns: Una letra representando el caso según en reglamento.
        :rtype: string
        """
        if self.altura_media > 20:
            if self.angulo <= 10:
                caso = 'F'
            else:
                raise excepciones.ErrorLineamientos(
                    'El Reglamento CIRSOC 102-2005 no provee lineamientos para'
                    ' calcular los coeficientes de presión para componentes y'
                    ' revestimientos para cubiertas a un agua con angulo > 10° y'
                    ' edificio de grandes alturas.'
                )
        elif self.angulo <= 3:
            caso = 'A'
        elif 3 < self.angulo <= 10:
            caso = 'D'
        elif 10 < self.angulo <= 30:
            caso = 'E'
        else:
            raise excepciones.ErrorLineamientos(
                'El Reglamento CIRSOC 102-2005 no provee lineamientos para'
                ' calcular los coeficientes de presión para componentes y'
                ' revestimientos para cubiertas a un agua con ángulo > 30°.'
            )
        return caso

    @cached_property
    def referencia(self):
        ref = {
            'A': 'Figura 5B', 'D': 'Figura 7A',
            'E': 'Figura 7A (cont.)', 'F': 'Figura 8'
        }
        return ref[self._caso()]


class Paredes:
    """Calcula los coeficientes de presión de paredes de edificio para SPRFV y
    Componentes y Revestimientos.

    :param float ancho: El ancho del edificio.
    :param float longitud: El longitud del edificio.
    :param float altura_media: La altura media de cubierta del edificio.
    :param float angulo_cubierta: El ángulo de cubierta del edificio.
    :param dict componentes: ``dict`` donde la "key" es el nombre del componente
        y el "value" es el area del mismo. Requerido para calcular las presiones
        sobre los componentes y revestimientos.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud, altura_media, angulo_cubierta,
                 componentes=None, metodo_sprfv='direccional'):
        self.sprfv = self.selector_sprfv(ancho, longitud, metodo_sprfv)
        self.componentes = ParedesComponentes(
            ancho, longitud, altura_media, angulo_cubierta, componentes
        )

    @staticmethod
    def selector_sprfv(ancho, longitud, metodo):
        if metodo == 'direccional':
            return ParedesSprfvMetodoDireccional(ancho, longitud)
        else:
            return ParedesMetodoEnvolvente()

    def __call__(self):
        return {
            'sprfv': self.sprfv(), 'componentes': self.componentes()
        }


class Cubierta:
    """Calcula los coeficientes de presión de cubierta de edificio para SPRFV y
    Componentes y Revestimientos.

    :param float ancho: El ancho de la cubierta.
    :param float longitud: La longitud de la cubierta.
    :param float altura_media: La altura media de la cubierta.
    :param float angulo: El ángulo de la cubierta.
    :param str tipo_cubierta: El tipo de cubierta.
        Valores aceptados = (plana, dos aguas, un agua)
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param dict componentes: ``dict`` donde la "key" es el nombre del componente
        y el "value" es el area del mismo. Requerido para calcular las presiones
        sobre los componentes y revestimientos.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud, altura_media, angulo, tipo_cubierta,
                 parapeto=0, alero=0, componentes=None,
                 metodo_sprfv='direccional'):
        self.sprfv = self.selector_sprfv(
            metodo_sprfv, ancho, longitud, altura_media, angulo
        )
        self.componentes = self.selector_componentes(
            tipo_cubierta, ancho, longitud, altura_media, angulo, parapeto,
            alero, componentes
        )

    @staticmethod
    def selector_sprfv(metodo, *args):
        if metodo == 'direccional':
            return CubiertaMetodoDireccional(*args)
        else:
            return CubiertaMetodoEnvolvente()

    @staticmethod
    def selector_componentes(tipo_cubierta, *args):
        if tipo_cubierta in ('plana', 'dos aguas'):
            return CubiertaDosAguasPlanaComponentes(*args)
        elif tipo_cubierta == 'un agua':
            return CubiertaUnAguaComponentes(*args)
        else:
            raise ValueError(
                'El código no provee lineamientos para calcular los coeficientes'
                ' de presión para componentes y revestimientos para tipo de'
                f' cubierta: "{tipo_cubierta}".'
            )

    def __call__(self):
        return {
            'sprfv': self.sprfv(), 'componentes': self.componentes()
        }


class Alero:
    """Calcula los coeficientes de presión de alero de cubierta de edificio para
    SPRFV y Componentes y Revestimientos.

    :param float ancho: El ancho de la cubierta.
    :param float longitud: La longitud de la cubierta.
    :param float altura_media: La altura media de la cubierta.
    :param float angulo: El ángulo de la cubierta.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud, altura_media, angulo,
                 metodo_sprfv='direccional'):
        self.sprfv = self.selector_sprfv(
            metodo_sprfv, ancho, longitud, altura_media, angulo
        )

    @staticmethod
    def selector_sprfv(metodo, *args):
        if metodo == 'direccional':
            return AleroMetodoDireccional(*args)
        else:
            return AleroMetodoEnvolvente()

    def __call__(self):
        return self.sprfv()


class Edificio:
    """Calcula los coeficientes de presión de edificio para SPRFV y
    Componentes y Revestimientos.

    :param float ancho: El ancho del edificio.
    :param float longitud: La longitud del edificio.
    :param float altura_media: La altura media de cubierta del edificio.
    :param float angulo_cubierta: El ángulo de cubierta del edificio.
    :param str tipo_cubierta: El tipo de cubierta del edificio.
    :param float parapeto: (opcional) La altura del parapeto de cubierta. Default=0.
    :param float alero: (opcional) La longitud del alero de cubierta. Default=0.
    :param dict componentes_paredes: Los componentes de paredes. Deben ser
        un ``dict`` donde la "key" es el nombre del componente y el "value" es
        el area del mismo. Requerido para calcular las presiones sobre los
        componentes y revestimientos.
    :param dict componentes_cubierta: Los componentes de cubierta. Deben ser
        un ``dict`` donde la "key" es el nombre del componente y el "value" es
        el area del mismo. Requerido para calcular las presiones sobre los
        componentes y revestimientos.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).
    """
    def __init__(self, ancho, longitud, altura_media, angulo_cubierta,
                 tipo_cubierta, alero=0, parapeto=0, componentes_paredes=None,
                 componentes_cubierta=None, metodo_sprfv='direccional'):
        self.paredes = Paredes(
            ancho, longitud, altura_media, angulo_cubierta, componentes_paredes,
            metodo_sprfv
        )
        self.cubierta = Cubierta(
            ancho, longitud, altura_media, angulo_cubierta, tipo_cubierta,
            parapeto, alero, componentes_cubierta, metodo_sprfv
        )
        if alero:
            self.alero = Alero(
                ancho, longitud, altura_media, angulo_cubierta, metodo_sprfv
            )

    @classmethod
    def desde_edifico(cls, edificio, metodo_sprfv):
        """Crea una instancia a partir de un edificio.

        :param edificio: Una instancia de :class:`geometria.Edificio`
        :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
            de presión para el SPRFV. Default=direccional.
            Valores aceptados = (direccional, envolvente).
        """
        # no me gusta poner cubierta.tipo, mejorarlo!!!
        args = (
            edificio.ancho, edificio.longitud, edificio.cubierta.altura_media,
            edificio.cubierta.angulo, edificio.cubierta.tipo,
            edificio.cubierta.alero, edificio.cubierta.parapeto,
            edificio.componentes_paredes, edificio.cubierta.componentes_cubierta
        )
        return cls(*args, metodo_sprfv)

    def __call__(self):
        valores = {'paredes': self.paredes(), 'cubierta': self.cubierta()}
        if hasattr(self, 'alero'):
            valores['alero'] = self.alero()
        return valores
