# Backend-Hackaton-CloudComputing
Este repositorio contiene el backend utilizado para la hackatón del curso de Cloud Computing durante el ciclo 2025-2
# parte de websocket
Buenísimo, ya tienes todo el backend armado, así que ahora es “solo” escuchar y pintar 😎

Te enseño dos cosas:

1. **Cómo conectarte al WebSocket desde el frontend.**
2. **Cómo usar esos mensajes para refrescar una tabla automáticamente.**

Voy a asumir que usas **React**, pero te dejo también la versión “JS puro”.

---

## 1. Conexión básica al WebSocket (React)

Primero, crea un pequeño helper para la conexión:

```js
// wsClient.js
export function connectToIncidentesWebSocket(onMessage) {
  // Pon aquí la URL que te devuelve `sls deploy`
  const WS_URL = "wss://dz0y9xvmal.execute-api.us-east-1.amazonaws.com/production";

  const ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    console.log("✅ WebSocket conectado");
  };

  ws.onclose = (event) => {
    console.log("❌ WebSocket cerrado", event.code, event.reason);
    // Aquí podrías intentar reconectar si quieres
  };

  ws.onerror = (err) => {
    console.error("⚠️ Error en WebSocket", err);
  };

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      onMessage(msg);
    } catch (e) {
      console.error("Mensaje WS inválido:", event.data);
    }
  };

  return ws;
}
```

---

## 2. Componente React que se mantiene sincronizado

Este componente:

* Hace un **fetch inicial** (REST) de los incidentes (puedes apuntarlo a tu API HTTP).
* Se conecta al WebSocket.
* Cada vez que llega un mensaje del stream (`eventName`, `newImage`, `oldImage`),
  actualiza el estado `incidentes`.
* El usuario solo ve que la tabla “se mueve” sola.

```jsx
// ListaIncidentes.jsx
import { useEffect, useState } from "react";
import { connectToIncidentesWebSocket } from "./wsClient";

export default function ListaIncidentes() {
  const [incidentes, setIncidentes] = useState([]);

  useEffect(() => {
    // 1. Cargar la data inicial (ajusta la URL a tu API REST)
    fetch("https://tu-api-rest.com/incidentes")
      .then((res) => res.json())
      .then((data) => {
        // data debe ser un array de incidentes [{id, titulo, estado, ...}]
        setIncidentes(data);
      })
      .catch((err) => console.error("Error cargando incidentes:", err));

    // 2. Conectar al WebSocket
    const ws = connectToIncidentesWebSocket((msg) => {
      console.log("📩 Mensaje WS:", msg);

      const { eventName, newImage, oldImage } = msg;

      // INSERT → agregamos
      if (eventName === "INSERT" && newImage) {
        setIncidentes((prev) => {
          // evitar duplicados si ya estaba
          if (prev.some((i) => i.id === newImage.id)) return prev;
          return [...prev, newImage];
        });
      }

      // MODIFY → reemplazamos el incidente
      if (eventName === "MODIFY" && newImage) {
        setIncidentes((prev) =>
          prev.map((i) => (i.id === newImage.id ? newImage : i))
        );
      }

      // REMOVE → lo sacamos de la lista
      if (eventName === "REMOVE" && oldImage) {
        setIncidentes((prev) =>
          prev.filter((i) => i.id !== oldImage.id)
        );
      }
    });

    // 3. Limpiar cuando se desmonte el componente
    return () => {
      ws.close();
    };
  }, []);

  return (
    <div>
      <h2>Incidentes en tiempo real</h2>
      <table border="1" cellPadding="4">
        <thead>
          <tr>
            <th>ID</th>
            <th>Título</th>
            <th>Estado</th>
            <th>Ubicación</th>
            <th>Urgencia</th>
          </tr>
        </thead>
        <tbody>
          {incidentes.map((inc) => (
            <tr key={inc.id}>
              <td>{inc.id}</td>
              <td>{inc.titulo}</td>
              <td>{inc.estado}</td>
              <td>{inc.ubicacion || "-"}</td>
              <td>{inc.urgencia || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

👉 Fíjate que:

* **No hay notificaciones, ni alerts, ni toasts.**
  El mensaje se usa solo para mantener el `state` actualizado.
* Cada vez que tu backend toque la tabla `Incidentes`, el stream manda un mensaje → el componente lo procesa → la tabla se re-renderiza sola.

---

## 3. Versión ultra simple en HTML + JS puro

Si quieres probar sin React, algo mínimo:

```html
<!DOCTYPE html>
<html>
  <body>
    <h2>Incidentes en tiempo real</h2>
    <pre id="log"></pre>

    <script>
      const log = (msg) => {
        document.getElementById("log").textContent += msg + "\n";
      };

      const WS_URL =
        "wss://dz0y9xvmal.execute-api.us-east-1.amazonaws.com/production";

      const ws = new WebSocket(WS_URL);

      ws.onopen = () => log("✅ Conectado");
      ws.onclose = () => log("❌ Desconectado");
      ws.onerror = (e) => log("⚠️ Error: " + e.message);

      ws.onmessage = (event) => {
        log("📩 " + event.data);
        // Aquí podrías parsear el JSON y actualizar el DOM:
        // const msg = JSON.parse(event.data);
      };
    </script>
  </body>
</html>
```

Ahí verías en `log` exactamente lo que ya viste en el tester, pero desde tu propia página.

---

## 4. Resumen

* El **backend ya hace el trabajo duro**:
  DynamoDB Stream → Lambda → WebSocket → mensaje `{eventName, newImage, oldImage}` a todos.
* En el **frontend**:

  * Te conectas al WebSocket con la URL del API (`wss://.../production`).
  * Escuchas `onmessage`.
  * Usas el contenido del mensaje para actualizar tu estado (`useState`) o el DOM.
* Con eso, cada cambio en la tabla se refleja automáticamente en la UI, sin que el usuario toque nada.

Si me dices qué estás usando exactamente en el frontend (React/Vite, Next, puro HTML con `<script>`, etc.), puedo adaptarte el código justo al setup que tienes.
