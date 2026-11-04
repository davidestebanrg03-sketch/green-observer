"""Pruebas de la sesión compartida y de los cambios heredados de la segunda versión."""
import unittest
from dataclasses import replace

from invernadero.parametros import Parametros, escenarios
from invernadero.sesion import SesionSimulacion, VELOCIDADES
from invernadero.simulador import Simulador


class PlanificadorFalso:
    """Imita after/after_cancel de Tkinter: las tareas se ejecutan a mano con ``correr``."""

    def __init__(self):
        self.tareas, self.sig, self.intervalos = {}, 1, []

    def after(self, ms, f):
        self.intervalos.append(ms)
        self.tareas[self.sig] = f
        self.sig += 1
        return self.sig - 1

    def after_cancel(self, i):
        self.tareas.pop(i, None)

    def correr(self, max_ticks=100000):
        n = 0
        while self.tareas and n < max_ticks:
            i = min(self.tareas)
            self.tareas.pop(i)()
            n += 1
        return n


def sesion(**cambios):
    plan = PlanificadorFalso()
    p = replace(Parametros(), **cambios)
    return plan, SesionSimulacion(plan, p, "prueba")


class TestSesion(unittest.TestCase):
    def test_dos_ventanas_ven_la_misma_simulacion(self):
        plan, s = sesion(duracion=60)
        vistas = {"a": [], "b": []}
        s.suscribir(lambda e: vistas["a"].append((e, s.sim.actual.t)), notificar=False)
        s.suscribir(lambda e: vistas["b"].append((e, s.sim.actual.t)), notificar=False)
        s.iniciar()
        plan.correr()
        self.assertTrue(s.terminado)
        self.assertEqual(vistas["a"], vistas["b"])
        self.assertEqual(vistas["a"][-1][0], "estado")          # último aviso: terminó
        self.assertAlmostEqual(s.sim.actual.t, 60.0)

    def test_pausar_detiene_el_reloj_sin_perder_el_estado(self):
        plan, s = sesion()
        s.iniciar()
        self.assertTrue(s.corriendo)
        s.pausar()
        self.assertFalse(s.corriendo)
        self.assertEqual(plan.tareas, {})
        s.iniciar()                                             # reanuda
        self.assertTrue(s.corriendo)

    def test_un_paso_y_ejecutar_todo(self):
        _, s = sesion(duracion=30)
        s.un_paso()
        self.assertEqual(len(s.sim.registros), 2)
        s.ejecutar_todo()
        self.assertTrue(s.terminado)
        self.assertEqual(len(s.sim.registros), 31)

    def test_cambiar_velocidad_en_marcha_reprograma(self):
        plan, s = sesion()
        s.set_velocidad(1)
        s.iniciar()
        self.assertEqual(plan.intervalos[-1], 1000)             # 1 paso por segundo
        s.set_velocidad(2000)
        self.assertEqual(plan.intervalos[-1], 40)               # lotes de pasos cada 40 ms
        self.assertEqual(len(plan.tareas), 1)                   # nunca hay dos relojes a la vez
        with self.assertRaises(ValueError):
            s.set_velocidad(0)

    def test_velocidad_rapida_avanza_varios_pasos_por_aviso(self):
        plan, s = sesion()
        s.set_velocidad(VELOCIDADES[-1])
        s.iniciar()
        plan.tareas[min(plan.tareas)]()
        self.assertEqual(len(s.sim.registros) - 1, round(VELOCIDADES[-1] * 0.04))

    def test_cargar_escenario_reemplaza_la_simulacion_y_avisa(self):
        plan, s = sesion()
        eventos = []
        s.suscribir(eventos.append, notificar=False)
        s.iniciar()
        s.cargar_escenario("Alta temperatura")
        self.assertFalse(s.corriendo)
        self.assertEqual(s.nombre, "Alta temperatura")
        self.assertEqual(s.p.Tmed, 29.0)
        self.assertEqual(len(s.sim.registros), 1)
        self.assertIn("nueva", eventos)

    def test_parametros_invalidos_no_alteran_la_sesion(self):
        _, s = sesion()
        sim_anterior = s.sim
        with self.assertRaises(ValueError):
            s.cargar(replace(Parametros(), H_min=90, H_max=70), "malo")
        self.assertIs(s.sim, sim_anterior)
        self.assertEqual(s.nombre, "prueba")

    def test_reiniciar_vuelve_a_t0_con_los_mismos_parametros(self):
        _, s = sesion(duracion=20)
        s.ejecutar_todo()
        p = s.p
        s.reiniciar()
        self.assertIs(s.p, p)
        self.assertEqual(s.sim.actual.t, 0.0)
        self.assertFalse(s.terminado)

    def test_observador_defectuoso_no_detiene_a_los_demas(self):
        _, s = sesion(duracion=10)
        ok = []
        s.suscribir(lambda e: 1 / 0, notificar=False)
        s.suscribir(ok.append, notificar=False)
        import contextlib, io
        with contextlib.redirect_stderr(io.StringIO()):
            s.un_paso()
        self.assertTrue(ok)

    def test_desuscribir(self):
        _, s = sesion()
        vistos = []
        obs = vistos.append
        s.suscribir(obs, notificar=False)
        s.desuscribir(obs)
        s.un_paso()
        self.assertEqual(vistos, [])

    def test_todos_los_escenarios_se_pueden_cargar_y_correr(self):
        _, s = sesion()
        for nombre in escenarios():
            with self.subTest(nombre):
                s.cargar_escenario(nombre)
                s.ejecutar_todo()
                self.assertTrue(s.terminado)


