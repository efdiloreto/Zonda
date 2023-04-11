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
from collections import namedtuple
import numpy as np
from cached_property import cached_property


_Constantes = namedtuple(
    'Constantes', ['alfa', 'zg', 'a_hat', 'b_hat', 'alpha_bar', 'b_bar',
                   'c', 'le', 'ep_bar', 'zmin']
)

_ParametrosTopograficos = namedtuple(
    'ParametrosTopograficos', ['factor_k', 'gamma', 'mu', 'lh', 'k1', 'k2', 'k3']
)

_constantes_exposicion = {
    'A': _Constantes(5, 457, 1 / 5, 0.64, 1 / 3, 0.3, 0.45, 55, 1 / 2, 18.3),
    'B': _Constantes(7, 366, 1 / 7, 0.84, 1 / 4, 0.45, 0.3, 98, 1 / 3, 9.2),
    'C': _Constantes(9.5, 274, 1 / 9.5, 1, 1 / 6.5, 0.65, 0.2, 152, 1 / 5, 4.6),
    'D': _Constantes(11.5, 213, 1 / 11.5, 1.07, 1 / 9, 0.8, 0.15, 198, 1 / 8, 2.1)
}


class Rafaga:
    """Clase Rafaga.

    Contiene métodos para calcular el factor de ráfaga.

    :param float ancho: El ancho de la estructura medido de forma normal a la
        dirección del viento.
    :param float longitud: El ancho de la estructura medido de forma paralelo a
        la dirección del viento.
    :param float altura: La altura de la estructura. Para edificios se toma la
        altura media.
    :param float altura_rafaga: La altura útil para calcular el factor de ráfaga.
        Por ejemplo, para edificios es 0.6 * altura media.
    :param float velocidad: La velocidad del viento en m/s.
    :param float frecuencia: La frecuencia natural de la estructura en hz.
    :param float beta: La relación de amortiguamiento crítico.
    :param str flexibilidad: La flexibilidad de la estructura.
        Valores aceptados = (rigida, flexible)
    :param bool factor_g_simplificado: Un booleano que indica si se debe usar
        0.85 como valor del factor de ráfaga.
    :param str categoria_exp: La categoría de exposición.
        Valores aceptados = (A, B, C, D)
    """
    def __init__(self, factor_g_simplificado, categoria_exp, **kwargs):
        args_aceptados = (
            'ancho', 'longitud', 'altura', 'altura_rafaga', 'velocidad',
            'frecuencia', 'beta', 'flexibilidad'
        )
        self.factor_g_simplificado = factor_g_simplificado
        self.categoria_exp = categoria_exp
        self.constantes_exp_terreno = _constantes_exposicion[self.categoria_exp]
        if not factor_g_simplificado:
            for key, valor in kwargs.items():
                if key in args_aceptados:
                    setattr(self, key, valor)

    @cached_property
    def parametros(self):
        """Calcula los parámetros de factor de ráfaga.

        :returns: ``namedtuple`` con los parámetros de factor de ráfaga.
        :rtype: tuple
        """
        parametros_rafaga = namedtuple('ParametrosRafaga', 'z iz lz gr r')
        z = max(self.altura_rafaga, self.constantes_exp_terreno.zmin)
        iz = self.constantes_exp_terreno.c * ((10 / z) ** (1 / 6))
        lz = self.constantes_exp_terreno.le * \
            ((z / 10) ** self.constantes_exp_terreno.ep_bar)
        if self.flexibilidad == 'flexible':
            gr = (2 * math.log(3600 * self.frecuencia)) ** 0.5 + 0.577 / (
                (2 * math.log(3600 * self.frecuencia)) ** 0.5)
            vz = self.constantes_exp_terreno.b_bar * \
                ((z / 10) ** self.constantes_exp_terreno.alpha_bar) * self.velocidad
            n1 = self.frecuencia * lz / vz
            rn = 7.47 * n1 / ((1 + 10.3 * n1) ** (5 / 3))
            nh = 4.6 * self.frecuencia * self.altura / vz
            nb = 4.6 * self.frecuencia * self.ancho / vz
            nl = 15.4 * self.frecuencia * self.longitud / vz
            n = (nh, nb, nl)
            ri = [1 / j - ((1 - np.e ** (-2 * j)) / (2 * j ** 2)) if j > 0
                  else 1 for j in n]
            rh, rb, rl = ri
            r = (rn * rh * rb * (0.53 + 0.47 * rl) / self.beta) ** 0.5
            return parametros_rafaga(z, iz, lz, gr, r)
        return parametros_rafaga(z, iz, lz, None, None)

    @cached_property
    def factor_q(self):
        """Calcula el factor Q.

        :rtype: float
        """
        factor_q = (1 / (1 + 0.63 * ((self.longitud + self.altura) /
                         self.parametros.lz) ** 0.63)) ** 0.5
        return factor_q

    def _rigida(self):
        """Calcula el factor de ráfaga para una estructura rígida.

        :rtype: float
        """
        g = ((1 + 1.7 * 3.4 * self.parametros.iz * self.factor_q) /
             (1 + 1.7 * 3.4 * self.parametros.iz)) * 0.925
        return g

    def _flexible(self):
        """Calcula el factor de ráfaga para una estructura flexible.

        :rtype: float
        """
        g = ((1 + 1.7 * self.parametros.iz * ((
            (3.4 * self.factor_q) ** 2 +
            (self.parametros.gr * self.parametros.r) ** 2) ** 0.5)) /
            (1 + 1.7 * 3.4 * self.parametros.iz)) * 0.925
        return g

    @cached_property
    def factor(self):
        """Calcula el factor de ráfaga de acuerdo a la flexibilidad de la
        estructura o si es considerado simplificado o no.

        :rtype: float
        """
        if self.factor_g_simplificado:
            return 0.85
        if self.flexibilidad == 'flexible':
            return self._flexible()
        return self._rigida()

    @classmethod
    def desde_edificio(cls, edificio, factor_g_simplificado, categoria_exp, **kwargs):
        """Crea dos instancias de :class:`Rafaga` para un edificio cuando se
        utiliza el método direccional para calcular las presiones sobre el SPRFV.

        :param edificio: Una instancia de :class:`geometria.Edificio`.

        :returns: ``dict`` que contiene dos instancias de :class:`Rafaga`, una
            para cuando el viento actua en direccion paralela a la cumbrera y
            otra cuando el viento actua en direccion normal a la cumbrera.
        :rtype: dict
        """
        ancho = edificio.ancho
        longitud = edificio.longitud
        altura = edificio.cubierta.altura_media
        altura_rafaga = 0.6 * altura
        paralelo = cls(
            factor_g_simplificado, categoria_exp, ancho=ancho,
            longitud=longitud, altura=altura, altura_rafaga=altura_rafaga,
            **kwargs
        )
        normal = cls(
            factor_g_simplificado, categoria_exp, ancho=longitud, longitud=ancho,
            altura=altura, altura_rafaga=altura_rafaga, **kwargs
        )
        return {'paralelo': paralelo, 'normal': normal}


