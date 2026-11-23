"""Testes automatizados das regras de negócio. Execute: python -m unittest -v"""
import csv
import os
import tempfile
import unittest
from decimal import Decimal as D

from rentsmart import Apartamento, Casa, Estudio, Orcamento, ExportadorCSV


class TestAluguel(unittest.TestCase):
    def aluguel(self, imovel):
        return Orcamento(imovel, 1).aluguel_mensal

    def test_apartamento_1_quarto_sem_criancas(self):
        self.assertEqual(self.aluguel(Apartamento(1, False, False)), D("665.00"))  # 700 - 5%

    def test_apartamento_1_quarto_com_criancas(self):
        self.assertEqual(self.aluguel(Apartamento(1, False, True)), D("700.00"))

    def test_apartamento_2_quartos_garagem_sem_criancas(self):
        # (700 + 200 + 300) = 1200 ; -5% = 1140
        self.assertEqual(self.aluguel(Apartamento(2, True, False)), D("1140.00"))

    def test_apartamento_2_quartos_garagem_com_criancas(self):
        self.assertEqual(self.aluguel(Apartamento(2, True, True)), D("1200.00"))

    def test_casa_1_quarto(self):
        self.assertEqual(self.aluguel(Casa(1, False)), D("900.00"))

    def test_casa_2_quartos_garagem_nao_tem_desconto(self):
        self.assertEqual(self.aluguel(Casa(2, True)), D("1450.00"))

    def test_estudio_sem_vagas(self):
        self.assertEqual(self.aluguel(Estudio(0)), D("1200.00"))

    def test_estudio_pacote_inicial(self):
        self.assertEqual(self.aluguel(Estudio(2)), D("1450.00"))

    def test_estudio_vagas_adicionais(self):
        self.assertEqual(self.aluguel(Estudio(4)), D("1570.00"))  # 1200 + 250 + 2*60


class TestTaxaEProjecao(unittest.TestCase):
    def test_parcelas_exatas(self):
        self.assertEqual(Orcamento(Casa(1, False), 5).valores_parcelas, [D("400.00")] * 5)

    def test_parcelas_com_ajuste_de_centavos(self):
        parcelas = Orcamento(Casa(1, False), 3).valores_parcelas
        self.assertEqual(sum(parcelas), D("2000.00"))
        self.assertEqual(parcelas, [D("666.66"), D("666.66"), D("666.68")])

    def test_parcelas_invalidas(self):
        with self.assertRaises(ValueError):
            Orcamento(Casa(1, False), 6)
        with self.assertRaises(ValueError):
            Orcamento(Casa(1, False), 0)

    def test_projecao_12_meses(self):
        linhas = Orcamento(Casa(1, False), 4).projecao()
        self.assertEqual(len(linhas), 12)
        self.assertEqual(linhas[0].total_mes, D("1400.00"))   # 900 + 500
        self.assertEqual(linhas[4].total_mes, D("900.00"))    # taxa já quitada
        self.assertEqual(linhas[-1].total_acumulado, D("900.00") * 12 + D("2000.00"))

    def test_quartos_invalidos(self):
        with self.assertRaises(ValueError):
            Casa(3, False)


class TestCSV(unittest.TestCase):
    def test_csv_gerado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = ExportadorCSV(os.path.join(pasta, "p.csv")).exportar(
                Orcamento(Apartamento(1, False, False), 5))
            with open(caminho, encoding="utf-8-sig") as f:
                linhas = list(csv.reader(f, delimiter=";"))
        self.assertEqual(len(linhas), 13)                      # cabeçalho + 12 meses
        self.assertEqual(linhas[1], ["1", "665,00", "400,00", "1065,00", "1065,00"])


if __name__ == "__main__":
    unittest.main()
