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
from functools import partial
from tempfile import NamedTemporaryFile
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPageSetupDialog
from zonda import excepciones, dialogos, recursos, reportes
from zonda.cirsoc import Edificio, CubiertaAislada, Cartel
from zonda.cirsoc.geometria import edificios
from zonda.cirsoc import excepciones as cirsoc_excepciones


class WidgetViento(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self._combobox_exposicion = QtWidgets.QComboBox()
        self._combobox_exposicion.addItems('A B C D'.split())
        self._combobox_exposicion.setMinimumWidth(50)

        datos_spinboxs = (
            ('velocidad', 20, 100, 55, ' m/s', False, 2,
             'Velocidad básica del viento.'),
            ('frecuencia', 0.1, 100, 1, ' Hz', True, 2,
             'Frecuencia natural de la estructura.'),
            ('beta', 0.01, 0.05, 0.02, None, False, 3,
             'Relación de amortiguamiento β, expresada como porcentaje del'
             ' crítico.')
        )
        self._spinboxs = {}
        for nombre, minimo, maximo, default, sufijo, estado, precision, status_tip in datos_spinboxs:
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setMinimum(minimo)
            spinbox.setMaximum(maximo)
            spinbox.setValue(default)
            spinbox.setSuffix(sufijo)
            spinbox.setEnabled(estado)
            spinbox.setDecimals(precision)
            spinbox.setStatusTip(status_tip)
            self._spinboxs[nombre] = spinbox

        ciudades_velocidad = (
            ('Bahía Blanca', 55),
            ('Bariloche', 46),
            ('Buenos Aires', 45),
            ('Catamarca', 43),
            ('Comodoro Rivadavia', 67.5),
            ('Córdoba', 45),
            ('Corrientes', 46),
            ('Formosa', 45),
            ('La Plata', 46),
            ('La Rioja', 44),
            ('Mar del Plata', 51),
            ('Mendoza', 39),
            ('Neuquén', 48),
            ('Paraná', 52),
            ('Posada', 45),
            ('Rawson', 60),
            ('Resistencia', 45),
            ('Río Gallegos', 60),
            ('Rosario', 50),
            ('Salta', 35),
            ('Santa Fé', 51),
            ('San Juan', 40),
            ('San Luis', 45),
            ('San Miguel de Tucumán', 40),
            ('San Salvador de Jujuy', 34),
            ('Santa Rosa', 50),
            ('Santiago del Estero', 43),
            ('Ushuaia', 60),
            ('Viedma', 60)
        )

        editar_velocidad = QtWidgets.QCheckBox('Velocidad')
        editar_velocidad.stateChanged.connect(
            lambda: self._editar_velocidad(editar_velocidad.isChecked())
        )

        self._combobox_ciudades = QtWidgets.QComboBox()
        for opcion, valor in ciudades_velocidad:
            self._combobox_ciudades.addItem(
                opcion, userData=QtCore.QVariant(valor)
            )
        self._combobox_ciudades.currentIndexChanged.connect(
            self._setear_velocidad_ciudad
        )

        self._factor_g_simplificado = QtWidgets.QCheckBox(
            'Considerar Factor de Ráfaga igual a 0.85'
        )
        self._factor_g_simplificado.setChecked(True)
        self._factor_g_simplificado.stateChanged.connect(
            lambda: self._estado_rafaga(self._factor_g_simplificado.isChecked())
        )

        flexibilidades = (('Rígida', 'rigida'), ('Flexible', 'flexible'))
        self._combobox_flex = QtWidgets.QComboBox()
        for opcion, valor in flexibilidades:
            self._combobox_flex.addItem(
                opcion, userData=QtCore.QVariant(valor)
            )

        textos_rafaga = (
            'Flexibilidad', 'Frecuencia Natural', 'Relación de amortiguamiento'
        )

        imagen = QtWidgets.QLabel()
        imagen.setToolTip('Figura 1A - CIRSOC 102 2005')
        imagen.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        ruta = os.path.join(recursos.CARPETA_IMAGENES, 'viento', 'mapa.png')
        pixmap = QtGui.QPixmap(ruta)
        imagen.setPixmap(pixmap)

        self._layout_grid_viento = QtWidgets.QGridLayout()
        self._layout_grid_viento.addWidget(
            QtWidgets.QLabel('Ciudad'), 0, 0,
            QtCore.Qt.AlignRight
        )
        self._layout_grid_viento.addWidget(self._combobox_ciudades, 0, 1)
        self._layout_grid_viento.addWidget(
            editar_velocidad, 1, 0, QtCore.Qt.AlignRight
        )
        self._layout_grid_viento.addWidget(self._spinboxs['velocidad'], 1, 1)
        self._layout_grid_viento.setColumnStretch(2, 1)

        layout_grid_exposicion = QtWidgets.QGridLayout()

        layout_grid_exposicion.addWidget(
            QtWidgets.QLabel('Categoría de Exposición'), 0, 0,
            QtCore.Qt.AlignRight
        )
        layout_grid_exposicion.addWidget(self._combobox_exposicion, 0, 1)
        layout_grid_exposicion.setColumnStretch(2, 1)

        self._layout_grid_rafaga = QtWidgets.QGridLayout()
        self._layout_grid_rafaga.addWidget(self._factor_g_simplificado, 0, 0, 1, 3)
        for i, texto in enumerate(textos_rafaga):
            self._layout_grid_rafaga.addWidget(
                QtWidgets.QLabel(texto), i + 1, 0, QtCore.Qt.AlignRight
            )
        self._layout_grid_rafaga.addWidget(self._combobox_flex, 1, 1)
        self._layout_grid_rafaga.addWidget(self._spinboxs['frecuencia'], 2, 1)
        self._layout_grid_rafaga.addWidget(self._spinboxs['beta'], 3, 1)

        self._layout_grid_rafaga.setColumnStretch(2, 1)

        box_viento = QtWidgets.QGroupBox('Velocidad básica del viento')
        box_viento.setLayout(self._layout_grid_viento)

        box_exposicion = QtWidgets.QGroupBox('Exposición')
        box_exposicion.setLayout(layout_grid_exposicion)

        box_rafaga = QtWidgets.QGroupBox('Factor de Ráfaga')
        box_rafaga.setLayout(self._layout_grid_rafaga)

        layout_principal = QtWidgets.QGridLayout()
        layout_principal.addWidget(box_viento, 0, 0)
        layout_principal.addWidget(box_exposicion, 1, 0)
        layout_principal.addWidget(box_rafaga, 2, 0)
        layout_principal.addWidget(imagen, 0, 1, 4, 1)
        layout_principal.setRowStretch(3, 1)
        layout_principal.setRowStretch(4, 2)
        layout_principal.setColumnStretch(1, 1)

        self.setLayout(layout_principal)
        self._estado_rafaga(True)

    def _estado_rafaga(self, estado):
        for fila in range(1, 4):
            for columna in range(2):
                widget = self._layout_grid_rafaga.itemAtPosition(fila, columna).widget()
                widget.setEnabled(not estado)

    def _setear_velocidad_ciudad(self):
        velocidad = self._combobox_ciudades.itemData(
            self._combobox_ciudades.currentIndex()
        )
        self._spinboxs['velocidad'].setValue(velocidad)

    def _editar_velocidad(self, estado):
        self._spinboxs['velocidad'].setEnabled(estado)
        for fila in range(0, 1):
            for columna in range(2):
                widget = self._layout_grid_viento.itemAtPosition(fila, columna).widget()
                widget.setEnabled(not estado)

    def _validar(self):
        if not self._factor_g_simplificado.isChecked():
            flexibilidad = self._combobox_flex.itemData(
                self._combobox_flex.currentIndex()
            )
            frecuencia = self._spinboxs['frecuencia'].value()
            if flexibilidad == 'rigida' and frecuencia < 1:
                raise excepciones.ErrorViento(
                    'Para que la estructura sea considerada rígida, la'
                    ' frecuencia debe debe ser mayor o igual a 1 Hz.'
                )
            elif flexibilidad == 'flexible' and frecuencia >= 1:
                raise excepciones.ErrorViento(
                    'Para que la estructura sea considerada flexible, la'
                    ' frecuencia debe ser menor a 1 Hz.'
                )

    def datos(self):
        self._validar()
        resultados_spinboxs = {
            key: spinbox.value() for key, spinbox in self._spinboxs.items()
        }
        flexibilidad = self._combobox_flex.itemData(
            self._combobox_flex.currentIndex()
        )
        datos = dict(
            factor_g_simplificado=self._factor_g_simplificado.isChecked(),
            categoria_exp=self._combobox_exposicion.currentText(),
            flexibilidad=flexibilidad,
            **resultados_spinboxs
        )
        return datos

    def __call__(self):
        return self.datos()


class WidgetTopografia(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._combobox_tipo_terreno = QtWidgets.QComboBox()
        self._combobox_tipo_terreno.addItems(
            ('Escarpa Bidimensional', 'Loma Bidimensional', 'Colina Tridimensional')
        )
        self._combobox_tipo_terreno.currentIndexChanged.connect(
            self._cambio_tipo_terreno
        )
        direcciones = (
            ('Barlovento de la cresta', 'barlovento'),
            ('Sotavento de la cresta', 'sotavento')
        )
        self._combobox_direccion = QtWidgets.QComboBox()
        for opcion, valor in direcciones:
            self._combobox_direccion.addItem(
                opcion, userData=QtCore.QVariant(valor)
            )
        textos_spinboxs = (
            'Distancia, L<sub>h</sub>', 'Distancia, X', 'Altura de Colina, H'
        )
        datos_spinboxs = (
            ('distancia_cresta', 1, 200, 50, ' m', True,
             'Distancia medida desde la cresta de la colina hasta el punto en'
             ' que la diferencia de elevación del terreno es la mitad de la'
             ' altura de la colina o escarpa.'),
            ('distancia_barlovento_sotavento', 1, 200, 50, ' m', True,
             'Distancia tomada desde la cima, en la dirección de barlovento o de'
             ' sotavento.'),
            ('altura_terreno', 5, 200, 40, ' m', True, 'Altura de loma o escarpa.')
        )

        self._spinboxs = {}
        for nombre, minimo, maximo, default, sufijo, activado, status_tip in datos_spinboxs:
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setMinimum(minimo)
            spinbox.setMaximum(maximo)
            spinbox.setValue(default)
            spinbox.setSuffix(sufijo)
            spinbox.setEnabled(activado)
            spinbox.setStatusTip(status_tip)
            self._spinboxs[nombre] = spinbox

        self._imagen = QtWidgets.QLabel()
        self._imagen.setFrameStyle(QtWidgets.QFrame.StyledPanel)

        self._layout_principal = QtWidgets.QGridLayout()

        self._layout_principal.addWidget(
            QtWidgets.QLabel('Tipo de Terreno'), 0, 0, QtCore.Qt.AlignRight
        )
        self._layout_principal.addWidget(self._combobox_tipo_terreno, 0, 1)
        self._layout_principal.addWidget(
            QtWidgets.QLabel('Dirección'), 1, 0, QtCore.Qt.AlignRight
        )
        self._layout_principal.addWidget(self._combobox_tipo_terreno, 0, 1)
        self._layout_principal.addWidget(self._combobox_direccion, 1, 1)
        for i, (nombre, widget) in enumerate(self._spinboxs.items()):
            self._layout_principal.addWidget(
                QtWidgets.QLabel(textos_spinboxs[i]), i + 2, 0, QtCore.Qt.AlignRight
            )
            self._layout_principal.addWidget(widget, i + 2, 1)
        self._layout_principal.addItem(QtWidgets.QSpacerItem(0, 20), 6, 0, 1, 2)
        self._layout_principal.addWidget(
            QtWidgets.QLabel(
                '* Se condisera que se satisfacen los puntos 1, 2 y 3 '
                'del artículo 5.7.1.'), 7, 0, 1, 3
        )
        self._layout_principal.setRowStretch(5, 1)
        self._layout_principal.setRowStretch(6, 2)

        self._layout_principal.addWidget(self._imagen, 0, 2, 6, 1)

        self._considerar_topografia = QtWidgets.QGroupBox('Considerar Topografía*')
        self._considerar_topografia.setCheckable(True)
        self._considerar_topografia.setChecked(False)
        self._considerar_topografia.setLayout(self._layout_principal)

        layout_vertical_principal = QtWidgets.QVBoxLayout()
        layout_vertical_principal.addWidget(self._considerar_topografia)
        layout_vertical_principal.addStretch()

        self.setLayout(layout_vertical_principal)
        self._cambio_tipo_terreno()

    def datos(self):
        resultados_spinboxs = {
            key: spinbox.value() for key, spinbox in self._spinboxs.items()
        }
        direccion = self._combobox_direccion.itemData(
            self._combobox_direccion.currentIndex()
        )
        datos = dict(
            considerar_topografia=self._considerar_topografia.isChecked(),
            tipo_terreno=self._combobox_tipo_terreno.currentText().lower(),
            direccion=direccion, **resultados_spinboxs
        )
        return datos

    def _cambio_tipo_terreno(self):
        tipo_terreno = self._combobox_tipo_terreno.currentText().lower()
        if tipo_terreno == 'escarpa bidimensional':
            imagen = 'escarpa.png'
        else:
            imagen = 'loma.png'
        ruta = os.path.join(recursos.CARPETA_IMAGENES, 'topografia', imagen)
        pixmap = QtGui.QPixmap(ruta)
        self._imagen.setPixmap(pixmap)

    def __call__(self):
        return self.datos()


class LineEditAlturasPersonalizadas(QtWidgets.QLineEdit):
    def __init__(self):
        super().__init__()
        self.setToolTip(
            'Ingrese los valores de altura separados por coma (",")'
        )
        self.setStatusTip(
            'Las alturas personalizadas donde se calcularán las presiones.'
        )

    def text(self):
        alturas_personalizadas = super().text()
        if alturas_personalizadas:
            try:
                alturas_personalizadas = [
                    float(altura) for altura in
                    alturas_personalizadas.split(',')
                ]
            except (ValueError, TypeError) as error:
                raise excepciones.ErrorEstructura(
                    'Las alturas personalizadas deben ser valores '
                    'numéricos separados por ","') from error
        return alturas_personalizadas


class WidgetCategoria(QtWidgets.QGroupBox):
    def __init__(self):
        super().__init__('Categoría')
        self._combobox = QtWidgets.QComboBox()
        self._combobox.addItems('I II III IV'.split())
        self._combobox.setMinimumWidth(50)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Categoría de la Estructura'))
        layout.addWidget(self._combobox)
        layout.addStretch()

        self.setLayout(layout)

    def datos(self):
        return self._combobox.currentText()

    def __call__(self):
        return self.datos()


class WidgetComponentes(QtWidgets.QTableWidget):
    def __init__(self, datos_iniciales=None):
        super().__init__()
        self.setColumnCount(2)
        self.setRowCount(30)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color:gainsboro }"
        )
        self.verticalHeader().setVisible(False)
        self.setHorizontalHeaderLabels(('Descripción', 'Área de influencia (m\u00B2)'))
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        for fila in range(self.rowCount()):
            for columna in range(self.columnCount()):
                self.setItem(fila, columna, QtWidgets.QTableWidgetItem())
        if datos_iniciales is not None:
            for i, (descripcion, area) in enumerate(datos_iniciales.items()):
                self.item(i, 0).setText(descripcion)
                self.item(i, 1).setText(str(area))

    def datos(self):
        datos = {}
        for fila in range(self.rowCount()):
            nombre = self.item(fila, 0).text()
            if nombre:
                if nombre not in datos:
                    try:
                        area = float(self.item(fila, 1).text())
                        if area <= 0:
                            raise ValueError(
                                'El valor de área debe ser un valor mayor o '
                                'igual que cero.'
                            )
                        datos[nombre] = float(self.item(fila, 1).text())
                    except ValueError as error:
                        raise excepciones.ErrorComponentes(
                            'El valor de área debe ser un valor numérico.'
                        ) from error
                else:
                    raise excepciones.ErrorComponentes(
                        'Existen nombres de componentes repetidos.'
                    )
        return datos or None

    def __call__(self):
        return self.datos()


