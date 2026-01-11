# Implementación Revamp DGE - Sistema por Etapas

## Resumen Ejecutivo

Refactorización completa del sistema DGE (Diseño Geométrico de Estructuras) implementando un **sistema por etapas** que reemplaza el código monolítico actual con módulos especializados y mantenibles.

## 1. Arquitectura Actual vs Nueva

### 1.1 Funcionamiento Actual (Referencia: diseno_cabezales_por_configuracion.md)

**Método Monolítico**:
```python
# EstructuraAEA_Geometria.py - ACTUAL
def dimensionar_unifilar(self, vano, flecha_max_conductor, flecha_max_guardia):
    # Todo en un solo método de 500+ líneas
    theta_max = self.calcular_theta_max(vano)
    distancias = self.calcular_distancias_minimas(flecha_max_conductor, theta_max)
    h1a, h2a, h3a = self._calcular_alturas_fases(D_fases, s_estructura, flecha_max_conductor)
    self._crear_nodos_estructurales_nuevo(h1a, h2a, h3a)
    # ... más código mezclado
```

**Problemas Identificados**:
- Código monolítico difícil de mantener
- Lógica de guardia limitada (solo casos básicos)
- Checkeos insuficientes
- Gráficos básicos sin etapas intermedias
- No hay validación exhaustiva de zonas de prohibición

### 1.2 Arquitectura Nueva (Por Etapas)

**Selector Principal**:
```python
# EstructuraAEA_Geometria.py - NUEVO
class EstructuraAEA_Geometria:
    def dimensionar_unifilar(self, vano, flecha_max_conductor, flecha_max_guardia, **kwargs):
        """Selector que ejecuta etapas secuencialmente"""
        
        # Validación inicial
        if self.terna == "Doble" and self.disposicion == "horizontal":
            print("ERROR: Caso no programado - Terna doble disposición horizontal")
            raise NotImplementedError("Configuración no soportada")
        
        # Ejecutar etapas
        self.etapa0 = GeometriaEtapa0(self)
        self.etapa1 = GeometriaEtapa1(self)
        self.etapa2 = GeometriaEtapa2(self)
        self.etapa3 = GeometriaEtapa3(self)
        self.etapa4 = GeometriaEtapa4(self)
        self.etapa5 = GeometriaEtapa5(self)
        self.etapa6 = GeometriaEtapa6(self)
        
        self.etapa0.ejecutar()
        self.etapa1.ejecutar(vano, flecha_max_conductor, flecha_max_guardia)
        self.etapa2.ejecutar()
        self.etapa3.ejecutar()
        self.etapa4.ejecutar()
        self.etapa5.ejecutar()
        self.etapa6.ejecutar()
```

## 2. Implementación por Etapas

### 2.1 Etapa 0: Nodo Base

**Archivo**: `EstructuraAEA_Geometria_Etapa0.py`

```python
class GeometriaEtapa0:
    def ejecutar(self):
        print("🔧 ETAPA 0: Nodo Base")
        self.geo.nodos["BASE"] = NodoEstructural("BASE", (0.0, 0.0, 0.0), "base")
        print("   ✅ Nodo BASE creado en (0, 0, 0)")
```

### 2.2 Etapa 1: h1a y Lmen1 (Primer Amarre)

**Archivo**: `EstructuraAEA_Geometria_Etapa1.py`

**Fórmula h1a (OBLIGATORIA)**:
```python
h1a = a + b + fmax + Lk + HADD
```

**Componentes de la fórmula**:
- `a`: **Altura base** - Distancia mínima vertical desde el suelo hasta el punto más bajo del conductor en su flecha máxima. Garantiza seguridad de personas/vehículos bajo la línea.
- `b`: **Altura eléctrica** - Distancia de seguridad eléctrica adicional requerida por normativa (AEA) según nivel de tensión. Previene descargas eléctricas.
- `fmax`: **Flecha máxima del conductor** - Máxima distancia vertical que el conductor desciende desde el punto de amarre bajo condiciones climáticas extremas (temperatura máxima).
- `Lk`: **Longitud de cadena de aisladores** - Longitud total de la cadena de suspensión/retención que conecta el conductor a la estructura. Si Lk=0, el conductor está fijado directamente.
- `HADD`: **Altura adicional de seguridad** - Margen de seguridad adicional configurable por el diseñador para compensar incertidumbres o requisitos específicos del proyecto.

**Cálculo Lmen1 (Iterativo)**:

Lmen1 se calcula como la **mínima longitud de ménsula** a la cual la zona `s_decmax` del conductor en **declinación máxima** NO es infringida por elementos fijos.

```python
class GeometriaEtapa1:
    def __init__(self, geometria):
        self.geo = geometria
    
    def ejecutar(self, vano, flecha_max_conductor, flecha_max_guardia):
        print("🔧 ETAPA 1: h1a y Lmen1")
        
        # Calcular parámetros base
        theta_max = self.geo.calcular_theta_max(vano)
        distancias = self.geo.calcular_distancias_minimas(flecha_max_conductor, theta_max)
        
        # Calcular h1a con fórmula obligatoria
        a = self.geo.altura_base
        b = self.geo.altura_electrica
        fmax = flecha_max_conductor
        Lk = self.geo.lk
        HADD = self.geo.hadd
        h1a = a + b + fmax + Lk + HADD
        
        # Calcular Lmen1 iterativamente
        Lmen1 = self._calcular_lmen1_iterativo(h1a, distancias, theta_max)
        
        # Guardar resultados
        self.geo.dimensiones.update({
            "h1a": h1a,
            "Lmen1": Lmen1,
            "s_tormenta": distancias['s_estructura'],  # Default = s_reposo
            "s_decmax": distancias['s_estructura'],    # Default = s_tormenta
            **distancias
        })
        
        # Crear nodo CROSS en h1a (si no es horizontal simple)
        if not (self.geo.disposicion == "horizontal" and self.geo.terna == "Simple"):
            self.geo.nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
            print(f"   🔵 Nodo CROSS_H1 creado en (0, 0, {h1a:.2f})")
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ h1a={h1a:.2f}m, Lmen1={Lmen1:.2f}m")
    
    def _ejecutar_conectador(self):
        """Ejecutar conectador de nodos al finalizar etapa"""
        print("   🔌 Ejecutando conectador de nodos...")
        conexiones_anteriores = set(self.geo.conexiones) if hasattr(self.geo, 'conexiones') else set()
        
        # Generar conexiones (método existente)
        self.geo._generar_conexiones()
        
        # Listar conexiones NUEVAS
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
    
    def _calcular_lmen1_iterativo(self, h1a, distancias, theta_max):
        """Calcular Lmen1 chequeando zona s_decmax en declinación máxima"""
        
        # CASO ESPECIAL: Horizontal Simple con Lk=0
        if (self.geo.disposicion == "horizontal" and 
            self.geo.terna == "Simple" and 
            self.geo.lk == 0 and
            self.geo.tipo_estructura not in ["Suspensión", "Suspension"]):
            
            D_fases = distancias['D_fases']
            Lmen_minima = self.geo.long_mensula_min_conductor
            Lmen1 = max(D_fases, Lmen_minima)
            print(f"   🔵 Horizontal Simple Lk=0: Lmen1 = max(D_fases={D_fases:.2f}, Lmen_min={Lmen_minima:.2f}) = {Lmen1:.2f}m")
            return Lmen1
        
        # CASO GENERAL: Iterativo con s_decmax
        s_decmax = distancias['s_decmax']
        Lmen_minima = self.geo.long_mensula_min_conductor
        Lk = self.geo.lk
        
        # Posición del conductor en declinación máxima
        Lmen1 = Lmen_minima
        max_iteraciones = 100
        incremento = 0.05  # 5cm por iteración
        
        for i in range(max_iteraciones):
            # Calcular posición conductor declinado
            x_conductor = Lmen1 + Lk * math.sin(math.radians(theta_max))
            z_conductor = h1a - Lk * math.cos(math.radians(theta_max))
            
            # Verificar infracciones con elementos fijos
            infraccion_columna = self._verificar_infraccion_columna(x_conductor, z_conductor, s_decmax)
            infraccion_mensula = self._verificar_infraccion_mensula(Lmen1, h1a, x_conductor, z_conductor, s_decmax)
            
            if infraccion_columna:
                # Aumentar Lmen1
                Lmen1 += incremento
                continue
            
            if infraccion_mensula:
                if Lk > 0:
                    # ERROR: Lk muy corta, NO se puede resolver aumentando Lmen1
                    print("   ❌ ERROR: Lk longitud cadena oscilante muy corta")
                    raise ValueError("Lk insuficiente para evitar infracción con ménsula. Aumentar Lk manualmente.")
                else:
                    # Lk=0: permitido infracción con ménsula, pero NO con columna
                    if not infraccion_columna:
                        break
            
            # No hay infracciones
            break
        
        return max(Lmen1, Lmen_minima)
```

### 2.3 Etapa 2: h2a (Segundo Amarre)

**Archivo**: `EstructuraAEA_Geometria_Etapa2.py`

