import yfinance as yf
import smtplib
import os
from email.mime.text import MIMEText
from datetime import datetime

def gestionar_historial(nueva_fecha):
    archivo_historial = "historial.txt"
    # 1. Leer historial existente si existe
    if os.path.exists(archivo_historial):
        with open(archivo_historial, "r") as f:
            lineas = f.readlines()
    else:
        lineas = []

    # 2. Añadir la nueva fecha al principio y mantener solo las últimas 5
    lineas.insert(0, f"{nueva_fecha}\n")
    lineas = lineas[:5]

    # 3. Guardar de nuevo en el archivo de texto
    with open(archivo_historial, "w") as f:
        f.writelines(lineas)
    
    # 4. Crear el bloque HTML para mostrarlo en la web
    items_html = "".join([f"<li style='margin-bottom:5px;'>✅ {l.strip()} UTC</li>" for l in lineas])
    return f"<ul style='list-style:none; padding:0; text-align:left; font-size:0.85rem; color:#787b86; margin-top:10px;'>{items_html}</ul>"

def generar_pronostico():
    ticker = yf.Ticker("EURUSD=X")
    data = ticker.history(period="2d", interval="1h")
    precio_actual = round(data['Close'].iloc[-1], 4)
    
    # Lógica de ejemplo para la sesión actual
    accion = "COMPRA (LONG)"
    color_accion = "#26a69a"
    tp = 1.1650
    sl = 1.1495
    razon = "Debilidad del USD tras datos macro y soporte validado en H1."

    return {
        "par": "EUR/USD",
        "accion": accion,
        "color": color_accion,
        "precio": precio_actual,
        "tp": tp,
        "sl": sl,
        "razon": razon,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def enviar_correo(p):
    sender_email = os.environ.get('SENDER_EMAIL')
    sender_password = os.environ.get('SENDER_PASSWORD')

    if not sender_email or not sender_password:
        return

    msg = MIMEText(f"Estrategia {p['par']}: {p['accion']} a {p['precio']}. TP: {p['tp']}, SL: {p['sl']}. Motivo: {p['razon']}")
    msg['Subject'] = f"🚀 SEÑAL {p['par']}: {p['accion']}"
    msg['From'] = sender_email
    msg['To'] = sender_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, sender_email, msg.as_string())
    except Exception as e:
        print(f"Error correo: {e}")

def actualizar_index_html(p):
    html_historial = gestionar_historial(p['fecha'])

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Forex Pro Hub</title>
        <style>
            body {{ background-color: #131722; color: #d1d4dc; font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; margin: 0; }}
            .layout-grid {{ display: grid; grid-template-columns: 1fr 2fr; gap: 20px; max-width: 1400px; margin: 0 auto; }}
            .card {{ background: #1e222d; border: 1px solid #434651; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }}
            .signal-badge {{ background-color: {p['color']}; color: white; padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; text-transform: uppercase; }}
            .price {{ font-size: 3rem; color: #ffffff; font-family: monospace; margin: 10px 0; }}
            .chart-container {{ height: 600px; background: #1e222d; border: 1px solid #434651; border-radius: 12px; overflow: hidden; }}
            .btn-update {{ background: #2962ff; color: white; border: none; padding: 15px; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%; margin: 20px 0; transition: 0.3s; }}
            .btn-update:hover {{ background: #1e4bd8; }}
            .history-section {{ margin-top: 25px; border-top: 1px solid #434651; padding-top: 15px; }}
            .label {{ color: #787b86; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }}
            @media (max-width: 900px) {{ .layout-grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <h1 style="text-align:center; margin-bottom:30px;">Forex Intelligence Hub 2026</h1>
        <div class="layout-grid">
            <div class="card">
                <div class="signal-badge">{p['accion']}</div>
                <h2 style="margin:0;">{p['par']}</h2>
                <div class="price">{p['precio']}</div>
                
                <div style="display:flex; justify-content:space-around; border-bottom:1px solid #434651; padding-bottom:15px; margin-top:20px;">
                    <div><span class="label">Take Profit</span><br><b style="color:#26a69a; font-size:1.4rem;">{p['tp']}</b></div>
                    <div><span class="label">Stop Loss</span><br><b style="color:#ef5350; font-size:1.4rem;">{p['sl']}</b></div>
                </div>

                <button id="updateBtn" class="btn-update" onclick="pedirToken()">🔄 ACTUALIZAR AHORA</button>

                <div style="text-align:left; background:#2a2e39; padding:15px; border-radius:8px; font-size:0.9rem;">
                    <strong>Análisis Fundamental:</strong><br>{p['razon']}
                </div>

                <div class="history-section">
                    <span class="label">Registro de Actividad:</span>
                    {html_historial}
                </div>
            </div>

            <div class="chart-container">
                <div id="tv_chart" style="height:100%;"></div>
                <script src="https://s3.tradingview.com/tv.js"></script>
                <script>
                    new TradingView.widget({{"autosize": true, "symbol": "FX:EURUSD", "interval": "60", "theme": "dark", "style": "1", "locale": "es", "container_id": "tv_chart"}});
                    
                    async function pedirToken() {{
                        const token = prompt("Introduce tu Token de GitHub (Classic):");
                        if(!token) return;
                        
                        const btn = document.getElementById('updateBtn');
                        btn.innerText = "⏳ DESPERTANDO BOT...";
                        btn.disabled = true;

                        // AJUSTA TU USUARIO Y REPO AQUÍ
                        const res = await fetch('https://api.github.com/repos/JoseGarcia65/oraculo_2/actions/workflows/main.yml/dispatches', {{
                            method: 'POST',
                            headers: {{ 'Authorization': `Bearer ${{token}}`, 'Accept': 'application/vnd.github.v3+json' }},
                            body: JSON.stringify({{ ref: 'main' }})
                        }});

                        if(res.ok) {{
                            alert("🚀 Señal enviada. El bot está trabajando. La página se recargará sola en 60s.");
                            setTimeout(() => {{ location.reload(); }}, 60000);
                        }} else {{
                            alert("❌ Error: Token inválido o permisos insuficientes.");
                            btn.innerText = "🔄 ACTUALIZAR AHORA";
                            btn.disabled = false;
                        }}
                    }}
                </script>
            </div>
        </div>
        <p style="text-align:center; font-size:0.7rem; color:#787b86; margin-top:20px;">Oráculo Bot v2.0 - {p['fecha']} UTC</p>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    datos = generar_pronostico()
    actualizar_index_html(datos)
    enviar_correo(datos)
