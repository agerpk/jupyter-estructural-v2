# Callbacks mínimos para la vista del Editor de Hipótesis
def register_callbacks(app):
    """Registra callbacks mínimos para la vista del Editor de Hipótesis"""
    from dash.dependencies import Input, Output, State, ALL
    from dash import callback_context, dash
    from dash import html
    import json
    import dash_bootstrap_components as dbc
    from utils.hipotesis_manager import HipotesisManager
    from pathlib import Path
    import base64
    from components.editor_hipotesis import crear_modal_editor_hipotesis

    @app.callback(
        Output('hip-list', 'children'),
        Input('menu-editor-hipotesis', 'n_clicks')
    )
    def _llenar_lista(n):
        hip_list = HipotesisManager.listar_hipotesis()
        items = [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in hip_list]
        return items

    @app.callback(
        Output('hip-seleccionada', 'data'),
        Input({'type': 'hip-item', 'name': ALL}, 'n_clicks'),
        State('hip-seleccionada', 'data')
    )
    def _seleccionar(n_clicks_list, current):
        ctx = callback_context
        if not ctx.triggered:
            return current
        prop = ctx.triggered[0]['prop_id'].split('.')[0]
        try:
            obj = json.loads(prop)
            nombre = obj.get('name')
            return nombre
        except Exception:
            return current

    @app.callback(
        Output('hip-activa-nombre', 'children'),
        Input('hip-list', 'children') # Se activa cuando la lista se carga
    )
    def _mostrar_hipotesis_activa_inicial(lista):
        activa = HipotesisManager.obtener_hipotesis_activa()
        return activa if activa else "Ninguna"


    @app.callback(
        Output('hip-detalle', 'children'),
        Input('hip-seleccionada', 'data')
    )
    def _mostrar_detalle(nombre):
        if not nombre:
            return html.Div('Seleccione una hipótesis')
        contenido = HipotesisManager.cargar_hipotesis_por_nombre(nombre.replace('.hipotesis.json',''))
        return html.Pre(json.dumps(contenido, indent=2, ensure_ascii=False))

    @app.callback(
        Output('modal-editor-hipotesis', 'children'),
        Output('modal-editor-hipotesis', 'is_open'),
        Output('hip-modal-datos', 'data'),
        Output('hip-modal-tipo', 'data'),
        Input('btn-editar-hip', 'n_clicks'),
        State('hip-seleccionada', 'data')
    )
    def _abrir_modal(n, nombre):
        if not n or not nombre:
            raise dash.exceptions.PreventUpdate
        nombre_sin = nombre.replace('.hipotesis.json','')
        datos = HipotesisManager.cargar_hipotesis_por_nombre(nombre_sin)
        if not datos:
            raise dash.exceptions.PreventUpdate
        hip_maestro = datos.get('hipotesis_maestro', {})
        # Elegir primer tipo disponible para editar
        tipos = list(hip_maestro.keys())
        tipo = tipos[0] if tipos else 'default'
        contenido_tipo = hip_maestro.get(tipo, {})
        # Crear modal con contenido
        new_modal = crear_modal_editor_hipotesis(tipo, {tipo: contenido_tipo})
        return new_modal, True, datos, tipo

    @app.callback(
        Output('hip-campos-container', 'children'),
        Output('hip-modal-tipo', 'data'),
        Input('hip-modal-tipo-select', 'value'),
        State('hip-modal-datos', 'data')
    )
    def _cambiar_tipo(tipo, datos):
        from dash import dash
        from dash import html
        import dash_bootstrap_components as dbc
        from components.editor_hipotesis import crear_editor_hipotesis_campo
        if not tipo or not datos:
            raise dash.exceptions.PreventUpdate
        hip_maestro = datos.get('hipotesis_maestro', {})
        contenido_tipo = hip_maestro.get(tipo, {})
        campos = [crear_editor_hipotesis_campo(codigo, datos) for codigo, datos in contenido_tipo.items()]
        return campos, tipo

    @app.callback(
        Output('hip-list', 'children', allow_duplicate=True),
        Output('hip-detalle', 'children'),
        Output('hip-toasts-container', 'children'),
        Input('btn-guardar-hipotesis', 'n_clicks'),
        State('hip-seleccionada', 'data'),
        State('hip-modal-datos', 'data'),
        State('hip-modal-tipo', 'data'),
        State({'type': 'hip-desc', 'index': ALL}, 'value'),
        State({'type': 'hip-desc', 'index': ALL}, 'id'),
        State({'type': 'hip-viento-estado', 'index': ALL}, 'value'),
        State({'type': 'hip-viento-dir', 'index': ALL}, 'value'),
        State({'type': 'hip-viento-factor', 'index': ALL}, 'value'),
        State({'type': 'hip-tiro-estado', 'index': ALL}, 'value'),
        State({'type': 'hip-tiro-patron', 'index': ALL}, 'value'),
        State({'type': 'hip-tiro-red-cond', 'index': ALL}, 'value'),
        State({'type': 'hip-tiro-red-guard', 'index': ALL}, 'value'),
        State({'type': 'hip-tiro-factor-cond', 'index': ALL}, 'value'),
        State({'type': 'hip-tiro-factor-guard', 'index': ALL}, 'value'),
        State({'type': 'hip-peso-factor', 'index': ALL}, 'value'),
        State({'type': 'hip-peso-hielo', 'index': ALL}, 'value'),
        State({'type': 'hip-sobrecarga', 'index': ALL}, 'value')
    )
    def _guardar(n_save, nombre_hipotesis, datos_modal, tipo_actual,
                 desc_vals, desc_ids,
                 viento_estado_vals, viento_dir_vals, viento_factor_vals,
                 tiro_estado_vals, tiro_patron_vals, tiro_red_cond_vals, tiro_red_guard_vals, tiro_factor_cond_vals, tiro_factor_guard_vals,
                 peso_factor_vals, peso_hielo_vals,
                 sobrecarga_vals):
        if not n_save or not datos_modal or not nombre_hipotesis:
            raise dash.exceptions.PreventUpdate
            
        # Build mapping from index to values
        indices = [d.get('index') for d in desc_ids]
        hip_maestro_new = {}
        for i, idx in enumerate(indices):
            key = str(idx)
            viento = None
            # Map viento
            try:
                viento = {
                    'estado': viento_estado_vals[i],
                    'direccion': viento_dir_vals[i],
                    'factor': float(viento_factor_vals[i]) if viento_factor_vals[i] is not None else 1.0
                }
            except Exception:
                viento = None
            tiro = {
                'estado': tiro_estado_vals[i] if tiro_estado_vals and len(tiro_estado_vals) > i else None,
                'patron': tiro_patron_vals[i] if tiro_patron_vals and len(tiro_patron_vals) > i else None,
                'reduccion_cond': tiro_red_cond_vals[i] if tiro_red_cond_vals and len(tiro_red_cond_vals) > i else 0.0,
                'reduccion_guardia': tiro_red_guard_vals[i] if tiro_red_guard_vals and len(tiro_red_guard_vals) > i else 0.0,
                'factor_cond': tiro_factor_cond_vals[i] if tiro_factor_cond_vals and len(tiro_factor_cond_vals) > i else 1.0,
                'factor_guard': tiro_factor_guard_vals[i] if tiro_factor_guard_vals and len(tiro_factor_guard_vals) > i else 1.0
            }
            peso = {
                'factor': peso_factor_vals[i] if peso_factor_vals and len(peso_factor_vals) > i else 1.0,
                'hielo': bool(peso_hielo_vals[i]) if peso_hielo_vals and len(peso_hielo_vals) > i else False
            }
            sobrecarga = sobrecarga_vals[i] if sobrecarga_vals and len(sobrecarga_vals) > i else 0
            hip_maestro_new[key] = {
                'desc': desc_vals[i] if desc_vals and len(desc_vals) > i else '',
                'viento': viento,
                'tiro': tiro,
                'peso': peso,
                'sobrecarga': sobrecarga
            }
        # Merge into existing datos_modal structure
        datos_modal['hipotesis_maestro'][tipo_actual] = hip_maestro_new
        
        # Validate
        ok, msg = HipotesisManager.validar_hipotesis(datos_modal.get('hipotesis_maestro', datos_modal))
        if not ok:
            toast = dbc.Toast(f'Save failed: {msg}', header='Guardar', duration=5000, is_open=True, color='danger')
            nombre_sin_ext = nombre_hipotesis.replace('.hipotesis.json', '')
            return [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in HipotesisManager.listar_hipotesis()], html.Pre(json.dumps(HipotesisManager.cargar_hipotesis_por_nombre(nombre_sin_ext), indent=2, ensure_ascii=False)), toast
            
        # Persist file
        HipotesisManager.guardar_hipotesis(nombre_hipotesis, datos_modal)
        
        toast = dbc.Toast('Guardado correctamente', header='Guardar', duration=3000, is_open=True, color='success')
        items = [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in HipotesisManager.listar_hipotesis()]
        detalle = html.Pre(json.dumps(datos_modal, indent=2, ensure_ascii=False))
        return items, detalle, toast

    @app.callback(
        Output('modal-editor-hipotesis', 'is_open', allow_duplicate=True),
        Input('btn-cancelar-hipotesis', 'n_clicks'),
        Input('btn-guardar-hipotesis', 'n_clicks'),
        Input('btn-eliminar-hipotesis', 'n_clicks'),
        State('modal-editor-hipotesis', 'is_open')
    )
    def _cerrar_modal(n_cancel, n_save, n_delete, is_open):
        # Close on cancel or after save/delete
        ctx = callback_context
        if not ctx.triggered:
            return is_open
        triggered = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered in ['btn-cancelar-hipotesis', 'btn-guardar-hipotesis', 'btn-eliminar-hipotesis']:
            return False
        return is_open

    @app.callback(
        Output('hip-activa-nombre', 'children', allow_duplicate=True),
        Output('hip-toasts-container', 'children', allow_duplicate=True),
        Input('btn-activar-hip', 'n_clicks'),
        State('hip-seleccionada', 'data'),
        prevent_initial_call=True
    )
    def _activar(n, nombre):
        if not n or not nombre:
            toast = dbc.Toast(
                "Por favor, seleccione una hipótesis de la lista para activarla.",
                header="Acción requerida",
                icon="warning",
                duration=4000,
            )
            return dash.no_update, toast

        nombre_sin_ext = nombre.replace('.hipotesis.json','')
        HipotesisManager.establecer_hipotesis_activa(nombre_sin_ext)
        
        toast = dbc.Toast(
            f"La hipótesis '{nombre}' ha sido activada.",
            header="Éxito",
            icon="success",
            duration=4000,
        )
        return nombre, toast

    @app.callback(
        Output('hip-list', 'children', allow_duplicate=True),
        Output('hip-detalle', 'children'),
        Input('btn-exportar-hipotesis', 'n_clicks'),
        State('hip-seleccionada', 'data')
    )
    def _exportar(n_exp, nombre_selec):
        if not n_exp or not nombre_selec:
            raise dash.exceptions.PreventUpdate
        nombre_sin = nombre_selec.replace('.hipotesis.json','')
        destino = HipotesisManager.export_hipotesis(nombre_sin)
        if not destino:
            return [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in HipotesisManager.listar_hipotesis()], html.Div('Archivo no encontrado para exportar'), dbc.Toast('Error exportando', header='Exportar', duration=4000, is_open=True, color='danger')
        toast = dbc.Toast(f'Exportado a {destino}', header='Exportar', duration=3000, is_open=True, color='info')
        return [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in HipotesisManager.listar_hipotesis()], html.Div(f'Exportado a {destino}'), toast

    @app.callback(
        Output('hip-list', 'children', allow_duplicate=True),
        Output('hip-detalle', 'children'),
        Input('upload-hipotesis', 'contents'),
        State('upload-hipotesis', 'filename')
    )
    def _importar(contents, filename):
        if not contents or not filename:
            raise dash.exceptions.PreventUpdate
        header, b64 = contents.split(',', 1)
        data = base64.b64decode(b64)
        hip_dir = Path(__file__).parent.parent / 'data' / 'hipotesis'
        hip_dir.mkdir(parents=True, exist_ok=True)
        # Ensure filename ends with .hipotesis.json
        if not filename.endswith('.hipotesis.json'):
            filename = filename + '.hipotesis.json'
        destino = hip_dir / filename
        destino.write_bytes(data)
        # Validate structure quickly
        try:
            with open(destino, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            ok, msg = HipotesisManager.validar_hipotesis(datos.get('hipotesis_maestro', datos))
            if not ok:
                toast = dbc.Toast(f'Import failed: {msg}', header='Importar', duration=5000, is_open=True, color='danger')
                return [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in HipotesisManager.listar_hipotesis()], html.Div('Error al importar'), toast
        except Exception as e:
            toast = dbc.Toast(f'Import failed: {e}', header='Importar', duration=5000, is_open=True, color='danger')
            return [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in HipotesisManager.listar_hipotesis()], html.Div('Error al importar'), toast

        hip_list = HipotesisManager.listar_hipotesis()
        items = [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in hip_list]
        detalle = html.Pre(json.dumps(HipotesisManager.cargar_hipotesis_por_nombre(destino.stem), indent=2, ensure_ascii=False))
        toast = dbc.Toast('Importado correctamente', header='Importar', duration=3000, is_open=True, color='success')
        return items, detalle, toast

    # --- Callbacks para Eliminar ---
    @app.callback(
        Output('modal-delete-hip', 'is_open'),
        Output('delete-hip-confirm-body', 'children'),
        Output('hip-toasts-container', 'children', allow_duplicate=True),
        Input('btn-eliminar-hip', 'n_clicks'),
        State('hip-seleccionada', 'data'),
        prevent_initial_call=True
    )
    def _abrir_modal_delete(n, nombre_seleccionado):
        if not n or not nombre_seleccionado:
            toast = dbc.Toast(
                "Por favor, seleccione una hipótesis de la lista para eliminar.",
                header="Acción requerida",
                icon="warning",
                duration=4000,
            )
            return False, dash.no_update, toast
        
        return True, f"¿Está seguro de que desea eliminar la hipótesis '{nombre_seleccionado}'? Esta acción no se puede deshacer.", dash.no_update

    @app.callback(
        Output('modal-delete-hip', 'is_open', allow_duplicate=True),
        Output('hip-list', 'children', allow_duplicate=True),
        Output('hip-seleccionada', 'data', allow_duplicate=True),
        Output('hip-toasts-container', 'children', allow_duplicate=True),
        Input('delete-hip-confirmar-btn', 'n_clicks'),
        State('hip-seleccionada', 'data'),
        prevent_initial_call=True
    )
    def _ejecutar_delete(n, nombre_seleccionado):
        if not n or not nombre_seleccionado:
            raise dash.exceptions.PreventUpdate

        nombre_sin_ext = nombre_seleccionado.replace('.hipotesis.json', '')
        res = HipotesisManager.eliminar_hipotesis(nombre_sin_ext)
        
        if res:
            toast = dbc.Toast('Eliminado correctamente.', header='Éxito', icon='success', duration=3000)
            hip_list = HipotesisManager.listar_hipotesis()
            items = [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in hip_list]
            return False, items, None, toast
        else:
            toast = dbc.Toast('Error al eliminar el archivo.', header='Error', icon='danger', duration=4000)
            return True, dash.no_update, dash.no_update, toast

    @app.callback(
        Output('modal-delete-hip', 'is_open', allow_duplicate=True),
        Input('delete-hip-cancelar-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def _cerrar_modal_delete(n):
        return False

    # --- Callbacks para Crear ---
    @app.callback(
        Output('modal-crear-hip', 'is_open'),
        Input('btn-crear-hip', 'n_clicks'),
        prevent_initial_call=True
    )
    def _abrir_modal_crear(n):
        return True

    @app.callback(
        Output('modal-crear-hip', 'is_open', allow_duplicate=True),
        Output('hip-list', 'children', allow_duplicate=True),
        Output('hip-toasts-container', 'children', allow_duplicate=True),
        Output('hip-seleccionada', 'data', allow_duplicate=True),
        Input('crear-hip-guardar-btn', 'n_clicks'),
        State('crear-hip-nombre-input', 'value'),
        prevent_initial_call=True
    )
    def _ejecutar_crear(n, nombre_nuevo):
        if not n or not nombre_nuevo or not nombre_nuevo.strip():
            toast = dbc.Toast("El nombre no puede estar vacío.", header="Error", icon="danger", duration=4000)
            return True, dash.no_update, toast, dash.no_update

        # Cargar la hipótesis activa como base, o la plantilla si no hay activa
        datos_base = HipotesisManager.cargar_hipotesis_activa()
        if not datos_base:
            print("INFO: No hay hipótesis activa, creando desde plantilla.")
            datos_base = HipotesisManager.cargar_hipotesis_por_nombre('plantilla')

        if not datos_base:
            toast = dbc.Toast("Error: No se encontró ni hipótesis activa ni plantilla para copiar.", header="Error", icon="danger", duration=5000)
            return True, dash.no_update, toast, dash.no_update

        # Guardar la copia
        HipotesisManager.guardar_hipotesis(nombre_nuevo, datos_base)
        # Establecer la nueva hipótesis como activa
        HipotesisManager.establecer_hipotesis_activa(nombre_nuevo)

        # Actualizar la lista y notificar
        hip_list = HipotesisManager.listar_hipotesis()
        items = [dbc.ListGroupItem(h, id={"type": "hip-item", "name": h}, action=True) for h in hip_list]
        toast = dbc.Toast(f"Hipótesis '{nombre_nuevo}' creada con éxito.", header="Éxito", icon="success", duration=3000)
        # Seleccionar la nueva hipótesis en el store (con extensión)
        seleccion_name = f"{nombre_nuevo}.hipotesis.json"
        return False, items, toast, seleccion_name

    @app.callback(
        Output('modal-crear-hip', 'is_open', allow_duplicate=True),
        Input('crear-hip-cancelar-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def _cerrar_modal_crear(n):
        return False
