# FAKTO – Plataforma CRM Multi-Tenant

## Descripción General
FAKTO es una solución SaaS CRM para equipos comerciales, diseñada para la industria de alimentos y adaptable a cualquier sector. Ofrece gestión avanzada de clientes, ventas, productos, contactos, historial y auditoría, con arquitectura multi-tenant, seguridad de nivel empresarial y automatización de procesos.

---

## Características Principales
- **Multi-tenant**: Aislamiento total de datos por empresa/cliente (tenant).
- **Seguridad avanzada**: Políticas RLS en todas las tablas sensibles.
- **Auditoría completa**: Registro automático de todas las operaciones críticas.
- **Soft delete**: Borrado lógico en todas las tablas clave.
- **Automatización**: Triggers para historial, protección de integridad y notificaciones.
- **Gestión de usuarios y preferencias**: Onboarding, invitaciones, preferencias personalizadas.
- **Escalabilidad**: Estructura preparada para integraciones externas y dashboards avanzados.

---

## Estructura de Tablas Clave
- `users`: Usuarios del sistema, roles, preferencias, último acceso, soft delete.
- `companies`: Empresas gestionadas, asignaciones, categorías, geolocalización, soft delete.
- `company_contacts`: Múltiples contactos por empresa, contacto principal, validación, soft delete.
- `company_assignments`: Historial de asignaciones de empresas a usuarios.
- `audit_logs`: Log centralizado de todas las operaciones críticas.
- `notification_events`: Eventos para notificaciones automáticas.
- `user_preferences`: Preferencias personalizadas por usuario.
- `user_invitations`: Invitaciones y onboarding de nuevos usuarios.
- `access_logs`: Registro de accesos y dispositivos.

---

## Seguridad y Gobernanza
- **RLS (Row Level Security)**: Acceso restringido por tenant y rol en todas las tablas sensibles.
- **Triggers**: Automatización de auditoría, historial, protección ante borrados y notificaciones.
- **Integridad referencial**: Foreign keys y restricciones para evitar inconsistencias.

---

## Auditoría y Trazabilidad
- Todas las operaciones (INSERT, UPDATE, DELETE/soft delete) se registran en `audit_logs`.
- Soft delete: Los registros no se eliminan físicamente, se marca la fecha en `deleted_at`.
- Historial de asignaciones y contactos siempre disponible.

### Ejemplo de consulta de auditoría
```sql
SELECT * FROM public.audit_logs WHERE table_name = 'companies' AND record_id = 'EMPRESA_UUID' ORDER BY timestamp DESC;
```

---

## Scripts de Ejemplo
- **Insertar empresa:**
```sql
INSERT INTO public.companies (client_name, tenant_id, assigned_to) VALUES ('Ejemplo S.A.', 'TENANT_UUID', 'USER_UUID');
```
- **Soft delete:**
```sql
DELETE FROM public.companies WHERE id = 'EMPRESA_UUID';
```
- **Reasignar empresas:**
```sql
SELECT public.reassign_companies_on_user_deactivation('USER_ORIGEN_UUID', 'USER_DESTINO_UUID');
```
- **Consultar logs de auditoría:**
```sql
SELECT * FROM public.audit_logs WHERE table_name = 'companies' AND timestamp > now() - interval '30 days';
```
- **Registrar preferencias de usuario:**
```sql
INSERT INTO public.user_preferences (user_id, language, theme) VALUES ('USER_UUID', 'es', 'dark') ON CONFLICT (user_id) DO UPDATE SET language = EXCLUDED.language, theme = EXCLUDED.theme;
```

---

## Recomendaciones de Operación
- Realizar backups periódicos y validar restauraciones.
- Auditar logs y accesos regularmente.
- Mantener documentación y políticas RLS actualizadas.
- Usar soft delete y triggers en todas las operaciones críticas.
- Aprovechar materialized views y logs para dashboards y KPIs.

---

## Recursos Útiles
- [Supabase RLS Docs](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Triggers](https://www.postgresql.org/docs/current/plpgsql-trigger.html)

---

## Contacto y soporte
Para dudas técnicas, onboarding de nuevos usuarios o integración con sistemas externos, contacta a tu equipo de desarrollo o soporte FAKTO.
