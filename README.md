# Buscador de Vuelos con Amadeus API

Este proyecto es un buscador de vuelos que utiliza la API de Amadeus para buscar vuelos de ida y vuelta. La aplicación está construida con Flask y proporciona una interfaz web moderna y fácil de usar.

## Requisitos Previos

- Python 3.x (Recomendado: 3.10 o 3.11)
- pip (gestor de paquetes de Python)
- Credenciales de API de Amadeus (Test Environment)

## Configuración del Entorno

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd amadeusai
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Linux/Mac
# o
venv\Scripts\activate  # En Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

Nota: Si estás usando Python 3.13, es posible que necesites instalar manualmente algunas dependencias adicionales:
```bash
pip install flask-mail
pip install --upgrade sqlalchemy
```

4. Configurar variables de entorno:
   - Crear un archivo `.env` en la raíz del proyecto basado en `.env.example`
   - Agregar las siguientes variables esenciales:
   ```env
   AMADEUS_API_KEY="tu_api_key_aquí"
   AMADEUS_API_SECRET="tu_api_secret_aquí"
   APP_ENV=development
   DATABASE_URL=sqlite:///bookings.db
   
   # Para el envío de correos (opcional en modo desarrollo)
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_USER=your_email@example.com
   EMAIL_PASSWORD=your_email_password
   EMAIL_USE_TLS=true
   EMAIL_FROM=noreply@example.com
   ```
   Puedes obtener las credenciales de Amadeus registrándote en [Amadeus for Developers](https://developers.amadeus.com/)

## Ejecución

Para ejecutar la aplicación:

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5005`

## Características

- Búsqueda de vuelos de ida y vuelta
- Autocompletado de aeropuertos y ciudades
- Selección de fechas con calendario interactivo
- Visualización de múltiples opciones de tarifas (Básica, Estándar, Familiar)
- Sistema completo de reservas con generación de PNR
- Integración con la API de Amadeus para crear reservas reales
- Formulario para datos de pasajeros (adultos, niños, infantes)
- Envío de correos electrónicos de confirmación
- Consulta de reservas existentes por código PNR
- Cargos de servicio para subagentes
- Interfaz responsiva y moderna
- Manejo inteligente de errores de la API

## Estructura del Proyecto

```
amadeusai/
├── app.py              # Aplicación principal Flask
├── requirements.txt    # Dependencias del proyecto
├── .env               # Variables de entorno (no incluido en git)
├── .env.example       # Plantilla para variables de entorno
├── instance/          # Directorio de instancia para la base de datos
├── emails/            # Directorio para guardar correos en modo desarrollo
└── templates/         # Plantillas HTML
    └── index.html     # Página principal
```

## Modos de Operación

- **Desarrollo**: Los correos se guardan como archivos HTML en la carpeta `emails/`
- **Pruebas**: Simula el comportamiento sin realizar llamadas reales a la API
- **Producción**: Realiza llamadas reales a la API y envía correos electrónicos

## Notas de Seguridad

- Nunca comitear el archivo `.env` al repositorio
- Las credenciales de API están configuradas para el entorno de pruebas
- Para producción, actualizar las URLs de API a las de producción y cambiar `APP_ENV=production`

## Contribuir

1. Fork el repositorio
2. Crear una rama para tu característica (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request