**Cálculo h2a con optimización por defasaje**:

```python
class GeometriaEtapa2:
    def ejecutar(self):
        print("🔧 ETAPA 2: h2a (segundo amarre)")
        
        # Calcular h2a_inicial
        h1a = self.geo.dimensiones["h1a"]
        D_fases = self.geo.dimensiones["D_fases"]
        s_reposo = self.geo.dimensiones["s_estructura"]
        Lk = self.geo.lk
        HADD_ENTRE_AMARRES = self.geo.hadd_entre_amarres
        
        if Lk > 0:
            h2a_inicial = max(
                h1a + D_fases + HADD_ENTRE_AMARRES,
                h1a + s_reposo + Lk + HADD_ENTRE_AMARRES
            )
        else:
            h2a_inicial = h1a + D_fases + HADD_ENTRE_AMARRES
        
        # Optimizar h2a si hay defasaje por hielo
        if self.geo.defasaje_mensula_hielo and self.geo.lmen_extra_hielo > 0:
            mensula_defasar = self.geo.mensula_defasar
            
            if mensula_defasar in ["primera", "primera y tercera"]:
                # Lmen1 fue incrementada, buscar zoptimo2
                Lmen2 = max(self.geo.dimensiones["Lmen1"], self.geo.long_mensula_min_conductor)
                zoptimo2 = self._buscar_altura_fuera_zonas_dfases(Lmen2, h1a, D_fases)
                h2a_final = zoptimo2 + HADD_ENTRE_AMARRES
                print(f"   🔵 Optimización por defasaje 'primera': h2a reducida a {h2a_final:.2f}m")
            elif mensula_defasar == "segunda":
                # Lmen2 será incrementada
                Lmen2 = max(self.geo.dimensiones["Lmen1"], self.geo.long_mensula_min_conductor) + self.geo.lmen_extra_hielo
                zoptimo2 = self._buscar_altura_fuera_zonas_dfases(Lmen2, h1a, D_fases)
                h2a_final = zoptimo2 + HADD_ENTRE_AMARRES
            else:
                h2a_final = h2a_inicial
        else:
            h2a_final = h2a_inicial
        
        self.geo.dimensiones["h2a"] = h2a_final
        
        # Crear nodo CROSS en h2a (si h2a > h1a)
        h1a = self.geo.dimensiones["h1a"]
        if h2a_final > h1a + 1e-3:  # Tolerancia 1mm
            self.geo.nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a_final), "cruce")
            print(f"   🔵 Nodo CROSS_H2 creado en (0, 0, {h2a_final:.2f})")
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ h2a={h2a_final:.2f}m")
    
    def _ejecutar_conectador(self):
        """Ejecutar conectador de nodos al finalizar etapa"""
        print("   🔌 Ejecutando conectador de nodos...")
        conexiones_anteriores = set(self.geo.conexiones)
        
        self.geo._generar_conexiones()
        
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
    
    def _buscar_altura_fuera_zonas_dfases(self, x_linea, h1a, D_fases):
        """Buscar altura mínima en línea x=x_linea que no infringe zonas D_fases de h1a"""
        Lk = self.geo.lk
        z_conductor_h1a = h1a - Lk
        
        # Zona prohibida D_fases alrededor de conductor h1a
        z_min_prohibida = z_conductor_h1a - D_fases
        z_max_prohibida = z_conductor_h1a + D_fases
        
        # Altura óptima: justo arriba de zona prohibida
        zoptimo2 = z_max_prohibida + Lk  # Sumar Lk porque es altura de amarre
        
        return zoptimo2
```

### 2.4 Etapa 3: h3a (Tercer Amarre)

**Archivo**: `EstructuraAEA_Geometria_Etapa3.py`

**Cálculo h3a con optimización por defasaje** (similar a Etapa 2):

```python
class GeometriaEtapa3:
    def ejecutar(self):
        print("🔧 ETAPA 3: h3a (tercer amarre)")
        
        # Solo aplica para disposición vertical
        if self.geo.disposicion != "vertical":
            print("   ⏭️  No aplica h3a para esta disposición (horizontal/triangular)")
            # NO asignar h3a, simplemente no existe
            return
        
        # Calcular h3a_inicial
        h2a = self.geo.dimensiones["h2a"]
        D_fases = self.geo.dimensiones["D_fases"]
        s_reposo = self.geo.dimensiones["s_estructura"]
        Lk = self.geo.lk
        HADD_ENTRE_AMARRES = self.geo.hadd_entre_amarres
        
        if Lk > 0:
            h3a_inicial = max(
                h2a + D_fases + HADD_ENTRE_AMARRES,
                h2a + s_reposo + Lk + HADD_ENTRE_AMARRES
            )
        else:
            h3a_inicial = h2a + D_fases + HADD_ENTRE_AMARRES
        
        # Optimizar h3a si hay defasaje por hielo
        if self.geo.defasaje_mensula_hielo and self.geo.lmen_extra_hielo > 0:
            mensula_defasar = self.geo.mensula_defasar
            
            if mensula_defasar in ["tercera", "primera y tercera"]:
                Lmen3 = max(self.geo.dimensiones["Lmen1"], self.geo.long_mensula_min_conductor) + self.geo.lmen_extra_hielo
                zoptimo3 = self._buscar_altura_fuera_zonas_dfases(Lmen3, h2a, D_fases)
                h3a_final = zoptimo3 + HADD_ENTRE_AMARRES
            elif mensula_defasar == "segunda":
                Lmen3 = max(self.geo.dimensiones["Lmen1"], self.geo.long_mensula_min_conductor)
                zoptimo3 = self._buscar_altura_fuera_zonas_dfases(Lmen3, h2a, D_fases)
                h3a_final = zoptimo3 + HADD_ENTRE_AMARRES
            else:
                h3a_final = h3a_inicial
        else:
            h3a_final = h3a_inicial
        
        self.geo.dimensiones["h3a"] = h3a_final
        
        # Crear nodo CROSS en h3a (si h3a > h2a)
        h2a = self.geo.dimensiones["h2a"]
        if h3a_final > h2a + 1e-3:  # Tolerancia 1mm
            self.geo.nodos["CROSS_H3"] = NodoEstructural("CROSS_H3", (0.0, 0.0, h3a_final), "cruce")
            print(f"   🔵 Nodo CROSS_H3 creado en (0, 0, {h3a_final:.2f})")
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ h3a={h3a_final:.2f}m")
    
    def _ejecutar_conectador(self):
        """Ejecutar conectador de nodos al finalizar etapa"""
        print("   🔌 Ejecutando conectador de nodos...")
        conexiones_anteriores = set(self.geo.conexiones)
        
        self.geo._generar_conexiones()
        
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
```

### 2.5 Etapa 4: Cable de Guardia

**Archivo**: `EstructuraAEA_Geometria_Etapa4.py`

