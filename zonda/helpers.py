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

import json
from pkg_resources import parse_version
from PyQt5 import QtCore, QtNetwork
from zonda import __about__


def hyperlink(link, texto):
    return f'<a href={link}>{texto}</a>'


class GithubReleaseHelper(QtCore.QObject):

    existe_nueva_version = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = QtNetwork.QNetworkAccessManager()
        self._manager.finished.connect(self.cuando_termine)

    def obtener_version(self):
        url = "https://api.github.com/repos/efdiloreto/Zonda/releases/latest"
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        self._manager.get(request)

    def cuando_termine(self, reply):
        respuesta = reply.readAll().data().decode()
        error = reply.error()
        if error == QtNetwork.QNetworkReply.NoError:
            datos = json.loads(respuesta)
            nueva_version = datos['tag_name']
            version_actual = __about__.__version__
            self.existe_nueva_version.emit(
                parse_version(nueva_version) > parse_version(version_actual)
            )