class TestMejorasDeLaSegundaVersion(unittest.TestCase):
    def test_ultimo_paso_recortado_cuando_la_duracion_no_es_multiplo_de_dt(self):
        sim = Simulador(replace(Parametros(), duracion=100, dt=30)).ejecutar()
        self.assertEqual([r.t for r in sim.registros], [0, 30, 60, 90, 100])

    def test_duracion_multiplo_no_cambia(self):
        sim = Simulador(replace(Parametros(), duracion=10, dt=1)).ejecutar()
        self.assertEqual(len(sim.registros), 11)
        self.assertEqual(sim.registros[-1].t, 10.0)

    def test_luz_total_no_supera_100(self):
        p = replace(Parametros(), usar_iluminacion=True, L_min=100.0, L_art=90.0, hora_inicio=11.0, duracion=120)
        sim = Simulador(p).ejecutar()
        self.assertTrue(all(r.L <= 100.0 + 1e-12 for r in sim.registros))
        self.assertTrue(any(r.luz for r in sim.registros))

    def test_la_planta_no_supera_K_aunque_euler_se_pase(self):
        p = replace(Parametros(), P0=49.9, K=50.0, r_max=5.0, T0=25.0, hora_inicio=12.0, duracion=60, dt=10)
        sim = Simulador(p).ejecutar()
        self.assertLessEqual(max(r.P for r in sim.registros), 50.0)

    def test_tiempo_con_actuadores_usa_duraciones_reales(self):
        sim = Simulador(replace(Parametros(), duracion=100, dt=30, H0=30.0)).ejecutar()
        self.assertEqual(sim.resumen()["min_riego"], 100.0)     # riego encendido todo el tiempo

    def test_nuevas_validaciones(self):
        for cambio in ({"P0": 60.0}, {"w_T": 0.0}, {"w_H": -1.0}, {"Lmax": -1.0}, {"L_min": 120.0},
                       {"L_art": -5.0}, {"ilum_hora_ini": 25.0}, {"R_on": -0.1}, {"E0": -0.1}):
            with self.subTest(cambio), self.assertRaises(ValueError):
                replace(Parametros(), **cambio).validar()


@unittest.skipUnless(__import__("importlib").util.find_spec("tkinter"), "Tkinter no disponible")
class TestInterfaz(unittest.TestCase):
    """Prueba de humo: abre las ventanas y comprueba que muestran la misma simulación."""

    def setUp(self):
        import tkinter as tk
        try:
            from interfaz.app import AplicacionGreenObserver
            self.app = AplicacionGreenObserver()
        except tk.TclError as e:                                # sin pantalla (servidor sin X)
            self.skipTest(f"sin entorno gráfico: {e}")
        self.app.withdraw()

    def tearDown(self):
        if hasattr(self, "app"):
            self.app.destroy()

    def test_ventanas_comparten_sesion(self):
        app = self.app
        app.abrir_control_center()
        app.abrir_invernadero()
        s = app.sesion
        self.assertIs(app.control_center.sesion, s)
        self.assertIs(app._ventana_inv.sesion, s)
        s.cargar_escenario("Baja humedad")
        for _ in range(120):
            s.un_paso()
        app.update()
        self.assertEqual(app._ventana_inv.cb_escenario.get(), "Baja humedad")
        self.assertEqual(app.control_center.cb_escenario.get(), "Baja humedad")
        self.assertIn("120", app.control_center.lbl_tiempo.cget("text"))
        self.assertIn("120", app._ventana_inv.lbl_estado.cget("text"))

    def test_abrir_dos_veces_reutiliza_la_ventana(self):
        self.app.abrir_invernadero()
        primera = self.app._ventana_inv
        self.app.abrir_invernadero()
        self.assertIs(primera, self.app._ventana_inv)

    def test_cerrar_invernadero_desuscribe(self):
        app = self.app
        app.abrir_invernadero()
        n = len(app.sesion._observadores)
        app._ventana_inv.cerrar()
        app.update()
        self.assertEqual(len(app.sesion._observadores), n - 1)
        app.sesion.un_paso()                                    # no debe fallar

    def test_aplicar_parametros_desde_el_formulario(self):
        app = self.app
        cc = app.control_center
        cc.vars["Tmed"].set("30")
        cc.aplicar_parametros()
        self.assertEqual(app.sesion.p.Tmed, 30.0)
        self.assertTrue(app.sesion.nombre.endswith("(editado)"))

    def test_todas_las_pestanas_se_dibujan_en_todos_los_escenarios(self):
        app = self.app
        app.abrir_control_center()
        app.deiconify()
        for nombre in escenarios():
            app.sesion.cargar_escenario(nombre)
            for _ in range(5):
                app.sesion.un_paso()
            for i in range(len(app.control_center.nb.tabs())):
                app.control_center.nb.select(i)
                app.update()


if __name__ == "__main__":
    unittest.main()
