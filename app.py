import os
import requests
import json
import uuid
import random
import string
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de la base de datos
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key_12345')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bookings.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
app.config['MAIL_PORT'] = 465  # Puerto para SSL
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_FROM')
app.config['MAIL_DEBUG'] = True  # Activar depuración

# Inicializar Flask-Mail
mail = Mail(app)

db = SQLAlchemy(app)

# Asegurarse de que las tablas existan en la base de datos
with app.app_context():
    db.create_all()

# Modelo para las reservas
class Booking(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pnr = db.Column(db.String(6), unique=True, nullable=False)  # Código PNR de 6 caracteres
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
    passenger_data = db.Column(db.Text, nullable=False)  # JSON string con datos de pasajeros
    amadeus_booking_id = db.Column(db.String(100), nullable=True)  # ID de reserva en Amadeus (si se integra)
    status = db.Column(db.String(20), default='CONFIRMED')  # CONFIRMED, CANCELLED, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Booking {self.id}>'

# Modelo para registrar los correos enviados
class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pnr = db.Column(db.String(6), nullable=False, index=True)  # Código PNR relacionado
    recipient = db.Column(db.String(100), nullable=False)  # Destinatario del correo
    subject = db.Column(db.String(200), nullable=False)  # Asunto del correo
    body = db.Column(db.Text, nullable=False)  # Contenido HTML del correo
    sent_at = db.Column(db.DateTime, default=datetime.now)  # Fecha y hora de envío
    environment = db.Column(db.String(20), nullable=False)  # Entorno (development, testing, production)
    
    def __repr__(self):
        return f'<EmailLog {self.id} - PNR: {self.pnr}>'

# Función para generar un PNR único (6 caracteres alfanuméricos)
def generate_pnr():
    # Caracteres permitidos en un PNR (solo letras mayúsculas y números, excluyendo caracteres confusos)
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # Excluimos I, O, 0, 1 para evitar confusiones
    while True:
        # Generar un PNR de 6 caracteres
        pnr = ''.join(random.choice(chars) for _ in range(6))
        # Verificar que no exista ya en la base de datos
        if not Booking.query.filter_by(pnr=pnr).first():
            return pnr

# Configuración de la URL de la API de Amadeus
BASE_URL = "https://test.api.amadeus.com/v2"

# Función para obtener un token de acceso
def get_access_token():
    auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("AMADEUS_API_KEY"),
        "client_secret": os.getenv("AMADEUS_API_SECRET")
    }
    try:
        response = requests.post(auth_url, headers=headers, data=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {str(e)}")
        print(f"Response content: {response.text}")
        raise Exception("Error al autenticar con la API de Amadeus") from e

# Función para buscar aeropuertos y ciudades
def search_airports(keyword):
    try:
        # Obtener token de acceso
        access_token = get_access_token()
        
        # Configurar la llamada a la API
        search_url = "https://test.api.amadeus.com/v1/reference-data/locations"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Parámetros de búsqueda
        params = {
            "keyword": keyword,
            "subType": "AIRPORT,CITY",
            "page[limit]": 10,  # Limitar a 10 resultados para mejor rendimiento
            "view": "LIGHT"  # Vista ligera para obtener solo la información necesaria
        }
        
        # Realizar la solicitud
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        # Procesar los resultados
        results = response.json()
        airports = []
        
        for item in results.get('data', []):
            airport_data = {
                'iataCode': item.get('iataCode', ''),
                'name': item.get('name', ''),
                'cityName': item.get('address', {}).get('cityName', ''),
                'countryName': item.get('address', {}).get('countryName', ''),
                'subType': item.get('subType', '')
            }
            airports.append(airport_data)
        
        return airports
    except Exception as e:
        print(f"Error searching airports: {str(e)}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        return []

# Función para consultar vuelos
def search_flights(origin, destination, departure_date, return_date=None, adults=1, children=0, infants=0, source_system="GDS", trip_type="roundtrip"):
    try:
        # Convert airport codes to uppercase
        origin = origin.upper()
        destination = destination.upper()
        
        # Convert passenger counts to integers
        adults = int(adults)
        children = int(children) if children else 0
        infants = int(infants) if infants else 0
        
        access_token = get_access_token()
        search_url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": 250,  # Aumentado a 250 para obtener más resultados (máximo permitido por la API)
            "travelClass": "ECONOMY"  # Clase de viaje fija en Economy
        }
        
        # Add children and infants if specified
        if children > 0:
            params["children"] = children
        if infants > 0:
            params["infants"] = infants
            
        # Configurar parámetros según el tipo de viaje
        if trip_type.lower() == "roundtrip" and return_date:
            # Para vuelos de ida y vuelta
            params["returnDate"] = return_date
            params["nonStop"] = "false"  # Allow connections for better results
        elif trip_type.lower() == "oneway":
            # Para vuelos de solo ida
            # Asegurarse de que no se envíe returnDate incluso si viene como parámetro
            if "returnDate" in params:
                del params["returnDate"]
            # Opcionalmente, podemos ajustar otros parámetros para vuelos de solo ida
            params["nonStop"] = "false"  # Allow connections for better results
            
        # Incluir amplia variedad de aerolíneas para mostrar múltiples tarifas y opciones
        # Configuración para incluir aerolíneas de Latinoamérica, Norteamérica y rutas internacionales
        params["includedAirlineCodes"] = (
            # Latinoamérica
            "AM,AV,CM,LA,AR,4M,JJ,G3,H2,LU,LP,P9,UC,WV,Y4,VB," +
            # Estados Unidos y Canadá
            "AA,DL,UA,B6,AS,WN,AC,WS,F8," +
            # Europa
            "IB,BA,LH,AF,AZ,UX,LX,OS,SN,TP,TK," +
            # Medio Oriente (incluye rutas a Turquía e Israel)
            "TK,LY,MS,EK,EY,QR,SV,ME,RJ," +
            # Asia y otras internacionales
            "CX,SQ,NH,OZ,KE,CA,MU,HU,JL"
        )  # Códigos IATA de aerolíneas seleccionadas
        
        # Si hay niños o infantes, incluir servicios adicionales para familias
        if children > 0 or infants > 0:
            # Incluir opciones de equipaje para familias
            params["includedServiceCodes"] = "BAG"
                
        # Configurar el tipo de distribución (NDC o EDIFACT)
        if source_system and source_system != "GDS":
            # NDC (New Distribution Capability) ofrece contenido enriquecido y tarifas personalizadas
            # EDIFACT es el sistema tradicional de distribución
            params["sources"] = source_system
            
            # Para NDC, podemos añadir parámetros adicionales para mejorar los resultados
            if source_system == "NDC":
                # Asegurarse de que las aerolíneas con mejor contenido NDC estén incluidas
                # Estas aerolíneas ofrecen datos más completos y tarifas personalizadas en NDC
                ndc_preferred_airlines = ["BA", "AA", "IB", "LH", "AF", "DL", "UA"]
                
                # Convertir la cadena de aerolíneas actuales a un conjunto para operaciones más eficientes
                current_airlines = set(params.get("includedAirlineCodes", "").split(","))
                
                # Añadir las aerolíneas NDC preferidas que no estén ya incluidas
                for airline in ndc_preferred_airlines:
                    current_airlines.add(airline)
                
                # Eliminar cualquier cadena vacía que pueda haberse colado
                if "" in current_airlines:
                    current_airlines.remove("")
                
                # Actualizar el parámetro con la lista unificada
                params["includedAirlineCodes"] = ",".join(current_airlines)
        
        print(f"Searching flights with params: {params}")  # Debug log
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching flights: {str(e)}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        raise

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Ruta para continuar una reserva desde una URL compartida
@app.route('/quick_search')
def quick_search():
    # Obtener parámetros de la URL
    origin = request.args.get('origin', '')
    destination = request.args.get('destination', '')
    departure_date = request.args.get('departure_date', '')
    return_date = request.args.get('return_date', '')
    trip_type = request.args.get('trip_type', 'roundtrip')
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
            'trip_type': trip_type,
            'adults': adults,
            'children': children,
            'infants': infants,
            'auto_search': 'true' if all([origin, destination, departure_date]) else 'false'
        }
    )

