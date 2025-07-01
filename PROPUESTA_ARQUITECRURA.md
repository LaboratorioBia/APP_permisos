# PROPUESTA DE MEJORA DE ARQUITECTURA – Proyecto de Permisos y Licencias

## 1. Introducción

El proyecto actual tiene una estructura funcional, (OJO! Esto no quiere decir que sea la mejor forma) sigue los lineamientos básicos de Django. Sin embargo, existen oportunidades de mejora para facilitar la escalabilidad, mantenimiento y separación de responsabilidades.

---

## 2. Propuesta de Mejora

### 2.1 Estructura recomendada del proyecto (Simple y escalable)

```plaintext
APP_PERMISOS/
│
├── app_permisos/            
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── utils/                  # Helpers, servicios o clases reutilizables
│   └── templates/              # Plantillas HTML
│
├── proyecto_permisos/         # 'core' Configuración del proyecto Django (Recomendado llamaro 'core')
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── static/   # ! Consolidar en una sola carpeta
│
├── .env
├── manage.py
├── .gitignore
└── requirements.txt

---

### 2.2 Recomendaciones específicas

* static/	Consolidar en una sola carpeta. Usar solo la de proyecto_permisos/ o la global, no ambas.
* .env	Bien ubicado. No subir a Git. Usar python-dotenv com os.getenv()
* templates/	Si hay muchas vistas, separar por módulo: templates/permisos/, templates/usuarios/, etc.
* templates/    Nuevamente, si hay muchas vistas, preferiblemente separar la logica del front
* views.py	Si crece, dividir en views/solicitudes.py, views/usuarios.py, etc.
* urls.py	Modularizar las rutas por área. Usar include().
* src/   No es necesario
* .html   La estructura del codigo segmentarla por bloques para una mejor legibilidad.

### 2.2 Recomendaciones específicas por componente

| Elemento         | Mejora propuesta |
|------------------|------------------|
| **`settings.py`**       | Aclarar la version se python para evitar conflictos al configurar el proyecto en un nuevo sistema o servidor |
| **`.env`**       | Estandarizar el uso. Asegurarse de **no subirlo al repositorio**. Usar `os.getenv()` con librerías como `python-dotenv`. |
| **`AUTH_USER_MODEL`** | Recomendado usar solo si se tiene control total sobre la base de datos. En sistemas ya existentes, puede causar conflictos si no se gestionan bien las migraciones. | ! Tener cuidado en esta parte

---

## 3. Buenas Prácticas en el Código

- Utilizar **comentarios claros** en funciones, especialmente en las vistas que interactúan con la base de datos o contienen lógica condicional compleja.
- Implementar manejo de errores con bloques `try-except` para evitar caídas inesperadas y facilitar el debugging.
- Usar **nombres de variables descriptivos** para mejorar la legibilidad del código.
- Aplicar **formateo de líneas largas**, usando saltos de línea en expresiones dentro de paréntesis, para respetar el máximo de 79–100 caracteres por línea y mejorar la estética del código.
- Separar la lógica de negocio de las vistas utilizando clases o funciones auxiliares (patrón "Service Layer").
- Crear un archivo `README.md` que describa el proyecto, cómo levantarlo localmente, y cómo contribuir (ideal en entornos colaborativos).

---

## 4. Conclusión

La presente propuesta busca implementar una arquitectura más limpia, modular y orientada a buenas prácticas, sin perder la funcionalidad actual del sistema. Estas sugerencias pueden adoptarse de forma progresiva, permitiendo que el equipo mantenga la estabilidad del proyecto mientras mejora su calidad técnica.

Aplicar estas prácticas permitirá que el sistema sea más **mantenible, escalable y robusto**, y facilitará la incorporación de nuevas funcionalidades o desarrolladores en el futuro.

# Justificación del uso de Django REST Framework (DRF) y Serializers (Cambio importante)
En el desarrollo del endpoint /api/solicitudes/, se decidió implementar Django REST Framework con el uso de serializers por los siguientes motivos técnicos y estratégicos:

* Separación de responsabilidades (SRP)
El uso de serializers permite mantener la lógica de negocio, la presentación de datos y el acceso a la base de datos claramente separados. Esto facilita la escalabilidad y el mantenimiento del sistema.

* Validación y serialización robusta
DRF permite validar y estructurar datos de forma clara, reutilizable y centralizada. Los serializers garantizan que los datos enviados o devueltos cumplan con las reglas esperadas.

* Compatibilidad con estándares REST
La API expuesta cumple con buenas prácticas REST, facilitando integraciones futuras (por ejemplo: aplicaciones móviles, frontend modernos o sistemas externos).
* Escalabilidad
La solución implementada puede ampliarse fácilmente a múltiples endpoints, paginación, filtrado, autenticación por token, etc., sin reestructurar el código base.
* Reutilización
El serializer puede ser utilizado en múltiples vistas (/api/solicitudes/, /api/exportar/, /api/licencias-detalle/, etc.), lo que evita duplicación de lógica.
* Compatibilidad con frontend dinámico (AJAX / fetch)
La estructura JSON devuelta por DRF es fácilmente consumida desde JavaScript usando fetch, lo que habilita interfaces dinámicas modernas sin necesidad de recargar la página.

## Conclusión:
La elección de DRF para la construcción del endpoint /api/solicitudes/ aporta claridad, robustez y una base sólida para la evolución del proyecto. Esta decisión no solo mejora el código actual, sino que también abre el camino a futuras integraciones y funcionalidades avanzadas.