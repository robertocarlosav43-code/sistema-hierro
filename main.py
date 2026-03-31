import telebot
import requests
from telebot import types
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
import time
import os

# ==========================================================
# 🛡️ SISTEMA DE HIERRO V8.0 - FULL UNIFICADO (P > 72%)
# PROPIEDAD DE ROBERTO - MODO FRANCOTIRADOR
# ==========================================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ODDS_API_KEY = "5f2bff853d800818ada03b708d5c9740"
SPORTS_API_KEY = "1de039af4aab5c0a59c37f3c61dbe798"

bot = telebot.TeleBot(TOKEN)

# ✅ USUARIOS AUTORIZADOS
USUARIOS_AUTORIZADOS = [789055410, 1068624379, 139426773]

# ✅ GESTIÓN DE BANCA (6000 Bs)
user_data = {
    "B": 6000.0, 
    "L": 0.20,         # Coeficiente de seguridad
    "C_base": 0.50, 
    "limite_bank": 0.05 # Máximo 300 Bs por jugada (5%)
}

# --- SERVIDOR PARA MANTENERLO VIVO ---
app = Flask('')
@app.route('/')
def home(): return "🦾 Modo Francotirador V8.0 - Activo"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- DETECTOR DE FATIGA (API-SPORTS) ---
def obtener_fatiga(team_name, sport):
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

# --- MOTOR DE ANÁLISIS V8.0 ---
def motor_hierro_v8(sport_key, limit=3):
    ahora_vzla = datetime.now() - timedelta(hours=4)
    limite_futuro = ahora_vzla + timedelta(hours=18)
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
                        if O < 1.30: continue 

                        P_implicita = (1 / O)
                        puntos_C = 0
                        alerta_f = ""

                        if 'nba' in sport_key or 'icehockey' in sport_key:
                            tipo = "nba" if 'nba' in sport_key else "nhl"
                            if obtener_fatiga(outcome['name'], tipo):
                                puntos_C -= 0.30
                                alerta_f = "⚠️ RIESGO: EQUIPO EN BACK-TO-BACK"
                            else:
                                puntos_C += 0.05

                        P_real = P_implicita + puntos_C
                        
                        # 🔥 SOLO PICKS CON > 72% DE PROBABILIDAD REAL
                        if P_real < 0.72: continue

                        edge = (P_real * O) - 1
                        monto = min(user_data["B"] * edge * user_data["L"], user_data["B"] * user_data["limite_bank"])

                        if monto > 10:
                            encontrados.append({
                                "evento": f"{partido['home_team']} vs {partido['away_team']}",
                                "hora": f_vzla.strftime("%I:%M %p"),
                                "pick": f"{outcome['name']}",
                                "cuota": O, "P": P_real, "monto": monto,
                                "alerta": alerta_f
                            })
                            partidos_procesados.add(id_p)

        return sorted(encontrados, key=lambda x: x['P'], reverse=True)[:limit]
    except: return []

# --- MANEJO DE COMANDOS ---
@bot.message_handler(func=lambda m: True)
def manejar_comandos(m):
    cid, txt, uid = m.chat.id, m.text, m.from_user.id

    if uid not in USUARIOS_AUTORIZADOS:
        bot.send_message(cid, "❌ Acceso denegado. ID no autorizado.")
        return

    if '/start' in txt:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Fútbol ⚽', 'NBA 🏀', 'NHL 🏒', 'Dupla 🔀', 'Banca 💰')
        bot.send_message(cid, "🦾 **SISTEMA DE HIERRO V8.0**\n\nBienvenido Roberto. Solo picks con >72% de probabilidad real detectada por APIs.", reply_markup=markup)
        return

    res = []
    if 'Fútbol' in txt:
        bot.send_message(cid, "🔎 Buscando favoritos sólidos en Europa...")
        res = motor_hierro_v8('soccer_spain_la_liga,soccer_england_premier_league,soccer_italy_serie_a,soccer_germany_bundesliga')
    elif 'NBA' in txt:
        bot.send_message(cid, "🏀 Analizando fatiga y cuotas NBA...")
        res = motor_hierro_v8('basketball_nba')
    elif 'NHL' in txt:
        bot.send_message(cid, "🏒 Analizando hielo y fatiga NHL...")
        res = motor_hierro_v8('icehockey_nhl')
    elif 'Dupla' in txt:
        bot.send_message(cid, "🔀 **Buscando Dupla Francotirador...**")
        p1 = motor_hierro_v8('basketball_nba', 1)
        p2 = motor_hierro_v8('soccer_spain_la_liga,soccer_england_premier_league,icehockey_nhl', 1)
        res_dupla = p1 + p2
        if len(res_dupla) < 2:
            bot.send_message(cid, "❌ No hay suficientes picks de >72% para armar una dupla segura ahora.")
            return
        c_total = res_dupla[0]['cuota'] * res_dupla[1]['cuota']
        monto_d = user_data["B"] * 0.01 
        msg = f"🔀 **DUPLA DE HIERRO (FILTRO 72%)**\n\n1️⃣ {res_dupla[0]['evento']}\n🎯 {res_dupla[0]['pick']} (@{res_dupla[0]['cuota']})\n\n2️⃣ {res_dupla[1]['evento']}\n🎯 {res_dupla[1]['pick']} (@{res_dupla[1]['cuota']})\n\n🔥 **CUOTA: @{c_total:.2f}**\n💰 **APUESTA: {monto_d:.2f} Bs.**"
        bot.send_message(cid, msg, parse_mode="Markdown")
        return
    elif 'Banca' in txt:
        bot.send_message(cid, f"💰 **BANCA ACTUAL: {user_data['B']:.2f} Bs.**\n🛡️ Límite por apuesta: 300.00 Bs.")
        return
    else: return

    if not res:
        bot.send_message(cid, "❌ No hay picks con seguridad >72% ahora mismo.")
    else:
        msg = "🛡️ **SELECCIÓN DE HIERRO (FRANCO) V8.0**\n\n"
        for r in res:
            msg += f"⏰ **{r['hora']}** | {r['evento']}\n🎯 Pick: `{r['pick']}` | @{r['cuota']}\n"
            if r['alerta']: msg += f"{r['alerta']}\n"
            msg += f"📊 Probabilidad Real: {r['P']:.1%}\n💰 **APUESTA: {r['monto']:.2f} Bs.**\n\n"
        bot.send_message(cid, msg, parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
