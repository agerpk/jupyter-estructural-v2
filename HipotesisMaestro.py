### 004 HIPOTESIS MAESTRO
hipotesis_maestro = {
    "Suspensión Recta": {
        "A0": {
            "desc": "EDS (TMA)",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A1": {
            "desc": "Vmax Transversal",
            "viento": {"estado": "Vmax", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A2": {
            "desc": "Vmax Longitudinal", 
            "viento": {"estado": "Vmax", "direccion": "Longitudinal", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A3": {
            "desc": "Vmax Oblicuo",
            "viento": {"estado": "Vmax", "direccion": "Oblicua", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A4": {
            "desc": "Vmed Transversal + hielo",
            "viento": {"estado": "Vmed", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmed", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": True},
            "sobrecarga": None
        },
        "A5": {
            "desc": "Tiro unilateral reducido",
            "viento": None,
            "tiro": {"estado": "Vmed", "patron": "bilateral", "reduccion_cond": 0.20, "reduccion_guardia": 0.40},
            "peso": {"factor": 1.0, "hielo": True},
            "sobrecarga": None
        },
        "B1": {
            "desc": "Pesos x 2.5 - C.S.",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 2.5, "hielo": False},
            "sobrecarga": 220.0
        },
        "C1": {
            "desc": "Carga longitudinal",
            "viento": None,
            "tiro": {"estado": "Vmed", "patron": "dos-unilaterales", "reduccion_cond": 0.0, "reduccion_guardia": 0.0,"factor_cond": 0.65, "factor_guardia": 0.7},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "C2": {
            "desc": "Sismo",
            "viento": None,
            "tiro": {"estado": "Tmin", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        }
    },
    
    "Suspensión angular": {
        "A0": {
            "desc": "EDS (TMA)",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A1": {
            "desc": "Vmax Transversal",
            "viento": {"estado": "Vmax", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A2": {
            "desc": "Vmax Longitudinal",
            "viento": {"estado": "Vmax", "direccion": "Longitudinal", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A3": {
            "desc": "Vmax Oblicuo", 
            "viento": {"estado": "Vmax", "direccion": "Oblicua", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A4": {
            "desc": "Vmed Transversal + hielo",
            "viento": {"estado": "Vmed", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmed", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": True},
            "sobrecarga": None
        },
        "A5": {
            "desc": "Tiro unilateral reducido",
            "viento": None,
            "tiro": {"estado": "Vmed", "patron": "bilateral", "reduccion_cond": 0.20, "reduccion_guardia": 0.40},
            "peso": {"factor": 1.0, "hielo": True},
            "sobrecarga": None
        },
        "B1": {
            "desc": "Pesos x 2.5 - C.S.",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 2.5, "hielo": False},
            "sobrecarga": 220.0
        },
        "C1": {
            "desc": "Carga longitudinal",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "unilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "C2": {
            "desc": "Sismo",
            "viento": None,
            "tiro": {"estado": "Tmin", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        }
    },
    
    "Retención / Ret. Angular": {
        "A0": {
            "desc": "EDS (TMA)",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A1": {
            "desc": "Vmax Transversal",
            "viento": {"estado": "Vmax", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A2": {
            "desc": "Vmax Longitudinal",
            "viento": {"estado": "Vmax", "direccion": "Longitudinal", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A3": {
            "desc": "Vmax Oblicuo",
            "viento": {"estado": "Vmax", "direccion": "Oblicua", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A4": {
            "desc": "Vmed Transversal + hielo", 
            "viento": {"estado": "Vmed", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmed", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": True},
            "sobrecarga": None
        },
        "B1": {
            "desc": "Pesos x 2.5 - C.S.",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 2.5, "hielo": False},
            "sobrecarga": 220.0
        },
        "B2": {
            "desc": "Pesos x 2.5 - Unilateral Completo",
            "viento": None,
            "tiro": {"estado": "Tmin", "patron": "unilateral", "factor_cond": 1.0, "factor_guardia": 1.0},
            "peso": {"factor": 2.5, "hielo": False},
            "sobrecarga": None
        },
        "C1": {
            "desc": "Tiro máximo unilateral en dos puntos",
            "viento": None,
            "tiro": {"estado": "máximo", "patron": "dos-unilaterales", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "C2": {
            "desc": "Sismo",
            "viento": None,
            "tiro": {"estado": "Tmin", "patron": "bilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        }
    },
    
    "Terminal": {
        "A0": {
            "desc": "EDS (TMA)",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "unilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A1": {
            "desc": "Vmax Transversal",
            "viento": {"estado": "Vmax", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmax", "patron": "unilateral", "factor_cond": 1.0, "factor_guardia": 1.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "A2": {
            "desc": "Vmed Transversal + hielo",
            "viento": {"estado": "Vmed", "direccion": "Transversal", "factor": 1.0},
            "tiro": {"estado": "Vmed", "patron": "unilateral", "factor_cond": 1.0, "factor_guardia": 1.0},
            "peso": {"factor": 1.0, "hielo": True},
            "sobrecarga": None
        },
        "B1": {
            "desc": "Pesos x 2.5 + Tiro unilateral (Tiro ma x 0.66)x  1.5",
            "viento": None,
            "tiro": {"estado": "Vmed", "patron": "unilateral", "factor_cond": 1.0, "factor_guardia": 1.0},
            "peso": {"factor": 2.5, "hielo": False},
            "sobrecarga": 220.0
        },
        "C1": {
            "desc": "Eliminación de una fase",
            "viento": None,
            "tiro": {"estado": "Vmed", "patron": "dos-unilaterales", "factor_cond": 1.0, "factor_guardia": 1.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        },
        "C2": {
            "desc": "Sismo",
            "viento": None,
            "tiro": {"estado": "TMA", "patron": "unilateral", "reduccion_cond": 0.0, "reduccion_guardia": 0.0},
            "peso": {"factor": 1.0, "hielo": False},
            "sobrecarga": None
        }
    }
}
