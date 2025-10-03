# Proyecto VetCare360

Este proyecto nace como herramienta de práctica libre para entender los principios SOLID y GRASP vistos en el curso de Arquitectura de Software I.

Es una aplicación web basada en Flask, y con uso de una base de datos de SQLite para efectos de desarrollo.

## Cómo ejecutar en local:

1. Asegurarse de tener Python instalado en la máquina.
2. Clonar o extraer en .zip el repositorio vetcare-stable

### Preparar entorno virtual:

1. En la raíz del proyecto, crear un entorno virtual: `python -m venv .venv`

2. Para activar el entorno virtual:

    * Windows: `.venv\Scripts\activate`
    * Unix-like: `source .venv/bin/activate`

3. Instalar dependencias: `pip install -r requirements.txt`

### Correr el proyecto: 

1. Con todo lo anterior, sólo quedaría ejecutar la app con el siguiente comando `python run.py`; con esto, se ejecuta la aplicación WSGI a través de un server de desarrollo.

## Errores conocidos: 

* Actualmente, dentro de la interfaz web, se tienen 8 opciones principales, dentro de las cuales hay algunas funcionalidades ya implementadas pero otras más en desarrollo, estas son:

    1. Dashboard (funciona)
    2. Clientes (funciona)
    3. Mascotas (funciona)
    4. Citas (funciona)
    5. Facturación (En desarrollo)
    6. Inventario (En desarrollo)
    7. Calendario (En desarrollo)
    8. Reportes (En desarrollo)

Además, existe otro módulo interno que se denomina Usuarios. Donde se gestionará el CRUD completo y tendrá funcionalidades como gestionar los usuarios, dependiendo del rol con el cual se inicie sesión.

    9. Usuarios (En desarrollo)

* Actualmente el sistema sólo sirve para gestionar (CRUD completo) todo lo relacionado con: Clientes, Mascotas y Citas, sin embargo, evidentemente carece de las demás features marcadas como "(En desarrollo)"
