#import "../utils/tag-referencing.typ": ref_name
#let architecture_description = [
  *Hardware:*
  - Circuito armado con los componentes descritos en la sección #ref_name(<pipeline>).

  - Laptop personal (HP Envy 17 cn2xxx, con Fedora Linux 44 x86_64):
    desarrollo del firmware de los ESP32, backend de Python con FastAPI,
    cliente móvil Flutter y documentación.

  - Teléfono físico Android (Samsung A35 5G): corre la app Flutter de PataCam.

  - Servidor casero (HP Laptop 17z-ca200, con Ubuntu Server 24.04.4 LTS x86_64): corre
    el backend hecho con FastAPI.

  - Dispensador Wi-Fi® para mascotas NHA-P610 (Nexxt Solutions Home): Alimentador inteligente
    utilizado como base del proyecto.


  *Software:*
  #lorem(40)
]
