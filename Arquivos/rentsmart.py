"""
RentSmart - Sistema de orçamento de locação da R.M Imóveis
==========================================================
Execute com:  python rentsmart.py

ÍNDICE DO ARQUIVO
  PARTE 1 - Funções de formatação (dinheiro)
  PARTE 2 - Classes dos imóveis (Imovel, ImovelComQuartos, Apartamento, Casa, Estudio)
  PARTE 3 - Classe Orcamento (cálculo do aluguel, da taxa e da projeção de 12 meses)
  PARTE 4 - Classe ExportadorCSV (gera o arquivo CSV)
  PARTE 5 - Entrada de dados e validação (menus e perguntas)
  PARTE 6 - Programa principal (une todas as partes)
"""

import csv
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP


# =====================================================================
# PARTE 1 - FORMATAÇÃO
# Funções simples para mostrar valores em reais (tela e CSV).
# Usamos Decimal (e não float) para não ter erros de arredondamento.
# =====================================================================

def formatar_moeda(valor: Decimal) -> str:
    """Ex.: 1234.5 -> 'R$ 1.234,50' (usado na tela)."""
    texto = f"{valor:,.2f}"                      # 1,234.50
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def formatar_numero_csv(valor: Decimal) -> str:
    """Ex.: 665 -> '665,00' (usado no CSV, vírgula decimal e sem símbolo)."""
    return f"{valor:.2f}".replace(".", ",")


def arredondar(valor: Decimal) -> Decimal:
    """Arredonda para duas casas decimais (centavos)."""
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# =====================================================================
# PARTE 2 - CLASSES DOS IMÓVEIS
# Hierarquia:
#   Imovel (abstrata)
#   ├── ImovelComQuartos (abstrata)  -> regras comuns de casa e apartamento
#   │   ├── Apartamento              -> + desconto de 5% sem crianças
#   │   └── Casa
#   └── Estudio                      -> regra própria de estacionamento
# =====================================================================

@dataclass(frozen=True)
class ItemOrcamento:
    """Uma linha do orçamento: descrição + valor (negativo = desconto)."""
    descricao: str
    valor: Decimal


class Imovel(ABC):
    """CLASSE BASE (abstrata): define o que todo imóvel precisa ter.
    Não se cria um 'Imovel' diretamente, apenas suas subclasses."""

    CATEGORIA = ""
    ALUGUEL_BASE = Decimal("0.00")

    @abstractmethod
    def descricao(self) -> str:
        """Texto curto com as escolhas do cliente."""

    @abstractmethod
    def adicionais(self) -> list[ItemOrcamento]:
        """Acréscimos mensais (quarto extra, garagem, vagas...)."""

    def desconto(self, subtotal: Decimal) -> ItemOrcamento | None:
        """Desconto comercial. Por padrão NÃO há desconto;
        só o Apartamento sobrescreve este método."""
        return None


class ImovelComQuartos(Imovel):
    """Regras COMPARTILHADAS por casas e apartamentos
    (1 ou 2 quartos + garagem opcional). Evita repetir código."""

    ADICIONAL_DOIS_QUARTOS = Decimal("0.00")   # cada subclasse define o seu valor
    VALOR_GARAGEM = Decimal("300.00")

    def __init__(self, quartos: int, tem_garagem: bool):
        if quartos not in (1, 2):
            raise ValueError("A quantidade de quartos deve ser 1 ou 2.")
        self.quartos = quartos
        self.tem_garagem = tem_garagem

    def descricao(self) -> str:
        garagem = "com garagem" if self.tem_garagem else "sem garagem"
        return f"{self.CATEGORIA} de {self.quartos} quarto(s), {garagem}"

    def adicionais(self) -> list[ItemOrcamento]:
        itens = []
        if self.quartos == 2:
            itens.append(ItemOrcamento("Adicional de 2 quartos", self.ADICIONAL_DOIS_QUARTOS))
        if self.tem_garagem:
            itens.append(ItemOrcamento("Vaga de garagem", self.VALOR_GARAGEM))
        return itens


