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
from PyQt5 import QtWidgets, QtGui, QtCore
from zonda import widgets, dialogos, __about__, recursos, helpers


class VentanaPrincipal(QtWidgets.QMainWindow):

    unidades = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self._unidades = None

        self.resize(1366, 768)
        self.setWindowTitle(f'Zonda {__about__.__version__}')
        self._menu = self.menuBar()

        self.label_calculos = QtWidgets.QLabel('Sin resultados')
        self.label_calculos.setAlignment(QtCore.Qt.AlignVCenter)

        self._label_nueva_version = QtWidgets.QLabel()
        self._label_nueva_version.setTextFormat(QtCore.Qt.RichText)
        self._label_nueva_version.setTextInteractionFlags(
            QtCore.Qt.TextBrowserInteraction
        )
        self._label_nueva_version.setOpenExternalLinks(True)
        self._label_nueva_version.setContentsMargins(0, 0, 5, 0)

        github_release = helpers.GithubReleaseHelper(self)
        github_release.existe_nueva_version.connect(self.chequear_version)
        github_release.obtener_version()

        barra_estado = self.statusBar()
        barra_estado.setSizeGripEnabled(False)
        barra_estado.addWidget(self.label_calculos)
        barra_estado.addPermanentWidget(self._label_nueva_version)

        self.setWindowIcon(QtGui.QIcon(os.path.join(recursos.CARPETA_ICONOS, 'zonda.svg')))
        self._widget_central = widgets.WidgetPrincipal(self)

        self.unidades.connect(self._widget_central._estructura.setear_unidades)

        self.setCentralWidget(self._widget_central)
        self._menu_configuracion()
        self._calcular()
        self._acerca_de()

    def chequear_version(self, nueva_version):
        if nueva_version:
            self._label_nueva_version.setText(
                helpers.hyperlink(
                    'https://github.com/efdiloreto/Zonda/releases',
                    'Hay una nueva versión disponible!'
                )
            )

    def _menu_configuracion(self):
        menu_configuracion = self._menu.addMenu('&Configuración')

        unidades_act = QtWidgets.QAction('&Unidades', self)
        unidades_act.setShortcut('Ctrl+U')
        unidades_act.triggered.connect(self._dialogo_unidades)

        menu_configuracion.addAction(unidades_act)

    def _dialogo_unidades(self):
        dialogo = dialogos.DialogoUnidades(self._unidades)
        if dialogo.exec_():
            self._unidades = dialogo()
            if self.unidades is not None:
                self.unidades.emit(self._unidades)

    def _calcular(self):
        calcular_act = QtWidgets.QAction('&Calcular', self)
        calcular_act.setShortcut('Alt+C')
        calcular_act.triggered.connect(self._widget_central.calcular)
        self._menu.addAction(calcular_act)

    def _acerca_de(self):
        acerca_de_act = QtWidgets.QAction('&Acerca', self)
        acerca_de_act.triggered.connect(dialogos.AcercaDe)
        self._menu.addAction(acerca_de_act)

    def closeEvent(self, event):
        event.ignore()
        dialogos.Gracias()
        event.accept()