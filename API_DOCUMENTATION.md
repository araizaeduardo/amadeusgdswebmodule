# Documentación de API - Buscador de Vuelos con Amadeus

Esta documentación proporciona información detallada sobre las APIs y funcionalidades de integración disponibles en el Buscador de Vuelos con Amadeus.

## Información General

**URL Base de Producción:** `https://vuelos.paseotravel.com`

Todos los endpoints y ejemplos en esta documentación utilizan esta URL base. Para entornos de desarrollo o pruebas, sustituya esta URL por la correspondiente a su entorno local o de staging.

## Índice

1. [Endpoints API](#endpoints-api)
   - [Búsqueda de Vuelos](#búsqueda-de-vuelos)
   - [Consulta de Reservas](#consulta-de-reservas)
2. [Enlaces Directos](#enlaces-directos)
   - [Quick Search](#quick-search)
   - [Parámetros Soportados](#parámetros-soportados)
3. [Integración con WhatsApp](#integración-con-whatsapp)
   - [Ejemplos de Integración](#ejemplos-de-integración)
   - [Flujos de Conversación](#flujos-de-conversación)
4. [Consideraciones Técnicas](#consideraciones-técnicas)
   - [Seguridad](#seguridad)
   - [Rendimiento](#rendimiento)

---

## Endpoints API

El sistema proporciona endpoints API RESTful que permiten a aplicaciones externas (como sistemas de WhatsApp) interactuar con el buscador de vuelos.

### Búsqueda de Vuelos

**Endpoint:** `/api/search_flights`

**Método:** GET

**Parámetros:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| origin | String | Sí | Código IATA del aeropuerto de origen (ej. MEX) |
| destination | String | Sí | Código IATA del aeropuerto de destino (ej. CUN) |
| departure_date | String | Sí | Fecha de salida en formato YYYY-MM-DD |
| return_date | String | Condicional | Fecha de regreso en formato YYYY-MM-DD. **Requerido** si trip_type es "roundtrip", **ignorado** si trip_type es "oneway" |
| trip_type | String | No | Tipo de viaje: "roundtrip" (ida y vuelta) o "oneway" (solo ida). Por defecto: "roundtrip" |
| adults | Integer | No | Número de adultos (por defecto: 1) |
| children | Integer | No | Número de niños (2-17 años) (por defecto: 0) |
| infants | Integer | No | Número de infantes (0-2 años) (por defecto: 0) |

**Ejemplos de solicitud:**

*Búsqueda de ida y vuelta (roundtrip):*
```
GET https://vuelos.paseotravel.com/api/search_flights?origin=MEX&destination=CUN&departure_date=2025-05-15&return_date=2025-05-20&trip_type=roundtrip&adults=2
```

*Búsqueda de solo ida (oneway):*
```
GET https://vuelos.paseotravel.com/api/search_flights?origin=MEX&destination=CUN&departure_date=2025-05-15&trip_type=oneway&adults=2
```

**Ejemplo de respuesta:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "price": {
        "total": "245.30",
        "currency": "EUR"
      },
      "segments": [
        {
          "departure": {
            "iataCode": "MEX",
            "at": "2025-05-15T06:20:00"
          },
          "arrival": {
            "iataCode": "CUN",
            "at": "2025-05-15T09:05:00"
          },
          "carrier": "AM",
          "number": "824"
        },
        {
          "departure": {
            "iataCode": "CUN",
            "at": "2025-05-20T10:15:00"
          },
          "arrival": {
            "iataCode": "MEX",
            "at": "2025-05-20T12:45:00"
          },
          "carrier": "AM",
          "number": "825"
        }
      ]
    },
    {
      "price": {
        "total": "312.75",
        "currency": "EUR"
      },
      "segments": [
        {
          "departure": {
            "iataCode": "MEX",
            "at": "2025-05-15T08:45:00"
          },
          "arrival": {
            "iataCode": "CUN",
            "at": "2025-05-15T11:30:00"
          },
          "carrier": "VB",
          "number": "1120"
        },
        {
          "departure": {
            "iataCode": "CUN",
            "at": "2025-05-20T14:30:00"
          },
          "arrival": {
            "iataCode": "MEX",
            "at": "2025-05-20T17:00:00"
          },
          "carrier": "VB",
          "number": "1121"
        }
      ]
    }
  ]
}
```

### Consulta de Reservas

**Endpoint:** `/api/find_booking`

**Método:** GET

**Parámetros:**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| pnr | String | Sí | Código PNR de la reserva (6 caracteres alfanuméricos) |

**Ejemplo de solicitud:**
```
GET https://vuelos.paseotravel.com/api/find_booking?pnr=ABC123
```

**Ejemplo de respuesta:**
```json
{
  "success": true,
  "booking": {
    "pnr": "ABC123",
    "status": "CONFIRMED",
    "fare_type": "STANDARD",
    "total_price": 490.60,
    "currency": "EUR",
    "contact_email": "cliente@ejemplo.com",
    "contact_phone": "+521234567890",
    "passengers": [
      {
        "firstName": "Juan",
        "lastName": "Pérez",
        "type": "ADULT"
      },
      {
        "firstName": "María",
        "lastName": "Pérez",
        "type": "ADULT"
      }
    ],
    "created_at": "2025-04-15 14:30:45"
  }
}
```

---

## Enlaces Directos

El sistema permite generar enlaces directos que precargan los parámetros de búsqueda en la interfaz web, facilitando a los usuarios continuar su búsqueda desde WhatsApp u otras plataformas.

### Quick Search

**URL Base:** `/quick_search`

Esta ruta permite precargar parámetros de búsqueda en el formulario y opcionalmente ejecutar la búsqueda automáticamente.

### Parámetros Soportados

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| origin | String | No | Código IATA del aeropuerto de origen |
| destination | String | No | Código IATA del aeropuerto de destino |
| departure_date | String | No | Fecha de salida en formato YYYY-MM-DD |
| return_date | String | No | Fecha de regreso en formato YYYY-MM-DD. Ignorado si trip_type es "oneway" |
| trip_type | String | No | Tipo de viaje: "roundtrip" (ida y vuelta) o "oneway" (solo ida). Por defecto: "roundtrip" |
| adults | Integer | No | Número de adultos (por defecto: 1) |
| children | Integer | No | Número de niños (2-17 años) (por defecto: 0) |
| infants | Integer | No | Número de infantes (0-2 años) (por defecto: 0) |
| auto_search | Boolean | No | Si es "true", ejecuta la búsqueda automáticamente al cargar la página |

**Ejemplos de enlaces directos:**

*Búsqueda de ida y vuelta (roundtrip):*
```
https://vuelos.paseotravel.com/quick_search?origin=MEX&destination=CUN&departure_date=2025-05-15&return_date=2025-05-20&trip_type=roundtrip&adults=2&auto_search=true
```

*Búsqueda de solo ida (oneway):*
```
https://vuelos.paseotravel.com/quick_search?origin=MEX&destination=CUN&departure_date=2025-05-15&trip_type=oneway&adults=2&auto_search=true
```

Este enlace precargará los campos del formulario con los valores especificados y ejecutará la búsqueda automáticamente.

---

## Integración con WhatsApp

El sistema está diseñado para integrarse con aplicaciones de mensajería como WhatsApp, permitiendo a los usuarios buscar vuelos y consultar reservas directamente desde la conversación.

### Ejemplos de Integración

#### Búsqueda de Vuelos

1. El usuario envía un mensaje solicitando vuelos: "Buscar vuelos de México a Cancún para el 15 de mayo"
2. El sistema de WhatsApp extrae los parámetros (origen, destino, fecha)
3. Realiza una solicitud a `/api/search_flights` con los parámetros extraídos
4. Procesa la respuesta JSON y envía un mensaje con los resultados
5. Incluye un enlace directo para continuar en la web: `https://vuelos.paseotravel.com/quick_search?origin=MEX&destination=CUN&departure_date=2025-05-15&trip_type=oneway&auto_search=true` (para solo ida) o `https://vuelos.paseotravel.com/quick_search?origin=MEX&destination=CUN&departure_date=2025-05-15&return_date=2025-05-20&trip_type=roundtrip&auto_search=true` (para ida y vuelta)

#### Consulta de Reservas

1. El usuario envía su código PNR: "Consultar reserva ABC123"
2. El sistema de WhatsApp extrae el código PNR
3. Realiza una solicitud a `/api/find_booking?pnr=ABC123`
4. Procesa la respuesta JSON y envía un mensaje con los detalles de la reserva

### Flujos de Conversación

Se recomienda implementar los siguientes flujos de conversación:

1. **Búsqueda Inicial**:
   - Preguntar origen y destino
   - Preguntar fechas
   - Preguntar número de pasajeros
   - Mostrar resultados resumidos (2-3 opciones)
   - Ofrecer enlace para ver más opciones en la web

2. **Consulta de Reserva**:
   - Solicitar código PNR
   - Mostrar detalles básicos de la reserva
   - Ofrecer opciones (enviar por email, modificar, cancelar)

---

## Consideraciones Técnicas

### Seguridad

- **Autenticación**: Para entornos de producción, se recomienda implementar autenticación en los endpoints API (como API keys o tokens JWT)
- **Validación**: Todos los parámetros de entrada son validados, pero se recomienda implementar validación adicional en el sistema de WhatsApp
- **Datos Sensibles**: No exponer información sensible en URLs o respuestas API

### Rendimiento

- **Caché**: Considerar implementar caché para resultados de búsqueda frecuentes
- **Límites de Tasa**: La API de Amadeus tiene límites de tasa. Monitorear el uso para evitar exceder estos límites
- **Optimización de Respuestas**: Las respuestas API están optimizadas para minimizar el tamaño de los datos transferidos

---

## Notas de Implementación

Para implementar la integración con WhatsApp, se recomienda utilizar:

1. **WhatsApp Business API** o **WhatsApp Cloud API** para enviar y recibir mensajes
2. Un servicio de NLP (Procesamiento de Lenguaje Natural) como Dialogflow o LUIS para extraer parámetros de los mensajes
3. Un servidor intermedio que maneje la lógica de negocio entre WhatsApp y el Buscador de Vuelos

---

Documentación generada el 16 de abril de 2025.