class Apartamento(ImovelComQuartos):
    """Apartamento: base R$ 700 | 2 quartos +R$ 200 | garagem +R$ 300
    | 5% de desconto se o cliente NÃO tem crianças."""

    CATEGORIA = "Apartamento"
    ALUGUEL_BASE = Decimal("700.00")
    ADICIONAL_DOIS_QUARTOS = Decimal("200.00")
    PERCENTUAL_DESCONTO_SEM_CRIANCAS = Decimal("0.05")

    def __init__(self, quartos: int, tem_garagem: bool, tem_criancas: bool):
        super().__init__(quartos, tem_garagem)
        self.tem_criancas = tem_criancas

    def descricao(self) -> str:
        criancas = "com crianças" if self.tem_criancas else "sem crianças"
        return f"{super().descricao()}, {criancas}"

    def desconto(self, subtotal: Decimal) -> ItemOrcamento | None:
        """5% sobre o aluguel (base + adicionais) para quem não tem crianças."""
        if self.tem_criancas:
            return None
        valor = arredondar(subtotal * self.PERCENTUAL_DESCONTO_SEM_CRIANCAS)
        return ItemOrcamento("Desconto de 5% (sem crianças)", -valor)


class Casa(ImovelComQuartos):
    """Casa: base R$ 900 | 2 quartos +R$ 250 | garagem +R$ 300 | sem desconto.
    Toda a lógica já vem de ImovelComQuartos; aqui só mudam os valores."""

    CATEGORIA = "Casa"
    ALUGUEL_BASE = Decimal("900.00")
    ADICIONAL_DOIS_QUARTOS = Decimal("250.00")


class Estudio(Imovel):
    """Estúdio: base R$ 1.200 | pacote de 2 vagas R$ 250 | vaga extra R$ 60."""

    CATEGORIA = "Estúdio"
    ALUGUEL_BASE = Decimal("1200.00")
    VAGAS_PACOTE_INICIAL = 2
    VALOR_PACOTE_INICIAL = Decimal("250.00")
    VALOR_VAGA_ADICIONAL = Decimal("60.00")

    def __init__(self, vagas: int):
        if vagas < 0:
            raise ValueError("A quantidade de vagas não pode ser negativa.")
        self.vagas = vagas

    def descricao(self) -> str:
        return f"Estúdio com {self.vagas} vaga(s) de estacionamento"

    def adicionais(self) -> list[ItemOrcamento]:
        itens = []
        if self.vagas >= 1:                                   # 1 ou 2 vagas = pacote
            itens.append(ItemOrcamento(
                f"Pacote de estacionamento ({self.VAGAS_PACOTE_INICIAL} vagas)",
                self.VALOR_PACOTE_INICIAL))
        extras = self.vagas - self.VAGAS_PACOTE_INICIAL       # da 3ª vaga em diante
        if extras > 0:
            itens.append(ItemOrcamento(
                f"{extras} vaga(s) extra(s) x {formatar_moeda(self.VALOR_VAGA_ADICIONAL)}",
                self.VALOR_VAGA_ADICIONAL * extras))
        return itens


# =====================================================================
# PARTE 3 - ORÇAMENTO
# Recebe um imóvel (de qualquer tipo) e calcula: aluguel mensal,
# parcelas da taxa contratual e projeção dos 12 meses.
# =====================================================================

@dataclass(frozen=True)
class LinhaProjecao:
    """Um mês da projeção de pagamentos."""
    mes: int
    aluguel: Decimal
    parcela_taxa: Decimal
    total_mes: Decimal
    total_acumulado: Decimal


