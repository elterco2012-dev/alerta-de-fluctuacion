# Wurth Argentina — Sistema de Alertas de Rotación de Vendedores

Detección temprana de riesgo de fuga de vendedores. La permanencia promedio cayó de 18 meses
(hace 10 años) a 5 meses hoy. El objetivo es detectar señales de deterioro **antes** de que
el vendedor renuncie, no analizar por qué se fue.

---

## Puesta en marcha (primera vez)

**Prerequisitos:** Python 64-bit y Python 32-bit instalados en Windows, con acceso a los DSN
de ODBC configurados en el equipo (MSPA = Informix, SUNDB = SQL Server, Wurth Reactor Produccion = MySQL).

```bat
:: 1. Poblar la base de datos desde las fuentes reales (Python 32-bit, ODBC)
scripts\inicializar_db.bat
scripts\sincronizar_todo.bat   (o sync_y_alertas.bat para también enviar alertas)

:: 2. Crear el primer usuario del dashboard
scripts\usuarios.bat alta <nombre_usuario> <contraseña> "Gerencia"

:: 3. Levantar el dashboard
streamlit run dashboard.py
```

> **Python 32-bit vs 64-bit:** los scripts de sincronización usan ODBC (Informix 32-bit).
> El dashboard y los scripts de análisis usan Python 64-bit. Los `.bat` detectan ambas
> versiones automáticamente vía `scripts\python_paths.bat` — no hace falta modificarlos.

---

## Uso diario

```bat
:: Sync + alertas automático (configurar con programar_alertas.bat para correr todos los días)
scripts\sync_y_alertas.bat
```

---

## Gestión de usuarios

```bat
scripts\usuarios.bat alta    <usuario> <clave> "<clave_acceso>"   :: nueva cuenta
scripts\usuarios.bat baja    <usuario>                             :: dar de baja
scripts\usuarios.bat clave   <usuario> <nueva_clave>              :: cambiar contraseña
scripts\usuarios.bat lista                                         :: ver todos los usuarios
```

`<clave_acceso>` es el nombre del supervisor/director tal como aparece en la base, o `"Gerencia"` para acceso total.

Ejemplos:
```bat
scripts\usuarios.bat alta daniel MiClave123 "Gerencia"
scripts\usuarios.bat alta jsup ClaveSegura "Zerbatto Jose Luis"
```

---

## Niveles de riesgo (score 1-10)

| Score | Nivel   | Indicación visual |
|-------|---------|-------------------|
| 8-10  | Crítico | Rojo — mayor urgencia |
| 6-7   | Alto    | Naranja |
| 4-5   | Medio   | Amarillo |
| 1-3   | Bajo    | Verde |

**La acción operativa es por ranking, no por umbral:** ordenar por score descendente
y empezar por los de mayor score. El nivel "crítico" es un indicador visual, no un
corte rígido de "estos necesitan reunión y los demás no".

---

## Señales activas (motor de scoring)

| Señal | Peso |
|---|---|
| % Plan < 55% promedio últimos meses | 2.0 |
| Ausencias no vacaciones > 2 días/mes en ventana crítica 1-3 | 2.0 |
| Ventana crítica mes 1-3 | 1.5 |
| Grupo con alta rotación histórica (riesgo_base > 0.40) | 1.5 |
| Balanza clientes negativa 2+ meses consecutivos (suma < -60) | 1.5 |
| Ventana crítica mes 4-6 | 1.0 |
| Ticket promedio cae > 5% por mes | 1.0 |
| Supervisor no acompañó en ventana crítica 1-6 | 1.0 |
| Sin clientes nuevos últimos 2 meses | 0.5 |

`RIESGO_REFERENCIA = 8.0` → score 10 cuando un vendedor activa plan + ausencias + ventana + grupo quemado.

---

## Archivos que nunca van al repositorio

```
data/wurth.db            ← base de datos local con datos del ERP
data/estado_alertas.json ← timestamps de última alerta
data/auth.json           ← usuarios y contraseñas hasheadas
data/auth_fails.json     ← conteo de intentos fallidos de login
.env                     ← variables de entorno con credenciales
scripts/*.txt            ← salidas de scripts de exploración/diagnóstico
scripts/vart_diagnostico.csv
```

---

## Regla absoluta — bases de datos externas: solo lectura

Los scripts de sincronización solo hacen `SELECT` en Informix (MSPA), SQL Server (SUNDB)
y MySQL (Reactor). Nunca `INSERT`, `UPDATE`, `DELETE` ni DDL en esas bases. La única
base donde se escribe es `data/wurth.db` (SQLite local).
