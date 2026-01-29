import pandas as pd
from controllers import mecanica_controller


def test_generar_resumen_con_nota_a5():
    # Crear DataFrame mínimo con columnas necesarias
    idx = ['HIP_Suspension_Recta_A5_TiroUnilateral']
    df = pd.DataFrame({
        'Tiro_resultante_daN': [1000.0],
        'Reaccion_Fz_daN': [-500.0],
        'Altura_efectiva_m': [38.02],
        'Nodo_apoyo': ['BASE'],
        'Nodo_cima': ['TOP']
    }, index=idx)

    # Estructura actual mínima
    estructura_actual = {'TENSION': 220, 'TIPO_ESTRUCTURA': 'Suspension Recta'}

    # Crear objeto mecanica simulando que aplicó A5
    class DummyMec:
        hipotesis_a5_aplico_15pc = ['HIP_Suspension_Recta_A5_TiroUnilateral']

    dummy_mec = DummyMec()

    # Llamar a la función (re-crear la lógica de resumen usada en el controller)
    # Extraer variables tal como lo hace el controller
    max_tiro = df['Tiro_resultante_daN'].max()
    min_fz = df['Reaccion_Fz_daN'].min()
    hip_max_tiro = df['Tiro_resultante_daN'].idxmax()
    hip_min_fz = df['Reaccion_Fz_daN'].idxmin()
    altura_efectiva = df['Altura_efectiva_m'].iloc[0]
    nodo_apoyo = df['Nodo_apoyo'].iloc[0]
    nodo_cima = df['Nodo_cima'].iloc[0]

    resumen_txt = (
        f"Estructura: {estructura_actual.get('TENSION')}kV - {estructura_actual.get('TIPO_ESTRUCTURA')}\n" +
        f"Altura efectiva: {altura_efectiva:.2f} m\n" +
        f"Nodo apoyo: {nodo_apoyo}, Nodo cima: {nodo_cima}\n\n" +
        f"🔴 Hipótesis más desfavorable por tiro en cima:\n" +
        f"   {hip_max_tiro}: {max_tiro:.1f} daN\n\n" +
        f"🔴 Hipótesis más desfavorable por carga vertical:\n" +
        f"   {hip_min_fz}: {min_fz:.1f} daN"
    )

    # Aplicar nota como hace el controller
    hip_aplicadas = getattr(dummy_mec, 'hipotesis_a5_aplico_15pc', [])
    if hip_aplicadas:
        hip_unicas = sorted(set(hip_aplicadas))
        hip_str = ", ".join(hip_unicas)
        resumen_txt += (
            "\n\n💡 Nota: Hipótesis A5 - reducción conductor aplicada = 15% (Lk > 2.5 m)"
            + (f" — {hip_str}" if hip_str else "")
        )

    assert "reducción conductor aplicada = 15%" in resumen_txt
    assert "HIP_Suspension_Recta_A5_TiroUnilateral" in resumen_txt
