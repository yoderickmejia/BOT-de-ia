# Guia de Inicio Rapido

## Paso 1: Instalar dependencias

```bash
pip install -r requirements.txt
```

## Paso 2: Configurar el archivo .env

Copia `.env.example` como `.env`:

```bash
cp .env.example .env
```

Edita `.env` con tus datos:

```
BINANCE_API_KEY=pega_tu_api_key_aqui
BINANCE_API_SECRET=pega_tu_api_secret_aqui
BINANCE_TESTNET=true   # <-- dejar en true mientras pruebas
```

### Donde obtener las API keys de Testnet (gratis, sin dinero real)
1. Ve a https://testnet.binance.vision
2. Inicia sesion con GitHub
3. Haz clic en "Generate HMAC_SHA256 Key"
4. Copia la API Key y Secret al .env

## Paso 3: Ejecutar el backtesting (ver como funciona la estrategia)

```bash
python -m backtester.backtest
```

Muestra cuantos trades habria hecho en los ultimos 500 periodos y el resultado.

## Paso 4: Ejecutar los tests

```bash
pytest tests/ -v
```

## Paso 5: Correr el bot en testnet

```bash
python main.py
```

El bot correra y mostrara logs en pantalla y en `data/bot.log`.

## Paso 6: Con Docker (opcional)

```bash
docker-compose up --build
```

---

## La estrategia en palabras simples

El bot usa dos indicadores:

| Indicador | Que hace |
|-----------|----------|
| **RSI (14)** | Mide si el mercado esta "barato" (< 35) o "caro" (> 65) |
| **EMA 20/50** | Muestra la tendencia: si el precio esta sobre la EMA50, es alcista |

**COMPRA cuando:** RSI < 35 (precio "barato") Y precio sobre EMA50 (tendencia buena)

**VENDE cuando:** RSI > 65 (precio "caro") O precio cae bajo EMA50 O Stop Loss O Take Profit

**Stop Loss:** 2% por debajo del precio de entrada (perdida maxima por trade)

**Take Profit:** 4% por encima del precio de entrada (ganancia objetivo)

---

## Notificaciones por Telegram (opcional)

1. Busca `@BotFather` en Telegram
2. Escribe `/newbot` y sigue los pasos
3. Copia el token al `.env` como `TELEGRAM_BOT_TOKEN`
4. Busca `@userinfobot` para obtener tu `TELEGRAM_CHAT_ID`

---

## ADVERTENCIAS

- **NUNCA** corras con `BINANCE_TESTNET=false` sin haber probado al menos 2 semanas en testnet
- **NUNCA** subas el archivo `.env` a GitHub
- El trading automatizado NO garantiza ganancias
