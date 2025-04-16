# Changelog - Buscador de Vuelos con Amadeus API

Todas las modificaciones notables del proyecto se documentarán en este archivo.

## [1.10.1] - 2025-04-09

### Añadido
- **Funcionalidad de envío de correos electrónicos**:
  - Implementación de la ruta `/send_booking_email` para procesar solicitudes de envío de confirmaciones
  - Simulación de envío de correos en modos "development" y "testing"
  - Guardado de correos en archivos HTML para facilitar la revisión durante el desarrollo
  - Envío real de correos electrónicos en modo "production"
  - Mensajes informativos sobre el comportamiento según el modo de entorno

### Corregido
- Solucionado el error "'str' object has no attribute 'get'" al procesar datos de pasajeros
- Mejorado el manejo de diferentes tipos de datos en la información de reservas
- Implementada validación robusta de formularios para el envío de correos

## [1.10.0] - 2025-04-09

### Añadido
- **Consulta de reservas por PNR**:
  - Nueva ruta `/find_booking` para buscar reservas existentes por código PNR
  - Modal interactivo para ingresar y buscar códigos PNR
  - Visualización detallada de la información de la reserva encontrada
  - Opciones para imprimir confirmación o enviar por email
  - Manejo de errores cuando no se encuentra la reserva

### Modificado
- Interfaz de usuario mejorada con botones en la sección principal para acceder a diferentes funcionalidades
- Integración con la funcionalidad existente de envío de emails

## [1.9.1] - 2025-04-09

### Añadido
- **Configuración avanzada para entornos de producción y desarrollo**:
  - Nuevas variables de entorno para controlar el comportamiento del sistema
  - Archivo `.env.example` con plantilla de configuración
  - Opciones para habilitar/deshabilitar el modo de prueba automático
  - Control sobre la visibilidad de mensajes de modo de prueba al usuario
  - Personalización de mensajes según el entorno (desarrollo vs producción)

### Modificado
- Función `create_amadeus_booking` actualizada para utilizar las nuevas variables de configuración
- Mensajes de error más amigables en producción
- Mayor flexibilidad para configurar qué códigos de error activan el modo de prueba

## [1.9.0] - 2025-04-09

### Añadido
- **Manejo mejorado de errores en reservas**:
  - Detección automática del error "SEGMENT SELL FAILURE" (código 34651) de Amadeus
  - Activación automática del modo de prueba cuando ocurre este error
  - Generación de PNR simulado para continuar con el proceso de reserva
  - Mensaje informativo para el usuario cuando se activa el modo de prueba

### Modificado
- Función `create_amadeus_booking` mejorada para manejar errores específicos
- Interfaz de usuario actualizada para mostrar mensajes informativos sobre el modo de prueba
- Mejora en la experiencia de usuario al realizar reservas, incluso cuando hay problemas con la API

## [1.8.0] - 2025-04-09

### Añadido
- **Autocompletado de aeropuertos y ciudades**:
  - Integración con la API de Airport & City Search de Amadeus
  - Sugerencias en tiempo real al escribir en los campos de origen y destino
  - Visualización de códigos IATA, nombres completos de aeropuertos y ubicaciones
  - Selección intuitiva de aeropuertos sin necesidad de conocer los códigos IATA
  - Interfaz de usuario mejorada con estilos para las sugerencias
  - Búsqueda por nombre de ciudad o aeropuerto (mínimo 2 caracteres)

### Modificado
- Campos de origen y destino ahora muestran información completa pero envían solo el código IATA
- Mejora en la experiencia de usuario al buscar vuelos

## [1.7.0] - 2025-04-09

### Añadido
- **Integración completa con API Flight Create Orders de Amadeus**:
  - Creación de reservas reales en el sistema de Amadeus
  - Formateo de datos de pasajeros según especificación de la API
  - Procesamiento de diferentes tipos de pasajeros (adultos, niños e infantes)
  - Utilización del PNR generado por Amadeus
  - Manejo de respuestas y errores de la API
  - Almacenamiento del ID de reserva de Amadeus en la base de datos local

## [1.6.0] - 2025-04-09

### Añadido
- **Sistema de PNR para reservas**:
  - Generación de códigos PNR de 6 caracteres alfanuméricos
  - Formato estándar de la industria aérea (letras mayúsculas y números)
  - Exclusión de caracteres confusos (I, O, 0, 1) para evitar errores
  - Campo de estado para las reservas (CONFIRMED, CANCELLED, etc.)
  - Preparación para integración con API de Amadeus para reservas reales