```python
class GeometriaEtapa4:
    def ejecutar(self):
        print("🔧 ETAPA 4: Creación de nodos conductores")
        
        # Crear nodo BASE
        self._crear_nodo_base()
        
        # Crear nodos conductores según disposición/terna
        if self.geo.disposicion == "horizontal":
            self._crear_conductores_horizontal()
        elif self.geo.terna == "Simple" and self.geo.disposicion == "vertical":
            self._crear_conductores_simple_vertical()
        elif self.geo.terna == "Simple" and self.geo.disposicion == "triangular":
            self._crear_conductores_simple_triangular()
        elif self.geo.terna == "Doble" and self.geo.disposicion == "vertical":
            self._crear_conductores_doble_vertical()
        elif self.geo.terna == "Doble" and self.geo.disposicion == "triangular":
            self._crear_conductores_doble_triangular()
        
        # Aplicar defasaje por hielo ANTES de crear nodos
        self._aplicar_defasaje_hielo_a_lmen()
        
        # Crear nodos CROSS en x=0 para cada altura
        self._crear_nodos_cross()
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ {len(self.geo.nodos)} nodos creados")
    
    def _crear_conductores_simple_vertical(self):
        """Terna simple vertical: C1, C2, C3"""
        h1a = self.geo.dimensiones["h1a"]
        h2a = self.geo.dimensiones["h2a"]
        h3a = self.geo.dimensiones["h3a"]
        Lmen1 = self.geo.dimensiones["Lmen1"]
        Lmen2 = Lmen1  # Misma longitud salvo defasaje
        Lmen3 = Lmen1
        
        # Aplicar lmen_extra_hielo según mensula_defasar
        if self.geo.defasaje_mensula_hielo:
            if self.geo.mensula_defasar == "primera":
                Lmen1 += self.geo.lmen_extra_hielo
            elif self.geo.mensula_defasar == "segunda":
                Lmen2 += self.geo.lmen_extra_hielo
            elif self.geo.mensula_defasar == "tercera":
                Lmen3 += self.geo.lmen_extra_hielo
            elif self.geo.mensula_defasar == "primera y tercera":
                Lmen1 += self.geo.lmen_extra_hielo
                Lmen3 += self.geo.lmen_extra_hielo
        
        # Crear nodos
        self.geo.nodos["C1"] = NodoEstructural("C1", (Lmen1, 0.0, h1a), "conductor", self.geo.cable_conductor)
        self.geo.nodos["C2"] = NodoEstructural("C2", (Lmen2, 0.0, h2a), "conductor", self.geo.cable_conductor)
        self.geo.nodos["C3"] = NodoEstructural("C3", (Lmen3, 0.0, h3a), "conductor", self.geo.cable_conductor)
    
    def _crear_nodos_cross(self):
        """Crear nodos CROSS en x=0 para cada altura de amarre"""
        h1a = self.geo.dimensiones["h1a"]
        h2a = self.geo.dimensiones["h2a"]
        h3a = self.geo.dimensiones["h3a"]
        tol_z = 1e-3
        
        # CROSS en h1a (salvo horizontal simple)
        if not (self.geo.disposicion == "horizontal" and self.geo.terna == "Simple"):
            self.geo.nodos["CROSS_H1"] = NodoEstructural("CROSS_H1", (0.0, 0.0, h1a), "cruce")
        
        # CROSS en h2a si h2a > h1a
        if self.geo.disposicion in ["triangular", "vertical"] and h2a > h1a + tol_z:
            self.geo.nodos["CROSS_H2"] = NodoEstructural("CROSS_H2", (0.0, 0.0, h2a), "cruce")
        
        # CROSS en h3a si h3a > h2a
        if self.geo.disposicion == "vertical" and h3a > h2a + tol_z:
            self.geo.nodos["CROSS_H3"] = NodoEstructural("CROSS_H3", (0.0, 0.0, h3a), "cruce")
    
    def _ejecutar_conectador(self):
        """Ejecutar conectador de nodos al finalizar etapa"""
        print("Ejecutando conectador de nodos...")
        conexiones_anteriores = set(self.geo.conexiones)
        
        # Generar conexiones (método existente)
        self.geo._generar_conexiones()
        
        # Listar conexiones NUEVAS
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"   INFO: {origen} → {destino} ({tipo})")
        
        if self.geo.cant_hg == 0:
            self._sin_guardia()
        elif self.geo.cant_hg == 1 and self.geo.hg_centrado:
            self._guardia_centrado()
        elif self.geo.cant_hg == 1 and not self.geo.hg_centrado:
            self._guardia_no_centrado()
        elif self.geo.cant_hg == 2:
            self._dos_guardias()
        
        # Crear nodo VIENTO
        self._crear_nodo_viento()
        
        # Ejecutar conectador
        self._ejecutar_conectador()
        
        print(f"   ✅ Cable guardia configurado: CANT_HG={self.geo.cant_hg}")
    
    def _guardia_centrado(self):
        """CANT_HG=1, HG_CENTRADO=True"""
        # Encontrar conductor más alejado del eje x=0
        max_dist_horizontal = 0
        max_z_conductor = 0
        
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor":
                x, y, z = nodo.coordenadas
                dist_horizontal = abs(x)
                z_conductor = z - self.geo.lk  # Posición real del conductor
                
                if dist_horizontal > max_dist_horizontal:
                    max_dist_horizontal = dist_horizontal
                if z_conductor > max_z_conductor:
                    max_z_conductor = z_conductor
        
        # Calcular altura guardia
        hhg = max_z_conductor + max_dist_horizontal * math.tan(math.radians(self.geo.ang_apantallamiento))
        
        # Crear nodo guardia centrado
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (0.0, defasaje_y, hhg), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        self.geo.hhg = hhg
        self.geo.lmenhg = 0.0
        
        print(f"   🛡️  Guardia centrado: HG1 en (0, {defasaje_y}, {hhg:.2f})")
    
    def _guardia_no_centrado(self):
        """CANT_HG=1, HG_CENTRADO=False"""
        # Calcular recta de apantallamiento para cada conductor
        rectas_apantallamiento = []
        
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor":
                x_nodo, y_nodo, z_nodo = nodo.coordenadas
                x_conductor = x_nodo
                z_conductor = z_nodo - self.geo.lk
                
                # Recta de apantallamiento desde conductor
                pendiente = -math.tan(math.radians(self.geo.ang_apantallamiento)) if x_conductor >= 0 else math.tan(math.radians(self.geo.ang_apantallamiento))
                
                # Distancia recta al origen
                dist_origen = abs(z_conductor - pendiente * x_conductor) / math.sqrt(1 + pendiente**2)
                
                rectas_apantallamiento.append({
                    'conductor': nombre,
                    'pendiente': pendiente,
                    'x_conductor': x_conductor,
                    'z_conductor': z_conductor,
                    'dist_origen': dist_origen
                })
        
        # Tomar recta con mayor distancia al origen
        recta_critica = max(rectas_apantallamiento, key=lambda r: r['dist_origen'])
        
        # Calcular Lmenhg y hhg
        Dhg = self.geo.dimensiones["Dhg"]
        HADD_HG = getattr(self.geo, 'hadd_hg', 0.0)
        
        # Lógica iterativa para respetar zonas prohibidas Dhg
        hhg_inicial = max(self.geo.dimensiones["h1a"], self.geo.dimensiones["h2a"], self.geo.dimensiones["h3a"]) + HADD_HG
        
        lmenhg, hhg = self._calcular_posicion_guardia_iterativo(recta_critica, Dhg, hhg_inicial)
    
    def _calcular_posicion_guardia_iterativo(self, recta_critica, Dhg, hhg_inicial):
        """Algoritmo iterativo para calcular lmenhg y hhg respetando zonas Dhg
        
        Proceso:
        1. Iniciar en hhg_inicial
        2. Calcular lmenhg desde recta de apantallamiento
        3. Verificar que no infringe zonas Dhg de conductores EN REPOSO (sin declinar)
        4. Si infringe, incrementar hhg y repetir
        5. Respetar long_mensula_min_guardia
        
        IMPORTANTE: Solo considerar conductores en REPOSO, no declinados.
        """
        Lk = self.geo.lk
        long_min = self.geo.long_mensula_min_guardia
        incremento_altura = 0.1  # 10cm por iteración
        max_iteraciones = 200
        
        hhg = hhg_inicial
        
        for i in range(max_iteraciones):
            # Calcular lmenhg desde recta de apantallamiento
            pendiente = recta_critica['pendiente']
            x_conductor = recta_critica['x_conductor']
            z_conductor = recta_critica['z_conductor']
            
            # Intersección de recta con altura hhg
            lmenhg_calc = abs((hhg - z_conductor) / pendiente) + abs(x_conductor)
            lmenhg = max(lmenhg_calc, long_min)
            
            # Verificar infracciones Dhg con conductores
            infraccion = False
            for nombre, nodo in self.geo.nodos.items():
                if nodo.tipo_nodo == "conductor":
                    x_c, y_c, z_c = nodo.coordenadas
                    z_conductor_real = z_c - Lk
                    
                    # Distancia 3D entre guardia y conductor
                    dist = math.sqrt((lmenhg - x_c)**2 + (hhg - z_conductor_real)**2)
                    
                    if dist < Dhg:
                        infraccion = True
                        break
            
            if not infraccion:
                return lmenhg, hhg
            
            # Incrementar altura y reintentar
            hhg += incremento_altura
        
        # Si no converge, retornar último valor
        print(f"   ⚠️  Advertencia: Algoritmo iterativo no convergió en {max_iteraciones} iteraciones")
        return lmenhg, hhg
        
        # Crear nodos (HG primero, luego TOP, luego verificar solapamiento)
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        
        # 1. Crear HG1 primero
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # 2. Crear TOP después
        self.geo.nodos["TOP"] = NodoEstructural("TOP", (0.0, 0.0, hhg + HADD_HG), "general")
        
        # 3. Verificar solapamiento TOP-HG1 (si dist < 0.01m, eliminar TOP)
        dist_top_hg1 = math.sqrt((lmenhg - 0)**2 + (defasaje_y - 0)**2 + (hhg - (hhg + HADD_HG))**2)
        if dist_top_hg1 < 0.01:
            del self.geo.nodos["TOP"]
            print("   ⚠️  Nodo TOP eliminado por solapamiento con HG1")
        
        self.geo.hhg = hhg
        self.geo.lmenhg = lmenhg
        
        print(f"   🛡️  Guardia no centrado: HG1 en ({lmenhg:.2f}, {defasaje_y}, {hhg:.2f})")
    
    def _dos_guardias(self):
        """CANT_HG=2"""
        # Similar a _guardia_no_centrado pero considerando solo conductores x>0
        conductores_derecha = []
        
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo == "conductor":
                x_nodo, y_nodo, z_nodo = nodo.coordenadas
                if x_nodo > 0:  # Solo lado derecho
                    conductores_derecha.append((nombre, x_nodo, z_nodo - self.geo.lk))
        
        # Calcular recta crítica solo para conductores derecha
        recta_critica = self._calcular_recta_critica(conductores_derecha)
        
        # Calcular posición iterativa
        Dhg = self.geo.dimensiones["Dhg"]
        HADD_HG = getattr(self.geo, 'hadd_hg', 0.0)
        hhg_inicial = max(self.geo.dimensiones["h1a"], self.geo.dimensiones["h2a"], self.geo.dimensiones["h3a"]) + HADD_HG
        
        lmenhg, hhg = self._calcular_posicion_guardia_iterativo(recta_critica, Dhg, hhg_inicial)
    
    def _calcular_posicion_guardia_iterativo(self, recta_critica, Dhg, hhg_inicial):
        """Algoritmo iterativo - Ver implementación en _guardia_no_centrado"""
        # Mismo algoritmo que en _guardia_no_centrado
        pass
        
        # Crear nodos (HG primero, luego TOP, luego verificar solapamiento)
        defasaje_y = getattr(self.geo, 'defasaje_y_guardia', 0.0)
        
        # 1. Crear HG1 y HG2 primero (AMBOS a hhg + HADD_HG)
        self.geo.nodos["HG1"] = NodoEstructural(
            "HG1", (lmenhg, defasaje_y, hhg + HADD_HG), "guardia",
            self.geo.cable_guardia1, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        cable_hg2 = self.geo.cable_guardia2 if self.geo.cable_guardia2 else self.geo.cable_guardia1
        self.geo.nodos["HG2"] = NodoEstructural(
            "HG2", (-lmenhg, defasaje_y, hhg + HADD_HG), "guardia",
            cable_hg2, self.geo.alpha_quiebre, self.geo.tipo_fijacion_base
        )
        
        # 2. Crear TOP1 y TOP2 después
        self.geo.nodos["TOP1"] = NodoEstructural("TOP1", (lmenhg, 0.0, hhg + HADD_HG), "general")
        self.geo.nodos["TOP2"] = NodoEstructural("TOP2", (-lmenhg, 0.0, hhg + HADD_HG), "general")
        
        # 3. Verificar solapamientos (si dist < 0.01m, eliminar TOP)
        if math.sqrt((0)**2 + (defasaje_y)**2 + (0)**2) < 0.01:
            del self.geo.nodos["TOP1"]
            print("   ⚠️  Nodo TOP1 eliminado por solapamiento con HG1")
        if math.sqrt((0)**2 + (defasaje_y)**2 + (0)**2) < 0.01:
            del self.geo.nodos["TOP2"]
            print("   ⚠️  Nodo TOP2 eliminado por solapamiento con HG2")
        
        self.geo.hhg = hhg
        self.geo.lmenhg = lmenhg
        
        print(f"   🛡️  Dos guardias: HG1 en ({lmenhg:.2f}, {defasaje_y}, {hhg:.2f}), HG2 en ({-lmenhg:.2f}, {defasaje_y}, {hhg + HADD_HG:.2f})")
    
    def _crear_nodo_viento(self):
        """Crear nodo VIENTO a 2/3 de altura máxima
        
        Ubicación: x=0, y=0, z=2/3*max(z de todos los nodos existentes)
        Se crea en Etapa 4 después de crear todos los nodos (conductores y guardias)
        """
        max_z = max(nodo.coordenadas[2] for nodo in self.geo.nodos.values())
        z_viento = (2/3) * max_z
        
        self.geo.nodos["VIENTO"] = NodoEstructural("VIENTO", (0.0, 0.0, z_viento), "viento")
        
        print(f"   🌪️  Nodo VIENTO en z={z_viento:.2f}m")
    
    def _ejecutar_conectador(self):
        """Ejecutar conectador de nodos al finalizar etapa"""
        print("   🔌 Ejecutando conectador de nodos...")
        conexiones_anteriores = set(self.geo.conexiones)
        
        self.geo._generar_conexiones()
        
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        if conexiones_nuevas:
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
```