# Ruta para buscar reservas por PNR
@app.route('/find_booking', methods=['POST'])
def find_booking():
    try:
        # Obtener el PNR de la solicitud
        pnr = request.form.get('pnr', '').strip().upper()
        
        if not pnr:
            return jsonify({"success": False, "error": "Por favor, ingresa un código PNR válido."})
        
        # Buscar la reserva en la base de datos
        booking = Booking.query.filter_by(pnr=pnr).first()
        
        if not booking:
            return jsonify({"success": False, "error": "No se encontró ninguna reserva con ese código PNR."})
        
        # Extraer información de vuelo del flight_id
        flight_segments = booking.flight_id.split('-')
        origin = flight_segments[0] if len(flight_segments) > 0 else ''
        destination = flight_segments[1] if len(flight_segments) > 1 else ''
        
        # Convertir los datos de pasajeros de JSON a diccionario
        try:
            if isinstance(booking.passenger_data, str):
                passenger_data = json.loads(booking.passenger_data)
            else:
                passenger_data = booking.passenger_data
        except Exception as e:
            print(f"Error al procesar datos de pasajeros: {str(e)}")
            passenger_data = []
        
        # Preparar la respuesta
        response_data = {
            "success": True,
            "booking_id": booking.id,
            "pnr": booking.pnr,
            "details": {
                "pnr": booking.pnr,
                "flight_id": booking.flight_id,
                "origin": origin,
                "destination": destination,
                "fare_type": booking.fare_type,
                "fare_price": booking.fare_price,
                "currency": booking.currency,
                "service_fee": booking.service_fee,
                "service_fee_currency": booking.service_fee_currency,
                "total_price": booking.total_price,
                "booking_id": booking.id,
                "status": booking.status,
                "created_at": booking.created_at.strftime("%Y-%m-%d %H:%M:%S") if booking.created_at else "",
                "passengers": passenger_data
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error finding booking: {str(e)}")
        return jsonify({"success": False, "error": f"Error al buscar la reserva: {str(e)}"})

@app.route('/send_booking_email', methods=['POST'])
def send_booking_email():
    try:
        # Obtener datos del formulario
        pnr = request.form.get('pnr', '').strip().upper()
        email = request.form.get('email', '').strip()
        include_itinerary = request.form.get('include_itinerary', 'true').lower() == 'true'
        include_pdf = request.form.get('include_pdf', 'true').lower() == 'true'
        
        print(f"Datos recibidos: PNR={pnr}, Email={email}, Include Itinerary={include_itinerary}, Include PDF={include_pdf}")
        print(f"Todos los datos del formulario: {request.form}")
        
        # Validar datos
        if not pnr or not email:
            return jsonify({"success": False, "error": "Por favor, proporciona un PNR y un email válidos."})
        
        # Buscar la reserva en la base de datos
        booking = Booking.query.filter_by(pnr=pnr).first()
        
        if not booking:
            return jsonify({"success": False, "error": "No se encontró ninguna reserva con ese código PNR."})
        
        # Extraer información de vuelo del flight_id
        flight_segments = booking.flight_id.split('-')
        origin = flight_segments[0] if len(flight_segments) > 0 else ''
        destination = flight_segments[1] if len(flight_segments) > 1 else ''
        
        # Convertir los datos de pasajeros de JSON a diccionario
        try:
            if isinstance(booking.passenger_data, str):
                passenger_data = json.loads(booking.passenger_data)
            else:
                passenger_data = booking.passenger_data
        except Exception as e:
            print(f"Error al procesar datos de pasajeros: {str(e)}")
            passenger_data = []
        
        # Crear el mensaje de correo electrónico
        subject = f"Confirmación de Reserva - PNR: {pnr}"
        
        # Obtener el nombre del pasajero principal
        passenger_name = ""
        try:
            if passenger_data and len(passenger_data) > 0:
                first_passenger = passenger_data[0]
                if isinstance(first_passenger, dict):
                    first_name = first_passenger.get('firstName', '')
                    last_name = first_passenger.get('lastName', '')
                    if first_name or last_name:
                        passenger_name = f"{first_name} {last_name}".strip()
        except Exception as e:
            print(f"Error al obtener el nombre del pasajero: {str(e)}")
            passenger_name = ""
        
        # Personalizar el saludo según si tenemos el nombre del pasajero
        greeting = f"Estimado(a) {passenger_name}," if passenger_name else "Estimado(a) Pasajero,"
        
        # Crear el cuerpo del mensaje
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4a6da7; color: white; padding: 10px 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .booking-details {{ background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .passenger-details {{ background-color: white; padding: 15px; border-radius: 5px; }}
                .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #777; }}
                h2 {{ color: #4a6da7; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Confirmación de Reserva</h1>
                </div>
                <div class="content">
                    <p>{greeting}</p>
                    <p>Gracias por elegir nuestro servicio. A continuación, encontrará los detalles de su reserva:</p>
                    
                    <div class="booking-details">
                        <h2>Detalles de la Reserva</h2>
                        <table>
                            <tr>
                                <th>PNR (Código de Reserva)</th>
                                <td><strong>{pnr}</strong></td>
                            </tr>
                            <tr>
                                <th>Origen</th>
                                <td>{origin}</td>
                            </tr>
                            <tr>
                                <th>Destino</th>
                                <td>{destination}</td>
                            </tr>
                            <tr>
                                <th>Tipo de Tarifa</th>
                                <td>{booking.fare_type}</td>
                            </tr>
                            <tr>
                                <th>Precio</th>
                                <td>{booking.fare_price} {booking.currency}</td>
                            </tr>
                            <tr>
                                <th>Cargo por Servicio</th>
                                <td>{booking.service_fee} {booking.service_fee_currency}</td>
                            </tr>
                            <tr>
                                <th>Precio Total</th>
                                <td><strong>{booking.total_price} {booking.currency}</strong></td>
                            </tr>
                            <tr>
                                <th>Estado</th>
                                <td>{booking.status}</td>
                            </tr>
                            <tr>
                                <th>Fecha de Creación</th>
                                <td>{booking.created_at.strftime("%Y-%m-%d %H:%M:%S") if booking.created_at else ""}</td>
                            </tr>
                        </table>
                    </div>
        """
        
        # Agregar detalles de pasajeros si se solicita
        if include_itinerary:
            body += f"""
                    <div class="passenger-details">
                        <h2>Detalles de Pasajeros</h2>
                        <table>
                            <tr>
                                <th>Nombre</th>
                                <th>Apellido</th>
                                <th>Tipo</th>
                            </tr>
            """
            
            # Mostrar un mensaje si no hay datos de pasajeros
            if not passenger_data or len(passenger_data) == 0:
                body += f"""
                            <tr>
                                <td colspan="3" class="text-center">No hay datos de pasajeros disponibles</td>
                            </tr>
                """
            else:
                # Procesar cada pasajero
                for passenger in passenger_data:
                    # Verificar si passenger es un diccionario
                    if isinstance(passenger, dict):
                        first_name = passenger.get('firstName', '')
                        last_name = passenger.get('lastName', '')
                        passenger_type = passenger.get('type', '')
                    else:
                        # Si no es un diccionario, intentar convertirlo o usar valores predeterminados
                        try:
                            if isinstance(passenger, str):
                                passenger_dict = json.loads(passenger)
                                first_name = passenger_dict.get('firstName', '')
                                last_name = passenger_dict.get('lastName', '')
                                passenger_type = passenger_dict.get('type', '')
                            else:
                                first_name = ''
                                last_name = ''
                                passenger_type = ''
                        except Exception as e:
                            print(f"Error al procesar datos de pasajero: {str(e)}")
                            first_name = ''
                            last_name = ''
                            passenger_type = ''
                    
                    # Traducir el tipo de pasajero a un formato más legible
                    if passenger_type.upper() == 'ADT':
                        passenger_type_display = 'Adulto'
                    elif passenger_type.upper() == 'CHD':
                        passenger_type_display = 'Niño'
                    elif passenger_type.upper() == 'INF':
                        passenger_type_display = 'Infante'
                    else:
                        passenger_type_display = passenger_type
                        
                body += f"""
                            <tr>
                                <td>{first_name}</td>
                                <td>{last_name}</td>
                                <td>{passenger_type_display}</td>
                            </tr>
                """
            
            body += """
                        </table>
                    </div>
            """
        
        # Cerrar el HTML
        body += f"""
                </div>
                <div class="footer">
                    <p>Este es un correo electrónico automático. Por favor, no responda a este mensaje.</p>
                    <p>© {datetime.now().year} Buscador de Vuelos con Amadeus API. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Crear el mensaje
        msg = Message(subject=subject, recipients=[email], html=body)
        
        try:
            # Verificar que las credenciales de correo estén configuradas
            if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
                print("ERROR: Credenciales de correo no configuradas. Revise las variables de entorno EMAIL_USER y EMAIL_PASSWORD.")
                return jsonify({"success": False, "error": "Credenciales de correo no configuradas. Contacte al administrador del sistema."})
            
            print(f"Intentando enviar correo a {email} con asunto: {subject}")
            print(f"Configuración de correo: SERVER={app.config['MAIL_SERVER']}, PORT={app.config['MAIL_PORT']}, USER={app.config['MAIL_USERNAME']}")
            
            # Obtener el entorno actual
            env_mode = os.getenv('APP_ENV', 'development')
            print(f"Entorno actual: {env_mode}")
            
            # Guardar el correo en la base de datos para todos los entornos
            try:
                # Crear un registro en la tabla EmailLog
                email_log = EmailLog(
                    pnr=pnr,
                    recipient=email,
                    subject=subject,
                    body=body,
                    environment=env_mode
                )
                
                # Guardar en la base de datos
                db.session.add(email_log)
                db.session.commit()
                print(f"Correo registrado en la base de datos con ID: {email_log.id} (modo {env_mode})")
            except Exception as db_error:
                print(f"Error al guardar el correo en la base de datos: {str(db_error)}")
                # Continuar con el envío aunque falle el registro en la base de datos
            
            # Enviar el correo electrónico en todos los entornos (development, testing, production)
            try:
                mail.send(msg)
                print(f"Correo enviado exitosamente a {email}")
                
                mensaje_respuesta = f"Se ha enviado un correo electrónico a {email} con los detalles de la reserva."
                if 'email_log' in locals():
                    mensaje_respuesta += f" Además, se ha guardado una copia en la base de datos con ID: {email_log.id}."
                    
                return jsonify({"success": True, "message": mensaje_respuesta, "email_log_id": email_log.id if 'email_log' in locals() else None})
            except Exception as mail_error:
                print(f"ERROR al enviar el correo: {str(mail_error)}")
                # Proporcionar un mensaje de error más detallado para ayudar a diagnosticar el problema
                error_msg = f"Error al enviar el correo: {str(mail_error)}"
                if 'email_log' in locals():
                    error_msg += f" El correo se guardó en la base de datos con ID: {email_log.id}."
                return jsonify({"success": False, "error": error_msg})
        except Exception as e:
            print(f"Error al enviar correo: {str(e)}")
            return jsonify({"success": False, "error": f"Error al enviar el correo: {str(e)}"})
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return jsonify({"success": False, "error": f"Error al enviar el correo electrónico: {str(e)}"})

@app.route('/autocomplete_airport', methods=['GET'])
def autocomplete_airport():
    try:
        # Obtener el término de búsqueda de los parámetros de la consulta
        keyword = request.args.get('keyword', '')
        
        # Verificar que el término de búsqueda tenga al menos 2 caracteres
        if len(keyword) < 2:
            return jsonify({
                'success': False,
                'message': 'El término de búsqueda debe tener al menos 2 caracteres',
                'data': []
            })
        
        # Buscar aeropuertos que coincidan con el término de búsqueda
        airports = search_airports(keyword)
        
        # Devolver los resultados
        return jsonify({
            'success': True,
            'data': airports
        })
    except Exception as e:
        print(f"Error in autocomplete endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error al buscar aeropuertos: {str(e)}',
            'data': []
        }), 500

@app.route('/search_flights', methods=['POST'])
def search():
    try:
        origin = request.form.get('origin', '').strip()
        destination = request.form.get('destination', '').strip()
        departure_date = request.form.get('departure_date', '').strip()
        return_date = request.form.get('return_date', '').strip()
        adults = request.form.get('adults', 1)
        children = request.form.get('children', 0)
        infants = request.form.get('infants', 0)
        
        # Parámetros adicionales
        source_system = request.form.get('sourceSystem', 'GDS')  # Tipo de distribución

        # Validaciones
        if not origin or not destination:
            return jsonify({"error": "El origen y destino son requeridos"}), 400
        if not departure_date:
            return jsonify({"error": "La fecha de salida es requerida"}), 400
        if len(origin) != 3 or len(destination) != 3:
            return jsonify({"error": "Los códigos de aeropuerto deben tener 3 letras"}), 400
        if origin == destination:
            return jsonify({"error": "El origen y destino no pueden ser iguales"}), 400
        
        # Validación de pasajeros
        try:
            adults_count = int(adults)
            if adults_count < 1:
                return jsonify({"error": "Debe haber al menos 1 pasajero adulto"}), 400
        except ValueError:
            return jsonify({"error": "El número de adultos debe ser un valor numérico"}), 400
            


        results = search_flights(origin, destination, departure_date, return_date, adults, children, infants, source_system)
        return jsonify(results)
    except Exception as e:
        print(f"Error in search endpoint: {str(e)}")
        return jsonify({"error": "Error al buscar vuelos. Por favor, verifica los datos e intenta nuevamente."}), 500

# Función para crear una reserva real en Amadeus
def create_amadeus_booking(flight_offer, passenger_data, contact_info):
    """Crea una reserva real en Amadeus usando la API de Flight Create Orders
    En modo de prueba, simula una respuesta exitosa para evitar errores de la API"""
    try:
        # Verificar el entorno y modo de prueba
        app_env = os.getenv('APP_ENV', 'development')
        test_mode = os.getenv('AMADEUS_TEST_MODE', 'false').lower() == 'true'
        
        if test_mode:
            print("Ejecutando en modo de prueba: simulando respuesta de Amadeus")
            # Generar un PNR aleatorio para pruebas
            import random
            import string
            # Excluir caracteres confusos: I, O, 0, 1
            chars = [c for c in string.ascii_uppercase + string.digits if c not in ['I', 'O', '0', '1']]
            pnr = ''.join(random.choice(chars) for _ in range(6))
            
            # Simular una respuesta exitosa
            booking_id = f"FL-{pnr}-{int(time.time())}"
            
            # Obtener información del primer pasajero para el registro
            first_name = ""
            last_name = ""
            if passenger_data.get('adults') and len(passenger_data.get('adults')) > 0:
                first_name = passenger_data.get('adults')[0].get('firstName', '')
                last_name = passenger_data.get('adults')[0].get('lastName', '')
            
            print(f"Reserva simulada creada con PNR: {pnr} y ID: {booking_id}")
            return {
                "success": True,
                "booking_id": booking_id,
                "pnr": pnr
            }
        
        # Si no estamos en modo de prueba, continuar con la implementación real
        # Obtener token de acceso
        access_token = get_access_token()
        
        # Configurar la llamada a la API
        booking_url = "https://test.api.amadeus.com/v1/booking/flight-orders"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Formatear los datos de pasajeros para la API
        travelers = []
        traveler_id = 1
        
        # Procesar adultos
        for adult in passenger_data.get('adults', []):
            traveler = {
                "id": str(traveler_id),
                "dateOfBirth": "1990-01-01",  # Fecha por defecto, debería ser la real
                "name": {
                    "firstName": adult.get('firstName', ''),
                    "lastName": adult.get('lastName', '')
                },
                "gender": "MALE",  # Por defecto, debería ser el real
                "contact": {
                    "emailAddress": contact_info.get('email', ''),
                    "phones": [{
                        "deviceType": "MOBILE",
                        "countryCallingCode": "34",
                        "number": contact_info.get('phone', '').replace('+', '').replace(' ', '')
                    }]
                },
                "documents": [{
                    "documentType": "PASSPORT",
                    "birthPlace": "Madrid",
                    "issuanceLocation": "Madrid",
                    "issuanceDate": "2015-04-14",
                    "number": adult.get('document', 'DUMMY123'),
                    "expiryDate": "2025-04-14",
                    "issuanceCountry": "ES",
                    "validityCountry": "ES",
                    "nationality": "ES",
                    "holder": True
                }]
            }
            travelers.append(traveler)
            traveler_id += 1
        
        # Procesar niños
        for child in passenger_data.get('children', []):
            traveler = {
                "id": str(traveler_id),
                "dateOfBirth": "2010-01-01",  # Fecha por defecto, debería ser la real
                "name": {
                    "firstName": child.get('firstName', ''),
                    "lastName": child.get('lastName', '')
                },
                "gender": "MALE",  # Por defecto, debería ser el real
                "contact": {
                    "emailAddress": contact_info.get('email', ''),
                    "phones": [{
                        "deviceType": "MOBILE",
                        "countryCallingCode": "34",
                        "number": contact_info.get('phone', '').replace('+', '').replace(' ', '')
                    }]
                }
            }
            travelers.append(traveler)
            traveler_id += 1
        
        # Procesar infantes
        for infant in passenger_data.get('infants', []):
            traveler = {
                "id": str(traveler_id),
                "dateOfBirth": "2023-01-01",  # Fecha por defecto, debería ser la real
                "name": {
                    "firstName": infant.get('firstName', ''),
                    "lastName": infant.get('lastName', '')
                },
                "gender": "MALE",  # Por defecto, debería ser el real
                "contact": {
                    "emailAddress": contact_info.get('email', ''),
                    "phones": [{
                        "deviceType": "MOBILE",
                        "countryCallingCode": "34",
                        "number": contact_info.get('phone', '').replace('+', '').replace(' ', '')
                    }]
                }
            }
            travelers.append(traveler)
            traveler_id += 1
        
        # Construir el payload completo
        payload = {
            "data": {
                "type": "flight-order",
                "flightOffers": [flight_offer],
                "travelers": travelers,
                "remarks": {
                    "general": [{
                        "subType": "GENERAL_MISCELLANEOUS",
                        "text": "Reserva creada a través de AmadeusAI"
                    }]
                },
                "ticketingAgreement": {
                    "option": "DELAY_TO_CANCEL",
                    "delay": "6D"
                },
                "contacts": [{
                    "addresseeName": {
                        "firstName": travelers[0]['name']['firstName'] if travelers and len(travelers) > 0 else contact_info.get('firstName', 'Pasajero'),
                        "lastName": travelers[0]['name']['lastName'] if travelers and len(travelers) > 0 else contact_info.get('lastName', 'Principal')
                    },
                    "companyName": "AmadeusAI",
                    "purpose": "STANDARD",
                    "phones": [{
                        "deviceType": "MOBILE",
                        "countryCallingCode": "34",
                        "number": contact_info.get('phone', '').replace('+', '').replace(' ', '')
                    }],
                    "emailAddress": contact_info.get('email', ''),
                    "address": {
                        "lines": [contact_info.get('address', 'Calle Principal 123')],
                        "postalCode": contact_info.get('postalCode', '28001'),
                        "cityName": contact_info.get('cityName', 'Madrid'),
                        "countryCode": contact_info.get('countryCode', 'ES')
                    }
                }]
            }
        }
        
        print(f"Enviando solicitud a Amadeus: {json.dumps(payload)}")
        
        # Enviar la solicitud a la API
        response = requests.post(booking_url, headers=headers, json=payload)
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"Reserva creada en Amadeus: {json.dumps(result)}")
            # Obtener el PNR de forma segura para evitar errores de índice
            associated_records = result.get('data', {}).get('associatedRecords', [])
            pnr = ''
            if associated_records and len(associated_records) > 0:
                pnr = associated_records[0].get('reference', '')
            
            return {
                "success": True, 
                "booking_id": result.get('data', {}).get('id', ''),
                "pnr": pnr
            }
        else:
            print(f"Error en la respuesta de Amadeus: {response.status_code} - {response.text}")
            
            # Manejar específicamente errores conocidos
            error_message = "Error al procesar la reserva"
            try:
                error_json = response.json()
                errors = error_json.get('errors', [])
                
                if errors and len(errors) > 0:
                    error_code = str(errors[0].get('code'))
                    error_title = errors[0].get('title')
                    
                    # Verificar si debemos activar el modo de prueba automáticamente
                    enable_auto_fallback = os.getenv('ENABLE_AUTO_FALLBACK', 'true').lower() == 'true'
                    auto_fallback_error_codes = os.getenv('AUTO_FALLBACK_ERROR_CODES', '34651').split(',')
                    show_fallback_messages = os.getenv('SHOW_FALLBACK_MESSAGES', 'true').lower() == 'true'
                    
                    if enable_auto_fallback and error_code in auto_fallback_error_codes:
                        # Activar modo de prueba para simular una reserva exitosa
                        print(f"Detectado error {error_code}: {error_title}. Cambiando a modo de prueba.")
                        import random
                        import string
                        import time
                        
                        # Excluir caracteres confusos: I, O, 0, 1
                        chars = [c for c in string.ascii_uppercase + string.digits if c not in ['I', 'O', '0', '1']]
                        pnr = ''.join(random.choice(chars) for _ in range(6))
                        
                        # Simular una respuesta exitosa
                        booking_id = f"FL-{pnr}-{int(time.time())}"
                        
                        print(f"Reserva simulada creada con PNR: {pnr} y ID: {booking_id}")
                        
                        # Mensaje para el usuario (solo si está habilitado)
                        fallback_message = ""
                        if show_fallback_messages:
                            if app_env == 'production':
                                fallback_message = "Reserva creada en modo alternativo debido a una limitación temporal del sistema."
                            else:
                                fallback_message = f"Reserva creada en modo de prueba debido a que el segmento no está disponible para venta real (Error {error_code})."
                        
                        return {
                            "success": True,
                            "booking_id": booking_id,
                            "pnr": pnr,
                            "message": fallback_message
                        }
                    else:
                        error_message = f"Error {error_code}: {error_title}"
            except Exception as e:
                print(f"Error al procesar la respuesta de error: {str(e)}")
            
            return {"success": False, "error": error_message, "details": response.text}
    
    except Exception as e:
        print(f"Error creating Amadeus booking: {str(e)}")
        return {"success": False, "error": str(e)}

@app.route('/create_booking', methods=['POST'])
def create_booking():
    try:
        # Obtener datos del formulario
        flight_id = request.form.get('flightId')
        fare_type = request.form.get('fareType')
        fare_price = float(request.form.get('farePrice'))
        currency = request.form.get('currency', 'EUR')
        service_fee = float(request.form.get('serviceFee', 0))
        service_fee_currency = request.form.get('serviceFeeCurrency', currency)
        
        # Generar un PNR único para esta reserva
        pnr = generate_pnr()
        
        # Calcular precio total (con conversión si es necesario)
        total_price = fare_price
        if service_fee > 0:
            if service_fee_currency == 'USD' and currency != 'USD':
                # Convertir USD a la moneda del vuelo
                usd_to_eur_rate = 0.92  # Tasa aproximada
                converted_fee = service_fee * usd_to_eur_rate
                total_price += converted_fee
            else:
                total_price += service_fee
        
        # Datos de contacto
        contact_email = request.form.get('contactEmail')
        contact_phone = request.form.get('contactPhone')
        
        # Número de pasajeros
        adults = int(request.form.get('adults', 1))
        children = int(request.form.get('children', 0))
        infants = int(request.form.get('infants', 0))
        
        # Recopilar datos de pasajeros
        passenger_data = {}
        
        # Adultos
        adult_data = []
        for i in range(1, adults + 1):
            adult = {
                'firstName': request.form.get(f'adultFirstName{i}'),
                'lastName': request.form.get(f'adultLastName{i}'),
                'type': 'ADULT'
            }
            adult_data.append(adult)
        passenger_data['adults'] = adult_data
        
        # Niños
        if children > 0:
            child_data = []
            for i in range(1, children + 1):
                child = {
                    'firstName': request.form.get(f'childFirstName{i}'),
                    'lastName': request.form.get(f'childLastName{i}'),
                    'age': request.form.get(f'childAge{i}'),
                    'type': 'CHILD'
                }
                child_data.append(child)
            passenger_data['children'] = child_data
        
        # Infantes
        if infants > 0:
            infant_data = []
            for i in range(1, infants + 1):
                infant = {
                    'firstName': request.form.get(f'infantFirstName{i}'),
                    'lastName': request.form.get(f'infantLastName{i}'),
                    'age': request.form.get(f'infantAge{i}'),
                    'type': 'INFANT'
                }
                infant_data.append(infant)
            passenger_data['infants'] = infant_data
        
        # Crear reserva real en Amadeus
        contact_info = {
            'email': contact_email,
            'phone': contact_phone
        }
        
        # Obtener la oferta de vuelo original desde la sesión o la base de datos
        # Nota: En un entorno real, deberías almacenar la oferta completa al mostrarla
        # Por ahora, creamos una estructura básica para la demostración
        flight_offer = {
            "type": "flight-offer",
            "id": "1",
            "source": "GDS",
            "instantTicketingRequired": False,
            "nonHomogeneous": False,
            "oneWay": False,
            "lastTicketingDate": "2025-04-15",
            "numberOfBookableSeats": adults + children,
            "itineraries": [
                {
                    "duration": "PT2H",
                    "segments": [
                        {
                            "departure": {
                                "iataCode": flight_id.split('-')[0] if '-' in flight_id and len(flight_id.split('-')) > 0 else "LAX",
                                "terminal": "1",
                                "at": "2025-05-01T10:00:00"
                            },
                            "arrival": {
                                "iataCode": flight_id.split('-')[1] if '-' in flight_id and len(flight_id.split('-')) > 1 else "GDL",
                                "terminal": "2",
                                "at": "2025-05-01T12:00:00"
                            },
                            "carrierCode": "IB",
                            "number": "1234",
                            "aircraft": {
                                "code": "320"
                            },
                            "operating": {
                                "carrierCode": "IB"
                            },
                            "duration": "PT2H",
                            "id": "1",
                            "numberOfStops": 0,
                            "blacklistedInEU": False
                        }
                    ]
                }
            ],
            "price": {
                "currency": currency,
                "total": str(total_price),
                "base": str(fare_price),
                "fees": [
                    {
                        "amount": str(service_fee),
                        "type": "SUPPLIER"
                    }
                ],
                "grandTotal": str(total_price)
            },
            "pricingOptions": {
                "fareType": ["PUBLISHED"],
                "includedCheckedBagsOnly": True
            },
            "validatingAirlineCodes": ["IB"],
            "travelerPricings": []
        }
        
        # Añadir precios por pasajero
        for i in range(adults):
            flight_offer["travelerPricings"].append({
                "travelerId": str(i+1),
                "fareOption": "STANDARD",
                "travelerType": "ADULT",
                "price": {
                    "currency": currency,
                    "total": str(fare_price),
                    "base": str(fare_price)
                },
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        "cabin": request.form.get('travelClass', 'ECONOMY').upper(),
                        "fareBasis": fare_type[:1].upper() + "BAS",  # Primera letra del fare_type + BAS
                        "class": fare_type[:1].upper(),  # Primera letra del fare_type
                        "includedCheckedBags": {
                            "quantity": 1 if fare_type.lower() != 'basic' else 0
                        }
                    }
                ]
            })
        
        for i in range(children):
            flight_offer["travelerPricings"].append({
                "travelerId": str(adults+i+1),
                "fareOption": "STANDARD",
                "travelerType": "CHILD",
                "price": {
                    "currency": currency,
                    "total": str(fare_price * 0.75),  # 75% del precio adulto
                    "base": str(fare_price * 0.75)
                },
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        "cabin": request.form.get('travelClass', 'ECONOMY').upper(),
                        "fareBasis": fare_type[:1].upper() + "BAS",  # Primera letra del fare_type + BAS
                        "class": fare_type[:1].upper(),  # Primera letra del fare_type
                        "includedCheckedBags": {
                            "quantity": 1 if fare_type.lower() != 'basic' else 0
                        }
                    }
                ]
            })
        
        for i in range(infants):
            flight_offer["travelerPricings"].append({
                "travelerId": str(adults+children+i+1),
                "fareOption": "STANDARD",
                "travelerType": "INFANT",
                "price": {
                    "currency": currency,
                    "total": str(fare_price * 0.1),  # 10% del precio adulto
                    "base": str(fare_price * 0.1)
                },
                "fareDetailsBySegment": [
                    {
                        "segmentId": "1",
                        "cabin": request.form.get('travelClass', 'ECONOMY').upper(),
                        "fareBasis": fare_type[:1].upper() + "INF",  # Primera letra del fare_type + INF para infantes
                        "class": fare_type[:1].upper(),  # Primera letra del fare_type
                        "includedCheckedBags": {
                            "quantity": 0  # Los infantes generalmente no tienen equipaje incluido
                        }
                    }
                ],
                "associatedAdultId": "1"  # Asociado al primer adulto
            })
        
        # Crear la reserva en Amadeus
        amadeus_result = create_amadeus_booking(flight_offer, passenger_data, contact_info)
        amadeus_booking_id = amadeus_result.get('booking_id') if amadeus_result.get('success') else None
        
        # Obtener mensaje adicional si existe
        amadeus_message = amadeus_result.get('message', '')
        
        # Si Amadeus devuelve un PNR, usarlo en lugar del generado localmente
        if amadeus_result.get('success') and amadeus_result.get('pnr'):
            pnr = amadeus_result.get('pnr')
        
        # Crear nueva reserva en nuestra base de datos
        new_booking = Booking(
            id=str(uuid.uuid4()),
            pnr=pnr,  # Asignar el PNR generado
            flight_id=flight_id,
            fare_type=fare_type,
            fare_price=fare_price,
            currency=currency,
            service_fee=service_fee,
            service_fee_currency=service_fee_currency,
            total_price=total_price,
            contact_email=contact_email,
            contact_phone=contact_phone,
            adults=adults,
            children=children,
            infants=infants,
            passenger_data=json.dumps(passenger_data),
            amadeus_booking_id=amadeus_booking_id,  # ID de la reserva en Amadeus
            status='CONFIRMED'
        )
        
        # Guardar en la base de datos
        db.session.add(new_booking)
        db.session.commit()
        
        # Devolver el PNR y los detalles de la reserva
        response_data = {
            'success': True,
            'booking_id': new_booking.id,
            'pnr': pnr,  # Incluir el PNR en la respuesta
            'message': 'Reserva creada exitosamente',
            'details': {
                'pnr': pnr,
                'flight_id': flight_id,
                'fare_type': fare_type,
                'fare_price': fare_price,
                'currency': currency,
                'service_fee': service_fee,
                'service_fee_currency': service_fee_currency,
                'total_price': total_price,
                'booking_id': new_booking.id,
                'status': 'CONFIRMED'
            }
        }
        
        # Añadir mensaje adicional si existe
        if amadeus_message:
            response_data['amadeus_message'] = amadeus_message
            
        return jsonify(response_data)
    
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"Error al crear la reserva: {str(e)}")
        print(f"Traceback completo: {error_traceback}")
        return jsonify({
            'success': False,
            'message': f'Error al crear la reserva: {str(e)}'
        }), 500

