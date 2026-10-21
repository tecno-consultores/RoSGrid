# Banderas Nativas e Identificadores en MikroTik RouterOS v7

Guía de referencia rápida para que el agente interprete la nomenclatura y estados de RouterOS devueltos en las respuestas JSON de la API REST (`/rest/*`) y del servidor MCP.

---

## 1. Banderas Estándar de RouterOS (Flags)

En las tablas de configuración (firewall, interfaces, rutas, pools, colas), RouterOS etiqueta los registros con flags uniletéricas que el agente debe respetar:

- **`[D]` (*Dynamic*):**
  - **Significado:** Registro generado automáticamente por un demonio o protocolo (ej. rutas BGP/OSPF aprendidas, direcciones asignadas por DHCP Client, leases activos, colas dinámicas PPPoE).
  - **Regla del Agente:** **Prohibido modificar o eliminar directamente registros `[D]`.** Para cambiar un parámetro dinámico, se debe modificar el perfil padre o la configuración del servicio emisor.
- **`[X]` (*Disabled*):**
  - **Significado:** Registro desactivado administrativamente (`disabled=true`).
  - **Regla del Agente:** La regla no procesa tráfico ni afecta el enrutamiento. Si se requiere reactivar, se debe emitir un `PATCH` con `{"disabled": false}` mediante el flujo Maker-Checker.
- **`[I]` (*Invalid*):**
  - **Significado:** Registro que apunta a un recurso inexistente o mal configurado (ej. regla de firewall asociada a una interfaz eliminada, o ruta estática con gateway inalcanzable).
  - **Regla del Agente:** Debe ser señalada como anomalía prioritaria en auditorías y reportes de diagnóstico.
- **`[R]` (*Running*):**
  - **Significado:** Interfaz física o lógica activa con enlace arriba (*link up*).
  - **Regla del Agente:** Si un puerto SFP o Ethernet no tiene el flag `[R]`, existe un problema en Capa 1 (cable desconectado, SFP sin potencia óptica o puerto apagado con `[X]`).

---

## 2. Identificadores Internos de RouterOS (`.id`)

- RouterOS v7 utiliza identificadores internos hexadecimales precedidos por un asterisco: `*1`, `*1A`, `*2B`.
- Al realizar mutaciones vía `rosgrid_propose_network_change` o consultas REST específicas, siempre que se haga referencia a un registro existente, debe utilizarse el `.id` exacto o el selector único (ej. `numbers`).
- Los `.id` son efímeros entre reinicios del enrutador o tras la eliminación de registros; nunca deben asumirse fijos a través del tiempo.