### 2.6 Etapa 5: Conexiones entre Nodos

**Archivo**: `EstructuraAEA_Geometria_Etapa5.py`

**Algoritmo Iterativo para Guardia No Centrado**:

```python
class GeometriaEtapa5:
    def ejecutar(self):
        print("🔧 ETAPA 5: Posicionamiento cable de guardia")
        print("Ejecutando conectador de nodos...")
        
        conexiones_anteriores = set(self.geo.conexiones)
        
        # Generar nuevas conexiones
        self._generar_conexiones_mensula()
        self._generar_conexiones_columna()
        
        # Identificar conexiones nuevas
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        
        if conexiones_nuevas:
            print("   📡 Conexiones NUEVAS encontradas:")
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      {origen} → {destino} ({tipo})")
        
        print(f"   ✅ {len(self.geo.conexiones)} conexiones totales")
    
    def _generar_conexiones_mensula(self):
        """Conexiones tipo ménsula entre nodos misma altura
        
        Incluye:
        - Nodos conductor
        - Nodos guardia
        - Nodos CROSS
        - Nodos TOP
        """
        nodos_por_altura = {}
        
        # Agrupar nodos por altura
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo in ["conductor", "guardia", "cruce", "general"]:
                z = nodo.coordenadas[2]
                if z not in nodos_por_altura:
                    nodos_por_altura[z] = []
                nodos_por_altura[z].append(nombre)
        
        # Generar conexiones por altura
        for altura, nodos in nodos_por_altura.items():
            if len(nodos) > 1:
                # Verificar que no "pasen por encima" de otros nodos
                nodos_ordenados = sorted(nodos, key=lambda n: self.geo.nodos[n].coordenadas[0])
                
                for i in range(len(nodos_ordenados) - 1):
                    origen = nodos_ordenados[i]
                    destino = nodos_ordenados[i + 1]
                    
                    # Verificar que no hay nodo intermedio
                    if not self._hay_nodo_intermedio(origen, destino, altura):
                        self.geo.conexiones.append((origen, destino, 'mensula'))
    
    def _generar_conexiones_columna(self):
        """Conexiones tipo columna verticales"""
        nodos_centrales = []
        
        # Encontrar nodos en eje central (x=0, y=0)
        for nombre, nodo in self.geo.nodos.items():
            x, y, z = nodo.coordenadas
            if abs(x) < 0.001 and abs(y) < 0.001:
                if nodo.tipo_nodo in ["base", "cruce", "general", "viento"]:
                    nodos_centrales.append((z, nombre))
        
        # Ordenar por altura y conectar adyacentes
        nodos_centrales.sort(key=lambda x: x[0])
        
        for i in range(len(nodos_centrales) - 1):
            origen = nodos_centrales[i][1]
            destino = nodos_centrales[i + 1][1]
            self.geo.conexiones.append((origen, destino, 'columna'))
```

### 2.7 Etapa 6: Checkeos Finales

**Archivo**: `EstructuraAEA_Geometria_Etapa6.py`

