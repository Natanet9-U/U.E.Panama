# Tests de Integración - U.E. Panama

## 1. Tests de Autenticación (auth_integration_tests.py)
- [ ] `test_usuario_login_exitoso` - Usuario existente login con credenciales correctas
- [ ] `test_usuario_login_fallido_password_incorrecto` - Login fallido con contraseña incorrecta
- [ ] `test_usuario_login_email_no_existe` - Login fallido con email que no existe
- [ ] `test_crear_usuario_y_login` - Flujo: crear usuario > login > obtener token
- [ ] `test_token_validacion_en_protected_route` - Token válido permite acceso
- [ ] `test_token_invalido_rechaza_acceso` - Token inválido rechaza acceso
- [ ] `test_sin_token_rechaza_acceso` - Sin token rechaza acceso
- [ ] `test_logout_invalida_token` - Token inválido después de logout
- [ ] `test_refresh_token` - Renovar token expirado

## 2. Tests de Usuarios (usuarios_integration_tests.py)
- [ ] `test_crear_usuario_completo` - Crear usuario con todos los campos
- [ ] `test_crear_usuario_email_duplicado` - Falla al crear usuario con email existente
- [ ] `test_crear_usuario_ci_duplicado` - Falla al crear usuario con CI existente
- [ ] `test_obtener_usuario_por_id` - GET /api/usuarios/<id>
- [ ] `test_listar_todos_usuarios` - GET /api/usuarios (con paginación)
- [ ] `test_filtrar_usuarios_por_estado_activo` - Filtrar usuarios activos/inactivos
- [ ] `test_buscar_usuarios_por_nombre` - Búsqueda por nombre o apellido
- [ ] `test_actualizar_usuario` - PUT /api/usuarios/<id> actualizar campos
- [ ] `test_desactivar_usuario` - Cambiar estado a inactivo (soft delete)
- [ ] `test_eliminar_usuario` - DELETE /api/usuarios/<id>

## 3. Tests de Estudiantes (estudiantes_integration_tests.py)
- [ ] `test_crear_estudiante_con_usuario_existente` - Crear estudiante vinculado a usuario
- [ ] `test_crear_estudiante_asignar_grado` - Crear estudiante y asignar grado
- [ ] `test_crear_estudiante_asignar_tutor` - Crear estudiante con tutor
- [ ] `test_obtener_estudiantes_por_grado` - Listar estudiantes de un grado específico
- [ ] `test_obtener_estudiantes_por_tutor` - Listar estudiantes de un tutor
- [ ] `test_cambiar_grado_estudiante` - Cambiar estudiante de grado
- [ ] `test_cambiar_tutor_estudiante` - Cambiar tutor de estudiante
- [ ] `test_estudiante_promedio_calificaciones` - Calcular promedio del estudiante

## 4. Tests de Docentes (docentes_integration_tests.py)
- [ ] `test_crear_docente_con_usuario` - Crear docente vinculado a usuario
- [ ] `test_asignar_docente_a_asignatura` - Asignar docente a una asignatura
- [ ] `test_docente_puede_crear_evaluacion` - Docente crea evaluación
- [ ] `test_docente_solo_ve_sus_estudiantes` - Docente solo ve estudiantes asignados
- [ ] `test_listar_asignaturas_por_docente` - Obtener asignaturas del docente

## 5. Tests de Grados (grados_integration_tests.py)
- [ ] `test_crear_grado_primaria` - Crear grado de primaria
- [ ] `test_crear_grado_secundaria` - Crear grado de secundaria
- [ ] `test_obtener_estudiantes_del_grado` - Listar estudiantes de un grado
- [ ] `test_obtener_docentes_del_grado` - Listar docentes asignados al grado
- [ ] `test_no_duplicar_grado_nivel_numero_paralelo` - Validar unicidad del grado

