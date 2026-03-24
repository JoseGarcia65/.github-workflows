import yfinance as yf
import os
import pandas as pd
from datetime import datetime

def calcular_rsi_manual(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def obtener_setups_momentum_puros():
    activos = [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X",
        "EURJPY=X", "GBPJPY=X", "EURGBP=X", "AUDJPY=X", "GBPAUD=X", "CHFJPY=X", "CADJPY=X"
    ]
    
    setups_finales = []
    print("Escaneando mercado: Mitigación H4 + Momentum...")
    
    for simbolo in activos:
        try:
            ticker = yf.Ticker(simbolo)
            # 1. Datos Diarios para RSI
            data_d = ticker.history(period="100d", interval="1d")
            if len(data_d) < 30: continue
            
            precio = data_d['Close'].iloc[-1]
            rsi = calcular_rsi_manual(data_d['Close']).iloc[-1]
            
            # 2. Datos H4 para Mitigación (CRT)
            data_h4 = ticker.history(period="5d", interval="1h")
            data_h4 = data_h4.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
            
            # Usamos la vela previa para detectar el barrido (CRT)
            vela_mit = data_h4.iloc[-2]
            
            señal = None
            fuerza = 0
            dec = 2 if "JPY" in simbolo else 4

            # Lógica: Mecha por debajo + RSI bajo (Compra) / Mecha por arriba + RSI alto (Venta)
            if (vela_mit['Low'] < vela_mit['Open']) and rsi < 52:
                señal = "COMPRA"
                fuerza = 100 - rsi
                sl = vela_mit['Low'] - (0.0005 if dec == 4 else 0.05)
                tp = precio + ((precio - sl) * 2)
            elif (vela_mit['High'] > vela_mit['Open']) and rsi > 48:
                señal = "VENTA"
                fuerza = rsi
                sl = vela_mit['High'] + (0.0005 if dec == 4 else 0.05)
                tp = precio - ((sl - precio) * 2)

            if señal:
                setups_finales.append({
                    "par": simbolo.replace("=X", ""),
                    "precio": round(precio, dec),
                    "rsi": round(rsi, 1),
                    "señal": señal,
                    "sl": round(sl, dec),
                    "tp": round(tp, dec),
                    "fuerza": fuerza
                })
        except: continue
            
    setups_finales.sort(key=lambda x: x['fuerza'], reverse=True)
    return setups_finales[:3]

def actualizar_index_html(top_setups):
    fecha_utc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Datos para el botón de TradingView (Top 1)
    if top_setups:
        top_par_base = top_setups[0]['par']
        top_par_tv = f"FX:{top_par_base.replace('/', '')}"
    else:
        top_par_base = "Buscando..."
        top_par_tv = "FX:EURUSD"

    cards_html = ""
    if not top_setups:
        cards_html = "<div style='grid-column: span 3; background:#2a2e39; padding:50px; border-radius:15px; text-align:center;'><h2>⚪ Buscando Mitigaciones...</h2><p>No hay señales con la volatilidad necesaria ahora.</p></div>"
    else:
        for p in top_setups:
            color = "#26a69a" if p['señal'] == "COMPRA" else "#ef5350"
            cards_html += f"""
            <div style="background:#1e222d; border-radius:12px; padding:25px; border:1px solid #434651; border-top:5px solid {color};">
                <div style="color:{color}; font-weight:bold; font-size:0.75rem;">MOMENTUM VALIDADO</div>
                <h2 style="margin:10px 0; font-size:1.8rem; color:#fff;">{p['par']}</h2>
                <div style="font-size:2.2rem; font-family:monospace; font-weight:bold; color:#fff; margin-bottom:15px;">{p['precio']}</div>
                <div style="display:flex; justify-content:space-between; background:#2a2e39; padding:10px; border-radius:8px; margin-bottom:15px;">
                    <div style="text-align:center;"><span style="color:#787b86; font-size:0.7rem;">SL</span><br><b style="color:#ef5350;">{p['sl']}</b></div>
                    <div style="text-align:center;"><span style="color:#787b86; font-size:0.7rem;">TP (1:2)</span><br><b style="color:#26a69a;">{p['tp']}</b></div>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="background:{color}; color:white; padding:5px 12px; border-radius:4px; font-weight:bold;">{p['señal']}</span>
                    <span style="color:#787b86; font-size:0.8rem;">RSI: {p['rsi']}</span>
                </div>
            </div>
            """

    # HTML con el Script corregido para evitar errores de despliegue
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Oráculo VIP | Radar</title>
        <style>
            body {{ background:#131722; color:#d1d4dc; font-family:sans-serif; padding:20px; }}
            .container {{ max-width:1100px; margin:0 auto; }}
            .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:20px; }}
            .btn-update {{ background:#2962ff; color:white; border:none; padding:12px 24px; border-radius:8px; cursor:pointer; font-weight:bold; float:right; }}
            .btn-tv {{ background:white; color:#131722; display:block; text-align:center; padding:18px; border-radius:10px; text-decoration:none; font-weight:bold; margin-top:30px; border: 2px solid #2962ff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:30px;">
                <h1>🚨 Radar VIP: Mitigación</h1>
                <button class="btn-update" id="upBtn" onclick="lanzarScan()">🔄 ESCANEAR</button>
            </div>
            <div class="grid">{cards_html}</div>
            <a href="https://es.tradingview.com/chart/?symbol={top_par_tv}" target="_blank" class="btn-tv">📊 ANALIZAR {top_par_base} EN TRADINGVIEW</a>
            <p style="text-align:center; color:#434651; font-size:0.7rem; margin-top:40px;">Actualizado: {fecha_utc} UTC</p>
        </div>

        <script>
            async function lanzarScan() {{
                let t = localStorage.getItem('gh_token');
                if(!t) {{ 
                    t = prompt("Introduce tu Token de GitHub:"); 
                    if(!t) return; 
                    localStorage.setItem('gh_token', t); 
                }}
                
                document.getElementById('upBtn').innerText = "⏳ ENVIANDO...";
                
                try {{
                    const res = await fetch('https://api.github.com/repos/JoseGarcia65/oraculo_2/actions/workflows/main.yml/dispatches', {{
                        method: 'POST',
                        headers: {{ 
                            'Authorization': 'Bearer ' + t,
                            'Accept': 'application/vnd.github.v3+json'
                        }},
                        body: JSON.stringify({{ ref: 'main' }})
                    }});

                    if(res.ok) {{
                        alert("🚀 Escaneo iniciado. Refresca en 60 segundos.");
                        setTimeout(() => location.reload(), 60000);
                    }} else {{
                        alert("Error de Token o Repositorio. Verifica tus permisos.");
                        localStorage.removeItem('gh_token');
                        location.reload();
                    }}
                }} catch (e) {{
                    alert("Error de conexión.");
                    location.reload();
                }}
            }}
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    top = obtener_setups_momentum_puros()
    actualizar_index_html(top)