class Orcamento:
    TAXA_CONTRATUAL = Decimal("2000.00")
    MAX_PARCELAS = 5
    MESES_PROJECAO = 12

    def __init__(self, imovel: Imovel, parcelas_taxa: int):
        if not 1 <= parcelas_taxa <= self.MAX_PARCELAS:
            raise ValueError(f"A taxa pode ser parcelada em 1 a {self.MAX_PARCELAS} vezes.")
        self.imovel = imovel
        self.parcelas_taxa = parcelas_taxa

    # ---- 3.1 Aluguel mensal -------------------------------------------
    @property
    def adicionais(self) -> list[ItemOrcamento]:
        return self.imovel.adicionais()          # polimorfismo: cada imóvel sabe os seus

    @property
    def subtotal(self) -> Decimal:
        """Aluguel-base + adicionais (antes do desconto)."""
        return self.imovel.ALUGUEL_BASE + sum((i.valor for i in self.adicionais), Decimal("0"))

    @property
    def desconto(self) -> ItemOrcamento | None:
        return self.imovel.desconto(self.subtotal)

    @property
    def aluguel_mensal(self) -> Decimal:
        desconto = self.desconto.valor if self.desconto else Decimal("0")
        return arredondar(self.subtotal + desconto)

    # ---- 3.2 Taxa contratual (separada do aluguel) --------------------
    @property
    def valores_parcelas(self) -> list[Decimal]:
        """Divide a taxa em parcelas; a última absorve a diferença de centavos."""
        n = self.parcelas_taxa
        base = (self.TAXA_CONTRATUAL / n).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        parcelas = [base] * (n - 1)
        parcelas.append(self.TAXA_CONTRATUAL - base * (n - 1))
        return parcelas

    # ---- 3.3 Projeção dos 12 meses ------------------------------------
    def projecao(self) -> list[LinhaProjecao]:
        parcelas = self.valores_parcelas
        linhas, acumulado = [], Decimal("0")
        for mes in range(1, self.MESES_PROJECAO + 1):
            parcela = parcelas[mes - 1] if mes <= len(parcelas) else Decimal("0.00")
            total = self.aluguel_mensal + parcela
            acumulado += total
            linhas.append(LinhaProjecao(mes, self.aluguel_mensal, parcela, total, acumulado))
        return linhas

    # ---- 3.4 Resumo para mostrar na tela ------------------------------
    def resumo(self) -> str:
        m = formatar_moeda
        linhas = [
            "=" * 56,
            "        RENTSMART - ORÇAMENTO DE LOCAÇÃO (R.M Imóveis)",
            "=" * 56,
            f"Imóvel: {self.imovel.descricao()}",
            "",
            "ALUGUEL MENSAL",
            f"  {'Aluguel-base ' + self.imovel.CATEGORIA.lower():<40}{m(self.imovel.ALUGUEL_BASE):>14}",
        ]
        for item in self.adicionais:
            linhas.append(f"  {item.descricao:<40}{m(item.valor):>14}")
        if self.desconto:
            linhas.append(f"  {'Subtotal':<40}{m(self.subtotal):>14}")
            linhas.append(f"  {self.desconto.descricao:<40}{'- ' + m(-self.desconto.valor):>14}")
        linhas += [
            "  " + "-" * 54,
            f"  {'VALOR MENSAL DO ALUGUEL':<40}{m(self.aluguel_mensal):>14}",
            "",
            "TAXA CONTRATUAL (cobrada separadamente do aluguel)",
            f"  {'Valor total da taxa':<40}{m(self.TAXA_CONTRATUAL):>14}",
        ]
        parcelas = self.valores_parcelas
        if len(parcelas) == 1:
            linhas.append(f"  {'Pagamento':<40}{'à vista':>14}")
        else:
            linhas.append(f"  {'Parcelamento':<40}{str(len(parcelas)) + 'x de ' + m(parcelas[0]):>14}")
            if parcelas[-1] != parcelas[0]:
                linhas.append(f"  {'(última parcela ajustada para)':<40}{m(parcelas[-1]):>14}")
        linhas += [
            "",
            f"TOTAL PREVISTO NOS PRIMEIROS 12 MESES: {m(self.projecao()[-1].total_acumulado)}",
            "=" * 56,
        ]
        return "\n".join(linhas)


# =====================================================================
# PARTE 4 - EXPORTAÇÃO PARA CSV
# Grava a projeção dos 12 meses. Usa ';' como separador, vírgula decimal
# e UTF-8 com BOM, para abrir certinho no Excel em português.
# =====================================================================

