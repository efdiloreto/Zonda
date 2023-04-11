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
from cached_property import cached_property


class CubiertaPlana:
    """Crea una cubierta plana.

    :param float longitud: La longitud de la cubierta.
    :param float ancho: El ancho de la cubierta.
    :param float altura_alero: La altura del alero medida desde el piso.
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param float altura_bloqueo: (opcional) La altura de bloqueo bajo la cubierta.
        Default=0.
    :param dict componentes_cubierta: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """

    tipo = 'plana'

    def __init__(self, ancho, longitud, altura_alero, parapeto=0, alero=0,
                 altura_bloqueo=0, componentes_cubierta=None, **kwargs):
        self.ancho = ancho
        self.longitud = longitud
        self.altura_alero = altura_alero
        self.parapeto = parapeto
        self.alero = alero
        self.componentes_cubierta = componentes_cubierta
        self.altura_bloqueo = altura_bloqueo

    @cached_property
    def relacion_bloqueo(self):
        return min(self.altura_bloqueo / self.altura_alero, 1)

    @cached_property
    def angulo(self):
        """Calcula el ángulo de la cubierta.

        :returns: cero grados.
        :rtype: int
        """
        return 0

    @cached_property
    def area(self):
        """Calcula el área de la cubierta.

        :rtype: float
        """
        return self.ancho * self.longitud

    @cached_property
    def altura_media(self):
        """Calcula la altura media de cubierta.

        :returns: La altura del alero, debido a que el ángulo de cubierta es 0°.
        :rtype: float
        """
        return self.altura_alero

    @cached_property
    def area_mojinete(self):
        """Calcula el area de la zona de mojinete de la pared.

        :rtype: int
        """
        return 0

    def __repr__(self):
        return f'<{self.__name__}(longitud={self.longitud}, ancho={self.ancho},' \
            f' altura_alero={self.altura_alero})>'

    def __str__(self):
        return 'Cubierta Plana'


class CubiertaDosAguas(CubiertaPlana):
    """Hereda de :class:`CubiertaPlana` y crea una cubierta a dos aguas.

    :param float longitud: La longitud de la cubierta.
    :param float ancho: El ancho de la cubierta.
    :param float altura_alero: La altura del alero medida desde el piso.
    :param float altura_cumbrera: La altura de cumbrera medida desde el piso.
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param float altura_bloqueo: (opcional) La altura de bloqueo bajo la cubierta.
        Default=0.
    :param dict componentes_cubierta: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """

    tipo = 'dos aguas'

    def __init__(self, ancho, longitud, altura_alero, altura_cumbrera,
                 parapeto=0, alero=0, altura_bloqueo=0,
                 componentes_cubierta=None, **kwargs):
        super().__init__(ancho, longitud, altura_alero, parapeto, alero,
                         altura_bloqueo, componentes_cubierta)
        self.altura_cumbrera = altura_cumbrera

    @cached_property
    def angulo(self):
        """Calcula el ángulo de la cubierta.

        :rtype: float
        """
        pendiente = (self.altura_cumbrera - self.altura_alero) / self.ancho
        angulo = math.atan(2 * pendiente)
        return math.degrees(angulo)

    @cached_property
    def area(self):
        """Calcula el área de la cubierta.

        :rtype: float
        """
        altura = self.altura_cumbrera - self.altura_alero
        perimetro_frontal = 2 * math.hypot(altura, self.ancho / 2)
        return perimetro_frontal * self.longitud

    @cached_property
    def altura_media(self):
        """Calcula la altura media de cubierta.

         :rtype: float
        """
        if self.angulo <= 10:
            return self.altura_alero
        return (self.altura_alero + self.altura_cumbrera) / 2

    @cached_property
    def area_mojinete(self):
        """Calcula el area de la zona de mojinete de la pared.

        :rtype: float
        """
        return self.ancho * self.altura_cumbrera / 2

    def __repr__(self):
        return f'<{self.__name__}(longitud={self.longitud}, ancho={self.ancho},' \
            f' altura_alero={self.altura_alero},' \
            f' altura_cumbrera={self.altura_cumbrera})>'

    def __str__(self):
        return 'Cubierta a Dos Aguas'


