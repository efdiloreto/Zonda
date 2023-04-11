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

import os
import gettext
from jinja2 import Environment, FileSystemLoader
from zonda import recursos
from pint import UnitRegistry

ureg = UnitRegistry()


def convertir(valor, unidad_inicial, unidad_final):
    if unidad_inicial == unidad_final:
        return valor
    valor *= ureg(unidad_inicial)
    return valor.to(unidad_final).magnitude


def unidad_html(unidad):
    return f'{ureg(unidad).units:~H}'


file_loader = FileSystemLoader(recursos.CARPETA_PLANTILLAS)
env = Environment(loader=file_loader, extensions=['jinja2.ext.i18n'])
env.globals.update(zip=zip, all=all)
env.install_gettext_callables(gettext.gettext, gettext.ngettext)
env.filters['convertir'] = convertir
env.filters['unidad_html'] = unidad_html

env.globals['SemanticCSS'] = os.path.join(recursos.CARPETA_CSS, 'semantic.min.css')
env.globals['IconosCSS'] = os.path.join(recursos.CARPETA_CSS, 'icon.min.css')
env.globals['CustomCSS'] = os.path.join(recursos.CARPETA_CSS, 'custom.css')


def reporte(plantilla, **kwargs):
    plantilla_ = env.get_template(plantilla)
    return plantilla_.render(**kwargs)