```python
class GeometriaEtapa6:
    def ejecutar(self):
        print("🔧 ETAPA 6: Conexiones entre nodos")
        print("Ejecutando conectador de nodos...")
        
        conexiones_anteriores = set(self.geo.conexiones)
        
        # Generar nuevas conexiones
        self._generar_conexiones_mensula()
        self._generar_conexiones_columna()
        
        # Identificar y listar SOLO conexiones NUEVAS
        conexiones_nuevas = set(self.geo.conexiones) - conexiones_anteriores
        
        if conexiones_nuevas:
            print("   📡 Conexiones NUEVAS encontradas:")
            for origen, destino, tipo in conexiones_nuevas:
                print(f"      INFO: {origen} → {destino} ({tipo})")
        
        print(f"   ✅ {len(self.geo.conexiones)} conexiones totales")
    
    def _hay_nodo_intermedio(self, origen, destino, altura):
        """Verificar si existe nodo intermedio entre origen y destino
        
        Evita conexiones que 'pasen por encima' de otros nodos.
        Ejemplo: No conectar C1 con C3 si existe C2 en el medio.
        """
        x_origen = self.geo.nodos[origen].coordenadas[0]
        x_destino = self.geo.nodos[destino].coordenadas[0]
        tol_z = 1e-3
        
        x_min = min(x_origen, x_destino)
        x_max = max(x_origen, x_destino)
        
        for nombre, nodo in self.geo.nodos.items():
            if nombre in [origen, destino]:
                continue
            
            x, y, z = nodo.coordenadas
            
            # Verificar si está en la misma altura y entre origen-destino
            if abs(z - altura) < tol_z and x_min < x < x_max:
                return True
        
        return False



**Checkeos por Declinación**:

```python
class GeometriaEtapa7:
    def ejecutar(self):
        print("🔧 ETAPA 7: Checkeos finales")
        
        errores = []
        advertencias = []
        
        # Checkear zonas de prohibición POR DECLINACIÓN
        errores.extend(self._checkear_zonas_prohibicion_por_declinacion())
        
        # Checkear apantallamiento
        errores.extend(self._checkear_apantallamiento())
        
        # Checkear conexiones
        errores.extend(self._checkear_conexiones())
        
        # Checkear sub-optimización
        advertencias.extend(self._checkear_suboptimizacion())
        
        # Imprimir resultados
        if errores:
            print("   ❌ ERRORES encontrados:")
            for error in errores:
                print(f"      ERROR: {error}")
        
        if advertencias:
            print("   ⚠️  ADVERTENCIAS:")
            for advertencia in advertencias:
                print(f"      ADVERTENCIA: {advertencia}")
        
        if not errores and not advertencias:
            print("   ✅ Todos los checkeos pasaron correctamente")
        
        # Generar gráficos finales
        self._generar_graficos_finales()
    
    def _checkear_zonas_prohibicion_por_declinacion(self):
        """Verificar infracciones por cada declinación por separado
        
        REGLA CRÍTICA: Comparar conductores SOLO con misma declinación.
        - Reposo vs Reposo
        - Tormenta vs Tormenta  
        - Declinación máxima vs Declinación máxima
        
        NO mezclar: conductor h1a declinado vs conductor h2a sin declinar.
        
        IMPORTANTE: Estos checkeos deben ejecutarse DURANTE las etapas intermedias
        (Etapa 2, 3, 4), no solo al final. Cada etapa debe verificar que los nodos
        recién creados no infrinjan zonas de nodos existentes.
        """
        errores = []
        
        s_reposo = self.geo.dimensiones["s_estructura"]
        s_tormenta = self.geo.dimensiones["s_tormenta"]
        s_decmax = self.geo.dimensiones["s_decmax"]
        D_fases = self.geo.dimensiones["D_fases"]
        Dhg = self.geo.dimensiones["Dhg"]
        
        theta_tormenta = self.geo.theta_tormenta
        theta_max = self.geo.theta_max
        Lk = self.geo.lk
        
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        elementos_fijos = [(n, nodo) for n, nodo in self.geo.nodos.items() 
                          if nodo.tipo_nodo in ["cruce", "general"] and abs(nodo.coordenadas[0]) < 0.001]
        
        # ESTADO 1: REPOSO
        for nombre_c, nodo_c in conductores:
            x_amarre, y_amarre, z_amarre = nodo_c.coordenadas
            x_conductor = x_amarre
            z_conductor = z_amarre - Lk
            
            # Conductor vs elementos fijos
            for nombre_e, nodo_e in elementos_fijos:
                dist = math.sqrt((x_conductor - nodo_e.coordenadas[0])**2 + 
                               (z_conductor - nodo_e.coordenadas[2])**2)
                if dist < s_reposo:
                    errores.append(f"REPOSO: {nombre_c}-{nombre_e}: {dist:.3f}m < s_reposo({s_reposo:.3f}m)")
            
            # Conductor vs conductor (mismo estado)
            for nombre_c2, nodo_c2 in conductores:
                if nombre_c >= nombre_c2:
                    continue
                x_c2, y_c2, z_c2 = nodo_c2.coordenadas
                z_conductor2 = z_c2 - Lk
                dist = math.sqrt((x_conductor - x_c2)**2 + (z_conductor - z_conductor2)**2)
                if dist < D_fases:
                    errores.append(f"REPOSO: {nombre_c}-{nombre_c2}: {dist:.3f}m < D_fases({D_fases:.3f}m)")
        
        # ESTADO 2: TORMENTA (similar con theta_tormenta y s_tormenta)
        # ESTADO 3: DECLINACIÓN MÁXIMA (similar con theta_max y s_decmax)
        
        return errores
    
    def _checkear_suboptimizacion(self):
        """Verificar que nodos no estén a altura mayor de la necesaria
        
        Criterio: Si un nodo conductor puede estar a menor altura sin
        infringir zonas de prohibición, advertir.
        """
        advertencias = []
        
        # Implementar lógica de verificación
        
        return advertencias
        
        errores = []
        advertencias = []
        
        # Checkear zonas de prohibición
        errores.extend(self._checkear_zonas_prohibicion())
        
        # Checkear apantallamiento
        errores.extend(self._checkear_apantallamiento())
        
        # Checkear conexiones
        errores.extend(self._checkear_conexiones())
        
        # Checkear optimización
        advertencias.extend(self._checkear_optimizacion())
        
        # Imprimir resultados
        if errores:
            print("   ❌ ERRORES encontrados:")
            for error in errores:
                print(f"      ERROR: {error}")
        
        if advertencias:
            print("   ⚠️  ADVERTENCIAS:")
            for advertencia in advertencias:
                print(f"      ADVERTENCIA: {advertencia}")
        
        if not errores and not advertencias:
            print("   ✅ Todos los checkeos pasaron correctamente")
        
        # Generar gráficos finales
        self._generar_graficos_finales()
    
    def _checkear_zonas_prohibicion(self):
        """Verificar infracciones de zonas de prohibición"""
        errores = []
        
        s = self.geo.dimensiones["s_estructura"]
        s_tormenta = self.geo.dimensiones["s_tormenta"]
        s_decmax = self.geo.dimensiones["s_decmax"]
        D_fases = self.geo.dimensiones["D_fases"]
        Dhg = self.geo.dimensiones["Dhg"]
        
        # Verificar distancias entre conductores
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        for i, (nombre1, nodo1) in enumerate(conductores):
            for j, (nombre2, nodo2) in enumerate(conductores[i+1:], i+1):
                dist = self._calcular_distancia_3d(nodo1.coordenadas, nodo2.coordenadas)
                if dist < D_fases:
                    errores.append(f"Distancia entre {nombre1}-{nombre2}: {dist:.3f}m < D_fases({D_fases:.3f}m)")
        
        # Verificar distancias conductor-estructura
        elementos_estructura = [(n, nodo) for n, nodo in self.geo.nodos.items() 
                               if nodo.tipo_nodo in ["cruce", "general"] and abs(nodo.coordenadas[0]) < 0.001]
        
        for nombre_c, nodo_c in conductores:
            for nombre_e, nodo_e in elementos_estructura:
                dist = self._calcular_distancia_3d(nodo_c.coordenadas, nodo_e.coordenadas)
                if dist < s:
                    errores.append(f"Distancia {nombre_c}-{nombre_e}: {dist:.3f}m < s_estructura({s:.3f}m)")
        
        return errores
    
    def _checkear_apantallamiento(self):
        """Verificar que todos los conductores estén bajo apantallamiento"""
        errores = []
        
        if self.geo.cant_hg == 0:
            return errores
        
        guardias = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "guardia"]
        conductores = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        for nombre_c, nodo_c in conductores:
            x_c, y_c, z_c = nodo_c.coordenadas
            z_conductor = z_c - self.geo.lk  # Posición real del conductor
            
            cubierto = False
            for nombre_g, nodo_g in guardias:
                x_g, y_g, z_g = nodo_g.coordenadas
                
                # Verificar si conductor está bajo el "paraguas" de este guardia
                dist_horizontal = math.sqrt((x_c - x_g)**2 + (y_c - y_g)**2)
                altura_apant = z_g - dist_horizontal * math.tan(math.radians(self.geo.ang_apantallamiento))
                
                if z_conductor <= altura_apant:
                    cubierto = True
                    break
            
            if not cubierto:
                dist_fuera = z_conductor - altura_apant
                errores.append(f"Conductor {nombre_c} fuera de apantallamiento: {dist_fuera:.3f}m")
        
        return errores
    
    def _generar_graficos_finales(self):
        """Generar gráficos finales de cabezal y estructura"""
        from .GraficoCabezal2D import GraficoCabezal2D
        from .GraficoEstructura2D import GraficoEstructura2D
        
        # Gráfico de cabezal con zonas de prohibición
        grafico_cabezal = GraficoCabezal2D(self.geo)
        self.geo.grafico_cabezal_final = grafico_cabezal.generar_completo()
        
        # Gráfico de estructura completa
        grafico_estructura = GraficoEstructura2D(self.geo)
        self.geo.grafico_estructura_final = grafico_estructura.generar_completo()
        
        print("   📊 Gráficos finales generados")
