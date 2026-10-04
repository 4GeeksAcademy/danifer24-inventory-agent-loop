# Sistema de gestión de inventario con IA

Una pequeña empresa familiar — una tienda de suministros para cafeterías con dos locales físicos — está perdiendo dinero. No por las ventas, sino porque nadie en el equipo puede responder con seguridad a una pregunta simple en un momento dado:

> "¿Tenemos suficiente de este producto para cubrir la semana?"

El stock se lleva en una hoja de cálculo compartida que nadie actualiza de forma consistente. La dueña, Carla, se ha puesto en contacto contigo después de ver una demo de un asistente de IA en una feria del sector.

No quiere un panel de control que tenga que mantener a mano — quiere poder hablar con un sistema y obtener respuestas. También quiere que el sistema actúe: registrar entregas, apuntar ventas y avisarle cuando algo esté por agotarse, todo mediante lenguaje natural.

## Objetivo

Tu trabajo es construir ese sistema. Tiene dos partes que deben funcionar juntas:

### 1. API REST con FastAPI

Una API REST construida con **FastAPI** que gestiona los datos del inventario.

Expone endpoints para:

- Listar productos.
- Registrar nuevos productos.
- Actualizar cantidades.
- Obtener alertas de stock bajo.

Los productos se almacenan en un fichero **CSV** para que los datos persistan entre sesiones.

### 2. Agente de IA

Un agente de IA escrito en **Python** que se conecta a un **LLM** y utiliza tu API como conjunto de herramientas (*tools*).

El agente funciona en un bucle:

1. Recibe un mensaje de Carla.
2. Razona sobre qué acción debe tomar.
3. Llama al endpoint de la API correspondiente como una *tool*.
4. Responde con el resultado.
5. Registra cada paso del proceso.

Cada paso de ese bucle queda registrado en un fichero:

```text
conversation_log.csv