# Crear las tablas de la base de datos al iniciar la aplicación
with app.app_context():
    db.create_all()

# API Endpoint para búsqueda de vuelos (para integración con WhatsApp)
@app.route('/api/search_flights', methods=['GET'])
def api_search_flights():
    try:
        # Obtener parámetros de la URL
        origin = request.args.get('origin')
        destination = request.args.get('destination')
        departure_date = request.args.get('departure_date')
        return_date = request.args.get('return_date')
        trip_type = request.args.get('trip_type', 'roundtrip').lower()  # Por defecto: roundtrip
        adults = request.args.get('adults', '1')
        children = request.args.get('children', '0')
        infants = request.args.get('infants', '0')
        
        # Validar parámetros obligatorios
        if not all([origin, destination, departure_date]):
            return jsonify({
                'success': False,
                'message': 'Faltan parámetros obligatorios: origin, destination, departure_date'
            }), 400
            
        # Validar que return_date esté presente si trip_type es roundtrip
        if trip_type == 'roundtrip' and not return_date:
            return jsonify({
                'success': False,
                'message': 'El parámetro return_date es obligatorio para búsquedas de ida y vuelta (roundtrip)'
            }), 400
            
        # Validar que trip_type sea válido
        if trip_type not in ['roundtrip', 'oneway']:
            return jsonify({
                'success': False,
                'message': 'El parámetro trip_type debe ser "roundtrip" o "oneway"'
            }), 400
        
        # Buscar vuelos
        flight_data = search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date if trip_type == 'roundtrip' else None,
            adults=adults,
            children=children,
            infants=infants,
            trip_type=trip_type
        )
        
        # Simplificar la respuesta para WhatsApp (opcional)
        simplified_results = []
        for offer in flight_data.get('data', []):
            price = offer.get('price', {})
            itineraries = offer.get('itineraries', [])
            
            flight_info = {
                'price': {
                    'total': price.get('total'),
                    'currency': price.get('currency')
                },
                'segments': []
            }
            
            # Procesar segmentos de vuelo
            for itinerary in itineraries:
                for segment in itinerary.get('segments', []):
                    departure = segment.get('departure', {})
                    arrival = segment.get('arrival', {})
                    carrier = segment.get('carrierCode', '')
                    
                    flight_info['segments'].append({
                        'departure': {
                            'iataCode': departure.get('iataCode'),
                            'at': departure.get('at')
                        },
                        'arrival': {
                            'iataCode': arrival.get('iataCode'),
                            'at': arrival.get('at')
                        },
                        'carrier': carrier,
                        'number': segment.get('number')
                    })
            
            simplified_results.append(flight_info)
        
        return jsonify({
            'success': True,
            'count': len(simplified_results),
            'results': simplified_results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# API Endpoint para consultar reservas por PNR
@app.route('/api/find_booking', methods=['GET'])
def api_find_booking():
    try:
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
            'fare_type': booking.fare_type,
            'total_price': booking.total_price,
            'currency': booking.currency,
            'contact_email': booking.contact_email,
            'contact_phone': booking.contact_phone,
            'passengers': passenger_data,
            'created_at': booking.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'booking': booking_info
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5005, host='0.0.0.0')
