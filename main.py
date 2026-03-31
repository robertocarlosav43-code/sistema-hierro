import telebot
import requests
from telebot import types
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
import time
import os

# ==========================================================
# 🛡️ SISTEMA DE HIERRO V8.0 - MODO FRANCOTIRADOR (P > 72%)
# ==========================================================

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ODDS_API_KEY = "5f2bff853d800818ada03b708d5c9740"
SPORTS_API_KEY = "1de039af4aab5c0a59c37f3c61dbe798"

bot = telebot.TeleBot(TOKEN)

# ✅ USUARIOS AUTORIZADOS
USUARIOS_AUTORIZADOS = [789055410, 1068624379, 139426773]

# ✅ BANCA Y GESTIÓN DE RIESGO (STAKE MÁXIMO 5%)
user_data = {
    "B": 6000.0, 
    "L": 0.20,         # Coeficiente de agresividad bajo para seguridad
    "C_base": 0.50, 
    "limite_bank": 0.05 # Máximo 300 Bs por jugada
}
historial_dia = []

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

# --- MOTOR DE ANÁLISIS V8.0 (SEGURIDAD TOTAL) ---
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
                        
                        # FILTRO 1: Cuota mínima lógica para este sistema
                        if O < 1.30: continue 

                        # FILTRO 2: Probabilidad Implícita (Solo queremos favoritos claros)
                        P_implicita = (1 / O)
                        
                        # Solo procesamos si la casa de apuestas da > 65% de probabilidad
                        # Luego aplicaremos nuestros filtros para ver si llega al 72%
                        if P_implicita < 0.65: continue 

                        puntos_C = 0
                        alerta_f = ""

                        # FILTRO 3: Fatiga en NBA/NHL
                        if 'nba' in sport_key or 'icehockey' in sport_key:
                            tipo = "nba" if 'nba' in sport_key else "nhl"
                            if obtener_fatiga(outcome['name'], tipo):
                                puntos_C -= 0.30
                                alerta_f = "⚠️ RIESGO: EQUIPO EN BACK-TO-BACK"
                            else:
                                puntos_C += 0.05

                        # CALCULO DE CONFIANZA FINAL
                        # Si tiene fatiga, la probabilidad real para nosotros baja
                        P_real = P_implicita + puntos_C
                        
                        # 🔥 LA REGLA DE ORO: Si no llega al 72%, se descarta.
                        if P_real < 0.72: continue

                        edge = (P_real * O) - 1
                        monto = min(user_data["B"] * edge * user_data["L"], user_data["B"] * user_data["limite_bank"])

                        if monto > 10: # No apostar migajas
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

    # Verificación de Seguridad
    if uid not in USUARIOS_AUTORIZADOS:
        bot.send_message(cid, "❌ No tienes autorización para acceder al Sistema de Hierro.")
        return

    if '/start' in txt:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Fútbol ⚽', 'NBA 🏀', 'NHL 🏒', 'Banca 💰')
        bot.send_message(cid, "🦾 **SISTEMA DE HIERRO V8.0**\n\nModo Francotirador activado. Solo picks con >72% de probabilidad real.", reply_markup=markup)
        return

    if 'Fútbol' in txt:
        bot.send_message(cid, "🔎 Buscando favoritos sólidos en Europa...")
        res = motor_hierro_v8('soccer_spain_la_liga,soccer_england_premier_league,soccer_italy_serie_a,soccer_germany_bundesliga')
    elif 'NBA' in txt:
        bot.send_message(cid, "🏀 Analizando fatiga y cuotas NBA...")
        res = motor_hierro_v8('basketball_nba')
    elif 'NHL' in txt:
        bot.send_message(cid, "🏒 Analizando hielo y fatiga NHL...")
        res = motor_hierro_v8('icehockey_nhl')
    elif 'Banca' in txt:
        bot.send_message(cid, f"💰 **BANCA ACTUAL: {user_data['B']:.2f} Bs.**\n🛡️ Riesgo máx: 300.00 Bs.")
        return
    else: return

    if not res:
        bot.send_message(cid, "❌ No hay picks que cumplan el estándar de seguridad (72%) ahora mismo.")
    else:
        msg = "🛡️ **SELECCIÓN DE HIERRO (ALTA CONFIANZA)**\n\n"
        for r in res:
            msg += f"⏰ **{r['hora']}** | {r['evento']}\n🎯 Pick: `{r['pick']}` | @{r['cuota']}\n"
            if r['alerta']: msg += f"{r['alerta']}\n"
            msg += f"📊 Probabilidad Real: {r['P']:.1%}\n💰 **APUESTA SUGERIDA: {r['monto']:.2f} Bs.**\n\n"
        bot.send_message(cid, msg, parse_mode="Markdown")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
