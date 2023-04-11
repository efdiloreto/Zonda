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
from collections import namedtuple, defaultdict
from cached_property import cached_property
from .base import PresionesBase


_PresionesEdificio = namedtuple('PresionesEdificio', 'pos neg')


class CubiertaSprfvMetodoDireccional(PresionesBase):
    """Hereda de :class:`PresionesBase` y calcula las presiones de cubierta para
    SPRFV usando el método direccional.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param float altura_media: La altura media de la cubierta.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
        son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
        acuerdo a la geometria del edificio cuando la direccion del viento es
        paralelo y normal a la cumbrera.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param str cerramiento: El cerramiento del edificio. Valores aceptados =
        (cerrado, parcialmente cerrado, abierto)
    :param dict cp: Los valores de coeficiente de presion para sprfv.
        Ver :class:`cp.CubiertaMetodoDireccional`.
    :param bool reducir_gcpi: (opcional) Indica si hay que reducir el valor de
        gcpi. Default = None.
    :param float aberturas_totales: (opcional) La suma de todas las aberturas
        del edificio. Default = None.
    :param float volumen_interno: (opcional) El volumen interno no dividido del
        edificio. Default = None.
    """
    def __init__(self, alturas, altura_media, categoria, velocidad, rafaga,
                 factor_topografico, cerramiento, cp, reducir_gcpi=False,
                 aberturas_totales=0, volumen_interno=None):
        super().__init__(alturas, categoria, velocidad, rafaga['paralelo'],
                         factor_topografico, 0.85)
        self.cerramiento = cerramiento
        self.cp = cp
        self.reducir_gcpi = reducir_gcpi
        self.aberturas_totales = aberturas_totales
        self.volumen_interno = volumen_interno
        self.factores_rafaga = {key: value.factor for key, value in rafaga.items()}
        self._bool_altura_media = alturas == altura_media
        self._presion_media_parcial = functools.partial(
            self._presiones, presion_velocidad=self.presion_velocidad_media,
            gcpi=self.gcpi,
            presion_velocidad_media=self.presion_velocidad_media
        )

    @cached_property
    def coeficiente_exposicion_media(self):
        """Coeficiente de exposición correspondiente a la altura media.

        :rtype: float
        """
        return self.coeficientes_exposicion[self._bool_altura_media][0]

    @cached_property
    def factor_topografico_media(self):
        """Factor topográfico correspondiente a la altura media.

        :rtype: float
        """
        return self.factor_topografico[self._bool_altura_media][0]

    @cached_property
    def presion_velocidad_media(self):
        """Presión de velocidad correspondiente a la altura media.

        :rtype: float
        """
        return self.presiones_velocidad[self._bool_altura_media][0]

    @cached_property
    def factor_reduccion_gcpi(self):
        """Calcula el factor de reduccion para el coeficiente de presion interna.

        :returns: El factor de reduccion.
        :rtype: float
        """
        if self.reducir_gcpi:
            if self.cerramiento == 'parcialmente cerrado':
                if self.volumen_interno and self.aberturas_totales:
                    reduccion = 0.5 * (1 + 1 / (1 + self.volumen_interno / 6954 /
                                       self.aberturas_totales) ** 0.5)
                    return min(reduccion, 1)
        return 1

    @cached_property
    def gcpi(self):
        """Calcula el coeficiente de presión interna de acuerdo al cerramiento
        del edificio.

        :returns: El coeficiente de presión interna.
        :rtype: float o int
        """
        cerramiento_gcpi = {
            'cerrado': 0.18, 'parcialmente cerrado': 0.55, 'abierto': 0
        }
        gcpi = cerramiento_gcpi[self.cerramiento] * self.factor_reduccion_gcpi
        return gcpi

    @cached_property
    def valores(self):
        """Calcula los valores de presión para la cubierta.

        :returns: ``dict`` con los valores de presión para viento en dirección
            paralelo y normal a la cumbrera para todas las zonas de cubierta.
        :rtype: dict
        """
        valores_cp = self.cp()
        valores = {}
        # Las keys son "paralelo" y "normal"
        for key, cp in valores_cp.items():
            valores[key] = self._calcular_presiones(
                cp, self.factores_rafaga[key],
                self._presion_media_parcial
            )
        return valores

    def _calcular_presiones(self, cp, factor_rafaga, func):
        """Función recursiva para iterar sobre un diccionario con valores de
        coeficientes de presión y aplicar una función para calcular las presiones
        correspondientes.

        :param dict cp: ``dict`` con los valores de coeficiente de presión.
        :param float factor_rafaga: El factor de ráfaga.
        :param float func: La función que calcula las presiones. En este caso
            se utiliza una función parcial que solo hay que pasarle el valor
            de cp y de rafaga. Ver el método "valores".
        """
        presiones = {}
        if not isinstance(cp, dict):
            return func(cp=cp, factor_rafaga=factor_rafaga)
        for key, valor in cp.items():
            if isinstance(valor, dict):
                presiones[key] = self._calcular_presiones(
                    valor, factor_rafaga, func
                )
            else:
                presiones[key] = func(cp=valor, factor_rafaga=factor_rafaga)
        return presiones

    def __call__(self):
        return self.valores

    @staticmethod
    def _presiones(presion_velocidad, cp, factor_rafaga, presion_velocidad_media,
                   gcpi=0):
        """Calcula la presión sobre una estructura de acuerdo a diferentes
        parámetros.

        :param float presion_velocidad: La presión de velocidad determinada a
            la altura requerida.
        :param float cp: El coeficiente de presión cp.
        :param float factor_rafaga: El factor de ráfaga.
        :param float presion_velocidad: La presión de velocidad determinada a
            la altura media.
        :param float gcpi: Coeficiente de presión interna.

        :returns: ``tuple`` con los valores correspondientes a +-GCpi.
        :rtype: tuple
        """
        q1 = presion_velocidad * factor_rafaga * cp
        q2 = presion_velocidad_media * gcpi
        q_pos = q1 - q2
        q_neg = q1 + q2
        return _PresionesEdificio(q_pos, q_neg)


