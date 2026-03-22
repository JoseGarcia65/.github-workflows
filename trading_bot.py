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

def obtener_top_3_setups():
    activos = [
        "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X",
        "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURCAD=X", "EURAUD=X", "EURNZD=X",
        "GBPJPY=X", "GBPCHF=X", "GBPCAD=X", "GBPAUD=X", "GBPNZD=X",
        "CHFJPY=X", "CADJPY=X", "AUDJPY=X", "NZDJPY=X",
        "AUDCAD=X", "AUDCHF=X", "AUDNZD=X", "NZDCAD=X", "NZDCHF=X", "CADCHF=X"
    ]
    
    setups_claros = []
    print("Escaneando mercado...")
    
    for simbolo in activos:
        try:
            ticker = yf.Ticker(simbolo)
            data = ticker.history(period="250d", interval="1d")
            if len(data) < 200: 
                continue
            
            precio = data['Close'].iloc[-1]
            sma_200 = data['Close'].rolling(window=200).mean().iloc[-1]
            rsi = calcular_rsi_manual(data['Close']).iloc[-1]
            
            if pd.isna(rsi): 
                continue

            # Lógica de señales
            señal = None
            fuerza_rsi = 0
            if precio > sma_200 and rsi < 45:
                señal = "COMPRA"
                fuerza_rsi = 50 - rsi
            elif precio < sma_200 and rsi > 55:
                señal = "VENTA"
                fuerza_rsi = rsi - 50

            if señal:
                dec = 2 if "JPY" in simbolo else 4
                setups_claros.append({
                    "par": simbolo.replace("=X", ""),
                    "precio": round(precio, dec),
                    "rsi": round(rsi, 1),
                    "señal": señal,
                    "fuerza": fuerza_rsi,
                    "tendencia": "ALCISTA" if precio > sma_200 else "BAJISTA"
                })
        except:
            continue
            
    setups_claros.sort(key=lambda x: x['fuerza'], reverse=True)
    return setups_claros[:3]

def actualizar_index_html(top_setups):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    top_par_tradingview = "FX_IDC:EURUSD" 
    top_par_base = "ESPERANDO..."
    
    cards_html = ""
    if not top_setups:
        cards_html = "<div style='grid-column: span 3; background:#2a2e39; padding:40px; border-radius:12px; text-align:center;'><h2>⚪ Mercado Neutral</h2><p>Sin señales claras.</p></div>"
    else:
        top_par_base = top_setups[0]['par']
        top_par_tradingview = f"FX:{top_par_base.replace('/', '')}"
        for p in top_setups:
            color = "#26a69a" if p['señal'] == "COMPRA" else "#ef5350"
            icono = "🟢" if p['señal'] == "COMPRA" else "🔴"
            cards_html += f"""
            <div style="background:#1e222d; border-radius:12px; padding:25px; border:1px solid #434651; text-align:center; border-top:4px solid {color};">
                <span style="background:{color}; color:white; padding:5px 15px; border-radius:20px; font-size:0.8rem; font-weight:bold;">{icono} {p['señal']}</span>
                <h1 style="margin:15px 0;">{p['par']}</h1>
                <div style="font-size:2.5rem; font-family:monospace; font-weight:bold;">{p['precio']}</div>
                <div style="display:flex; justify-content:space-between; margin-top:20px; color:#787b86; font-size:0.8rem;">
                    <div>RSI: {p['rsi']}</div>
                    <div style="color:{color};">{p['tendencia']}</div>
                </div>
            </div>"""

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Radar VIP</title>
        <style>
            body {{ background:#131722; color:#d1d4dc; font-family:sans-serif; padding:20px; }}
            .container {{ max-width:1000px; margin:0 auto; }}
            .grid {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:20px; }}
            .btn-update {{ background:#2962ff; color:white; border:none; padding:12px 20px; border-radius:6px; cursor:pointer; font-weight:bold; float:right; }}
            .btn-chart {{ background:white; color:#131722; display:block; text-align:center; padding:15px; border-radius:8px; text-decoration:none; font-weight:bold; margin-top:30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <button class="btn-update" onclick="pedirToken()">🔄 ACTUALIZAR</button>
            <h1>🚨 Radar VIP: Top 3</h1>
            <div class="grid">{cards_html}</div>
            {f'<a href="https://es.tradingview.com/chart/?symbol={top_par_tradingview}" target="_blank" class="btn-chart">📊 ABRIR GRÁFICO DE {top_par_base}</a>' if top_setups else ''}
            <p style="text-align:center; color:#434651; font-size:0.7rem; margin-top:50px;">{fecha} UTC</p>
        </div>
        <script>
            async function pedirToken() {{
                let t = localStorage.getItem('gh_token');
                if(!t) {{ t = prompt("Token:"); if(!t) return; localStorage.setItem('gh_token', t); }}
                const res = await fetch('https://api.github.com/repos/JoseGarcia65/oraculo_2/actions/workflows/main.yml/dispatches', {{
                    method:'POST', headers:{{ 'Authorization':`Bearer ${{t}}` }}, body: JSON.stringify({{ref:'main'}})
                }});
                if(res.ok) {{ alert("🚀 Escaneando..."); setTimeout(()=>location.reload(), 60000); }}
                else {{ localStorage.removeItem('gh_token'); location.reload(); }}
            }}
        </script>
    </body>
    </html>"""
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    actualizar_index_html(obtener_top_3_setups())