class CubiertaUnAgua(CubiertaDosAguas):
    """Hereda de :class:`CubiertaDosAguas` y crea una cubierta a un agua.

    :param float longitud: La longitud de la cubierta.
    :param float ancho: El ancho de la cubierta.
    :param float altura_alero: La altura del alero medida desde el piso.
    :param float altura_cumbrera: La altura de cumbrera medida desde el piso.
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param float altura_bloqueo: (opcional) La altura de bloqueo bajo la cubierta.
        Default=0.
    :param str posicion_bloqueo: (opcional) La posición de bloqueo bajo la cubierta.
        Default='alero mas bajo'.
        Valores aceptados = ('alero mas bajo', 'alero mas alto')
    :param dict componentes_cubierta: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """

    tipo = 'un agua'

    def __init__(self, ancho, longitud, altura_alero, altura_cumbrera,
                 parapeto=0, alero=0, altura_bloqueo=0,
                 posicion_bloqueo='alero mas bajo',
                 componentes_cubierta=None, **kwargs):
        super().__init__(ancho, longitud, altura_alero, altura_cumbrera,
                         parapeto, alero, altura_bloqueo, componentes_cubierta)
        self.altura_cumbrera = altura_cumbrera
        self.posicion_bloqueo = posicion_bloqueo

    @cached_property
    def angulo(self):
        """Calcula el ángulo de la cubierta.

        :returns: El ángulo de la cubierta en grados.
        :rtype: float
        """
        pendiente = (self.altura_cumbrera - self.altura_alero) / self.ancho
        angulo = math.atan(pendiente)
        return math.degrees(angulo)

    @cached_property
    def area(self):
        """Calcula el área de la cubierta.

        :rtype: float
        """
        altura = self.altura_cumbrera - self.altura_alero
        perimetro_frontal = math.hypot(altura, self.ancho)
        return perimetro_frontal * self.longitud

    def __str__(self):
        return 'Cubierta a Un Agua'


class CubiertaMansarda(CubiertaDosAguas):
    """Hereda de :class:`CubiertaDosAguas` y crea una cubierta a la mansarda.

    :param float longitud: La longitud de la cubierta.
    :param float ancho: El ancho de la cubierta.
    :param float altura_alero: La altura del alero medida desde el piso.
    :param float altura_cumbrera: La altura de cumbrera medida desde el piso.
    :param float ancho_central: El ancho central de la cubierta.
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param float altura_bloqueo: (opcional) La altura de bloqueo bajo la cubierta.
        Default=0.
    :param dict componentes_cubierta: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """

    tipo = 'mansarda'

    def __init__(self, ancho, longitud, altura_alero, altura_cumbrera,
                 ancho_central, parapeto=0, alero=0, altura_bloqueo=0,
                 componentes_cubierta=None, **kwargs):
        super().__init__(ancho, longitud, altura_alero, altura_cumbrera, parapeto,
                         alero, altura_bloqueo, componentes_cubierta)
        self.ancho_central = ancho_central

    @cached_property
    def angulo(self):
        """Calcula el ángulo de la cubierta.

        :returns: El ángulo de la cubierta en grados.
        :rtype: float
        """
        pendiente = (self.altura_cumbrera - self.altura_alero) / self._ancho_util
        angulo = math.atan(pendiente)
        return math.degrees(angulo)

    @cached_property
    def area(self):
        """Calcula el área de la cubierta.

        :rtype: float
        """
        altura = self.altura_cumbrera - self.altura_alero
        perimetro_frontal = 2 * math.hypot(altura, self._ancho_util()) + \
            self.ancho_central
        return perimetro_frontal * self.longitud

    @cached_property
    def _ancho_util(self):
        """Calcula el ancho disponible para calcular el angulo de cubierta.

        :rtype: float
        """
        return (self.ancho - self.ancho_central) / 2

    def __repr__(self):
        return f'<{self.__name__}(longitud={self.longitud}, ancho={self.ancho},' \
            f' altura_alero={self.altura_alero},' \
            f' altura_cumbrera={self.altura_cumbrera},' \
            f' ancho_central={self.ancho_central})>'

    def __str__(self):
        return 'Cubierta a la Mansarda'


def cubierta(tipo, ancho, longitud, altura_alero, **kwargs):
    """Construye una cubierta.

    :param str tipo: El tipo de cubierta.
        Valores aceptados = (plana, dos aguas, un agua, mansarda)
    :param float longitud: La longitud de la cubierta.
    :param float ancho: El ancho de la cubierta.
    :param float altura_alero: La altura del alero medida desde el piso.
    :param float altura_cumbrera: La altura de cumbrera medida desde el piso.
    :param float ancho_central: El ancho central de la cubierta. Solo necesario
        cuando es cubierta a la mansarda.
    :param float parapeto: (opcional) La altura del parapeto. Default=0.
    :param float alero: (opcional) La longitud del alero. Default=0.
    :param dict componentes_cubierta: (opcional) ``dict`` donde la "key" es el
        nombre del componente y el "value" es el area del mismo. Requerido para
        calcular las presiones sobre los componentes y revestimientos.

    :returns: una instancia de cubierta.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    cubiertas = {
        'plana': CubiertaPlana, 'dos aguas': CubiertaDosAguas,
        'un agua': CubiertaUnAgua, 'mansarda': CubiertaMansarda
    }
    return cubiertas[tipo](ancho, longitud, altura_alero, **kwargs)