class CubiertaSprfvMetodoEnvolvente(PresionesBase):
    pass


class AleroSprfvMetodoDireccional(CubiertaSprfvMetodoDireccional):
    """Hereda de :class:`PresionesBase` y calcula las presiones del alero para
    SPRFV usando el método direccional.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param float altura_media: La altura media de la cubierta.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
        son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
        acuerdo a la geometria del edificio cuando la direccion del viento es
        paralelo y normal a la cumbrera.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param cp: Una instancia de :class:`cp.AleroMetodoDireccional`.
    """
    def __init__(self, alturas, altura_media, categoria, velocidad, rafaga,
                 factor_topografico, cp):
        super().__init__(alturas, altura_media, categoria, velocidad, rafaga,
                         factor_topografico, 'abierto', cp)
        self._presion_media_parcial = functools.partial(
            self._presiones, presion_velocidad=self.presion_velocidad_media,
        )

    @cached_property
    def valores(self):
        """Calcula los valores de presión para el alero.

        :returns: ``dict`` con los valores de presión para viento en dirección
            paralelo y normal a la cumbrera para todas las zonas de cubierta.
        :rtype: dict
        """
        valores_cp = self.cp()
        valores = {}
        # Las keys son "paralelo" y "normal"
        for key, cp in valores_cp.items():
            valores[key] = self._calcular_presiones(
                cp, self.factores_rafaga[key],
                self._presion_media_parcial
            )
        return valores

    @staticmethod
    def _presiones(presion_velocidad, cp, factor_rafaga):
        """Calcula la presión sobre una estructura de acuerdo a diferentes
        parámetros.

        :param float presion_velocidad: La presión de velocidad determinada a
            la altura requerida.
        :param float cp: El coeficiente de presión cp.
        :param float factor_rafaga: El factor de ráfaga.

        :rtype: float
        """
        return presion_velocidad * factor_rafaga * cp


class AleroComponentes:
    pass


class AleroSprfvMetodoEnvolvente:
    pass