class WidgetCartel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        textos_geometria = (
            'Altura Superior, H<sub>s</sub>', 'Altura Inferior, H<sub>i</sub>',
            'Ancho, B', 'Profundidad'
        )

        datos_spinboxs = (
            ('altura_superior', 0.1, 300, 10, ' m'),
            ('altura_inferior', 0, 200, 0, ' m'),
            ('ancho', 0.1, 300, 5, ' m'),
            ('profundidad', 0.1, 50, 1, ' m')
        )
        self._spinboxs = {}
        for nombre, minimo, maximo, default, sufijo in datos_spinboxs:
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setMinimum(minimo)
            spinbox.setMaximum(maximo)
            spinbox.setValue(default)
            spinbox.setSuffix(sufijo)
            self._spinboxs[nombre] = spinbox

        self._alturas_personalizadas = LineEditAlturasPersonalizadas()

        self._categoria = WidgetCategoria()

        self._imagen = QtWidgets.QLabel()
        self._imagen.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        imagen = os.path.join(recursos.CARPETA_IMAGENES, 'estructuras', 'cartel.png')
        self._imagen.setPixmap(QtGui.QPixmap(imagen))

        self._es_parapeto = QtWidgets.QCheckBox('Calcular como parapeto de edificio')
        self._es_parapeto.setStatusTip(
            'Si se activa, se considera el parapeto actuando como un cartel a'
            ' nivel de terreno.'
        )

        grid_layout_geometria = QtWidgets.QGridLayout()

        grid_layout_geometria.addWidget(self._es_parapeto, 0, 0, 1, 2)

        for i, texto in enumerate(textos_geometria):
            grid_layout_geometria.addWidget(
                QtWidgets.QLabel(texto), i + 1, 0,
                QtCore.Qt.AlignRight
            )

        for i, spinbox in enumerate(self._spinboxs.values()):
            grid_layout_geometria.addWidget(spinbox, i + 1, 1)

        grid_layout_geometria.addWidget(
            QtWidgets.QLabel('Personalizar Alturas:'), 5, 0
        )
        grid_layout_geometria.addWidget(
            self._alturas_personalizadas, 6, 0, 1, 2
        )
        grid_layout_geometria.addWidget(self._imagen, 0, 3, 10, 1)

        box_estructura = QtWidgets.QGroupBox('Geometría')
        box_estructura.setLayout(grid_layout_geometria)

        layout_principal = QtWidgets.QVBoxLayout()
        layout_principal.addWidget(box_estructura)
        layout_principal.addWidget(self._categoria)
        layout_principal.addStretch()

        self.setLayout(layout_principal)

    def _validar(self):
        valor_altura_superior = self._spinboxs['altura_superior'].value()
        valor_altura_inferior = self._spinboxs['altura_inferior'].value()
        if valor_altura_inferior >= valor_altura_superior:
            raise excepciones.ErrorEstructura(
                'La altura superior debe ser mayor a la altura inferior.'
            )

    def datos(self):
        self._validar()
        resultados_spinboxs = {
            key: spinbox.value() for key, spinbox in self._spinboxs.items() if spinbox.isEnabled()
        }
        datos = dict(
            alturas_personalizadas=self._alturas_personalizadas.text() or None,
            categoria=self._categoria(),
            es_parapeto=self._es_parapeto.isChecked(),
            **resultados_spinboxs
        )
        return datos

    def __call__(self):
        return self.datos()