## 6. Tests de Notas y Evaluaciones (notas_integration_tests.py)
- [ ] `test_crear_nota_estudiante` - Crear nota para un estudiante
- [ ] `test_crear_nota_invalida_fuera_rango` - Falla si nota < 0 o > 100
- [ ] `test_docente_crea_nota_su_asignatura` - Docente solo crea notas en su asignatura
- [ ] `test_no_puede_crear_nota_otro_docente` - Autorización: no crear nota de otro docente
- [ ] `test_obtener_notas_estudiante` - Listar notas de un estudiante
- [ ] `test_obtener_notas_por_asignatura` - Listar notas por asignatura
- [ ] `test_actualizar_nota_antes_fecha_cierre` - Actualizar nota antes de fecha límite
- [ ] `test_no_actualizar_nota_despues_fecha_cierre` - Falla después de fecha cierre
- [ ] `test_calcular_promedio_asignatura` - Promedio de notas en asignatura

## 7. Tests de Períodos Académicos (periodos_integration_tests.py)
- [ ] `test_crear_periodo_academico` - Crear nuevo período
- [ ] `test_obtener_periodo_actual` - Obtener período académico vigente
- [ ] `test_cambiar_periodo_activo` - Cambiar período activo
- [ ] `test_no_crear_periodos_solapados` - Validar que períodos no se superpongan

## 8. Tests de Roles y Permisos (roles_integration_tests.py)
- [ ] `test_usuario_admin_puede_crear_usuarios` - Admin: crear usuarios
- [ ] `test_usuario_docente_no_puede_crear_usuarios` - Docente: no puede crear usuarios
- [ ] `test_usuario_estudiante_solo_ve_sus_datos` - Estudiante: acceso solo a sus datos
- [ ] `test_cambiar_rol_usuario` - Cambiar rol de usuario
- [ ] `test_asignar_multiples_roles` - Usuario puede tener múltiples roles

## 9. Tests de Middleware y Validación (middleware_integration_tests.py)
- [ ] `test_middleware_log_request` - Middleware registra requests
- [ ] `test_middleware_log_error` - Middleware registra errores
- [ ] `test_cors_headers_presentes` - Respuesta tiene headers CORS
- [ ] `test_request_con_caracteres_especiales` - Validar XSS prevention
- [ ] `test_validar_input_sql_injection` - Prevenir SQL injection

## 10. Tests de Flujos Completos (workflows_integration_tests.py)
- [ ] `test_workflow_creacion_escuela` - Crear estructura: grados > asignaturas > docentes > estudiantes
- [ ] `test_workflow_creacion_estudiante_y_asignacion` - Crear estudiante > asignar grado > asignar tutor
- [ ] `test_workflow_evaluacion_completa` - Docente crea evaluación > califica > estudiante ve nota
- [ ] `test_workflow_cambio_grado_estudiante` - Cambiar estudiante de grado (con todas sus relaciones)
- [ ] `test_workflow_cierre_periodo` - Cierre de período > generar boletín > archivar datos

## 11. Tests de Base de Datos (database_integrity_tests.py)
- [ ] `test_cascade_delete_usuario` - Eliminar usuario elimina sus relaciones
- [ ] `test_cascade_delete_grado` - Eliminar grado actualiza estudiantes
- [ ] `test_integridad_referencial_estudiante_grado` - Validar FK a grado
- [ ] `test_transaccion_rollback` - Falla en transacción revierte cambios
- [ ] `test_unique_constraint_email` - Constraint único en email funciona
- [ ] `test_unique_constraint_ci` - Constraint único en CI funciona

## 12. Tests de Servicios (services_integration_tests.py)
- [ ] `test_auth_service_create_token` - Servicio de auth crea token
- [ ] `test_auth_service_decode_token` - Servicio decodifica token
- [ ] `test_auth_service_token_expired` - Validar expiración de token
- [ ] `test_email_service_envio_confirmacion` - Enviar email de confirmación
- [ ] `test_reporte_service_generar_boletín` - Generar boletín académico

---

**Total: ~95+ Tests de Integración**

### Por Prioridad:
1. **Crítico**: Autenticación, Usuarios, Estudiantes, Notas
2. **Alta**: Docentes, Grados, Roles, Flujos completos
3. **Media**: Períodos, Middleware, Servicios
4. **Baja**: Validaciones adicionales, Casos edge