class ExportadorCSV:
    CABECALHO = ["Mês", "Aluguel (R$)", "Parcela da taxa contratual (R$)",
                 "Total do mês (R$)", "Total acumulado (R$)"]

    def __init__(self, caminho: str = "projecao_12_meses.csv"):
        self.caminho = caminho

    def exportar(self, orcamento: Orcamento) -> str:
        with open(self.caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow(self.CABECALHO)
            for linha in orcamento.projecao():
                escritor.writerow([
                    linha.mes,
                    formatar_numero_csv(linha.aluguel),
                    formatar_numero_csv(linha.parcela_taxa),
                    formatar_numero_csv(linha.total_mes),
                    formatar_numero_csv(linha.total_acumulado),
                ])
        return self.caminho


# =====================================================================
# PARTE 5 - ENTRADA DE DADOS E VALIDAÇÃO
# Cada função repete a pergunta até o usuário responder algo válido.
# =====================================================================

def ler_opcao(pergunta: str, opcoes: dict[str, str]) -> str:
    """Mostra um menu e só aceita uma das chaves listadas."""
    while True:
        print(f"\n{pergunta}")
        for chave, texto in opcoes.items():
            print(f"  [{chave}] {texto}")
        escolha = input("Sua escolha: ").strip()
        if escolha in opcoes:
            return escolha
        print("Opção inválida. Tente novamente.")


def ler_inteiro(pergunta: str, minimo: int, maximo: int) -> int:
    """Lê um número inteiro dentro de um intervalo."""
    while True:
        texto = input(f"\n{pergunta} ({minimo} a {maximo}): ").strip()
        try:
            valor = int(texto)
        except ValueError:
            print("Digite apenas números inteiros.")
            continue
        if minimo <= valor <= maximo:
            return valor
        print(f"Valor fora do intervalo permitido ({minimo} a {maximo}).")


def ler_sim_nao(pergunta: str) -> bool:
    """Lê uma resposta s/n e devolve True ou False."""
    while True:
        texto = input(f"\n{pergunta} (s/n): ").strip().lower()
        if texto in ("s", "sim"):
            return True
        if texto in ("n", "nao", "não"):
            return False
        print("Responda com 's' ou 'n'.")


# =====================================================================
# PARTE 6 - PROGRAMA PRINCIPAL
# Fluxo: perguntar -> criar o imóvel -> criar o orçamento -> mostrar -> CSV
# =====================================================================

def montar_imovel() -> Imovel:
    """Pergunta as características e devolve o objeto de imóvel adequado."""
    categoria = ler_opcao("Qual categoria de imóvel o cliente deseja?", {
        "1": "Apartamento (base R$ 700,00)",
        "2": "Casa (base R$ 900,00)",
        "3": "Estúdio (base R$ 1.200,00)",
    })

    if categoria == "3":                                      # Estúdio
        vagas = ler_inteiro(
            "Quantas vagas de estacionamento? (0 = nenhuma; pacote de 2 vagas por "
            "R$ 250,00, vaga extra R$ 60,00)", 0, 10)
        return Estudio(vagas)

    quartos = ler_inteiro("Quantos quartos?", 1, 2)           # Casa ou Apartamento
    garagem = ler_sim_nao("Deseja vaga de garagem (+ R$ 300,00/mês)?")
    if categoria == "2":
        return Casa(quartos, garagem)
    tem_criancas = ler_sim_nao("O cliente possui crianças?")  # só apartamento
    return Apartamento(quartos, garagem, tem_criancas)


def main() -> None:
    print("Bem-vindo(a) ao RentSmart - R.M Imóveis")

    imovel = montar_imovel()                                  # 1) entradas do imóvel
    parcelas = ler_inteiro(                                   # 2) condição da taxa
        "Em quantas parcelas deseja pagar a taxa contratual de R$ 2.000,00?",
        1, Orcamento.MAX_PARCELAS)

    orcamento = Orcamento(imovel, parcelas)                   # 3) cálculo
    print("\n" + orcamento.resumo())                          # 4) resumo na tela

    caminho = ExportadorCSV().exportar(orcamento)             # 5) CSV de 12 meses
    print(f"\nProjeção dos 12 meses salva em: {caminho}")


if __name__ == "__main__":
    main()