class WidgetCubiertaAislada(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        textos_geometria = (
            'Ancho, B', 'Altura de Alero, H<sub>a</sub>',
            'Altura de Cumbrera, H<sub>c</sub>',
            'Altura de Bloqueo, H<sub>b</sub>', 'Longitud',
        )

        tipos_cubierta = ('Dos Aguas', 'Un Agua')
        self._combobox_tipo_cubierta = QtWidgets.QComboBox()
        self._combobox_tipo_cubierta.addItems(tipos_cubierta)
        self._combobox_tipo_cubierta.currentIndexChanged.connect(
            self._cambio_tipo_cubierta
        )

        datos_spinboxs = (
            ('ancho', 1, 2000, 30, ' m'),
            ('altura_alero', 1, 200, 6, ' m'),
            ('altura_cumbrera', 1, 200, 9, ' m'),
            ('altura_bloqueo', 0, 300, 5, ' m'),
            ('longitud', 1, 2000, 60, ' m')
        )
        self._spinboxs = {}
        for nombre, minimo, maximo, default, sufijo in datos_spinboxs:
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setMinimum(minimo)
            spinbox.setMaximum(maximo)
            spinbox.setValue(default)
            spinbox.setSuffix(sufijo)
            self._spinboxs[nombre] = spinbox

        posiciones_bloqueo = ('Alero mas bajo', 'Alero mas alto')
        self._combobox_posicion_bloqueo = QtWidgets.QComboBox()
        self._combobox_posicion_bloqueo.addItems(posiciones_bloqueo)

        self._categoria = WidgetCategoria()

        self._imagen = QtWidgets.QLabel()
        self._imagen.setFrameStyle(QtWidgets.QFrame.StyledPanel)

        self._grid_layout_geometria = QtWidgets.QGridLayout()

        self._grid_layout_geometria.addWidget(
            QtWidgets.QLabel('Tipo de Cubierta'), 0, 0, QtCore.Qt.AlignRight
        )
        self._grid_layout_geometria.addWidget(self._combobox_tipo_cubierta, 0, 1)

        for i, texto in enumerate(textos_geometria):
            self._grid_layout_geometria.addWidget(
                QtWidgets.QLabel(texto), i + 1, 0,
                QtCore.Qt.AlignRight
            )

        for i, spinbox in enumerate(self._spinboxs.values()):
            self._grid_layout_geometria.addWidget(spinbox, i + 1, 1)

        self._grid_layout_geometria.addWidget(
            QtWidgets.QLabel('Posición del bloqueo'), 6, 0, QtCore.Qt.AlignRight
        )
        self._grid_layout_geometria.addWidget(self._combobox_posicion_bloqueo, 6, 1)
        self._grid_layout_geometria.addWidget(self._imagen, 0, 2, 8, 1)

        box_estructura = QtWidgets.QGroupBox('Geometría')
        box_estructura.setLayout(self._grid_layout_geometria)

        layout_principal = QtWidgets.QVBoxLayout()
        layout_principal.addWidget(box_estructura)
        layout_principal.addWidget(self._categoria)
        layout_principal.addStretch()

        self.setLayout(layout_principal)
        self._cambio_tipo_cubierta()

    def _cambio_tipo_cubierta(self):
        tipo_cubierta = self._combobox_tipo_cubierta.currentText().lower()
        bool_cubierta = tipo_cubierta == 'un agua'
        self._grid_layout_geometria.itemAtPosition(6, 0).widget().setEnabled(bool_cubierta)
        self._grid_layout_geometria.itemAtPosition(6, 1).widget().setEnabled(bool_cubierta)
        ruta = os.path.join(
            recursos.CARPETA_IMAGENES, 'estructuras', 'aislada', tipo_cubierta + '.png'
        )
        self._imagen.setPixmap(QtGui.QPixmap(ruta))

    def datos(self):
        resultados_spinboxs = {
            key: spinbox.value() for key, spinbox in self._spinboxs.items() if spinbox.isEnabled()
        }
        datos = dict(
            tipo_cubierta=self._combobox_tipo_cubierta.currentText().lower(),
            posicion_bloqueo=self._combobox_posicion_bloqueo.currentText().lower(),
            categoria=self._categoria(),
            **resultados_spinboxs
        )
        return datos

    def __call__(self):
        return self.datos()


class WidgetEdificio(QtWidgets.QWidget):

    reporte_actualizado = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._componentes = {
            'componentes_paredes': None,
            'componentes_cubierta': None
        }

        textos_geometria = (
            'Ancho, B', 'Altura de Alero, H<sub>a</sub>',
            'Altura de Cumbrera, H<sub>c</sub>', 'Longitud',
            'Elevación sobre el terreno'
        )

        tipos_cubierta = ('Dos Aguas', 'Un Agua', 'Plana')
        self._combobox_tipo_cubierta = QtWidgets.QComboBox()
        self._combobox_tipo_cubierta.addItems(tipos_cubierta)
        self._combobox_tipo_cubierta.currentIndexChanged.connect(
            self._cambio_tipo_cubierta
        )

        datos_spinboxs = (
            ('ancho', 1, 300, 30, ' m', True),
            ('altura_alero', 1, 300, 6, ' m', True),
            ('altura_cumbrera', 1, 300, 16, ' m', True),
            ('longitud', 1, 300, 60, ' m', True),
            ('elevacion', 0, 200, 0, ' m', True),
            ('alero', 0, 20, 0, ' m', False),
            ('parapeto', 0, 20, 0, ' m', False)
        )
        self._spinboxs = {}
        for nombre, minimo, maximo, default, sufijo, activado in datos_spinboxs:
            spinbox = QtWidgets.QDoubleSpinBox()
            spinbox.setMinimum(minimo)
            spinbox.setMaximum(maximo)
            spinbox.setValue(default)
            spinbox.setSuffix(sufijo)
            spinbox.setEnabled(activado)
            self._spinboxs[nombre] = spinbox

        self._checkbox_alero = QtWidgets.QCheckBox('Alero')
        self._checkbox_alero.setLayoutDirection(QtCore.Qt.RightToLeft)
        self._checkbox_alero.stateChanged.connect(
            self._spinboxs['alero'].setEnabled
        )

        self._checkbox_parapeto = QtWidgets.QCheckBox('Parapeto')
        self._checkbox_parapeto.setLayoutDirection(QtCore.Qt.RightToLeft)
        self._checkbox_parapeto.stateChanged.connect(self._parapeto)

        self._mensaje_parapeto = QtWidgets.QErrorMessage()
        self._mensaje_parapeto.setWindowTitle('Aviso parapeto')
        self._mensaje_parapeto.setFixedWidth(350)
        self._mensaje_parapeto.setFixedHeight(250)

        self._alturas_personalizadas = LineEditAlturasPersonalizadas()
        self._alturas_personalizadas.setStatusTip(
            'Las alturas personalizadas donde se calcularán las presiones para'
            ' paredes a barlovento.'
        )

        self._categoria = WidgetCategoria()

        self._combobox_cerramiento = QtWidgets.QComboBox()
        self._combobox_cerramiento.addItems(
            ('Cerrado', 'Parcialmente Cerrado')
        )

        boton_calcular_cerramiento = QtWidgets.QPushButton('Verificar')
        boton_calcular_cerramiento.clicked.connect(self.reporte_cerramiento)

        self._checkbox_unico_volumen = QtWidgets.QCheckBox(
            'El edificio es un único volumen sin particionar'
        )
        self._checkbox_unico_volumen.setStatusTip(
            'Si se activa, se adopta como volumen interno el volumen total del'
            ' edificio.'
        )
        self._checkbox_unico_volumen.stateChanged.connect(
            lambda: self._toggle_volumen(self._checkbox_unico_volumen.isChecked())
        )

        texto_aberturas = (
            'Pared 1', 'Pared 2', 'Pared 3', 'Pared 4', 'Cubierta'
        )

        self._spinboxs_aberturas = {
            key: QtWidgets.QDoubleSpinBox() for key in texto_aberturas
        }
        for spinbox in self._spinboxs_aberturas.values():
            spinbox.setMinimum(0)
            spinbox.setMaximum(100000000)
            spinbox.setValue(0)
            spinbox.setSuffix(' m2')

        self._spinbox_volumen = QtWidgets.QDoubleSpinBox()
        self._spinbox_volumen.setMinimum(1)
        self._spinbox_volumen.setMaximum(100000000)
        self._spinbox_volumen.setSuffix(' m3')

        self._imagen = QtWidgets.QLabel()
        self._imagen.setFrameStyle(QtWidgets.QFrame.StyledPanel)

        boton_componentes = QtWidgets.QPushButton('Componentes y Revestimientos')
        boton_componentes.clicked.connect(self._dialogo_componentes)

        self._grid_layout_geometria = QtWidgets.QGridLayout()
        self._grid_layout_geometria.addWidget(
            QtWidgets.QLabel('Tipo de Cubierta'), 0, 0, QtCore.Qt.AlignRight
        )
        self._grid_layout_geometria.addWidget(self._combobox_tipo_cubierta, 0, 1)

        for i, texto in enumerate(textos_geometria):
            self._grid_layout_geometria.addWidget(
                QtWidgets.QLabel(texto), i + 1, 0,
                QtCore.Qt.AlignRight
            )

        for i, spinbox in enumerate(self._spinboxs.values()):
            self._grid_layout_geometria.addWidget(spinbox, i + 1, 1)

        self._grid_layout_geometria.addWidget(self._checkbox_alero, 6, 0)
        self._grid_layout_geometria.addWidget(self._checkbox_parapeto, 7, 0)
        self._grid_layout_geometria.addWidget(
            QtWidgets.QLabel('Personalizar Alturas:'), 8, 0
        )
        self._grid_layout_geometria.addWidget(
            self._alturas_personalizadas, 9, 0, 1, 2
        )
        self._grid_layout_geometria.addWidget(self._imagen, 0, 3, 10, 1)
        self._grid_layout_geometria.addWidget(boton_componentes, 11, 0)

        layout_cerramiento = QtWidgets.QGridLayout()
        layout_cerramiento.addWidget(QtWidgets.QLabel('Clasificación'), 0, 0)
        layout_cerramiento.addWidget(self._combobox_cerramiento, 0, 1)
        layout_cerramiento.addWidget(boton_calcular_cerramiento, 0, 2)
        layout_cerramiento.setColumnStretch(3, 1)

        grid_layout_aberturas = QtWidgets.QGridLayout()
        for i, (key, spinbox) in enumerate(self._spinboxs_aberturas.items()):
            grid_layout_aberturas.addWidget(
                QtWidgets.QLabel(key), i, 0,
                QtCore.Qt.AlignRight
            )
            grid_layout_aberturas.addWidget(spinbox, i, 1)
        grid_layout_aberturas.setRowStretch(5, 1)

        box_aberturas = QtWidgets.QGroupBox('Aberturas')
        box_aberturas.setLayout(grid_layout_aberturas)
        box_aberturas.setStatusTip('')

        self._grid_layout_reduccion_gcpi = QtWidgets.QGridLayout()
        self._grid_layout_reduccion_gcpi.addWidget(
            self._checkbox_unico_volumen, 0, 0, 1, 2
        )
        self._grid_layout_reduccion_gcpi.addWidget(
            QtWidgets.QLabel('Volumen interno no dividido, V<sub>i</sub>'), 1, 0
        )
        self._grid_layout_reduccion_gcpi.addWidget(self._spinbox_volumen, 1, 1)
        self._grid_layout_reduccion_gcpi.setRowStretch(2, 1)

        box_estructura = QtWidgets.QGroupBox('Geometría')
        box_estructura.setLayout(self._grid_layout_geometria)

        self._box_reduccion_gcpi = QtWidgets.QGroupBox(
            'Considerar reducción de coeficiente de presión interna'
        )
        self._box_reduccion_gcpi.setLayout(self._grid_layout_reduccion_gcpi)
        self._box_reduccion_gcpi.setCheckable(True)
        self._box_reduccion_gcpi.setChecked(False)

        box_cerramiento = QtWidgets.QGroupBox('Cerramiento')
        box_cerramiento.setLayout(layout_cerramiento)

        layout_principal = QtWidgets.QGridLayout()
        layout_principal.addWidget(box_estructura, 0, 0, 1, 2)
        layout_principal.addWidget(self._box_reduccion_gcpi, 1, 0)
        layout_principal.addWidget(self._categoria, 2, 0)
        layout_principal.addWidget(box_cerramiento, 3, 0)
        layout_principal.addWidget(box_aberturas, 1, 1, 3, 1)
        layout_principal.setRowStretch(5, 1)

        self.setLayout(layout_principal)
        self._cambio_tipo_cubierta()

    def _cambio_tipo_cubierta(self):
        tipo_cubierta = self._combobox_tipo_cubierta.currentText().lower()
        bool_cubierta = tipo_cubierta == 'plana'
        self._grid_layout_geometria.itemAtPosition(3, 0).widget().setEnabled(not bool_cubierta)
        self._grid_layout_geometria.itemAtPosition(3, 1).widget().setEnabled(not bool_cubierta)
        ruta = os.path.join(
            recursos.CARPETA_IMAGENES, 'estructuras', 'edificio', tipo_cubierta + '.png'
        )
        self._imagen.setPixmap(QtGui.QPixmap(ruta))

    def _parapeto(self, estado):
        if self._checkbox_parapeto.isChecked():
            self._mensaje_parapeto.showMessage(
                'La altura del parapeto solo se utiliza para determinar los coeficientes'
                ' de presión para componentes y revestimientos. Para determinar las'
                ' presiones sobre el mismo se debe calcular como un cartel elevado'
                ' a la altura deseada, tal y como se calcula en el ejemplo Nº3 de la'
                ' "Guía para el uso del Reglamento Argentino de acción del viento'
                ' sobre las construcciones."'
            )
        self._spinboxs['parapeto'].setEnabled(estado)

    def _toggle_volumen(self, estado):
        for i in range(2):
            widget = self._grid_layout_reduccion_gcpi.itemAtPosition(1, i).widget()
            widget.setEnabled(not estado)

    def _dialogo_componentes(self):
        dialogo = dialogos.DialogoComponentes(self._componentes)
        if dialogo.exec_():
            self._componentes = dialogo()

    def _validar(self):
        tipo_cubierta = self._combobox_tipo_cubierta.currentText().lower()
        valor_altura_alero = self._spinboxs['altura_alero'].value()
        valor_altura_cumbrera = self._spinboxs['altura_cumbrera'].value()
        if tipo_cubierta != 'plana':
            if valor_altura_alero >= valor_altura_cumbrera:
                raise excepciones.ErrorEstructura(
                    'La altura de cumbrera debe ser mayor a la altura de alero.'
                )

    def datos(self):
        self._validar()
        resultados_spinboxs = {
            key: spinbox.value() for key, spinbox in self._spinboxs.items() if spinbox.isEnabled()
        }
        aberturas = tuple(
            spinbox.value() for spinbox in self._spinboxs_aberturas.values()
        )
        volumen_interno = self._spinbox_volumen.value()
        if self._checkbox_unico_volumen.isChecked() or not \
                self._box_reduccion_gcpi.isChecked():
            volumen_interno = None
        datos = dict(
            categoria=self._categoria(),
            tipo_cubierta=self._combobox_tipo_cubierta.currentText().lower(),
            alturas_personalizadas=self._alturas_personalizadas.text() or None,
            cerramiento=self._combobox_cerramiento.currentText().lower(),
            reducir_gcpi=self._box_reduccion_gcpi.isChecked(),
            aberturas=aberturas,
            volumen_interno=volumen_interno,
            metodo_sprfv='direccional',
            **self._componentes,
            **resultados_spinboxs,
        )
        return datos

    def reporte_cerramiento(self):
        try:
            edificio = edificios(**self())
            reporte_str = reportes.reporte(
                'cerramiento.html', edificio=edificio
            )
            self.reporte_actualizado.emit(reporte_str)
        except excepciones.ErrorEstructura as error:
            QtWidgets.QMessageBox.warning(self, 'Error de Datos de Entrada', str(error))

    def __call__(self):
        return self.datos()


class WidgetStackedEstructuras(QtWidgets.QStackedWidget):
    def __init__(self):
        super().__init__()

        self.addWidget(WidgetEdificio())
        self.addWidget(WidgetCartel())
        self.addWidget(WidgetCubiertaAislada())

    def datos(self):
        widget = self.currentWidget()
        return widget()

    def __call__(self):
        return self.datos()


class WidgetEstructuras(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        estructuras = (
            'Edificios', 'Carteles llenos y paredes', 'Cubiertas Aisladas')
        combobox_estructuras = QtWidgets.QComboBox()
        combobox_estructuras.addItems(estructuras)

        self._estructuras = WidgetStackedEstructuras()

        combobox_estructuras.currentIndexChanged.connect(
            self._estructuras.setCurrentIndex
        )

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel('Tipo de estructura:'), 0, 0)
        layout.addWidget(combobox_estructuras, 0, 1)
        layout.addWidget(self._estructuras, 1, 0, 1, 4)
        layout.setColumnStretch(2, 1)
        layout.setVerticalSpacing(10)

        self.setLayout(layout)

    def datos(self):
        return self._estructuras()

    def cirsoc_calculo(self):
        estructuras = (Edificio, Cartel, CubiertaAislada)
        return estructuras[self._estructuras.currentIndex()]

    def __call__(self):
        return self.datos()


class WidgetCirsoc(QtWidgets.QTabWidget):

    reporte_actualizado = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._unidades = {
            'presion': 'N / m ** 2',
            'fuerza': 'N'
        }

        self.estructura = WidgetEstructuras()
        self.viento = WidgetViento()
        self.topografia = WidgetTopografia()

        self.addTab(self.estructura, 'Estructura')
        self.addTab(self.viento, 'Viento')
        self.addTab(self.topografia, 'Topografía')

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum
        )

    def enviar_reporte(self):
        estructura = self._generar_estructura()
        if estructura is not None:
            try:
                reporte_str = reportes.reporte(
                    f'{estructura}.html', estructura=estructura,
                    unidades=self._unidades
                )
            except cirsoc_excepciones.ErrorLineamientos as error:
                QtWidgets.QMessageBox.warning(self, 'Advertencia', str(error))
            self.reporte_actualizado.emit(reporte_str)

    def _generar_estructura(self):
        estructura = self.estructura.cirsoc_calculo()
        try:
            parametros = dict(
                **self.estructura(),
                **self.viento(),
                **self.topografia()
            )
            return estructura(**parametros)
        except excepciones.ErrorEstructura as error:
            QtWidgets.QMessageBox.warning(self, 'Error de Datos de Entrada', str(error))
            self.setCurrentIndex(0)
        except excepciones.ErrorViento as error:
            QtWidgets.QMessageBox.warning(self, 'Error de Datos de Entrada', str(error))
            self.setCurrentIndex(1)
        except excepciones.ErrorLineamientos as error:
            QtWidgets.QMessageBox.warning(self, 'Error de Datos de Entrada', str(error))

    @QtCore.pyqtSlot(object)
    def setear_unidades(self, unidades):
        self._unidades = unidades


