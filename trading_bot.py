import yfinance as yf
import os
import pandas as pd
from datetime import datetime

def calcular_rsi_manual(series, window=14):
    """Calcula el RSI sin librerías externas para evitar errores en GitHub Actions"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def verificar_mitigacion_h4(simbolo):
    """
    SMC Logic: Verifica si hubo una mecha (shadow) que mitigó el lado contrario 
    en el timeframe de 4 horas antes de la dirección actual.
    """
    try:
        ticker = yf.Ticker(simbolo)
        df_h4 = ticker.history(period="3d", interval="1h") # Usamos 1h para reconstruir H4 con precisión
        if len(df_h4) < 8: return False, False
        
        # Agrupamos en bloques de 4 para simular velas de 4h
        df_h4 = df_h4.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
        
        ultima = df_h4.iloc[-1]
        previa = df_h4.iloc[-2]
        
        # Mitigación para COMPRA: La vela previa barrió por debajo del Open (mecha inferior larga)
        mit_baja = (previa['Low'] < previa['Open']) and (ultima['Close'] > ultima['Open'])
        # Mitigación para VENTA: La vela previa barrió por arriba del Open (mecha superior larga)
        mit_alta = (previa['High'] > previa['Open']) and (ultima['Close'] < ultima['Open'])
        
        return mit_baja, mit_alta
    except:
        return False, False

def obtener_top_3_setups():
    activos = [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X",
        "EURJPY=X", "GBPJPY=X", "EURGBP=X", "AUDJPY=X", "GBPAUD=X", "CHFJPY=X"
    ]
    
    setups_finales = []
    print("Iniciando escaneo con Filtro de Mitigación H4...")
    
    for simbolo in activos:
        try:
            ticker = yf.Ticker(simbolo)
            data_d = ticker.history(period="250d", interval="1d")
            if len(data_d) < 200: continue
            
            precio = data_d['Close'].iloc[-1]
            sma_200 = data_d['Close'].rolling(window=200).mean().iloc[-1]
            rsi = calcular_rsi_manual(data_d['Close']).iloc[-1]
            
            # 1. Filtro de Tendencia Macro
            es_alcista = precio > sma_200 and rsi < 55
            es_bajista = precio < sma_200 and rsi > 45
            
            if not (es_alcista or es_bajista): continue

            # 2. Filtro de Mitigación (CRT) en H4
            mit_baja, mit_alta = verificar_mitigacion_h4(simbolo)
            
            señal = None
            fuerza = 0
            if es_alcista and mit_baja:
                señal = "COMPRA"
                fuerza = 60 - rsi # Prioriza RSIs más bajos en compras
            elif es_bajista and mit_alta:
                señal = "VENTA"
                fuerza = rsi - 40 # Prioriza RSIs más altos en ventas

            if señal:
                dec = 2 if "JPY" in simbolo else 4
                setups_finales.append({
                    "par": simbolo.replace("=X", ""),
                    "precio": round(precio, dec),
                    "rsi": round(rsi, 1),
                    "señal": señal,
                    "fuerza": fuerza,
                    "nota": "CRT Mitigado (H4)"
                })
        except: continue
            
    # Ordenamos por fuerza del setup y tomamos los 3 mejores
    setups_finales.sort(key=lambda x: x['fuerza'], reverse=True)
    return setups_finales[:3]

def actualizar_index_html(top_setups):
    fecha_utc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Configuración del botón de TradingView para el par #1
    if top_setups:
        top_par_base = top_setups[0]['par']
        top_par_tv = f"FX:{top_par_base.replace('/', '')}"
    else:
        top_par_base = "EUR/USD"
        top_par_tv = "FX:EURUSD"

    cards_html = ""
    if not top_setups:
        cards_html = """
        <div style="grid-column: span 3; background:#2a2e39; padding:50px; border-radius:15px; text-align:center; border:1px solid #434651;">
            <h2 style="color:#787b86; margin:0;">⚪ Sin señales institucionales claras</h2>
            <p style="color:#787b86;">Esperando mitigación de rango en H4...</p>
        </div>
        """
    else:
        for p in top_setups:
            color = "#26a69a" if p['señal'] == "COMPRA" else "#ef5350"
            cards_html += f"""
            <div style="background:#1e222d; border-radius:12px; padding:25px; border:1px solid #434651; border-top:5px solid {color}; transition: 0.3s;">
                <div style="color:{color}; font-size:0.7rem; font-weight:bold; text-transform:uppercase; letter-spacing:1px;">{p['nota']}</div>
                <h2 style="margin:10px 0; font-size:2rem; color:#fff;">{p['par']}</h2>
                <div style="font-size:2.5rem; font-family:monospace; font-weight:bold; color:#fff;">{p['precio']}</div>
                <div style="margin-top:20px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="background:{color}; color:white; padding:6px 15px; border-radius:4px; font-weight:bold; font-size:0.9rem;">{p['señal']}</span>
                    <span style="color:#787b86; font-size:0.85rem;">RSI: <b>{p['rsi']}</b></span>
                </div>
            </div>
            """

    html_full = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Oráculo VIP | Radar Institucional</title>
        <style>
            body {{ background:#131722; color:#d1d4dc; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding:20px; margin:0; }}
            .wrapper {{ max-width:1100px; margin:0 auto; }}
            .header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:40px; border-bottom:1px solid #2a2e39; padding-bottom:20px; }}
            .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:25px; }}
            .btn-update {{ background:#2962ff; color:white; border:none; padding:14px 28px; border-radius:8px; cursor:pointer; font-weight:bold; font-size:0.9rem; transition:0.3s; }}
            .btn-update:hover {{ background:#1e4bd8; transform: scale(1.02); }}
            .btn-tv {{ background:#ffffff; color:#131722; display:flex; align-items:center; justify-content:center; padding:20px; border-radius:10px; text-decoration:none; font-weight:bold; margin-top:40px; font-size:1.1rem; transition:0.3s; border: 2px solid transparent; }}
            .btn-tv:hover {{ background:#f0f3fa; border-color: #2962ff; }}
            .footer {{ text-align:center; margin-top:60px; color:#434651; font-size:0.75rem; border-top: 1px solid #2a2e39; padding-top:20px; }}
        </style>
    </head>
    <body>
        <div class="wrapper">
            <div class="header">
                <div>
                    <h1 style="margin:0; font-size:1.8rem; color:#fff;">🚨 Radar VIP: Mitigación H4</h1>
                    <p style="color:#787b86; margin:5px 0 0 0;">Filtro SMA 200 + CRT (Context Range Trade)</p>
                </div>
                <button class="btn-update" id="upBtn" onclick="ejecutarAccion()">🔄 ACTUALIZAR SCANNER</button>
            </div>

            <div class="grid">
                {cards_html}
            </div>

            {f'''
            <a href="https://es.tradingview.com/chart/?symbol={top_par_tv}" target="_blank" class="btn-tv">
                📊 ABRIR GRÁFICO PROFESIONAL DE {top_par_base} (TOP #1)
            </a>
            ''' if top_setups else ''}

            <div class="footer">
                Sincronización de Red: {fecha_utc} UTC | Basado en algoritmos de Mitigación Institutional
            </div>
        </div>

        <script>
            async function ejecutarAccion() {{
                let t = localStorage.getItem('gh_token');
                if(!t) {{ 
                    t = prompt("Introduce tu Token de GitHub:"); 
                    if(!t) return; 
                    localStorage.setItem('gh_token', t); 
                }}
                
                const btn = document.getElementById('upBtn');
                btn.innerText = "⏳ ESCANEANDO CRT...";
                btn.disabled = true;

                const res = await fetch('https://api.github.com/repos/JoseGarcia65/oraculo_2/actions/workflows/main.yml/dispatches', {{
                    method:'POST',
                    headers:{{ 'Authorization': 'Bearer ' + t }},
                    body: JSON.stringify({{ ref: 'main' }})
                }});

                if(res.ok) {{
                    alert("🚀 Scanner iniciado. Los 3 mejores pares con mitigación aparecerán en 60s.");
                    setTimeout(() => location.reload(), 60000);
                }} else {{
                    alert("Error de Token.");
                    localStorage.removeItem('gh_token');
                    location.reload();
                }}
            }}
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_full)

if __name__ == "__main__":
    top_3 = obtener_top_3_setups()
    actualizar_index_html(top_3)