```

## 3. Refactorización de Gráficos

### 3.1 Dos Gráficos Principales

**IMPORTANTE**: Solo existen DOS gráficos finales:
1. **Gráfico de Cabezal** (2D, vista lateral XZ)
2. **Gráfico de Estructura Completa** (2D, vista lateral XZ)

Cada etapa define **elementos que se irán agregando** a estos gráficos, pero NO son gráficos separados por etapa.

### 3.2 Elementos por Etapa

#### Etapa 1 - Elementos a Dibujar:
- Nodos conductor creados (puntos de amarre)
- Línea Lk (cadena desde amarre hasta conductor)
- Línea fmax (flecha máxima, en rojo)
- Línea HADD (punteada)
- Línea a+b (altura base + altura eléctrica, gris)
- Cadenas Lk declinadas (según controles)
- Conductores declinados (patches)
- Círculos de zonas prohibición (según controles)

#### Etapa 2 - Elementos a Dibujar:
- Nodo h2a (punto de amarre)
- Línea Lk desde h2a
- NO se dibuja fmax ni HADD (no relevantes en esta etapa)
- Zonas prohibición alrededor de conductores

#### Etapa 3 - Elementos a Dibujar:
- Similar a Etapa 2 pero para h3a

#### Etapa 4 - Elementos a Dibujar:
- Nodos guardia (HG1, HG2)
- Zona de apantallamiento (conos invertidos)
- Líneas de apantallamiento (recta crítica)
- Control para mostrar/ocultar área y líneas

#### Etapa 5 - Elementos a Dibujar:
- Conexiones ménsula (horizontales)
- Conexiones columna (verticales)
- Diferente color para cada tipo

#### Etapa 6 - Publicación Final:
- Recién ahora se "publican" los gráficos finales
- Gráfico de cabezal con todos los elementos
- Gráfico de estructura completa con todos los elementos
- Estos reemplazan los gráficos existentes en EstructuraAEA_Graficos

### 3.3 Controles Interactivos por Nodo

**Archivo**: `GraficoCabezal2D.py`

**REGLA CRÍTICA**: Para CADA nodo conductor generar controles individuales:

```python
class GraficoCabezal2D:
    def __init__(self, geometria):
        self.geo = geometria
        self.controles_por_nodo = {}  # {nombre_nodo: {controles}}
    
    def generar_completo(self):
        """Generar gráfico interactivo con controles por nodo"""
        fig = go.Figure()
        
        # Crear controles para cada nodo conductor
        conductores = [n for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "conductor"]
        
        for nombre_conductor in conductores:
            self.controles_por_nodo[nombre_conductor] = {
                'declinacion_tormenta': 'off',  # izq, der, ambos, off
                'declinacion_maxima': 'off',    # izq, der, ambos, off
                'mostrar_s_reposo': True,
                'mostrar_s_tormenta': False,
                'mostrar_s_decmax': False,
                'mostrar_D_fases': True,
                'mostrar_Dhg': False
            }
        
        # Dibujar estructura base
        self._dibujar_estructura_base(fig)
        
        # Dibujar conductores con declinaciones según controles
        self._dibujar_conductores_con_declinaciones(fig)
        
        # Dibujar zonas de prohibición con clipping
        self._dibujar_zonas_prohibicion_con_clipping(fig)
        
        # Dibujar guardias y apantallamiento
        self._dibujar_guardias(fig)
        self._dibujar_zona_apantallamiento(fig)
        
        # Configurar layout con botones interactivos Plotly
        self._configurar_controles_interactivos_plotly(fig)
        
        return fig
    
    def _configurar_controles_interactivos_plotly(self, fig):
        """Configurar botones interactivos usando updatemenus de Plotly
        
        Para cada nodo conductor se generan:
        - Botones de declinación tormenta: izq, der, ambos, off
        - Botones de declinación máxima: izq, der, ambos, off
        - Toggles para zonas: s_reposo, s_tormenta, s_decmax, D_fases, Dhg
        """
        updatemenus = []
        
        for i, nombre_conductor in enumerate(self.controles_por_nodo.keys()):
            # Botón declinación tormenta
            updatemenus.append({
                'buttons': [
                    {'label': 'Tormenta OFF', 'method': 'restyle', 'args': ['visible', [True]]},
                    {'label': 'Tormenta IZQ', 'method': 'restyle', 'args': ['visible', [True]]},
                    {'label': 'Tormenta DER', 'method': 'restyle', 'args': ['visible', [True]]},
                    {'label': 'Tormenta AMBOS', 'method': 'restyle', 'args': ['visible', [True]]}
                ],
                'direction': 'down',
                'showactive': True,
                'x': 0.1,
                'y': 1.0 - i*0.15,
                'xanchor': 'left',
                'yanchor': 'top'
            })
        
        fig.update_layout(updatemenus=updatemenus)
    
    def _dibujar_conductores_con_declinaciones(self, fig):
        """Dibujar conductores con línea Lk y patch en extremo
        
        - Línea Lk: desde amarre hasta conductor
        - Lk se inclina según ángulo (tormenta o máximo)
        - Conductor: PATCH (marcador grande) en extremo de Lk
        - Zonas prohibidas: círculos alrededor del patch
        """
        Lk = self.geo.lk
        
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo != "conductor":
                continue
            
            x_amarre, y_amarre, z_amarre = nodo.coordenadas
            controles = self.controles_por_nodo[nombre]
            
            # Dibujar posiciones según controles
            posiciones = []
            
            # Reposo (siempre)
            posiciones.append({
                'x': x_amarre,
                'z': z_amarre - Lk,
                'angulo': 0,
                'label': 'reposo'
            })
            
            # Tormenta
            if controles['declinacion_tormenta'] != 'off':
                theta = self.geo.theta_tormenta
                if controles['declinacion_tormenta'] in ['izq', 'ambos']:
                    posiciones.append({
                        'x': x_amarre - Lk * math.sin(math.radians(theta)),
                        'z': z_amarre - Lk * math.cos(math.radians(theta)),
                        'angulo': -theta,
                        'label': 'tormenta_izq'
                    })
                if controles['declinacion_tormenta'] in ['der', 'ambos']:
                    posiciones.append({
                        'x': x_amarre + Lk * math.sin(math.radians(theta)),
                        'z': z_amarre - Lk * math.cos(math.radians(theta)),
                        'angulo': theta,
                        'label': 'tormenta_der'
                    })
            
            # Declinación máxima (similar)
            
            # Dibujar cada posición
            for pos in posiciones:
                # Línea Lk
                fig.add_trace(go.Scatter(
                    x=[x_amarre, pos['x']],
                    y=[z_amarre, pos['z']],
                    mode='lines',
                    line=dict(color='gray', width=2),
                    name=f"{nombre}_Lk_{pos['label']}"
                ))
                
                # Patch (marcador grande) en extremo
                fig.add_trace(go.Scatter(
                    x=[pos['x']],
                    y=[pos['z']],
                    mode='markers',
                    marker=dict(size=15, color='red', symbol='circle'),
                    name=f"{nombre}_{pos['label']}"
                ))
    
    def _dibujar_zonas_prohibicion_con_clipping(self, fig):
        """Dibujar zonas de prohibición con clipping para evitar sombreado doble
        
        REGLA: Cuando múltiples zonas se solapan:
        - Dibujar TODAS las zonas
        - Recortar intersecciones (boolean geometry)
        - NO duplicar alpha en áreas solapadas
        
        Usar shapely para operaciones de clipping.
        """
        from shapely.geometry import Point
        from shapely.ops import unary_union
        
        s_reposo = self.geo.dimensiones["s_estructura"]
        s_tormenta = self.geo.dimensiones["s_tormenta"]
        s_decmax = self.geo.dimensiones["s_decmax"]
        D_fases = self.geo.dimensiones["D_fases"]
        Dhg = self.geo.dimensiones["Dhg"]
        
        # Recolectar todas las zonas como círculos (shapely)
        zonas = []
        
        for nombre, nodo in self.geo.nodos.items():
            if nodo.tipo_nodo != "conductor":
                continue
            
            controles = self.controles_por_nodo[nombre]
            x_amarre, y_amarre, z_amarre = nodo.coordenadas
            x_conductor = x_amarre
            z_conductor = z_amarre - self.geo.lk
            
            punto = Point(x_conductor, z_conductor)
            
            if controles['mostrar_s_reposo']:
                zonas.append(punto.buffer(s_reposo))
            if controles['mostrar_s_tormenta']:
                zonas.append(punto.buffer(s_tormenta))
            if controles['mostrar_D_fases']:
                zonas.append(punto.buffer(D_fases))
        
        # Unión de zonas (evita sombreado doble)
        union_zonas = unary_union(zonas)
        
        # Dibujar unión como área sombreada
        # Convertir shapely geometry a coordenadas plotly
        if union_zonas.geom_type == 'Polygon':
            x_coords, z_coords = union_zonas.exterior.xy
            fig.add_trace(go.Scatter(
                x=list(x_coords),
                y=list(z_coords),
                fill='toself',
                fillcolor='rgba(173, 216, 230, 0.3)',
                line=dict(color='gray', width=1, dash='dash'),
                name='Zonas prohibición',
                showlegend=True
            ))
        elif union_zonas.geom_type == 'MultiPolygon':
            for polygon in union_zonas.geoms:
                x_coords, z_coords = polygon.exterior.xy
                fig.add_trace(go.Scatter(
                    x=list(x_coords),
                    y=list(z_coords),
                    fill='toself',
                    fillcolor='rgba(173, 216, 230, 0.3)',
                    line=dict(color='gray', width=1, dash='dash'),
                    name='Zonas prohibición',
                    showlegend=False
                ))

**Archivo**: `EstructuraAEA_Graficos.py` (NUEVO)

```python
class EstructuraAEA_Graficos:
    def __init__(self, geometria):
        self.geometria = geometria
    
    def graficar_cabezal(self, **kwargs):
        """Selector para gráfico de cabezal"""
        from .GraficoCabezal2D import GraficoCabezal2D
        grafico = GraficoCabezal2D(self.geometria)
        return grafico.generar(**kwargs)
    
    def graficar_estructura(self, **kwargs):
        """Selector para gráfico de estructura"""
        from .GraficoEstructura2D import GraficoEstructura2D
        grafico = GraficoEstructura2D(self.geometria)
        return grafico.generar(**kwargs)
    
    def graficar_nodos_coordenadas(self, **kwargs):
        """Gráfico 3D de nodos (mantener existente)"""
        # Reutilizar código actual
        pass
```