class WidgetReporte(QtWidgets.QWidget):

    calculos_terminados = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._printer = QPrinter()
        self._printer.setPageMargins(25, 10, 10, 10, QPrinter.Millimeter)

        self._vista_web = QtWebEngineWidgets.QWebEngineView()
        self._vista_web.setAutoFillBackground(False)
        self._vista_web.setContentsMargins(20, 20, 20, 20)
        self._vista_web.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self._vista_web.loadFinished.connect(self._calculos_correctos)

        formatos_funciones = (
            ('HTML', self.exportar_html),
            ('TXT', self.exportar_txt),
            ('PDF', self.exportar_pdf)
        )

        self._botones = []
        for formato, funcion in formatos_funciones:
            boton = QtWidgets.QPushButton()
            boton.setEnabled(False)
            pixmap = QtGui.QPixmap(
                os.path.join(recursos.CARPETA_ICONOS, formato.lower() + '.svg')
            )
            icono = QtGui.QIcon(pixmap)
            boton.setIcon(icono)
            boton.setIconSize(pixmap.rect().size())
            boton.setFlat(True)
            boton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            boton.clicked.connect(funcion)
            self._botones.append(boton)

        exportar_layout = QtWidgets.QVBoxLayout()
        for boton in self._botones:
            exportar_layout.addWidget(boton)
        exportar_layout.addStretch()

        exportar_grupo = QtWidgets.QGroupBox('Exportar:')
        exportar_grupo.setLayout(exportar_layout)

        layout_principal = QtWidgets.QGridLayout()
        layout_principal.addWidget(self._vista_web, 0, 0, 2, 1)
        layout_principal.addWidget(exportar_grupo, 0, 1)

        layout_principal.setRowStretch(1, 1)
        self.setLayout(layout_principal)

    @QtCore.pyqtSlot(str)
    def setear_html(self, html_str):
        self.calculos_terminados.emit('Calculando...')

        # por lo visto no funciona 'setHtml' por el momento. Por eso hay que
        # hacer un archivo temporal y levantar el html desde ahí.
        # Ver -> https://stackoverflow.com/q/51388443/6788927
        with NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as tmp:
            tmp.write(html_str)
            self._vista_web.load(QtCore.QUrl.fromLocalFile(tmp.name))

    def exportar_html(self):
        nombre, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Exportar a HTML', 'Reporte.html', filter='html (*.html)'
        )
        if nombre:
            self._vista_web.page().toHtml(partial(self.guardar, nombre))

    def exportar_txt(self):
        nombre, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Exportar a TXT', 'Reporte.txt', filter='txt (*.txt)'
        )
        if nombre:
            self._vista_web.page().toPlainText(partial(self.guardar, nombre))

    def exportar_pdf(self):
        dialogo = QPageSetupDialog(self._printer, self)
        if dialogo.exec_():
            self._printer = dialogo.printer()
            nombre, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, 'Exportar a PDF', 'Reporte.pdf', filter='pdf (*.pdf)'
            )
            if nombre:
                pl = self._printer.pageLayout()
                self._vista_web.page().printToPdf(nombre, pl)

    def _calculos_correctos(self, estado):
        for boton in self._botones:
            boton.setEnabled(estado)
        self.calculos_terminados.emit('Cálculos correctos')

    @staticmethod
    def guardar(nombre, datos):
        with open(nombre, mode='w', encoding='utf-8') as archivo:
            archivo.write(datos)


