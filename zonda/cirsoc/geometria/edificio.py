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

from collections import namedtuple
from cached_property import cached_property
from .utilidades import array_alturas
from .cubiertas import cubierta


AreasEdificio = namedtuple(
    'AreasEdificio', 'frente izquierda trasera derecha cubierta'
)


class Edificio:
    """Crea un edificio.

    :param float longitud: La longitud del edificio.
    :param float ancho: El ancho del edificio.
    :param float elevacion: La altura desde el suelo desde donde se consideran
        las presiones del viento sobre el edificio.
    :param cubierta: La cubierta del edificio. Debe ser una instancia de las
        siguientes clases: (:class:`CubiertaPlana`, :class:`CubiertaDosAguas`,
        :class:`CubiertaUnAgua`, :class:`CubiertaMansarda`)
    :param list alturas_personalizadas: (opcional) Las alturas sobre las que se
        calcularán las presiones de viento sobre paredes a barlovento. Puede ser
        ``list`` o ``tuple``.
    :param dict componentes_paredes: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.
    :param float volumen_interno: El volumen interno no dividido del edificio.
    :param tuple aberturas: Las aberturas del edificio para cada pared y cubierta.
        Debe tener 5 valores para las paredes frontal, izquierda, trasera,
        derecha y cubierta. En ese orden.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, ancho, longitud, elevacion, cubierta,
                 alturas_personalizadas=None, componentes_paredes=None,
                 volumen_interno=None, aberturas=None, **kwargs):
        self.ancho = ancho
        self.longitud = longitud
        self.elevacion = elevacion
        self.cubierta = cubierta
        self.alturas_personalizadas = alturas_personalizadas
        self.componentes_paredes = componentes_paredes
        self.volumen_interno = volumen_interno or self.volumen
        self._aberturas = aberturas or [0] * 5

    def _area_frontal(self):
        """Calcula el area de la pared frontal.

        :rtype: float
        """
        return self.ancho * self.cubierta.altura_alero + self.cubierta.area_mojinete

    def _area_trasera(self):
        """Calcula el area de la pared trasera.

        :rtype: float
        """
        return self._area_frontal()

    def _area_derecha(self):
        """Calcula el area de la pared derecha.

        :rtype: float
        """
        return self.longitud * self.cubierta.altura_alero

    def _area_izquierda(self):
        """Calcula el area de la pared izquierda.

        Se considera que para cubiertas a un agua la cumbrera esta del lado de
        la pared izquierda.

        :rtype: float or int
        """
        if type(self.cubierta).__name__ == 'CubiertaUnAgua':
            return self.longitud * self.cubierta.altura_cumbrera
        return self._area_derecha()

    @cached_property
    def areas(self):
        """Retorna las areas de las paredes y el techo.

        :returns: ``namedtuple`` con las areas de las paredes y el techo.
        :rtype: tuple
        """
        areas = AreasEdificio(
            self._area_frontal(),
            self._area_izquierda(),
            self._area_trasera(),
            self._area_derecha(),
            self.cubierta.area
        )
        return areas

    @cached_property
    def aberturas(self):
        """Retorna las aberturas del edificio. Se filtran para que no sean
        menores que cero y que no sean mayores que las paredes o cubierta que las
        contienen.

        :returns: ``namedtuple`` con las areas de las aberturas de paredes y techo.
        :rtype: tuple
        """
        aberturas = tuple(
            min(abertura, area) if abertura >= 0 else 0 for abertura,
            area in zip(self._aberturas, self.areas)
        )
        return AreasEdificio(*aberturas)

    @cached_property
    def areas_totales(self):
        return sum(self.areas)

    @cached_property
    def aberturas_totales(self):
        return sum(self.aberturas)

    @cached_property
    def volumen(self):
        """Calcula el volumen interno del edificio.

        :rtype: float
        """
        return self._area_frontal() * self.longitud

    @cached_property
    def alturas(self):
        """Crea un array de alturas desde :attr:`elevacion` a
        :attr:`altura_cumbrera`.

        :returns: Un array de alturas ordenada.
        :rtype: :class:`~numpy:numpy.ndarray`
        """
        try:
            altura_superior = self.cubierta.altura_cumbrera
        except AttributeError:
            altura_superior = self.cubierta.altura_alero
        alturas = array_alturas(
            self.elevacion, altura_superior, self.alturas_personalizadas,
            self.cubierta.altura_alero, self.cubierta.altura_media
        )
        return alturas

    @cached_property
    def a0i(self):
        return tuple(
            self.aberturas_totales - abertura for abertura in self.aberturas[:-1]
        )

    @cached_property
    def agi(self):
        return tuple(
            self.areas_totales - area for area in self.areas[:-1]
        )

    @cached_property
    def min_areas(self):
        return tuple(min(0.4, 0.01 * area) for area in self.areas[:-1])

    @cached_property
    def cerramiento_condicion_1(self):
        """Chequea para cada pared si su abertura supera el 80% del area.

        :returns: Tuple con booleanos para cada pared.
        """
        return tuple(
            abertura >= 0.8 * area for abertura, area in
            zip(self.aberturas[:-1], self.areas[:-1])
        )

    @cached_property
    def cerramiento_condicion_2(self):
        """Chequea si el área total de aberturas en una pared que recibe
        presión externa positiva excede la  suma  de  las  áreas  de  aberturas
        en  el  resto  de  la  envolvente  del  edificio  (paredes y cubierta)
        en más del 10%.

        :returns: Tuple con booleanos para cada pared.
        """
        return tuple(
            abertura > 1.1 * area for abertura, area in
            zip(self.aberturas[:-1], self.a0i)
        )

    @cached_property
    def cerramiento_condicion_3(self):
        """Chequea si el área total de aberturas en una pared que recibe presión
        externa positiva excede el  valor  menor  entre  0,4  m2  ó  el  1%  del
        área  de  dicha  pared.

        :returns: Tuple con booleanos para cada pared.
        """
        return tuple(
            abertura > area for abertura, area in
            zip(self.aberturas[:-1], self.min_areas[:-1])
        )

    @cached_property
    def cerramiento_condicion_4(self):
        """Chequea si el  porcentaje  de  aberturas en el resto de
        la envolvente del edificio no excede el 20%.

        :returns: Tuple con booleanos para cada pared.
        """
        return tuple(
            abertura / area <= 0.2 for abertura, area in zip(self.a0i, self.agi)
        )

    def __repr__(self):
        return f'<{self.__name__}(longitud={self.longitud}, ancho={self.ancho},' \
            f' elevacion={self.elevacion},' \
            f' cubierta={self.cubierta.__repr__().lower()})>'

    def __str__(self):
        return 'Edificio'


def edificio(ancho, longitud, elevacion, altura_alero, tipo_cubierta, **kwargs):
    """Construye un edificio.

    :param float longitud: La longitud del edificio.
    :param float ancho: El ancho del edificio.
    :param float elevacion: La altura desde el suelo desde donde se consideran
        las presiones del viento sobre el edificio.
    :param float altura_alero: La altura del alero medida desde el piso.
    :param str tipo_cubierta: El tipo de cubierta.
        Valores aceptados = ('plana', 'dos aguas', 'un agua', 'mansarda')
    :param float altura_cumbrera: La altura de cumbrera medida desde el piso.
        Solo necesario cuando la cubierta no es plana.
    :param float ancho_central: El ancho central de la cubierta. Solo necesario
        cuando es cubierta a la mansarda.
    :param list alturas_personalizadas: (opcional) Las alturas sobre las que se
        calcularán las presiones de viento sobre paredes a barlovento. Puede ser
        ``list`` o ``tuple``.
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param dict componentes_paredes: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.
    :param dict componentes_cubierta: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.

    :returns: Una instancia de :class:`Edificio`.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    cubierta_edificio = cubierta(
        tipo_cubierta, ancho, longitud, altura_alero, **kwargs
    )
    edificio = Edificio(
        ancho, longitud, elevacion, cubierta_edificio, **kwargs
    )
    return edificio
