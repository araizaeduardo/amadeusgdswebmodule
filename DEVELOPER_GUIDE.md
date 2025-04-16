# Guía para Desarrolladores - Buscador de Vuelos con Amadeus

Esta guía proporciona instrucciones detalladas para desarrolladores que trabajen con el Buscador de Vuelos con Amadeus, incluyendo configuración, estructura del proyecto, y guías de implementación para nuevas características.

## Índice

1. [Configuración del Entorno](#configuración-del-entorno)
2. [Estructura del Proyecto](#estructura-del-proyecto)
3. [Flujo de Datos](#flujo-de-datos)
4. [Integración con Amadeus API](#integración-con-amadeus-api)
5. [Sistema de Reservas](#sistema-de-reservas)
6. [Endpoints API](#endpoints-api)
7. [Integración con WhatsApp](#integración-con-whatsapp)
8. [Guía de Contribución](#guía-de-contribución)

---

## Configuración del Entorno

### Requisitos Previos

- Python 3.10 o 3.11 (recomendado)
- pip (gestor de paquetes de Python)
- Credenciales de API de Amadeus (Test Environment)

### Pasos de Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <url-del-repositorio>
   cd amadeusai
   ```

2. **Crear un entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Linux/Mac
   # o
   venv\Scripts\activate  # En Windows
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

   **Nota para Python 3.13**: Si estás usando Python 3.13, es posible que necesites instalar manualmente algunas dependencias:
   ```bash
   pip install flask-mail
   pip install --upgrade sqlalchemy
   ```

4. **Configurar variables de entorno**:
   - Crear un archivo `.env` en la raíz del proyecto basado en `.env.example`
   - Configurar las siguientes variables:
     ```
     # Credenciales de Amadeus API
     AMADEUS_API_KEY=tu_api_key_aquí
     AMADEUS_API_SECRET=tu_api_secret_aquí
     
     # Modo de entorno (development, testing, production)
     APP_ENV=development
     
     # Configuración de manejo de errores
     ENABLE_AUTO_FALLBACK=true
     SHOW_FALLBACK_MESSAGES=true
     AUTO_FALLBACK_ERROR_CODES=34651
     
     # Configuración de la base de datos
     DATABASE_URL=sqlite:///bookings.db
     
     # Configuración de email (para enviar confirmaciones)
     EMAIL_HOST=smtp.example.com
     EMAIL_PORT=587
     EMAIL_USER=your_email@example.com
     EMAIL_PASSWORD=your_email_password
     EMAIL_USE_TLS=true
     EMAIL_FROM=noreply@example.com
     ```

5. **Ejecutar la aplicación**:
   ```bash
   python app.py
   ```
   La aplicación estará disponible en `http://localhost:5005`

---

## Estructura del Proyecto

```
amadeusai/
├── app.py              # Aplicación principal Flask
├── requirements.txt    # Dependencias del proyecto
├── .env               # Variables de entorno (no incluido en git)
├── .env.example       # Plantilla para variables de entorno
├── .gitignore         # Archivos a ignorar por git
├── instance/          # Directorio de instancia para la base de datos
├── emails/            # Directorio para guardar correos en modo desarrollo
├── API_DOCUMENTATION.md # Documentación de la API
├── DEVELOPER_GUIDE.md  # Esta guía para desarrolladores
└── templates/         # Plantillas HTML
    └── index.html     # Página principal
```

### Componentes Principales

- **app.py**: Contiene toda la lógica de la aplicación, incluyendo:
  - Configuración de Flask y extensiones
  - Modelo de datos (clase `Booking`)
  - Funciones de utilidad (generación de PNR, tokens de acceso)
  - Rutas de la aplicación web
  - Endpoints API
  - Lógica de búsqueda y reserva de vuelos

- **templates/index.html**: Interfaz de usuario principal con:
  - Formulario de búsqueda
  - Visualización de resultados
  - Formulario de datos de pasajeros
  - Modal de confirmación de reserva
  - Funcionalidad de autocompletado de aeropuertos

---

## Flujo de Datos

### Búsqueda de Vuelos

1. El usuario ingresa parámetros de búsqueda (origen, destino, fechas, pasajeros)
2. La aplicación obtiene un token de acceso de Amadeus API
3. Se realiza una solicitud a la API de Flight Offers Search
4. Los resultados se procesan y se muestran al usuario
5. El usuario puede seleccionar una tarifa para continuar

### Proceso de Reserva

1. El usuario selecciona una tarifa y completa el formulario de pasajeros
2. La aplicación formatea los datos según los requisitos de Amadeus
3. Se realiza una solicitud a la API de Flight Create Orders
4. Se genera un PNR y se almacena la reserva en la base de datos local
5. Se muestra la confirmación al usuario

### Consulta de Reservas

1. El usuario ingresa un código PNR
2. La aplicación busca la reserva en la base de datos local
3. Se muestran los detalles de la reserva al usuario
4. El usuario puede imprimir la confirmación o enviarla por email

---

## Integración con Amadeus API

El proyecto utiliza las siguientes APIs de Amadeus:

### 1. Flight Offers Search

- **Endpoint**: `https://test.api.amadeus.com/v2/shopping/flight-offers`
- **Método**: GET
- **Función**: `search_flights()`
- **Parámetros principales**:
  - `originLocationCode`: Código IATA del aeropuerto de origen
  - `destinationLocationCode`: Código IATA del aeropuerto de destino
  - `departureDate`: Fecha de salida
  - `returnDate`: Fecha de regreso (opcional)
  - `adults`: Número de adultos
  - `children`: Número de niños
  - `infants`: Número de infantes

### 2. Airport & City Search

- **Endpoint**: `https://test.api.amadeus.com/v1/reference-data/locations`
- **Método**: GET
- **Función**: `search_airports()`
- **Parámetros principales**:
  - `keyword`: Texto para buscar aeropuertos/ciudades
  - `subType`: Tipos de ubicaciones a buscar

### 3. Flight Create Orders

- **Endpoint**: `https://test.api.amadeus.com/v1/booking/flight-orders`
- **Método**: POST
- **Función**: `create_amadeus_booking()`
- **Parámetros principales**:
  - `flight_offer`: Oferta de vuelo seleccionada
  - `passenger_data`: Datos de los pasajeros
  - `contact_info`: Información de contacto

### Manejo de Errores

- La aplicación implementa un sistema de fallback automático para errores específicos
- El error "SEGMENT SELL FAILURE" (código 34651) activa automáticamente el modo de prueba
- En modo de prueba, se simula una respuesta exitosa para continuar con el flujo de reserva

---

## Sistema de Reservas

### Modelo de Datos

La clase `Booking` define la estructura de las reservas:

```python
class Booking(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pnr = db.Column(db.String(6), unique=True, nullable=False)
    flight_id = db.Column(db.String(100), nullable=False)
    fare_type = db.Column(db.String(20), nullable=False)
    fare_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    service_fee = db.Column(db.Float, default=0)
    service_fee_currency = db.Column(db.String(3), default='EUR')
    total_price = db.Column(db.Float, nullable=False)
    contact_email = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    adults = db.Column(db.Integer, default=1)
    children = db.Column(db.Integer, default=0)
    infants = db.Column(db.Integer, default=0)
    passenger_data = db.Column(db.Text, nullable=False)
    amadeus_booking_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='CONFIRMED')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Generación de PNR

Los códigos PNR (Passenger Name Record) se generan con la función `generate_pnr()`:
- 6 caracteres alfanuméricos
- Exclusión de caracteres confusos (I, O, 0, 1)
- Verificación de unicidad en la base de datos

### Flujo de Creación de Reservas

1. El usuario selecciona un vuelo y tarifa
2. Completa el formulario con datos de pasajeros
3. La función `create_booking()` procesa la solicitud
4. Se formatea la oferta de vuelo y los datos de pasajeros
5. Se llama a `create_amadeus_booking()` para crear la reserva en Amadeus
6. Se crea un registro en la base de datos local
7. Se devuelve el PNR y detalles de la reserva

---

## Endpoints API

El sistema proporciona endpoints API para integración con sistemas externos como WhatsApp.

### 1. Búsqueda de Vuelos

**Endpoint**: `/api/search_flights`
**Método**: GET
**Implementación**: Función `api_search_flights()`

```python
@app.route('/api/search_flights', methods=['GET'])
def api_search_flights():
    # Obtener parámetros de la URL
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    departure_date = request.args.get('departure_date')
    return_date = request.args.get('return_date')
    adults = request.args.get('adults', '1')
    children = request.args.get('children', '0')
    infants = request.args.get('infants', '0')
    
    # Validar parámetros obligatorios
    if not all([origin, destination, departure_date]):
        return jsonify({
            'success': False,
            'message': 'Faltan parámetros obligatorios: origin, destination, departure_date'
        }), 400
    
    # Buscar vuelos
    flight_data = search_flights(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
        children=children,
        infants=infants
    )
    
    # Simplificar la respuesta
    simplified_results = []
    # ... (código de procesamiento)
    
    return jsonify({
        'success': True,
        'count': len(simplified_results),
        'results': simplified_results
    })
```

### 2. Consulta de Reservas

**Endpoint**: `/api/find_booking`
**Método**: GET
**Implementación**: Función `api_find_booking()`

```python
@app.route('/api/find_booking', methods=['GET'])
def api_find_booking():
    pnr = request.args.get('pnr')
    
    if not pnr:
        return jsonify({
            'success': False,
            'message': 'Falta el parámetro PNR'
        }), 400
    
    # Buscar la reserva en la base de datos
    booking = Booking.query.filter_by(pnr=pnr.upper()).first()
    
    if not booking:
        return jsonify({
            'success': False,
            'message': 'No se encontró ninguna reserva con ese PNR'
        }), 404
    
    # Convertir datos de pasajeros de JSON a diccionario
    passenger_data = json.loads(booking.passenger_data)
    
    # Crear respuesta con datos de la reserva
    booking_info = {
        'pnr': booking.pnr,
        'status': booking.status,
        # ... (más campos)
    }
    
    return jsonify({
        'success': True,
        'booking': booking_info
    })
```

### 3. Enlaces Directos

**Endpoint**: `/quick_search`
**Método**: GET
**Implementación**: Función `quick_search()`

```python
@app.route('/quick_search')
def quick_search():
    # Obtener parámetros de la URL
    origin = request.args.get('origin', '')
    destination = request.args.get('destination', '')
    departure_date = request.args.get('departure_date', '')
    return_date = request.args.get('return_date', '')
    adults = request.args.get('adults', '1')
    children = request.args.get('children', '0')
    infants = request.args.get('infants', '0')
    
    # Pasar los parámetros a la plantilla
    return render_template(
        'index.html',
        prefill={
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'adults': adults,
            'children': children,
            'infants': infants,
            'auto_search': 'true' if all([origin, destination, departure_date]) else 'false'
        }
    )
```

---

## Integración con WhatsApp

### Arquitectura Recomendada

1. **Sistema de WhatsApp**:
   - Recibe mensajes de los usuarios
   - Extrae parámetros mediante NLP
   - Realiza solicitudes a los endpoints API
   - Formatea y envía respuestas a los usuarios

2. **Servidor de Buscador de Vuelos**:
   - Expone endpoints API para búsqueda y consulta
   - Procesa solicitudes y devuelve resultados en formato JSON
   - Proporciona enlaces directos para continuar en la web

### Implementación de Enlaces Directos

El archivo `index.html` contiene código JavaScript para manejar parámetros prefijados:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Obtener datos prefijados si existen
    {% if prefill %}
    const prefillData = {{ prefill|tojson|safe }};
    
    // Rellenar campos del formulario
    if (prefillData.origin) {
        document.getElementById('origin').value = prefillData.origin;
        document.getElementById('origin_code').value = prefillData.origin;
    }
    
    if (prefillData.destination) {
        document.getElementById('destination').value = prefillData.destination;
        document.getElementById('destination_code').value = prefillData.destination;
    }
    
    // ... (más campos)
    
    // Ejecutar búsqueda automáticamente si se solicita
    if (prefillData.auto_search === 'true') {
        setTimeout(() => {
            document.querySelector('#flightSearchForm button[type="submit"]').click();
        }, 1000);
    }
    {% endif %}
});
```

### Consideraciones Importantes

1. **Campos de Origen y Destino**:
   - El formulario utiliza campos ocultos (`origin_code` y `destination_code`) para los códigos IATA
   - Al prefijar valores, es necesario rellenar tanto los campos visibles como los ocultos

2. **Autocompletado**:
   - La funcionalidad de autocompletado puede interferir con los valores prefijados
   - Se recomienda usar códigos IATA válidos en los enlaces directos

---

## Guía de Contribución

### Flujo de Trabajo

1. **Crear una rama para tu característica**:
   ```bash
   git checkout -b feature/nueva-caracteristica
   ```

2. **Realizar cambios y pruebas**:
   - Seguir las convenciones de código existentes
   - Probar exhaustivamente las nuevas funcionalidades
   - Documentar los cambios realizados

3. **Actualizar el CHANGELOG.md**:
   - Añadir una nueva entrada con el formato adecuado
   - Describir las características añadidas, modificadas o corregidas

4. **Crear un Pull Request**:
   - Describir claramente los cambios realizados
   - Mencionar cualquier dependencia o configuración nueva

### Convenciones de Código

- **Python**: Seguir PEP 8
- **JavaScript**: Usar camelCase para variables y funciones
- **HTML/CSS**: Usar clases descriptivas y mantener la estructura existente
- **Comentarios**: Documentar funciones complejas y decisiones de diseño

### Pruebas

Antes de enviar cambios, probar:
1. Búsqueda de vuelos con diferentes parámetros
2. Proceso completo de reserva
3. Consulta de reservas existentes
4. Endpoints API con herramientas como Postman
5. Enlaces directos con diferentes combinaciones de parámetros

---

Documentación generada el 16 de abril de 2025.