class Topografia:
    """Clase Topografia.

    Contiene metodos para calcular el factor topografico.

    Args:
        :param str categoria_exp: La categoría de exposición.
            Valores aceptados = (A, B, C, D)
        :param bool considerar_topografia: Un booleano que indica si se tiene
            que calcular la topografia.
        :param str tipo_terreno: El tipo de colina.
            Valores aceptados = (loma bidimensional, escarpa bidimensional,
            colina tridimensional)
        :param float altura_terreno: La altura de la colina.
        :param float distancia_cresta: La distancia en la dirección de
            barlovento, medida desde la cresta de la colina o escarpa.
        :param float distancia_barlovento_sotavento: distancia tomada desde la
            cima, en la dirección de barlovento o de sotavento.
        :param str direccion: La direccion para la el argumento
            `distancia_barlovento_sotavento`. Valores aceptados =
            (barlovento, sotavento)
        :param alturas: Las alturas de la estructura donde calcular las
            presiones. Puede ser un único valor númerico o de tipo
            :class:`~numpy:numpy.ndarray`.
    """
    def __init__(self, considerar_topografia, alturas, **kwargs):
        argumentos_aceptados = (
            'categoria_exp', 'tipo_terreno', 'altura_terreno', 'distancia_cresta',
            'distancia_barlovento_sotavento', 'direccion'
        )
        self.considerar_topografia = considerar_topografia
        self.alturas = alturas
        if considerar_topografia:
            for key, valor in kwargs.items():
                if key in argumentos_aceptados:
                    setattr(self, key, valor)

    def topografia_considerada(self):
        """Chequea si es necesario considerar la topografia.

        :rtype: bool
        """
        if not self.considerar_topografia:
            return False
        if self.altura_terreno / self.distancia_cresta >= 0.2 and (
            (self.categoria_exp in ('A', 'B') and self.altura_terreno > 20) or
                (self.categoria_exp in ('C', 'D') and self.altura_terreno > 5)):
            return True
        return False

    @cached_property
    def parametros(self):
        """Calcula los parámetros de factor topográfico.

        :returns: ``namedtuple`` con los parámetros del factor topográfico.
        :rtype: tuple
        """
        # Referencia = CIRSOC 102-2005 Fig. 2
        param_topo_vel = {
            'loma bidimensional': {'factor_k': {'A': 1.3, 'B': 1.3,
                                                'C': 1.45, 'D': 1.55},
                                   'gamma': 3, 'mu': {'barlovento': 1.5,
                                                      'sotavento': 1.5}},
            'escarpa bidimensional': {'factor_k': {'A': 0.75, 'B': 0.75,
                                                   'C': 0.85, 'D': 0.95},
                                      'gamma': 2.5, 'mu': {'barlovento': 1.5,
                                                           'sotavento': 4}},
            'colina tridimensional': {'factor_k': {'A': 0.95, 'B': 0.95,
                                                   'C': 1.05, 'D': 1.15},
                                      'gamma': 4, 'mu': {'barlovento': 1.5,
                                                         'sotavento': 1.5}}
        }
        # Lh Referencia: CiIRSOC 102 2005 Fig. 2 Nota 2
        lh = max(self.distancia_cresta, 2 * self.altura_terreno)
        k_factor = param_topo_vel[self.tipo_terreno]['factor_k'][self.categoria_exp]
        gamma = param_topo_vel[self.tipo_terreno]['gamma']
        mu = param_topo_vel[self.tipo_terreno]['mu'][self.direccion]
        k1 = k_factor * self.altura_terreno / lh
        k2 = 1 - self.distancia_barlovento_sotavento / mu / lh
        k3 = np.e ** (-1 * gamma * self.alturas / lh)
        return _ParametrosTopograficos(k_factor, gamma, mu, lh, k1, k2, k3)

    @cached_property
    def factor(self):
        """Calcula el factor topográfico.

        :returns: Un array si hay varias alturas sobre las cuales hay que calcular
            el factor topográfico. En caso de que haya una única altura retorna
            un float.
        :rtype: :class:`~numpy:numpy.ndarray` o float
        """
        if not self.topografia_considerada():
            try:
                kzt = np.fromiter((1 for i in range(len(self.alturas))), float)
            except TypeError:
                kzt = 1.00
            return kzt
        return (1 + self.parametros.k1 * self.parametros.k2 * self.parametros.k3) ** 2
