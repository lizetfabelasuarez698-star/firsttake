# First Take: verificar etiquetas de Instagram

Cuando un creador etiqueta al negocio en un post de Instagram, el sistema lo
verifica solo y le activa su beneficio (descuento o producto). Un premio por
creador, y solo si usó el @handle real.

## El algoritmo, paso a paso

```
Llega aviso de Meta
  │
  ├─ ¿La firma es de Meta?            no → rechazar (401)
  │
  ├─ Por cada publicación mencionada:
  │    ├─ ¿Fue en un comentario?       sí → ignorar
  │    ├─ Pedir el post a Instagram (texto + autor)
  │    ├─ ¿El texto trae @handle EXACTO del negocio?   no → ignorar  (Caso 3)
  │    ├─ ¿El autor es un creador registrado?         no → ignorar
  │    └─ ¿Es su primer canje? (revisar y guardar en un paso)
  │           sí → ACTIVAR beneficio                         (Caso 1)
  │           no → ignorar, ya canjeó                        (Caso 2)
  │
  └─ Responder 200 a Meta
```

## Qué hay en cada archivo

| Archivo | Qué hace |
|---|---|
| `api/verify-tag.py` | La función de servidor `/api/verify-tag` en Vercel. Único lugar que lee el token. |
| `verificacion/menciones.py` | Lógica pura: encuentra los @handles y decide. Sin internet. |
| `verificacion/webhook.py` | Une todo: firma → posts → decisión → canje. |
| `verificacion/instagram.py` | Habla con la Graph API de Instagram. |
| `verificacion/canjes.py` | La tabla de canjes (`redemptions`): memoria, Upstash Redis o Supabase. |
| `datos/creadores.json` | Lista de creadores y el beneficio de cada uno. |
| `pruebas/` | Pruebas de los 3 casos, con un Instagram falso. |

## Correr las pruebas

```bash
cd /Users/lizetfabela/proyectos/first-take
```

```bash
python3 -m unittest discover -s pruebas -t . -v
```

## Publicar en Vercel (cuando estés lista)

1. Sube esta carpeta a Vercel (`vercel` desde la terminal o importándola desde GitHub).
2. Pon las variables de `.env.example` en Project > Settings > Environment Variables.
3. En tu app de Meta, Webhooks de Instagram: URL `https://<tu-proyecto>.vercel.app/api/verify-tag`,
   el mismo `META_VERIFY_TOKEN`, y suscríbete al campo `mentions`.

## Supabase (3.21)

1. Crea el proyecto en supabase.com (ver Pre-Class Work de 3.21).
2. Corre `supabase/schema.sql` en el SQL Editor de tu proyecto: crea la
   tabla `redemptions` con Row Level Security.
3. En Vercel, Project > Settings > Environment Variables, agrega
   `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` (la service_role, NO la
   publishable/anon — ver `.env.example`).
4. Con esas dos variables presentes, `api/verify-tag.py` usa
   `AlmacenSupabase` en vez de Upstash o memoria, sin tocar nada más.

## Límites que hay que saber

- **Historias**: no entran. Las menciones en historias llegan por otro webhook y piden el
  permiso `instagram_manage_messages`.
- **Canjes en Vercel**: sin Upstash, los canjes viven en memoria y se pierden entre llamadas,
  así que el Caso 2 solo se cumple en producción con Upstash configurado.
- El creador se identifica por su @usuario; si se lo cambia, cuenta como otra persona.
