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

import numpy as np
from cached_property import cached_property
from zonda.cirsoc import excepciones


class CubiertaAisladaDosAguas:
    """Esta clase utiliza para determinar los coeficientes de presión neta de
    cubiertas aisladas a dos aguas.

    :param float angulo: El ángulo de la cubierta.
    :param float relacion_bloqueo: La relación entre la altura de bloqueo y la
        altura de alero de cubierta.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, angulo, relacion_bloqueo):
        if -5 < angulo < 5:
            raise excepciones.ErrorLineamientos(
                'El Reglamento no provee lineamientos para calcular los'
                ' coeficientes de presión neta para cubiertas aisladas'
                f' a dos aguas con ángulo igual a {angulo:.2f}°.'
            )
        self.angulo = angulo
        self.relacion_bloqueo = relacion_bloqueo

    @cached_property
    def referencia(self):
        return 'Tabla I.2'

    @cached_property
    def valores(self):
        """Calcula los factores Cpn para una cubierta a dos aguas.

        :returns: Los valores de Cf para cada zona de la cubierta
        :rtype: dict
        """
        angulos = (-20, -15, -10, -5, 5, 10, 15, 20, 25, 30)
        maximos_valores_globales = (0.7, 0.5, 0.4, 0.3, 0.3, 0.4, 0.4, 0.6, 0.7, 0.9)
        maximos_valores_zona_a = (0.8, 0.6, 0.6, 0.5, 0.6, 0.7, 0.9, 1.1, 1.2, 1.3)
        maximos_valores_zona_b = (1.6, 1.5, 1.4, 1.5, 1.8, 1.8, 1.9, 1.9, 1.9, 1.9)
        maximos_valores_zona_c = (0.6, 0.7, 0.8, 0.8, 1.3, 1.4, 1.4, 1.5, 1.6, 1.6)
        maximos_valores_zona_d = (1.7, 1.4, 1.1, 0.8, 0.4, 0.4, 0.4, 0.4, 0.5, 0.7)
        minimos_valores_globales = (
            (-0.7, -1.5), (-0.6, -1.5), (-0.6, -1.4), (-0.5, -1.4), (-0.6, -1.2),
            (-0.7, -1.2), (-0.8, -1.2), (-0.9, -1.2), (-1.0, -1.2), (-1.0, -1.2)
        )
        minimos_valores_zona_a = (
            (-0.9, -1.5), (-0.8, -1.5), (-0.8, -1.4), (-0.5, -1.4), (-0.6, -1.2),
            (-0.7, -1.2), (-0.9, -1.2), (-1.2, -1.2), (-1.4, -1.2), (-1.4, -1.2)
        )
        minimos_valores_zona_b = (
            (-1.3, -2.4), (-1.3, -2.7), (-1.3, -2.5), (-1.3, -2.3), (-1.4, -2.0),
            (-1.5, -1.8), (-1.7, -1.6), (-1.8, -1.5), (-1.9, -1.4), (-1.9, -1.3)
        )
        minimos_valores_zona_c = (
            (-1.6, -2.4), (-1.6, -2.6), (-1.5, -2.5), (-1.6, -2.4), (-1.4, -1.8),
            (-1.4, -1.6), (-1.4, -1.3), (-1.4, -1.2), (-1.4, -1.1), (-1.4, -1.1)
        )
        minimos_valores_zona_d = (
            (-0.6, -1.2), (-0.6, -1.2), (-0.6, -1.2), (-0.6, -1.2), (-1.1, -1.5),
            (-1.4, -1.6), (-1.8, -1.7), (-2.0, -1.7), (-2.0, -1.6), (-2.0, -1.6)
        )
        valor_maximo_global = np.interp(self.angulo, angulos, maximos_valores_globales)
        valor_maximo_zona_a = np.interp(self.angulo, angulos, maximos_valores_zona_a)
        valor_maximo_zona_b = np.interp(self.angulo, angulos, maximos_valores_zona_b)
        valor_maximo_zona_c = np.interp(self.angulo, angulos, maximos_valores_zona_c)
        valor_maximo_zona_d = np.interp(self.angulo, angulos, maximos_valores_zona_d)

        bloqueos = [0, 1]

        minimos_valores_globales_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_globales
        )
        minimos_valores_caso_a_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_zona_a
        )
        minimos_valores_caso_b_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_zona_b
        )
        minimos_valores_caso_c_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_zona_c
        )
        minimos_valores_caso_d_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_zona_d
        )

        valor_minimo_global = np.interp(
            self.angulo, angulos, minimos_valores_globales_relacion
        )
        valor_minimo_zona_a = np.interp(
            self.angulo, angulos, minimos_valores_caso_a_relacion
        )
        valor_minimo_zona_b = np.interp(
            self.angulo, angulos, minimos_valores_caso_b_relacion
        )
        valor_minimo_zona_c = np.interp(
            self.angulo, angulos, minimos_valores_caso_c_relacion
        )
        valor_minimo_zona_d = np.interp(
            self.angulo, angulos, minimos_valores_caso_d_relacion
        )

        valores = {
            'global': {
                'máx': valor_maximo_global,
                'mín': valor_minimo_global
            },
            'local': {
                'a': {'máx': valor_maximo_zona_a,
                      'mín': valor_minimo_zona_a},
                'b': {'máx': valor_maximo_zona_b,
                      'mín': valor_minimo_zona_b},
                'c': {'máx': valor_maximo_zona_c,
                      'mín': valor_minimo_zona_c},
                'd': {'máx': valor_maximo_zona_d,
                      'mín': valor_minimo_zona_d}
            }
        }
        return valores

    @classmethod
    def desde_cubierta(cls, cubierta):
        """Crea una instancia a partir de una cubierta.

        :param cubierta: Una instancia de :class:`geometria.CubiertaDosAguas`
        """
        return cls(cubierta.angulo, cubierta.relacion_bloqueo)

    def __call__(self):
        return self.valores


class CubiertaAisladaUnAgua:
    """Esta clase utiliza para determinar los coeficientes de presión neta de
    cubiertas aisladas a un agua.

    :param float angulo: El ángulo de la cubierta.
    :param float relacion_bloqueo: La relación entre la altura de bloqueo y la
        altura de alero de cubierta.

    .. note:: Todos los parámetros numéricos deben ser positivos.
    """
    def __init__(self, angulo, relacion_bloqueo, posicion_bloqueo):
        if not 0 <= angulo <= 30:
            raise excepciones.ErrorLineamientos(
                'El Reglamento no provee lineamientos para calcular los'
                ' coeficientes de presión neta para cubiertas aisladas'
                f' a un agua con ángulo igual a {angulo}°.'
            )
        self.angulo = angulo
        self.relacion_bloqueo = relacion_bloqueo
        self.posicion_bloqueo = posicion_bloqueo

    @cached_property
    def referencia(self):
        return 'Tabla I.1'

    @cached_property
    def valores(self):
        """Calcula los factores Cpn para una cubierta a un agua.

        :returns: Los valores de Cf para cada zona de la cubierta
        :rtype: dict
        """
        angulos = (0, 5, 10, 15, 20, 25, 30)
        maximos_valores_globales = (0.2, 0.4, 0.5, 0.7, 0.8, 1, 1.2)
        maximos_valores_zona_a = (0.5, 0.8, 1.2, 1.4, 1.7, 2, 2.2)
        maximos_valores_zona_b = (1.8, 2.1, 2.4, 2.7, 2.9, 3.1, 3.2)
        maximos_valores_zona_c = (1.1, 1.3, 1.6, 1.8, 2.1, 2.3, 2.4)
        minimos_valores_globales = {
            'alero mas bajo': ((-0.5, -1.2), (-0.7, -1.4), (-0.9, -1.4), (-1.1, -1.5),
                               (-1.3, -1.5), (-1.6, -1.4), (-1.8, -1.4)),
            'alero mas alto': ((-0.5, -1.2), (-0.7, -1.2), (-0.9, -1.1), (-1.1, -1),
                               (-1.3, -0.9), (-1.6, -0.8), (-1.8, -0.8))
        }
        minimos_valores_zona_a = {
            'alero mas bajo': ((-0.6, -1.3), (-1.1, -1.4), (-1.5, -1.4), (-1.8, -1.5),
                               (-2.2, -1.5), (-2.6, -1.4), (-3.0, -1.4)),
            'alero mas alto': ((-0.6, -1.3), (-1.1, -1.2), (-1.5, -1.1), (-1.8, -1),
                               (-2.2, -0.9), (-2.6, -0.8), (-3.0, -0.8))
        }
        minimos_valores_zona_b = (
            (-1.3, -1.8), (-1.7, -2.6), (-2.0, -2.6), (-2.4, -2.9), (-2.8, -2.9),
            (-3.2, -2.5), (-3.8, -2.0)
        )
        minimos_valores_zona_c = {
            'alero mas bajo': ((-1.4, -2.2), (-1.8, -2.6), (-2.1, -2.7), (-2.5, -2.8),
                               (-2.9, -2.7), (-3.2, -2.5), (-3.6, -2.3)),
            'alero mas alto': ((-1.4, -2.2), (-1.8, -2.1), (-2.1, -1.8), (-2.5, -1.6),
                               (-2.9, -1.5), (-3.2, -1.4), (-3.6, -1.2)),
        }
        valor_maximo_global = np.interp(
            self.angulo, angulos, maximos_valores_globales
        )
        valor_maximo_zona_a = np.interp(
            self.angulo, angulos, maximos_valores_zona_a
        )
        valor_maximo_zona_b = np.interp(
            self.angulo, angulos, maximos_valores_zona_b
        )
        valor_maximo_zona_c = np.interp(
            self.angulo, angulos, maximos_valores_zona_c
        )

        bloqueos = [0, 1]

        minimos_valores_globales_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_globales[self.posicion_bloqueo]
        )
        minimos_valores_caso_a_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_zona_a[self.posicion_bloqueo]
        )
        minimos_valores_caso_b_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_zona_b
        )
        minimos_valores_caso_c_relacion = tuple(
            np.interp(self.relacion_bloqueo, bloqueos, valores)
            for valores in minimos_valores_zona_c[self.posicion_bloqueo]
        )

        valor_minimo_global = np.interp(
            self.angulo, angulos, minimos_valores_globales_relacion
        )
        valor_minimo_zona_a = np.interp(
            self.angulo, angulos, minimos_valores_caso_a_relacion
        )
        valor_minimo_zona_b = np.interp(
            self.angulo, angulos, minimos_valores_caso_b_relacion
        )
        valor_minimo_zona_c = np.interp(
            self.angulo, angulos, minimos_valores_caso_c_relacion
        )
        valores = {
            'global': {
                'máx': valor_maximo_global,
                'mín': valor_minimo_global
            },
            'local': {
                'a': {'máx': valor_maximo_zona_a,
                      'mín': valor_minimo_zona_a},
                'b': {'máx': valor_maximo_zona_b,
                      'mín': valor_minimo_zona_b},
                'c': {'máx': valor_maximo_zona_c,
                      'mín': valor_minimo_zona_c}
            }
        }
        return valores

    @classmethod
    def desde_cubierta(cls, cubierta):
        """Crea una instancia a partir de una cubierta.

        :param cubierta: Una instancia de :class:`geometria.CubiertaUnAgua`
        """
        return cls(cubierta.angulo, cubierta.relacion_bloqueo,
                   cubierta.posicion_bloqueo)

    def __call__(self):
        return self.valores


def cubierta_aislada(cubierta):
    if cubierta.tipo == 'dos aguas':
        return CubiertaAisladaDosAguas.desde_cubierta(cubierta)
    elif cubierta.tipo == 'un agua':
        return CubiertaAisladaUnAgua.desde_cubierta(cubierta)
    else:
        raise excepciones.ErrorLineamientos(
            'El Reglamento no provee lineamientos para cubiertas aisladas de'
            f' tipo: {cubierta.tipo}'
        )