class ParedesSprfvMetodoDireccional(CubiertaSprfvMetodoDireccional):
    """Hereda de :class:`CubiertaSprfvMetodoDireccional` y calcula las presiones
    de paredes para SPRFV usando el método direccional.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param float altura_media: La altura media de la cubierta.
    :param float altura_alero: La altura de alero del edificio.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
        son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
        acuerdo a la geometria del edificio cuando la direccion del viento es
        paralelo y normal a la cumbrera.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param cp: Una instancia de :class:`cp.Edificio`.
    """
    def __init__(self, alturas, altura_media, altura_alero, categoria, velocidad,
                 rafaga, factor_topografico, cerramiento, cp, reducir_gcpi=False,
                 aberturas_totales=0, volumen_interno=None):
        super().__init__(alturas, altura_media, categoria, velocidad, rafaga,
                         factor_topografico, cerramiento, cp, reducir_gcpi,
                         aberturas_totales, volumen_interno)
        self._bool_alero = alturas <= altura_alero

    @cached_property
    def coeficientes_exposicion_alero(self):
        """Coeficiente de exposición calculado hasta la altura de alero.

        :rtype: `~numpy:numpy.ndarray`
        """
        return self.coeficientes_exposicion[self._bool_alero]

    @cached_property
    def factor_topografico_alero(self):
        """Factor topográfico calculado hasta la altura de alero.

        :rtype: `~numpy:numpy.ndarray`
        """
        return self.factor_topografico[self._bool_alero]

    @cached_property
    def presion_velocidad_alero(self):
        """La presión de velocidad calculada hasta la altura de alero.

        :rtype: `~numpy:numpy.ndarray`
        """
        return self.presiones_velocidad[self._bool_alero]

    @cached_property
    def valores(self):
        """Calcula los valores de presión para las paredes.

        :returns: ``dict`` con los valores de presión para viento en dirección
            paralelo y normal a la cumbrera para todas las paredes.
        :rtype: dict
        """
        valores_cp = self.cp()
        presiones_paredes = defaultdict(dict)
        for direccion, diccionario in valores_cp.items():
            for pared, cp in diccionario.items():
                if pared == 'barlovento':
                    if direccion == 'normal':
                        qi = self.presion_velocidad_alero
                    else:
                        qi = self.presiones_velocidad
                else:
                    qi = self.presion_velocidad_media
                presiones_paredes[direccion][pared] = self._presiones(
                    qi, cp, self.factores_rafaga[direccion], self.gcpi,
                    self.presion_velocidad_media
                )
        return presiones_paredes


class ParedesSprfvMetodoEnvolvente:
    pass


class MixinCr:
    """Clase "Mixin" para extender la funcionalidad de otras clases. No debe ser
    usada por si sola.
    """
    def _presiones_componentes(self):
        """Calcula las presiones para componentes y revestimientos.

        :returns: ``dict`` con las presiones para cada componente.
        :rtype: dict
        """
        valores_cp = self.cp()
        pressures = defaultdict(dict)
        for name, zones in valores_cp.items():
            for zone, valor_cp in zones.items():
                pressures[name][zone] = self._presion_media_parcial(
                    cp=valor_cp, factor_rafaga=1
                )
        return pressures


class CubiertaComponentes(CubiertaSprfvMetodoDireccional, MixinCr):
    """Calcula las presiones para componentes y revestimiento para cubierta.
    """

    @cached_property
    def valores(self):
        """Retorna los valores de presión.

        :returns: ``dict`` con las presiones para cada componente.
        :rtype: dict
        """
        return self._presiones_componentes()


class ParedesComponentes(ParedesSprfvMetodoDireccional, MixinCr):
    """Calcula las presiones para componentes y revestimiento para paredes.
    """
    def _presiones_cr_caso_b(self):
        """Calcula las presiones sobre los componentes de pared cuando hay que
        utilizar la Figura 8 del Reglamento CIRSOC 102-05.

        :returns: ``dict`` con las presiones para cada componente.
        :rtype: dict
        """
        valores_cp = self.cp()
        presiones = defaultdict(lambda: defaultdict(dict))
        for pared in ('barlovento', 'lateral', 'sotavento'):
            if pared == 'barlovento':
                qi = self.presiones_velocidad
            else:
                qi = self.presion_velocidad_media
            for nombre, zona in valores_cp.items():
                for zona, valor_gcp in zona.items():
                    presiones[pared][nombre][zona] = \
                        self._presiones(qi, valor_gcp, 1, self.gcpi,
                                        self.presion_velocidad_media)
        return presiones

    @cached_property
    def valores(self):
        """Retorna los valores de presión.

        :returns: ``dict`` con las presiones para cada componente.
        :rtype: dict
        """
        if self.cp._caso() == 'B':
            return self._presiones_cr_caso_b()
        return self._presiones_componentes()