### 3.2 Gráfico de Cabezal Especializado

**Archivo**: `GraficoCabezal2D.py`

```python
class GraficoCabezal2D:
    def __init__(self, geometria):
        self.geo = geometria
    
    def generar_completo(self):
        """Generar gráfico completo con todas las características"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Dibujar estructura base
        self._dibujar_estructura_base(ax)
        
        # Dibujar conductores con cadenas
        self._dibujar_conductores_cadenas(ax)
        
        # Dibujar guardias
        self._dibujar_guardias(ax)
        
        # Dibujar zona de apantallamiento
        self._dibujar_zona_apantallamiento(ax)
        
        # Dibujar zonas de prohibición
        self._dibujar_zonas_prohibicion(ax)
        
        # Configurar ejes y leyenda
        self._configurar_grafico(ax)
        
        return fig
    
    def _dibujar_zona_apantallamiento(self, ax):
        """Dibujar conos invertidos de apantallamiento"""
        if self.geo.cant_hg == 0:
            return
        
        guardias = [(n, nodo) for n, nodo in self.geo.nodos.items() if nodo.tipo_nodo == "guardia"]
        
        for nombre_g, nodo_g in guardias:
            x_g, y_g, z_g = nodo_g.coordenadas
            
            # Calcular extensión del cono
            altura_terminacion = min(nodo.coordenadas[2] - self.geo.lk 
                                   for nodo in self.geo.nodos.values() 
                                   if nodo.tipo_nodo == "conductor")
            
            extension = (z_g - altura_terminacion) * math.tan(math.radians(self.geo.ang_apantallamiento))
            
            # Dibujar líneas de apantallamiento
            ax.plot([x_g - extension, x_g], [altura_terminacion, z_g], 
                   '--', color='green', alpha=0.7, label='Apantallamiento')
            ax.plot([x_g + extension, x_g], [altura_terminacion, z_g], 
                   '--', color='green', alpha=0.7)
            
            # Rellenar área
            ax.fill([x_g - extension, x_g, x_g + extension], 
                   [altura_terminacion, z_g, altura_terminacion], 
                   color='lightgreen', alpha=0.3)
```

## 4. Compatibilidad con Cálculos Previos

### 4.1 Parámetros Existentes (Mantener 100%)

```python
# MANTENER - Ya calculados en etapas previas
parametros_existentes = {
    "D_fases": "✅ Calculado en Etapa 1",
    "s_estructura": "✅ Calculado en Etapa 1 (s_reposo)",
    "Dhg": "✅ Calculado en Etapa 1", 
    "theta_max": "✅ Calculado en Etapa 1",
    "ang_apantallamiento": "✅ Parámetro de entrada",
    "h1a, h2a, h3a": "✅ Calculado en Etapa 1",
    "lmen, lmenhg": "✅ Calculado en Etapa 1",
    "hhg": "✅ Calculado en Etapa 4"
}
```

### 4.2 Nuevos Parámetros (Defaults)

```python
# NUEVOS - Con valores por defecto
parametros_nuevos = {
    "s_tormenta": "s_estructura",  # Default = s_reposo
    "s_decmax": "s_estructura",    # Default = s_tormenta  
    "defasaje_y_guardia": 0.0,     # Default = 0
    "altura_terminacion": "h1a - Lk"  # Calculado automáticamente
}
```

## 5. Compatibilidad con UI Actual

### 5.1 Parámetros UI Existentes (NO cambiar)

```python
# YA EXISTEN en vista_parametros.py - NO MODIFICAR
parametros_ui_existentes = {
    "ang_apantallamiento": "✅ Ya existe",
    "hadd_hg": "✅ Ya existe", 
    "long_mensula_min_guardia": "✅ Ya existe",
    "hg_centrado": "✅ Ya existe",
    "cant_hg": "✅ Ya existe"
}
```

### 5.2 Nuevo Parámetro UI

**Archivo**: `components/vista_parametros.py`

```python
# NUEVO PARÁMETRO - Defasaje Y guardia
nuevo_control = {
    "defasaje_y_guardia": {
        "tipo": "number",
        "valor": 0.0,
        "min": -2.0,
        "max": 2.0, 
        "step": 0.1,
        "descripcion": "Defasaje Y guardia [m] - Desplazamiento longitudinal de nodos guardia para cálculos mecánicos. No afecta apantallamiento.",
        "categoria": "Cable Guardia"
    }
}
```

**Justificación**: Permite ajustar posición longitudinal de guardias para cálculos mecánicos posteriores sin afectar el diseño de apantallamiento.

## 6. Plan de Migración

### Fase 1: Estructura Base (Semana 1)
1. Crear archivos de etapas vacíos
2. Implementar selector principal
3. Mover código existente a Etapa2
4. Mantener funcionamiento actual

### Fase 2: Nuevas Etapas (Semana 2-3)
1. Implementar Etapa4 (guardia avanzada)
2. Implementar Etapa5 (conexiones mejoradas)
3. Implementar Etapa6 (checkeos exhaustivos)

### Fase 3: Gráficos Especializados (Semana 4)
1. Crear GraficoCabezal2D y GraficoEstructura2D
2. Implementar gráficos por etapa
3. Migrar visualizaciones existentes

### Fase 4: Testing y Optimización (Semana 5)
1. Testing exhaustivo de todas las configuraciones
2. Optimización de performance
3. Documentación completa

## 7. Archivos a Crear

### Nuevos Archivos Core
- `EstructuraAEA_Geometria_Etapa0.py` - Nodo base
- `EstructuraAEA_Geometria_Etapa1.py` - Cálculos base (h1a, Lmen1)
- `EstructuraAEA_Geometria_Etapa2.py` - Segundo amarre (h2a)
- `EstructuraAEA_Geometria_Etapa3.py` - Tercer amarre (h3a)
- `EstructuraAEA_Geometria_Etapa4.py` - Cable guardia
- `EstructuraAEA_Geometria_Etapa5.py` - Conexiones
- `EstructuraAEA_Geometria_Etapa6.py` - Checkeos exhaustivos

### Nuevos Archivos Gráficos
- `GraficoCabezal2D.py` - Gráfico cabezal especializado
- `GraficoEstructura2D.py` - Gráfico estructura completa
- `GraficoEtapas.py` - Gráficos intermedios por etapa

### Archivos a Modificar
- `EstructuraAEA_Geometria.py` - Convertir en selector
- `EstructuraAEA_Graficos.py` - Convertir en selector

## 8. Beneficios del Revamp

### Mantenibilidad
- Código modular por etapas
- Cada etapa es independiente y testeable
- Fácil agregar nuevas configuraciones

### Funcionalidad
- Lógica avanzada de cable guardia
- Checkeos exhaustivos de zonas de prohibición
- Gráficos especializados por etapa
- Validación completa de apantallamiento

### Compatibilidad
- 100% compatible con UI actual
- Mantiene todos los parámetros existentes
- Migración gradual sin interrupciones

### Performance
- Ejecución por etapas permite debugging granular
- Gráficos optimizados por tipo
- Checkeos eficientes con early exit

Este revamp transforma el sistema DGE de un código monolítico a una arquitectura modular y extensible, manteniendo total compatibilidad con el sistema existente.

---

## 9. Casos de Prueba (Testing Manual por Usuario)

**IMPORTANTE**: Tras implementar cada etapa, marcar issue como `🔧 TESTING PENDIENTE` y dejar verificación final en manos del usuario.

### 9.1 Matriz de Pruebas

| ID | Terna | Disposición | Lk | Defasaje Hielo | CANT_HG | HG_CENTRADO | Descripción |
|----|-------|--------------|-------|----------------|---------|-------------|-------------|
| T01 | Simple | Vertical | 0 | No | 0 | - | Caso base sin guardia |
| T02 | Simple | Vertical | 2.5 | No | 1 | True | Guardia centrado |
| T03 | Simple | Vertical | 2.5 | No | 1 | False | Guardia no centrado |
| T04 | Simple | Vertical | 2.5 | Primera | 1 | False | Defasaje primera altura |
| T05 | Simple | Triangular | 2.5 | No | 1 | False | Triangular simple |
| T06 | Simple | Horizontal | 0 | No | 1 | False | Horizontal Lk=0 |
| T07 | Doble | Vertical | 2.5 | No | 2 | - | Dos guardias |
| T08 | Doble | Triangular | 2.5 | Primera | 2 | - | Doble triangular con hielo |
| T09 | Simple | Vertical | 2.5 | Segunda | 1 | False | Defasaje segunda altura |
| T10 | Simple | Vertical | 2.5 | Tercera | 1 | False | Defasaje tercera altura |
| T11 | Simple | Vertical | 2.5 | Primera y tercera | 2 | - | Defasaje múltiple |
| T12 | Doble | Horizontal | - | - | - | - | ERROR esperado |

### 9.2 Verificaciones por Caso

