# Comandos Git para Merge de Ramas

## Objetivo
Mergear `develop_nodos` → `develop` → `main`, y luego volver a `develop_nodos` con todo sincronizado.

**Actualización**: Después de mergear, borrar `develop_nodos` y continuar en `develop`.

## Comandos a Ejecutar

### 1. Asegurarse de estar en develop_nodos y commitear cambios

```bash
# Verificar rama actual
git branch

# Si hay cambios sin commitear, agregarlos
git status
git add .
git commit -m "Fix DGE: Vista vacía, callbacks separados, modal nodos con toast"
```

### 2. Cambiar a develop y mergear develop_nodos

```bash
# Cambiar a develop
git checkout develop

# Mergear develop_nodos en develop
git merge develop_nodos

# Si hay conflictos, resolverlos y luego:
# git add .
# git commit -m "Merge develop_nodos into develop"
```

### 3. Cambiar a main y mergear develop

```bash
# Cambiar a main
git checkout main

# Mergear develop en main
git merge develop

# Si hay conflictos, resolverlos y luego:
# git add .
# git commit -m "Merge develop into main"
```

### 4. Volver a develop_nodos y sincronizar

```bash
# Volver a develop_nodos
git checkout develop_nodos

# Mergear main en develop_nodos para sincronizar
git merge main

# O alternativamente, mergear develop:
# git merge develop
```

### 5. Verificar estado final

```bash
# Verificar que estás en develop_nodos
git branch

# Ver el log para confirmar que todo está sincronizado
git log --oneline --graph --all -10
```

## Resultado Final

Después de ejecutar estos comandos:
- ✅ `develop_nodos` tiene todos los cambios
- ✅ `develop` tiene todos los cambios de `develop_nodos`
- ✅ `main` tiene todos los cambios de `develop`
- ✅ Estás de vuelta en `develop_nodos`
- ✅ Las tres ramas están sincronizadas

## Comandos Resumidos (Sin Conflictos)

```bash
# Desde develop_nodos
git add .
git commit -m "Fix DGE: Vista vacía, callbacks separados, modal nodos con toast"

# Mergear a develop
git checkout develop
git merge develop_nodos

# Mergear a main
git checkout main
git merge develop

# Volver a develop_nodos y sincronizar
git checkout develop_nodos
git merge main
```

## Si Quieres Hacer Push a Remoto

```bash
# Después de los merges locales, hacer push de todas las ramas
git push origin develop_nodos
git push origin develop
git push origin main
```

## Notas Importantes

- Si hay conflictos durante el merge, Git te pedirá que los resuelvas manualmente
- Usa `git status` para ver qué archivos tienen conflictos
- Después de resolver conflictos: `git add .` y `git commit`
- Si quieres abortar un merge: `git merge --abort`

## Verificación de Sincronización

Para verificar que las tres ramas están en el mismo estado:

```bash
# Ver el último commit de cada rama
git log develop_nodos -1 --oneline
git log develop -1 --oneline
git log main -1 --oneline

# Si los tres muestran el mismo commit hash, están sincronizadas
```

---

## Borrar Rama develop_nodos (Local y Remoto)

Después de mergear todo y ya no necesitar la rama `develop_nodos`:

### 1. Cambiar a develop

```bash
# Asegurarse de NO estar en la rama que vas a borrar
git checkout develop
```

### 2. Borrar rama local

```bash
# Borrar rama local develop_nodos
git branch -d develop_nodos

# Si Git no te deja borrarla (porque no está mergeada), forzar:
# git branch -D develop_nodos
```

### 3. Borrar rama remota

```bash
# Borrar rama del repositorio remoto
git push origin --delete develop_nodos
```

### 4. Verificar que se borró

```bash
# Ver ramas locales
git branch

# Ver ramas remotas
git branch -r

# Ver todas las ramas
git branch -a
```

### Comandos Resumidos

```bash
# Cambiar a develop
git checkout develop

# Borrar rama local
git branch -d develop_nodos

# Borrar rama remota
git push origin --delete develop_nodos
```

### Resultado Final

- ✅ Estás en rama `develop`
- ✅ Rama `develop_nodos` borrada localmente
- ✅ Rama `develop_nodos` borrada del remoto
- ✅ Todos los cambios están en `develop` y `main`

### Notas

- `-d` borra la rama solo si está completamente mergeada
- `-D` fuerza el borrado incluso si no está mergeada
- Usa `-d` para seguridad (te avisará si hay commits sin mergear)
