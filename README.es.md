# Inventario con IA

API FastAPI con persistencia en `products.csv` y agente CLI en Python puro, sin frameworks de agentes. El agente observa el mensaje, consulta al LLM, ejecuta sus tools y devuelve los resultados al contexto hasta recibir una respuesta final.

## Preparación

Necesitas Python 3.10 o posterior, uv y una clave de Groq con acceso al modelo elegido. Con el entorno listo, instala las dependencias desde la raíz del proyecto:

```bash
uv add fastapi uvicorn groq python-dotenv
```

Los comandos con `uv run` usan el entorno `.venv` del proyecto sin tener que activarlo manualmente.

Configura tu archivo `.env` (no lo subas a Git):

```dotenv
GROQ_API_KEY=tu_clave
GROQ_MODEL=qwen/qwen3.8-27b
INVENTORY_API_URL=http://127.0.0.1:8000
```

Solo la clave es obligatoria. El modelo y la URL tienen los valores por defecto mostrados. La API permite configurar `INVENTORY_CSV` e `INVENTORY_ALERT_THRESHOLD` mediante variables de entorno; el umbral por defecto es 10. El agente carga `.env`; para la API puedes usar `uv run uvicorn api.app:app --reload --env-file .env`.

## Arrancar el sistema

Necesitas dos terminales abiertos al mismo tiempo, ambos en la raíz del proyecto. La API debe estar en ejecución antes de arrancar el agente.

Terminal 1: arrancar la API.

```bash
uv run uvicorn api.app:app --reload
```

Terminal 2: arrancar el agente.

```bash
uv run python agent.py
```

La documentación interactiva de la API está en http://127.0.0.1:8000/docs. Puedes pedir, por ejemplo, "Lista el inventario", "Registra Leche con 5 litros", "Añade 3 unidades al producto 1" o "Qué productos tienen menos de 20 unidades". Escribe `salir` para terminar el agente.

## Detener y relanzar

Pulsa Ctrl + C en cada terminal: detén primero el agente y luego la API. `conversation_log.csv` se escribe incrementalmente, cerrando el archivo después de cada evento, por lo que los eventos ya registrados no se pierden si detienes una sesión. Una petición interrumpida puede haber cambiado el stock: consúltalo antes de repetirla.

Para relanzar el agente, ejecuta `uv run python agent.py` de nuevo en el Terminal 2. No es necesario reiniciar la API. El historial en memoria empieza una nueva sesión, pero las conversaciones anteriores permanecen intactas en `conversation_log.csv`: las filas nuevas siempre se añaden, nunca se sobreescriben.

El registro contiene `actor`, `message`, `tool_call` y `timestamp` (ISO 8601 en UTC). Registra mensajes del usuario, respuestas del agente, llamadas y resultados de tools. Puede contener información sensible del inventario.

## Endpoints

- `GET /inventory`: lista todos los productos.
- `POST /inventory`: crea un producto con `name`, `quantity` y `unit`.
- `PATCH /inventory/{product_id}`: actualiza el stock con `delta` positivo o negativo.
- `GET /inventory/alerts?threshold=10`: lista cantidades estrictamente inferiores al umbral.

El bucle tiene un límite de 20 rondas por mensaje para evitar ejecución indefinida. Los errores de la API se devuelven al LLM y las escrituras no se reintentan automáticamente.

## Respuestas cortadas

Cada consulta a Groq solicita un máximo de 4096 tokens de generación. Si Groq indica que alcanzó el límite, el agente pide continuar el texto y une los fragmentos antes de imprimirlos. Las continuaciones también cuentan dentro de las 20 rondas y no permiten ejecutar nuevas tools.

Si llega una llamada a tool en una respuesta cortada, el agente no la ejecuta y muestra un aviso. Si no puede completar el texto o agota las rondas, conserva los fragmentos disponibles y avisa de la interrupción. El CSV registra cada fragmento recibido por separado.