class Cubierta:
    """Calcula las presiones de viento sobre una cubierta de edificio para SPRFV
    y Componentes y Revestimientos.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param float altura_media: La altura media de cubierta del edificio.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
        son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
        acuerdo a la geometria del edificio cuando la direccion del viento es
        paralelo y normal a la cumbrera.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param str cerramiento: El cerramiento del edificio. Valores aceptados =
        (cerrado, parcialmente cerrado, abierto).
    :param cp: Una instancia de :class:`cp.Cubierta`.
    :param bool reducir_gcpi: (opcional) Indica si hay que reducir el valor de
        gcpi. Default = None.
    :param float aberturas_totales: (opcional) La suma de todas las aberturas
        del edificio. Default = None.
    :param float volumen_interno: (opcional) El volumen interno no dividido del
        edificio. Default = None.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).
    """
    def __init__(self, alturas, altura_media, categoria, velocidad, rafaga,
                 factor_topografico, cerramiento, cp, reducir_gcpi=False,
                 aberturas_totales=None, volumen_interno=None,
                 metodo_sprfv='direccional'):
        self.sprfv = self.selector_sprfv(
            metodo_sprfv, alturas, altura_media, categoria, velocidad, rafaga,
            factor_topografico, cerramiento, cp.sprfv, reducir_gcpi,
            aberturas_totales, volumen_interno
        )
        self.componentes = CubiertaComponentes(
            alturas, altura_media, categoria, velocidad, rafaga,
            factor_topografico, cerramiento, cp.componentes, reducir_gcpi,
            aberturas_totales, volumen_interno
        )

    @staticmethod
    def selector_sprfv(metodo, *args):
        """Selecciona que clase utilizar para calcular las presiones sobre el
        SPRFV de acuerdo al método elegido.
        """
        if metodo == 'direccional':
            return CubiertaSprfvMetodoDireccional(*args)
        else:
            return CubiertaSprfvMetodoEnvolvente(*args)

    def __call__(self):
        return {'sprfv': self.sprfv(), 'componentes': self.componentes()}


class Alero:
    """Calcula las presiones de viento sobre un alero de edificio para SPRFV
    y Componentes y Revestimientos.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param float altura_media: La altura media de cubierta del edificio.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
        son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
        acuerdo a la geometria del edificio cuando la direccion del viento es
        paralelo y normal a la cumbrera.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param cp: Una instancia de :class:`cp.Alero`.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).
    """
    def __init__(self, alturas, altura_media, categoria, velocidad, rafaga,
                 factor_topografico, cerramiento, cp, metodo_sprfv='direccional'):
        self.sprfv = self.selector_sprfv(
            metodo_sprfv, alturas, altura_media, categoria, velocidad, rafaga,
            factor_topografico, cp
        )
        self.componentes = AleroComponentes()

    @staticmethod
    def selector_sprfv(metodo, *args):
        """Selecciona que clase utilizar para calcular las presiones sobre el
        SPRFV de acuerdo al método elegido.
        """
        if metodo == 'direccional':
            return AleroSprfvMetodoDireccional(*args)
        else:
            return AleroSprfvMetodoEnvolvente(*args)

    def __call__(self):
        return self.sprfv()


class Paredes:
    """Calcula las presiones de viento sobre las paredes de edificio para SPRFV
    y Componentes y Revestimientos.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param float altura_media: La altura media de cubierta del edificio.
    :param float altura_media: La altura de alero de cubierta del edificio.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
        son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
        acuerdo a la geometria del edificio cuando la direccion del viento es
        paralelo y normal a la cumbrera.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param str cerramiento: El cerramiento del edificio. Valores aceptados =
        (cerrado, parcialmente cerrado, abierto).
    :param cp: Una instancia de :class:`cp.Paredes`.
    :param float aberturas_totales: (opcional) La suma de todas las aberturas
        del edificio. Default = None.
    :param float volumen_interno: (opcional) El volumen interno no dividido del
        edificio. Default = None.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).
    """
    def __init__(self, alturas, altura_media, altura_alero, categoria,
                 velocidad, rafaga, factor_topografico, cerramiento, cp,
                 reducir_gcpi=False, aberturas_totales=None, volumen_interno=None,
                 metodo_sprfv='direccional'):
        self.sprfv = self.selector_sprfv(
            metodo_sprfv, alturas, altura_media, altura_alero, categoria,
            velocidad, rafaga, factor_topografico, cerramiento, cp.sprfv,
            reducir_gcpi, aberturas_totales, volumen_interno
        )
        self.componentes = ParedesComponentes(
            alturas, altura_media, altura_alero, categoria, velocidad, rafaga,
            factor_topografico, cerramiento, cp.componentes, reducir_gcpi,
            aberturas_totales, volumen_interno
        )

    @staticmethod
    def selector_sprfv(metodo, *args):
        """Selecciona que clase utilizar para calcular las presiones sobre el
        SPRFV de acuerdo al método elegido.
        """
        if metodo == 'direccional':
            return ParedesSprfvMetodoDireccional(*args)
        else:
            return ParedesSprfvMetodoEnvolvente()

    def __call__(self):
        return {'sprfv': self.sprfv(), 'componentes': self.componentes()}