Para cada caso verificar:

1. **Fórmula h1a**: `h1a = a + b + fmax + Lk + HADD`
2. **Lmen1**: No infracciones de s_decmax en declinación máxima
3. **Nodos CROSS**: Creados en x=0 para cada altura
4. **Conectador**: Ejecutado al final de cada etapa con log de conexiones NUEVAS
5. **Zonas por declinación**: Checkeos separados (reposo, tormenta, máxima)
6. **Apantallamiento**: Todos los conductores cubiertos
7. **Gráficos**: Controles por nodo funcionando
8. **Clipping**: Zonas solapadas sin sombreado doble

### 9.3 Escenarios de Solapamiento

- **Zona s_reposo + D_fases**: Verificar clipping correcto
- **TOP + HG1**: Distancia < 0.01m → eliminar TOP
- **Múltiples conductores**: Zonas D_fases solapadas

### 9.4 Tolerancias Numéricas

- **Agrupación alturas**: `tol_z = 1e-3 m`
- **Solapamiento nodos**: `dist < 0.01 m`
- **Comparaciones float**: Usar tolerancias, NO igualdad exacta
A continuación se registran, de forma precisa y estricta, las correcciones que **deben** quedar en la documentación tal como se solicitó (NO se tocará código en esta tarea):

- Etapa 1 — Cálculo de alturas y Lmen (IMPORTANTE)
  - **h1a**: documentar explícitamente la fórmula obligatoria
    `h1a = a + b + fmax + Lk + HADD` y explicar cada término.
  - **Lmen1**: definir que se calculará como la mínima longitud de ménsula a la que **la zona s_decmax del conductor en declinación máxima** no es infringida por elementos fijos. Reglas adicionales:
    - Si la infracción la produce **columna/nodo**, aumentar `Lmen1` hasta resolver.
    - Si la infracción la produce **la propia ménsula Lmen1**, intentar aumentar `Lk` (solo si `Lk>0`); si no alcanza, **imprimir** exactamente: `Error, Lk longitud cadena oscilante muy corta`.
    - Si `Lk==0` no se debe forzar incremento de `Lk` y la situación queda permitida respecto a la ménsula, pero **no** respecto a elementos columna/nodos.
  - **Hielo / defasaje**: documentar que, si `defasaje_mensula_hielo=True` y `mensula_defasar` incluye la "primera", se aplica `lmen_extra_hielo` *antes* de generar el nodo C1 (es decir, Lmen1 incrementada en ese punto).
  - **Horizontal con Lk=0**: documentar que en terna simple disposición horizontal se toma `Lmen1 = max(D_fases, Lmen_minima)` (ignorando efectos de hielo) y que se generan C1,C2,C3 como en la especificación.

- Etapa 2 — Creación de nodos conductores (ALTO)
  - Añadir paso detallado: generar nodos C1/C2/C3 (y reflejados) según los casos (simple/doble y vertical/horizontal/triangular) respetando `lmen`, `lmen2c` y aplicando `lmen_extra_hielo` según `mensula_defasar` (primera/segunda/tercera) antes de crear los nodos correspondientes.
  - Indicar que **los nodos CROSS** se generan en `x=0` para cada altura de amarre generada y que el **conectador** debe ejecutarse (log: "Ejecutando conectador de nodos...") **al finalizar la creación de nodos en cada etapa** (esto es necesario para que fases posteriores lean conexiones actualizadas).

- Declinaciones y representación gráfica (ALTO)
  - Especificar controles interactivos por NODO conductor: para cada amarre generar botones/controles: `Declinación tormenta (izq, der, ambos, off)`, `Declinación máxima (izq, der, ambos, off)` y toggles para `s_reposo`, `s_tormenta`, `s_decmax`, `D_fases`, `Dhg`.
  - Definir dibujo: la declinación dibuja una línea `Lk` desde el amarre hasta el cable; `Lk` se inclina respecto a vertical por el ángulo correspondiente; el conductor se representa con un patch (marcador grande) en el extremo de `Lk` y las zonas prohibidas son **círculos** centrados en ese extremo con radios (s, s_tormenta, s_decmax, D_fases, Dhg) y área sombreada.
  - Aclarar la regla visual: cuando múltiples zonas se solapan, **dibujar todas** pero recortar las intersecciones para evitar sombreado doble (operación de clipping/boolean geometry; no duplicar alpha para intersecciones).

- Zonas de prohibición: estados y comparaciones (ALTO)
  - Aclarar la regla de chequeo: todos los chequeos de zonas **deben** evaluarse por **cada declinación por separado** (reposo, tormenta, declinación máxima). Para cada declinación:
    - Comparar conductores vs conductores **solo** con la misma declinación (p. ej. cond_h1a con declinación tormenta vs cond_h2a en tormenta). No comparar mezclando declinaciones.
    - Comparar conductor vs elementos fijos (ménsula/columna/cruceta/nodos) usando `s` correspondiente a la declinación considerada.
    - Verificar `Dhg` entre guardias y conductores según el estado correspondiente.
  - Documentar que los mensajes de ERROR deben incluir: tipo de infracción, elementos involucrados y distancia de infracción.

- Conectador y ejecución por etapas (MEDIO)
  - Especificar claramente que el 'conectador' (generador de conexiones) **debe ejecutarse** inmediatamente al final de cada etapa que genere nodos (Etapa 1/2/4 cuando apliquen), e imprimir `Ejecutando conectador de nodos...` seguido por la lista de **conexiones nuevas** encontradas (nivel INFO).

- Reglas de tolerancias y comparaciones numéricas (MEDIO)
  - Establecer tolerancias: agrupar alturas usando `tol_z = 1e-3 m` (evitar comparaciones exactas en floats) y considerar solapamiento TOP/HG si distancia < 0.01 m (no crear TOP si se solapa con HG).

- UI / parámetros (MEDIO)
  - Indicar los parámetros que la UI debe exponer o mantener: `defasaje_y_guardia` (opcional, default 0.0), `defasaje_mensula_hielo` (bool), `lmen_extra_hielo` (float), `mensula_defasar` ("primera"/"segunda"/"tercera"), `long_mensula_min_conductor`/`long_mensula_min_guardia`.
  - Documentar que `s_tormenta` y `s_decmax` por defecto son iguales a `s_estructura` salvo que la configuración los sobrescriba.

- Gráficos y caching (pequeño)
  - Reforzar la regla de cache: cuando se guarden gráficos (Plotly u otros) en caché siempre guardar **JSON** y **PNG** (convención del repo) para que los gráficos puedan reproducirse y renderizarse desde cache.

- Tests y documentación (ALTO — pruebas por usuario HUMANO)
  - Incluir lista de casos de prueba que el usuario (humano) debe ejecutar manualmente: ternas (simple/doble) y disposiciones (vertical/horizontal/triangular), Lk=0 vs Lk>0, defasaje hielo en primera/segunda/tercera, CANT_HG = 0/1/2 y HG_CENTRADO True/False, y escenarios de solapamiento de zonas.
  - Añadir en el doc la instrucción de marcar las issues como `🔧 TESTING PENDIENTE` tras implementar cada etapa y dejar la verificación final en manos del usuario.

---

## 10. Reglas de Cache y Persistencia

### 10.1 Formato Dual para Gráficos Plotly

**REGLA OBLIGATORIA**: Siempre guardar PNG + JSON

```python
# Guardar figura Plotly
fig.write_image(f"cabezal_{hash}.png", width=1200, height=800)
fig.write_json(f"cabezal_{hash}.json")

# Cargar figura Plotly
with open(f"cabezal_{hash}.json", 'r') as f:
    fig_dict = json.load(f)
fig = go.Figure(fig_dict)
```

**Motivo**: 
- PNG: Exportar/documentar
- JSON: Interactividad en Dash (zoom, pan, hover)

### 10.2 Convención del Repositorio

Todos los gráficos en `data/cache/` deben tener ambos formatos para reproducibilidad.

## 11. Arquitectura Corregida - Resumen de Etapas

### Etapa 0: Nodo Base
- Crear nodo BASE en (0, 0, 0)

### Etapa 1: h1a y Lmen1
- Calcular h1a con fórmula obligatoria
- Calcular Lmen1 iterativamente chequeando s_decmax
- Manejar infracciones columna vs ménsula

### Etapa 2: h2a
- Calcular h2a_inicial
- Optimizar con defasaje hielo (buscar zoptimo2)
- Aplicar HADD_ENTRE_AMARRES

### Etapa 3: h3a
- Similar a Etapa 2
- Solo para disposición vertical

### Etapa 4: Cable de Guardia
- Calcular posición con algoritmo iterativo
- Respetar zonas Dhg
- Crear nodo VIENTO
- Ejecutar conectador

### Etapa 5: Conexiones
- Generar conexiones ménsula/columna
- Detectar nodos intermedios
- Listar SOLO conexiones NUEVAS

### Etapa 6: Checkeos
- Checkear zonas POR DECLINACIÓN
- Checkear apantallamiento
- Checkear sub-optimización
- Generar gráficos finales