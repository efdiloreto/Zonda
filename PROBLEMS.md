# Problemas Conocidos

## El instalador es detectado como un virus.
A veces los antivirus detectan falsos positivos sobre software que no tienen cierta reputación. Zonda es totalmente open-source y usa librerias open-source. La librería encargada de compilar es [cx_Freeze](https://github.com/anthony-tuininga/cx_Freeze).

##  El programa no puede iniciarse porque VCRUNTIME140.DLL falta en el equipo
Se necesitan instalar los paquetes de Visual C++ Redistributable (32 bit). Se debe descargar el archivo *"vc_redist.x86.exe"* desde [acá](https://www.microsoft.com/es-ar/download/details.aspx?id=48145).