class Edificio:
    """Calcula las presiones de viento sobre un edificio para SPRFV
    y Componentes y Revestimientos.

    :param alturas: Las alturas de la estructura donde calcular las
        presiones. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param float altura_media_cubierta: La altura media de cubierta del edificio.
    :param str categoria: La categoría de la estructura. Valores aceptados =
        (I, II, III, IV)
    :param float velocidad: La velocidad del viento en m/s.
    :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
        son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
        acuerdo a la geometria del edificio cuando la direccion del viento es
        paralelo y normal a la cumbrera.
    :param factor_topografico: Los factores topográficos correspondientes a cada
        altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
    :param str cerramiento: El cerramiento del edificio. Valores aceptados =
        (cerrado, parcialmente cerrado, abierto).
    :param cp: Una instancia de :class:`cp.Edificio`.
    :param bool reducir_gcpi: (opcional) Indica si hay que reducir el valor de
        gcpi. Default = None.
    :param float aberturas_totales: (opcional) La suma de todas las aberturas
        del edificio. Default = None.
    :param float volumen_interno: (opcional) El volumen interno no dividido del
        edificio. Default = None.
    :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
        de presión para el SPRFV. Default=direccional.
        Valores aceptados = (direccional, envolvente).
    """
    def __init__(self, alturas, altura_media_cubierta, altura_alero_cubierta,
                 categoria, velocidad, rafaga, factor_topografico, cerramiento,
                 cp, alero=0, reducir_gcpi=False, aberturas_totales=None,
                 volumen_interno=None, metodo_sprfv='direccional'):
        self.cubierta = Cubierta(
            alturas, altura_media_cubierta, categoria, velocidad, rafaga,
            factor_topografico, cerramiento, cp.cubierta, reducir_gcpi,
            aberturas_totales, volumen_interno, metodo_sprfv
        )
        self.paredes = Paredes(
            alturas, altura_media_cubierta, altura_alero_cubierta, categoria,
            velocidad, rafaga, factor_topografico, cerramiento, cp.paredes,
            reducir_gcpi, aberturas_totales, volumen_interno, metodo_sprfv
        )
        if alero:
            self.alero = Alero(
                alturas, altura_media_cubierta, categoria, velocidad, rafaga,
                factor_topografico, cerramiento, cp.alero, metodo_sprfv
            )

    @cached_property
    def valores(self):
        valores = {'paredes': self.paredes(), 'cubierta': self.cubierta()}
        if hasattr(self, 'alero'):
            valores['alero'] = self.alero()
        return valores

    @classmethod
    def desde_edificio(cls, geometria, cp, categoria, velocidad, rafaga,
                       factor_topografico, cerramiento, reducir_gcpi=False,
                       metodo_sprfv='direccional'):
        """Crea una instancia a partir instancia de geometria y cp de un
        edificio.

        :param geometria: Una instancia de :class:`geometria.Edificio`
        :param cp: Una instancia de :class:`cp.Edificio`
        :param str categoria: La categoría de la estructura. Valores aceptados =
            (I, II, III, IV)
        :param float velocidad: La velocidad del viento en m/s.
        :param dict rafaga: ``dict`` con keys "paralelo" y "normal" donde los valores
            son instancias de :class:`Rafaga`. Las instancias debe ser creadas de
            acuerdo a la geometria del edificio cuando la direccion del viento es
            paralelo y normal a la cumbrera.
        :param factor_topografico: Los factores topográficos correspondientes a cada
            altura de la estructura. Debe ser de tipo :class:`~numpy:numpy.ndarray`.
        :param str cerramiento: El cerramiento del edificio. Valores aceptados =
            (cerrado, parcialmente cerrado, abierto).
        :param bool reducir_gcpi: (opcional) Indica si hay que reducir el valor de
            gcpi. Default = None.
        :param str metodo_sprfv: El método a utilizar para calcular los coeficientes
            de presión para el SPRFV. Default=direccional.
            Valores aceptados = (direccional, envolvente).
        """
        args = (
            geometria.alturas, geometria.cubierta.altura_media,
            geometria.cubierta.altura_alero, categoria, velocidad, rafaga,
            factor_topografico, cerramiento, cp, geometria.cubierta.alero,
            reducir_gcpi, geometria.aberturas_totales, geometria.volumen_interno,
            metodo_sprfv
        )
        return cls(*args)

    def __call__(self):
        return self.valores
