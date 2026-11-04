"""Pruebas automáticas.  Ejecutar con:  python -m unittest -v"""
import math
import unittest
from dataclasses import replace

from invernadero import modelo, verificacion
from invernadero.parametros import Parametros, escenarios
from invernadero.simulador import Simulador


class TestModelo(unittest.TestCase):
    def test_tasa_humedad(self):
        self.assertAlmostEqual(modelo.tasa_humedad(0, 0.8), -0.8)
        self.assertAlmostEqual(modelo.tasa_humedad(2.5, 0.8), 1.7)

    def test_temperatura_ambiente_extremos(self):
        p = Parametros(hora_inicio=0.0)
        self.assertAlmostEqual(modelo.temperatura_ambiente(15 * 60, p), p.Tmed + p.Amp_T)
        self.assertAlmostEqual(modelo.temperatura_ambiente(3 * 60, p), p.Tmed - p.Amp_T)

    def test_luz_natural(self):
        p = Parametros(hora_inicio=0.0)
        self.assertAlmostEqual(modelo.luz_natural(12 * 60, p), p.Lmax)
        self.assertAlmostEqual(modelo.luz_natural(9 * 60, p), p.Lmax * math.sqrt(2) / 2)
        self.assertEqual(modelo.luz_natural(22 * 60, p), 0.0)   # de noche

    def test_ventilacion_aumenta_intercambio(self):
        p = Parametros(a_sol=0.0)
        self.assertLess(modelo.tasa_temperatura(35, 30, 0, True, p),
                        modelo.tasa_temperatura(35, 30, 0, False, p))


class TestManual(unittest.TestCase):
    def test_humedad_del_documento(self):
        for n, manual, prog, dif in verificacion.comparar_humedad_manual():
            self.assertLess(dif, 1e-9, f"paso {n}")

    def test_temperatura_manual(self):
        for caso, n, m, c, d in verificacion.comparar_temperatura_manual():
            self.assertLess(d, 1e-9, f"{caso} paso {n}")


class TestControl(unittest.TestCase):
    def test_riego_se_activa_y_desactiva(self):
        s = Simulador(replace(Parametros(), H0=45.0, E0=0.06)).ejecutar()
        tipos = [e[1] for e in s.eventos]
        self.assertIn("riego_on", tipos)
        self.assertIn("riego_off", tipos)

    def test_sin_control_no_hay_eventos_de_actuadores(self):
        s = Simulador(replace(Parametros(), control_activo=False)).ejecutar()
        self.assertEqual([e[1] for e in s.eventos], ["inicio", "fin"])

    def test_histeresis_evita_oscilacion(self):
        s = Simulador(Parametros()).ejecutar()
        self.assertLess(len(s.eventos), 30)

    def test_iluminacion(self):
        s = Simulador(escenarios()["Poca luz / nublado"]).ejecutar()
        self.assertGreater(s.resumen()["act_luz"], 0)


class TestNumerico(unittest.TestCase):
    def test_euler_converge(self):
        e = dict(verificacion.error_vs_dt(dts=(10, 1, 0.1)))
        self.assertGreater(e[10], e[1])
        self.assertGreater(e[1], e[0.1])

    def test_euler_es_de_primer_orden(self):
        e = dict(verificacion.error_vs_dt(dts=(1, 0.5)))
        self.assertAlmostEqual(e[1] / e[0.5], 2.0, delta=0.15)

    def test_comportamientos(self):
        for desc, ok in verificacion.verificar_comportamientos():
            self.assertTrue(ok, desc)

    def test_parametros_invalidos(self):
        with self.assertRaises(ValueError):
            Simulador(replace(Parametros(), dt=0))
        with self.assertRaises(ValueError):
            Simulador(replace(Parametros(), H_min=80, H_max=70))



class TestFormulario(unittest.TestCase):
    def test_todos_los_parametros_tienen_campo(self):
        from dataclasses import fields
        from invernadero.campos import BOOLEANOS, CAMPOS
        en_form = {c[0] for _, lista in CAMPOS for c in lista} | {b[0] for b in BOOLEANOS}
        self.assertEqual(en_form, {f.name for f in fields(Parametros)})


if __name__ == "__main__":
    unittest.main()
