import yfinance as yf
import os
import pandas as pd
from datetime import datetime

def calcular_rsi_manual(series, window=14):
    """Calcula el RSI sin librerías externas"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def obtener_analisis_profundo():
    activos = [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X",
        "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURCAD=X", "EURAUD=X", "EURNZD=X",
        "GBPJPY=X", "GBPCHF=X", "GBPCAD=X", "GBPAUD=X", "GBPNZD=X",
        "CHFJPY=X", "CADJPY=X", "AUDJPY=X", "NZDJPY=X",
        "AUDCAD=X", "AUDCHF=X", "AUDNZD=X",
        "NZDCAD=X", "NZDCHF=X", "CADCHF=X"
    ]
    
    resultados = []
    print(f"Analizando {len(activos)} pares con RSI nativo...")
    
    for simbolo in activos:
        try:
            ticker = yf.Ticker(simbolo)
            data = ticker.history(period="250d", interval="1d")
            if len(data) < 200: continue
            
            precio = data['Close'].iloc[-1]
            sma_200 = data['Close'].rolling(window=200).mean().iloc[-1]
            
            # Calculamos el RSI con nuestra nueva función
            rsi_series = calcular_rsi_manual(data['Close'])
            rsi = rsi_series.iloc[-1]
            
            # Lógica de Semáforos
            señal = "ESPERAR"
            color_web = "#787b86" 
            icono = "⚪"

            if precio > sma_200 and rsi < 45:
                señal = "COMPRA"
                color_web = "#26a69a" # Verde
                icono = "🟢"
            elif precio < sma_200 and rsi > 55:
                señal = "VENTA"
                color_web = "#ef5350" # Rojo
                icono = "🔴"

            dec = 2 if "JPY" in simbolo else 4
            resultados.append({
                "par": simbolo.replace("=X", ""),
                "precio": round(precio, dec),
                "rsi": round(rsi, 1) if not pd.isna(rsi) else 50.0,
                "señal": señal,
                "color": color_web,
                "icono": icono,
                "tendencia": "ALCISTA" if precio > sma_200 else "BAJISTA"
            })
        except: continue
            
    resultados.sort(key=lambda x: x['señal'] == "ESPERAR")
    return resultados

def actualizar_index_html(lista_pares):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filas = ""
    for p in lista_pares:
        filas += f"""
        <tr style="border-bottom: 1px solid #2a2e39;">
            <td style="padding:15px; font-weight:bold;">{p['par']}</td>
            <td style="padding:15px; font-family:monospace;">{p['precio']}</td>
            <td style="padding:15px; color:{'#26a69a' if p['tendencia'] == 'ALCISTA' else '#ef5350'}; font-size:0.7rem;">{p['tendencia']}</td>
            <td style="padding:15px; color:#aaa;">{p['rsi']}</td>
            <td style="padding:15px;">
                <span style="background:{p['color']}; color:white; padding:6px 12px; border-radius:20px; font-size:0.75rem; font-weight:bold;">
                    {p['icono']} {p['señal']}
                </span>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Radar de Oportunidades Forex</title>
        <style>
            body {{ background:#131722; color:#d1d4dc; font-family:sans-serif; padding:20px; }}
            .box {{ max-width:1000px; margin:0 auto; background:#1e222d; border-radius:12px; padding:25px; border:1px solid #434651; }}
            table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
            th {{ text-align:left; color:#787b86; font-size:0.7rem; text-transform:uppercase; padding:15px; border-bottom:2px solid #434651; }}
            .btn {{ background:#2962ff; color:white; border:none; padding:12px 25px; border-radius:6px; cursor:pointer; font-weight:bold; }}
            .status-bar {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; }}
        </style>
    </head>
    <body>
        <div class="box">
            <div class="status-bar">
                <div>
                    <h1 style="margin:0; font-size:1.5rem;">🚨 Radar Global de Divisas</h1>
                    <p style="color:#787b86; font-size:0.8rem;">SMA 200 + RSI Momentum (Cálculo Nativo)</p>
                </div>
                <button id="updateBtn" class="btn" onclick="pedirToken()">🔄 ESCANEAR</button>
            </div>
            <table>
                <thead>
                    <tr><th>Par</th><th>Precio</th><th>Tendencia</th><th>RSI</th><th>Señal Operativa</th></tr>
                </thead>
                <tbody>{filas}</tbody>
            </table>
            <p style="text-align:center; font-size:0.7rem; color:#434651; margin-top:20px;">Último barrido: {fecha} UTC</p>
        </div>
        <script>
            async function pedirToken() {{
                let t = localStorage.getItem('gh_token');
                if(!t) {{ t = prompt("Token GitHub:"); if(!t) return; localStorage.setItem('gh_token', t); }}
                document.getElementById('updateBtn').innerText = "⏳ BUSCANDO SETUPS...";
                const res = await fetch('https://api.github.com/repos/JoseGarcia65/oraculo_2/actions/workflows/main.yml/dispatches', {{
                    method:'POST', headers:{{ 'Authorization':`Bearer ${{t}}` }}, body: JSON.stringify({{ref:'main'}})
                }});
                if(res.ok) {{ alert("🚀 Escaneando mercado... Refresca en 1 min."); setTimeout(()=>location.reload(), 60000); }}
                else {{ localStorage.removeItem('gh_token'); location.reload(); }}
            }}
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    actualizar_index_html(obtener_analisis_profundo())
