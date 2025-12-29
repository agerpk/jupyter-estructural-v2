# QA Testing Protocol

## Regla Fundamental
**LA IA NUNCA PUEDE MARCAR PROBLEMAS COMO RESUELTOS. SOLO EL USUARIO PUEDE HACERLO.**

## Estados de Problemas

### ❌ FALLA
- Problema identificado y confirmado por el usuario
- Requiere implementación de fix

### 🔧 TESTING PENDIENTE  
- Fix implementado por la IA
- Esperando testing y confirmación del usuario
- **LA IA SIEMPRE DEBE USAR ESTE ESTADO DESPUÉS DE IMPLEMENTAR FIXES**
- **NUNCA cambiar a RESUELTO sin confirmación explícita del usuario**

### ✅ RESUELTO
- **SOLO el usuario puede marcar problemas como RESUELTOS**
- Requiere testing exitoso y confirmación explícita del usuario
- **LA IA NUNCA DEBE USAR ESTE ESTADO**

## Workflow

1. **Usuario identifica problema** → Estado: ❌ FALLA
2. **IA implementa fix** → Estado: 🔧 TESTING PENDIENTE  
3. **Usuario confirma que funciona** → Estado: ✅ RESUELTO

## Responsabilidades

### IA:
- Implementar fixes
- **SIEMPRE marcar como "TESTING PENDIENTE" después de implementar**
- **NUNCA marcar como "RESUELTO" bajo ninguna circunstancia**

### Usuario:
- Identificar problemas
- Testing de fixes
- **ÚNICO autorizado para marcar como "RESUELTO"**

## IMPORTANTE PARA FUTURAS SESIONES
**La IA debe recordar que NUNCA puede resolver problemas, solo implementar fixes y marcarlos como TESTING PENDIENTE.**