class WidgetResultados(QtWidgets.QTabWidget):
    def __init__(self):
        super().__init__()
        self.reporte = WidgetReporte()
        self.addTab(self.reporte, 'Reporte')


class WidgetPrincipal(QtWidgets.QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self._estructura = WidgetCirsoc()
        resultados = WidgetResultados()
        boton_calcular = QtWidgets.QPushButton()
        pixmap = QtGui.QPixmap(
            os.path.join(recursos.CARPETA_ICONOS, 'calculator-solid.svg')
        )
        icono = QtGui.QIcon(pixmap)
        boton_calcular.setIcon(icono)
        boton_calcular.setIconSize(QtCore.QSize(30, 30))
        boton_calcular.setFlat(True)

        self._estructura.reporte_actualizado.connect(resultados.reporte.setear_html)
        self._estructura.estructura._estructuras.currentWidget().reporte_actualizado.connect(resultados.reporte.setear_html)

        resultados.reporte.calculos_terminados.connect(self.parent.label_calculos.setText)

        layout_principal = QtWidgets.QHBoxLayout()
        layout_principal.addWidget(self._estructura)
        layout_principal.addWidget(resultados)
        layout_principal.setContentsMargins(10, 10, 10, 0)

        self.setLayout(layout_principal)

    def calcular(self):
        self._estructura.enviar_reporte()
