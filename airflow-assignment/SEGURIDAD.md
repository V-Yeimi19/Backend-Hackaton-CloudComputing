# 🔒 Seguridad - Credenciales de AWS

## ⚠️ IMPORTANTE

**NUNCA** commitees credenciales de AWS al repositorio. GitHub detecta automáticamente secretos y bloqueará el push.

## ✅ Solución al Error de GitHub

Si recibiste un error de "Push cannot contain secrets", sigue estos pasos:

### 1. Eliminar credenciales del historial

```bash
# Opción A: Usar git filter-branch (si ya hiciste commit)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch airflow-assignment/env.template" \
  --prune-empty --tag-name-filter cat -- --all

# Opción B: Si es el último commit, hacer amend
git commit --amend
# Editar el archivo para quitar las credenciales
git push --force-with-lease
```

### 2. Verificar que .env está en .gitignore

El archivo `.env` (donde van tus credenciales reales) debe estar en `.gitignore`:

```bash
# Verificar
cat .gitignore | grep "\.env"

# Si no está, agregarlo
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
```

### 3. Usar el template correctamente

1. **NO** edites `env.template` con credenciales reales
2. Copia el template a `.env`:
   ```bash
   cp env.template .env
   ```
3. Edita `.env` (que está en .gitignore) con tus credenciales
4. El archivo `.env` nunca se subirá al repositorio

## 📝 Flujo Correcto

```bash
# 1. Copiar template
cp env.template .env

# 2. Editar .env con tus credenciales (localmente, no se commitea)
nano .env  # o tu editor preferido

# 3. Verificar que .env no está en git
git status  # .env NO debe aparecer

# 4. Solo commitea env.template (sin credenciales)
git add env.template
git commit -m "Update env template"
```

## 🔑 Obtener Credenciales de AWS Academy

1. Ve a AWS Academy
2. Accede a tu laboratorio
3. Haz clic en "AWS Details" o "Show"
4. Copia las credenciales
5. Péguelas SOLO en el archivo `.env` (nunca en `env.template`)

## ✅ Verificación

Antes de hacer commit, verifica:

```bash
# Ver qué archivos se van a committear
git status

# Verificar que .env NO está listado
# Si aparece, agregarlo a .gitignore:
echo ".env" >> .gitignore
git rm --cached .env
```

## 🚨 Si ya hiciste commit con credenciales

1. **Rotar las credenciales inmediatamente** en AWS Academy
2. Eliminar el commit del historial (ver paso 1 arriba)
3. Asegurarte de que `.env` está en `.gitignore`
4. Usar solo `env.template` (sin credenciales) en el repositorio

