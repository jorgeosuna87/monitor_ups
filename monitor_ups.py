import requests
from nut2 import PyNUTClient
import os
import time
import logging
import argparse
from typing import Dict, Any

# Configuración
WEBHOOK_URL = "http://example.com/notify"  # Reemplaza con tu URL real
LOW_BATTERY_THRESHOLD = 20
UPS_NAME = "CyberPower850"  # Nombre predeterminado del UPS
CHECK_INTERVAL = 60  # Intervalo de verificación en segundos

# Configurar logging
logging.basicConfig(
    filename='ups_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def notify(message: str) -> None:
    """Envía una notificación al webhook configurado."""
    try:
        response = requests.post(WEBHOOK_URL, json={"message": message})
        if response.status_code == 200:
            logging.info("Notificación enviada exitosamente")
        else:
            logging.error(f"Error al enviar notificación: {response.status_code}")
    except Exception as e:
        logging.error(f"Error al enviar notificación: {e}")

def shutdown_system() -> None:
    """Inicia el apagado del sistema."""
    notify("Apagando el sistema debido a nivel bajo de batería.")
    logging.info("Iniciando apagado del sistema")
    try:
        os.system("sudo shutdown -h now")
    except Exception as e:
        logging.error(f"Fallo al iniciar el apagado: {e}")

def get_ups_vars(client: PyNUTClient, ups_name: str) -> Dict[str, Any]:
    """Obtiene las variables del UPS."""
    try:
        return client.list_vars(ups_name)
    except Exception as e:
        logging.error(f"Error al obtener variables del UPS: {e}")
        return {}

def monitor_ups(ups_name: str) -> None:
    """Monitorea el estado del UPS."""
    client = PyNUTClient()
    
    while True:
        try:
            ups_list = client.list_ups()
            if ups_name not in ups_list:
                logging.error(f"UPS {ups_name} no encontrado. UPS disponibles: {', '.join(ups_list)}")
                return

            ups_vars = get_ups_vars(client, ups_name)
            
            battery_charge = int(ups_vars.get('battery.charge', '0'))
            ups_status = ups_vars.get('ups.status', 'Unknown')
            battery_runtime = int(ups_vars.get('battery.runtime', '0'))

            logging.info(f"Nivel de batería: {battery_charge}%")
            logging.info(f"Estado del UPS: {ups_status}")
            logging.info(f"Tiempo restante de batería: {battery_runtime} segundos")

            if "OL" not in ups_status:
                notify(f"Advertencia: UPS no en línea (Estado: {ups_status})")
                if "OB" in ups_status:
                    notify(f"Corte de energía detectado. Nivel de batería: {battery_charge}%")

            if battery_charge < LOW_BATTERY_THRESHOLD:
                notify(f"Advertencia: Nivel de batería bajo ({battery_charge}%) - Apagando el sistema.")
                shutdown_system()
                break

        except Exception as e:
            logging.error(f"Error al conectar con NUT: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitorear estado del UPS")
    parser.add_argument("--ups", default=UPS_NAME, help="Nombre del UPS a monitorear")
    args = parser.parse_args()

    logging.info(f"Iniciando monitor de UPS para {args.ups}")
    monitor_ups(args.ups)