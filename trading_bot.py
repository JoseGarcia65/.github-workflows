import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

def generar_pronostico():
    # 1. Obtener precio real del mercado (Forex GBP/USD)
    ticker = yf.Ticker("GBPUSD=X")
    data = ticker.history(period="1d", interval="1m")
    precio_actual = round(data['Close'].iloc[-1], 5)
    
    # 2. Lógica de trading simple (Ejemplo: Compra si el precio está subiendo)
    tp = round(precio_actual + 0.0040, 5)
    sl = round(precio_actual - 0.0025, 5)
    
    return {
        "par": "GBP/USD",
        "precio": precio_actual,
        "tp": tp,
        "sl": sl,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def actualizar_index_html(p):
    # Esta función crea el nuevo código visual de tu web con los datos reales
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Forex Live Bot</title>
        <style>
            body {{ background: #131722; color: white; font-family: sans-serif; text-align: center; padding-top: 50px; }}
            .card {{ background: #1e222d; border: 1px solid #363c4e; padding: 30px; border-radius: 15px; display: inline-block; }}
            .price {{ font-size: 3rem; color: #26a69a; font-family: monospace; }}
            .info {{ color: #787b86; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>{p['par']} - EN VIVO</h1>
            <div class="price">{p['precio']}</div>
            <p>🎯 Take Profit: <span style="color:#26a69a">{p['tp']}</span></p>
            <p>🛑 Stop Loss: <span style="color:#ef5350">{p['sl']}</span></p>
            <div class="info">Última actualización: {p['fecha']} (Sesión Actual)</div>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    datos = generar_pronostico()
    actualizar_index_html(datos)
    print(f"Web actualizada con precio: {datos['precio']}")
    # Aquí podrías llamar también a tu función de enviar_correo(datos)
