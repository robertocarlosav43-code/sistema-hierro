import telebot
import requests
from telebot import types
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
import time
import os

# --- CONFIGURACIÓN DE PODER ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ODDS_API_KEY = "5f2bff853d800818ada03b708d5c9740"
SPORTS_API_KEY = "1de039af4aab5c0a59c37f3c61dbe798"

bot = telebot.TeleBot(TOKEN)
USUARIOS_AUTORIZADOS = [789055410, 1068624379]
user_data = {"B": 1500.0, "L": 0.20, "C_base": 0.4, "limite_bank": 0.02}
historial_dia = []

# --- SERVIDOR WEB ---
app = Flask('')
@app.route('/')
def home(): return "🦾 Sistema de Hierro V7.1 - Omnisciente Activo"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- FUNCIONES DE ANÁLISIS DE ESTADÍSTICAS (API-SPORTS) ---

def obtener_fatiga(team_name, sport):
    """Detecta B2B (partido ayer) para NBA o NHL"""
    endpoint = "nba" if sport == "nba" else "hockey"
    url = f"https://v2.{endpoint}.api-sports.io/games"
    ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    headers = {'x-rapidapi-key': SPORTS_API_KEY, 'x-rapidapi-host': f'v2.{endpoint}.api-sports.io'}
    try:
        res = requests.get(url, params={'date': ayer}, headers=headers, timeout=5).json()
        for game in res.get('response', []):
            if team_name in [game['teams']['home']['name'], game['teams']['away']['name']]:
                return True
        return False
    except: return False

# --- MOTOR DE ANÁLISIS INTEGRADO V7.1 ---

def motor_hierro_v7(sport_key, limit=3):
    ahora_vzla = datetime.now() - timedelta(hours=4)
    limite_futuro = ahora_vzla + timedelta(hours=20) # Filtro de Horario Preciso
    encontrados = []
    partidos_procesados = set()

    try:
        url_odds = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
        data = requests.get(url_odds, timeout=10).json()

        for partido in data:
            id_p = partido['id']
            if id_p in partidos_procesados: continue

            f_vzla = datetime.strptime(partido['commence_time'], "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=4)
            if not (ahora_vzla <= f_vzla <= limite_futuro): continue

            for bookmaker in partido['bookmakers'][:1]:
                for market in bookmaker['markets']:
                    for outcome in market['outcomes']:
                        O = outcome['price']
                        if O < 1.28: continue 

                        P_real = (1 / O) * 1.14 
                        edge = (P_real * O) - 1
                        if edge < 0.15: continue 

                        # --- FILTROS DE INTELIGENCIA ---
                        puntos_C = 0
                        alerta_f = ""

                        if 'nba' in sport_key or 'icehockey' in sport_key:
                            tipo = "nba" if 'nba' in sport_key else "nhl"
                            if obtener_fatiga(outcome['name'], tipo):
                                puntos_C -= 0.25
                                alerta_f = f"⚠️ FATIGA {tipo.upper()} DETECTADA"
                            else:
                                puntos_C += 0.10

                        C = min(1.0, max(0.1, user_data["C_base"] + puntos_C))

                        num, den = (P_real * O) - 1, O - 1
                        k_f = (num / den) if den > 0 else 0
                        monto = min(user_data["B"] * k_f * C * user_data["L"], user_data["B"] * user_data["limite_bank"])

                        if monto > 1.5:
                            encontrados.append({
                                "evento": f"{partido['home_team']} vs {partido['away_team']}",
                                "hora": f_vzla.strftime("%I:%M %p"),
                                "pick": f"{outcome['name']}",
                                "cuota": O, "P": P_real, "C": C, "monto": monto,
                                "alerta": alerta_f, "edge": edge
                            })
                            partidos_procesados.add(id_p)

        return sorted(encontrados, key=lambda x: x['edge'], reverse=True)[:limit]
    except: return []

# --- COMANDOS DEL BOT ---

@bot.message_handler(func=lambda m: m.from_user.id in USUARIOS_AUTORIZADOS)
def manejar_comandos(m):
    global historial_dia
    cid, txt = m.chat.id, m.text

    if 'Fútbol' in txt:
        bot.send_message(cid, "🔎 Escaneando Ligas Top Europeas...")
        res = motor_hierro_v7('soccer_spain_la_liga,soccer_england_premier_league,soccer_italy_serie_a,soccer_germany_bundesliga')
    elif 'NBA' in txt:
        bot.send_message(cid, "🏀 Escaneando NBA + Filtro B2B...")
        res = motor_hierro_v7('basketball_nba')
    elif 'NHL' in txt:
        bot.send_message(cid, "🏒 Escaneando NHL + Filtro B2B...")
        res = motor_hierro_v7('icehockey_nhl')
    elif 'Dupla' in txt:
        bot.send_message(cid, "🔀 Generando Dupla de Hierro (Combinada)...")
        p1 = motor_hierro_v7('basketball_nba,soccer_england_premier_league', 1)
        p2 = motor_hierro_v7('icehockey_nhl,soccer_spain_la_liga', 1)
        res_dupla = p1 + p2
        if len(res_dupla) < 2:
            bot.send_message(cid, "❌ No hay suficientes picks de alta confianza para una dupla segura.")
            return
        c_total = res_dupla[0]['cuota'] * res_dupla[1]['cuota']
        monto_d = user_data["B"] * 0.01 # 1% fijo por ser combinada
        msg = f"🔀 **DUPLA DE HIERRO**\n\n1️⃣ {res_dupla[0]['evento']}\n🎯 {res_dupla[0]['pick']}\n\n2️⃣ {res_dupla[1]['evento']}\n🎯 {res_dupla[1]['pick']}\n\n🔥 **CUOTA: @{c_total:.2f}**\n💰 **APUESTA: {monto_d:.2f} Bs.**"
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    elif 'Banca' in txt:
        bot.send_message(cid, f"💰 **BANCA ACTUAL: {user_data['B']:.2f} Bs.**")
        return
    else: return

    if not res:
        bot.send_message(cid, "❌ Filtros de Hierro: No hay picks seguros ahora. Reintenta más tarde.")
    else:
        msg = "🛡️ **CARTERA DE HIERRO V7.1**\n\n"
        for r in res:
            historial_dia.append(r)
            msg += f"⏰ **{r['hora']}** | {r['evento']}\n🎯 Pick: `{r['pick']}` | @{r['cuota']}\n"
            if r['alerta']: msg += f"{r['alerta']}\n"
            msg += f"📈 P: {r['P']:.1%} | Confianza: {r['C']:.2f}\n💰 **APUESTA: {r['monto']:.2f} Bs.**\n\n"
        bot.send_message(cid, msg, parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