## [1.5.0] - 2025-04-09

### Añadido
- **Sistema de reservas reales**:
  - Base de datos SQLAlchemy para almacenamiento persistente de reservas
  - Endpoint API para procesar y guardar reservas (/create_booking)
  - Generación de número único de reserva (UUID)
  - Almacenamiento completo de datos de pasajeros y detalles de vuelo
  - Manejo de errores y respuestas en la interfaz de usuario

## [1.4.0] - 2025-04-09

### Añadido
- **Cargo de Servicio para subagentes**:
  - Campo para añadir comisión de servicio al precio del vuelo
  - Opción para especificar el cargo en USD o en la moneda original del vuelo
  - Conversión automática de divisas con tasa aproximada (0.92 EUR/USD)
  - Cálculo en tiempo real del precio total incluyendo el cargo
  - Desglose detallado de precios en la confirmación de reserva

## [1.3.0] - 2025-04-09

### Añadido
- **Formulario de datos de pasajeros**:
  - Implementación de ventana modal al seleccionar una tarifa
  - Formularios dinámicos que se adaptan al número de pasajeros seleccionados
  - Campos para datos de contacto (email y teléfono)
  - Proceso de confirmación de reserva
  - Soporte para adultos, niños e infantes con campos específicos para cada tipo

### Modificado
- Límite máximo de 9 adultos por reserva
- Actualización del rango de edad para niños a 2-17 años
- Mejoras en la interfaz de usuario para el proceso de reserva

## [1.2.0] - 2025-04-09

### Añadido
- **Visualización de múltiples opciones de tarifas**:
  - Implementación de tres opciones de precios por vuelo (Básica, Estándar y Familiar)
  - Diseño de botones compactos con códigos de colores para cada tipo de tarifa
  - Posicionamiento optimizado de los botones de precios a la derecha de la tarjeta
  - Información descriptiva sobre lo que incluye cada tipo de tarifa

### Modificado
- Simplificación del formulario de búsqueda eliminando opciones redundantes
- Mejora en la presentación visual de los resultados de búsqueda
- Optimización del backend para incluir siempre opciones de múltiples tarifas

## [1.1.0] - 2025-04-09

### Añadido
- **Nuevo diseño de resultados de vuelos**:
  - Formato similar al de aerolíneas comerciales (estilo Viva Aerobus)
  - Resumen visual de vuelos de ida y vuelta con información destacada
  - Visualización de duración del vuelo con línea indicadora
  - Botón para expandir/contraer detalles adicionales
  - Mejora en la presentación de fechas y horarios

### Modificado
- Rediseño completo de las tarjetas de vuelos
- Mejora en la visualización de logos de aerolíneas
- Optimización del formato de presentación de información

## [1.0.0] - 2025-04-09

### Añadido
- **Opciones de pasajeros**:
  - Campo para número de adultos (mínimo 1)
  - Campo para número de niños (2-12 años)
  - Campo para número de infantes (0-2 años)

- **Mejoras en la búsqueda**:
  - Aumento del número máximo de resultados de 5 a 250
  - Implementación de paginación con 10 vuelos por página
  - Controles de navegación entre páginas (anterior/siguiente)
  - Contador de resultados totales y página actual
  - Desplazamiento suave al cambiar de página

- **Información de aerolíneas**:
  - Visualización del nombre de la aerolínea en cada segmento
  - Visualización de la aerolínea principal en la tarjeta del vuelo
  - Logos de aerolíneas junto a sus nombres (usando pics.avs.io)
  - Códigos IATA de las aerolíneas
  - Números de vuelo cuando están disponibles

- **Opciones de tarifa**:
  - Opción de tarifa familiar (Family Fare) para familias que viajan juntas
  - Selección de clase de viaje (Economy, Premium Economy, Business, First)
  - Selección de tipo de distribución (NDC o EDIFACT) para diferentes tipos de tarifas

- **Mejoras visuales**:
  - Diseño responsivo para diferentes dispositivos
  - Tarjetas de vuelo con información detallada
  - Insignias para información destacada
  - Animaciones suaves al cargar resultados

### Modificado
- Actualización del backend para procesar los nuevos parámetros
- Mejora en la presentación de los resultados de búsqueda
- Optimización de la interfaz de usuario para mejor experiencia

### Corregido
- Validación de parámetros de entrada
- Manejo de errores en la comunicación con la API

## [0.1.0] - Versión inicial

### Añadido
- Búsqueda básica de vuelos de ida y vuelta
- Visualización de precios y detalles básicos
- Interfaz web con Flask
