# 🚨 Solución al Error de GitHub: "Push cannot contain secrets"

## Problema

GitHub detectó credenciales de AWS en el archivo `env.template` y bloqueó el push por seguridad.

## ✅ Solución Rápida

### Paso 1: Eliminar credenciales del commit actual

```bash
# Si es el último commit, puedes hacer amend
git commit --amend
# El archivo env.template ya está corregido (sin credenciales)
git push --force-with-lease
```

### Paso 2: Si ya hiciste push anteriormente

Necesitas eliminar las credenciales del historial:

```bash
# Opción A: Si solo quieres eliminar del último commit
git reset --soft HEAD~1
# Editar env.template para quitar credenciales (ya está hecho)
git add env.template
git commit -m "Remove credentials from env.template"
git push --force-with-lease
```

### Paso 3: Verificar que .env está en .gitignore

```bash
# Verificar
cat .gitignore | grep "\.env"

# Si no aparece, ya está agregado en airflow-assignment/.gitignore
```

## 📝 Flujo Correcto para el Futuro

1. **NUNCA** pongas credenciales en `env.template`
2. Copia el template a `.env`:
   ```bash
   cp env.template .env
   ```
3. Edita `.env` con tus credenciales (este archivo NO se commitea)
4. Solo commitea `env.template` (sin credenciales)

## 🔑 Obtener Nuevas Credenciales

Si las credenciales ya fueron expuestas:

1. **ROTAR las credenciales inmediatamente** en AWS Academy
2. Obtener nuevas credenciales
3. Ponerlas SOLO en el archivo `.env` (nunca en `env.template`)

## ✅ Verificación

Antes de hacer commit:

```bash
# Ver qué se va a committear
git status

# Verificar que .env NO aparece
# Si aparece, agregarlo a .gitignore:
echo ".env" >> .gitignore
git rm --cached .env
```

## 🎯 Comandos para Resolver Ahora

```bash
# 1. Asegurarte de que estás en la rama correcta
git status

# 2. El archivo env.template ya está corregido (sin credenciales)
# Verificar que está correcto:
cat airflow-assignment/env.template | grep "AWS_ACCESS_KEY_ID"

# Debe mostrar: AWS_ACCESS_KEY_ID= (vacío)

# 3. Hacer commit del cambio
git add airflow-assignment/env.template
git commit -m "Remove AWS credentials from env.template - use .env file instead"

# 4. Hacer push
git push
```

Si aún tienes problemas, puedes usar:

```bash
# Forzar el push (solo si es necesario)
git push --force-with-lease
```

