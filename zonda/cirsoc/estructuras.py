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

from . import geometria as ge
from . import cp
from .factores import Topografia, Rafaga
from . import presiones as pr


class Cartel:
    def __init__(self, profundidad, ancho, altura_inferior, altura_superior,
                 velocidad, categoria_exp, factor_g_simplificado,
                 considerar_topografia, categoria, **kwargs):
        self.ancho = ancho
        self.profundidad = profundidad
        self.altura_inferior = altura_inferior
        self.altura_superior = altura_superior
        self.velocidad = velocidad
        self.categoria_exp = categoria_exp
        self.factor_g_simplificado = factor_g_simplificado
        self.considerar_topografia = considerar_topografia
        self.categoria = categoria
        self.__dict__.update(kwargs)
        alturas_personalizadas = kwargs.get('alturas_personalizadas')
        es_parapeto = kwargs.get('es_parapeto', False)
        self.geometria = ge.Cartel(
            profundidad, ancho, altura_inferior, altura_superior,
            alturas_personalizadas
        )
        self.cf = cp.Cartel.desde_cartel(self.geometria, es_parapeto)
        self.rafaga = Rafaga(
            factor_g_simplificado, categoria_exp, altura=altura_superior,
            ancho=ancho, longitud=profundidad,
            altura_rafaga=self.geometria.altura_media, velocidad=velocidad,
            **kwargs
        )
        self.topografia = Topografia(
            considerar_topografia, self.geometria.alturas,
            categoria_exp=categoria_exp, **kwargs
        )
        self.presiones = pr.Cartel.desde_cartel(
            self.geometria, categoria, velocidad, self.rafaga,
            self.topografia.factor, self.cf
        )

    def __str__(self):
        return 'Cartel'


class CubiertaAislada:
    def __init__(self, ancho, longitud, altura_alero, altura_bloqueo,
                 posicion_bloqueo, altura_cumbrera, tipo_cubierta, velocidad,
                 categoria_exp, factor_g_simplificado, considerar_topografia,
                 categoria, **kwargs):
        self.ancho = ancho
        self.longitud = longitud
        self.altura_alero = altura_alero
        self.altura_cumbrera = altura_cumbrera
        self.altura_bloqueo = altura_bloqueo
        self.tipo_cubierta = tipo_cubierta
        self.posicion_bloqueo = posicion_bloqueo
        self.velocidad = velocidad
        self.categoria_exp = categoria_exp
        self.factor_g_simplificado = True
        self.considerar_topografia = considerar_topografia
        self.categoria = categoria
        self.__dict__.update(kwargs)
        self.geometria = ge.cubiertas.cubierta(
            tipo_cubierta, ancho, longitud, altura_alero,
            altura_cumbrera=altura_cumbrera, altura_bloqueo=altura_bloqueo,
            posicion_bloqueo=posicion_bloqueo
        )
        self.cpn = cp.cubierta_aislada(self.geometria)
        self.rafaga = Rafaga(True, categoria_exp=categoria_exp, **kwargs)
        self.topografia = Topografia(
            considerar_topografia, self.geometria.altura_media,
            categoria_exp=categoria_exp, **kwargs
        )
        self.presiones = pr.CubiertaAislada.desde_cubierta(
            self.geometria, categoria, velocidad, self.rafaga,
            self.topografia.factor, self.cpn
        )

    def __str__(self):
        return 'Cubierta-Aislada'


class Edificio:
    def __init__(self, ancho, longitud, elevacion, altura_alero, tipo_cubierta,
                 metodo_sprfv, velocidad, categoria_exp, factor_g_simplificado,
                 considerar_topografia, cerramiento, categoria, reducir_gcpi=False,
                 **kwargs):
        self.ancho = ancho
        self.longitud = longitud
        self.elevacion = elevacion
        self.altura_alero = altura_alero
        self.tipo_cubierta = tipo_cubierta
        self.metodo_sprfv = metodo_sprfv
        self.velocidad = velocidad
        self.categoria_exp = categoria_exp
        self.factor_g_simplificado = factor_g_simplificado
        self.considerar_topografia = considerar_topografia
        self.cerramiento = cerramiento
        self.categoria = categoria
        self.reducir_gcpi = reducir_gcpi
        self.__dict__.update(kwargs)
        self.geometria = ge.edificios(
            ancho, longitud, elevacion, altura_alero, tipo_cubierta, **kwargs
        )
        self.cp = cp.Edificio.desde_edifico(self.geometria, metodo_sprfv)
        self.rafaga = Rafaga.desde_edificio(
            self.geometria, factor_g_simplificado, categoria_exp,
            velocidad=velocidad, **kwargs
        )
        self.topografia = Topografia(
            considerar_topografia, self.geometria.alturas,
            categoria_exp=categoria_exp, **kwargs
        )
        self.presiones = pr.Edificio.desde_edificio(
            self.geometria, self.cp, categoria, velocidad, self.rafaga,
            self.topografia.factor, cerramiento, reducir_gcpi, metodo_sprfv
        )

    def __str__(self):
        return 'Edificio'
