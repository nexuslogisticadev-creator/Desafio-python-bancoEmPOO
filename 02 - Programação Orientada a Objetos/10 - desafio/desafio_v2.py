import textwrap
from abc import ABC, abstractclassmethod, abstractproperty
from datetime import datetime
from colorama import Fore, Style
import logging

# Configurações do logger para escrever em um arquivo .txt
logging.basicConfig(
    filename="log.txt",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
)


class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(cls, conta):
        pass


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self, conta)


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)
        if sucesso_transacao:
            conta.historico.adicionar_transacao(self, conta)


class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao, conta):
        data_hora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        tipo_transacao = transacao.__class__.__name__
        valor_transacao = transacao.valor
        numero_conta = conta.numero

        # Verificar se a transação já foi adicionada anteriormente
        for t in self._transacoes:
            if (
                t["conta"] == numero_conta
                and t["tipo"] == tipo_transacao
                and t["valor"] == valor_transacao
            ):
                return

        # Registro da transação no arquivo .txt
        with open("log.txt", "a") as file:
            file.write(
                f"Conta: {numero_conta} | Tipo: {tipo_transacao} | "
                f"Valor: R$ {valor_transacao:.2f} | ({data_hora})\n"
            )

        registro_transacao = (
            f"{Fore.CYAN}Conta: {numero_conta} | Tipo: {tipo_transacao} | "
            f"Valor: R$ {valor_transacao:.2f} | ({data_hora})"
            f"{Style.RESET_ALL}"
        )
        self._transacoes.append(
            {
                "conta": numero_conta,
                "tipo": tipo_transacao,
                "valor": valor_transacao,
                "data": data_hora,
                "registro": registro_transacao,
            }
        )


class Cliente:
    def __init__(self, endereco):
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        transacao.registrar(conta)
        conta.historico.adicionar_transacao(transacao, conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)


class PessoaFisica(Cliente):
    def __init__(self, nome, data_nascimento, cpf, endereco):
        super().__init__(endereco)
        self.nome = nome
        self.cpf = cpf

        while True:
            try:
                data_nascimento_dt = datetime.strptime(data_nascimento, "%d-%m-%Y")
                data_atual = datetime.now()
                if data_nascimento_dt > data_atual:
                    raise ValueError(
                        "❌ Data de nascimento não pode ser maior que a data atual. ❌"
                    )
                else:
                    self.data_nascimento = data_nascimento
                    break
            except ValueError as e:
                print(e)
                data_nascimento = input(
                    "Informe uma nova data de nascimento (dd-mm-aaaa): "
                )

    def __repr__(self):
        return f"PessoaFisica(nome={self.nome}, cpf={self.cpf}, data_nascimento={self.data_nascimento}, endereco={self.endereco})"


class Conta:
    def __init__(self, numero, cliente):
        self._saldo = 0
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._historico = Historico()

    @classmethod
    def nova_conta(cls, cliente, numero):
        return cls(numero, cliente)

    @property
    def saldo(self):
        return self._saldo

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    @property
    def historico(self):
        return self._historico

    def sacar(self, valor):
        saldo = self.saldo
        excedeu_saldo = valor > saldo

        if excedeu_saldo:
            print(
                Fore.RED
                + "\n❌❌❌ Operação falhou! Você não tem saldo suficiente. ❌❌❌"
            )
            print(Style.RESET_ALL)  # Resetando a cor
            return False

        elif valor <= 0:
            print(
                Fore.RED
                + "\n❌❌❌ Operação falhou! O valor informado é inválido. ❌❌❌"
            )
            print(Style.RESET_ALL)  # Resetando a cor
            return False

        self._saldo -= valor
        print(
            Fore.GREEN
            + f"\n✅✅✅ Saque realizado com sucesso! {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} ✅✅✅"
        )
        print(Style.RESET_ALL)  # Resetando a cor
        return True

    def depositar(self, valor):
        if valor <= 0:
            print(
                Fore.RED
                + "\n❌❌❌ Operação falhou! O valor informado é inválido. ❌❌❌"
            )
            print(Style.RESET_ALL)  # Resetando a cor
            return False

        self._saldo += valor
        print(
            Fore.GREEN
            + f"\n✅✅✅ Depósito realizado com sucesso! {datetime.now().strftime('%d-%m-%Y %H:%M:%S')} ✅✅✅"
        )
        print(Style.RESET_ALL)  # Resetando a cor
        return True


class ContaCorrente(Conta):
    def __init__(self, numero, cliente, limite=500, limite_saques=3):
        super().__init__(numero, cliente)
        self._limite = limite
        self._limite_saques = limite_saques

    def sacar(self, valor):
        numero_saques = sum(
            1
            for transacao in self.historico.transacoes
            if transacao["tipo"] == Saque.__name__
        )
        excedeu_limite = valor > self._limite
        excedeu_saques = numero_saques >= self._limite_saques

        if excedeu_limite:
            print(
                Fore.RED
                + "\n❌❌❌ Operação falhou! O valor do saque excede o limite. ❌❌❌"
            )
            print(Style.RESET_ALL)  # Resetando a cor
            return False

        elif excedeu_saques:
            print(
                Fore.RED
                + "\n❌❌❌ Operação falhou! Número máximo de saques excedido. ❌❌❌"
            )
            print(Style.RESET_ALL)  # Resetando a cor
            return False

        return super().sacar(valor)

    def __str__(self):
        return f"""{Fore.WHITE}
    ========== CONTA CORRENTE ==========
            Agência:\t{self.agencia}
            C/C:\t{self.numero}
            Titular:\t{self.cliente.nome}
    {Style.RESET_ALL}"""


def menu():
    menu_text = f"""{Fore.CYAN + Style.BRIGHT}
    ================ MENU ================
    [d]💰\tDepositar
    [s]💸\tSacar
    [e]📊\tExtrato
    [nc]📋\tNova conta
    [nu]👤\tNovo usuário
    [lc]📄\tListar contas
    [q]🚪\tSair
    => {Style.RESET_ALL}"""
    return input(textwrap.dedent(menu_text))


def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print(Fore.YELLOW + "\n❗❗❗ Cliente não possui conta! ❗❗❗")
        print(Style.RESET_ALL)  # Resetando a cor
        return

    # FIXME: não permite cliente escolher a conta
    return cliente.contas[0]


def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print(Fore.RED + "\n❌❌❌ Cliente não encontrado! ❌❌❌")
        print(Style.RESET_ALL)  # Resetando a cor
        return

    valor = float(input("Informe o valor do depósito: "))
    transacao = Deposito(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


def sacar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print(Fore.RED + "\n❌❌❌ Cliente não encontrado! ❌❌❌")
        print(Style.RESET_ALL)  # Resetando a cor
        return

    valor = float(input("Informe o valor do saque: "))
    transacao = Saque(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


def exibir_extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print(Fore.RED + "\n❌❌❌ Cliente não encontrado! ❌❌❌")
        print(Style.RESET_ALL)  # Resetando a cor
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    print(Fore.CYAN + "\n================ EXTRATO ================")
    transacoes = conta.historico.transacoes

    extrato = ""
    if not transacoes:
        extrato = "Não foram realizadas movimentações."
    else:
        for transacao in transacoes:
            tipo_transacao = transacao["tipo"]
            texto_formatado = f"\n{tipo_transacao} ({transacao['data']}):\n\tR$ {transacao['valor']:.2f}\n"

            # Aplicar cor vermelha se for um saque
            if tipo_transacao == "Saque":
                texto_formatado = f"{Fore.RED}{texto_formatado}{Style.RESET_ALL}"
            # Aplicar cor amarela se for um depósito
            elif tipo_transacao == "Deposito":
                texto_formatado = f"{Fore.YELLOW}{texto_formatado}{Style.RESET_ALL}"

            extrato += texto_formatado

    print(extrato)
    print(f"\n{Fore.CYAN}Saldo:\n\tR$ {conta.saldo:.2f}{Style.RESET_ALL}")
    print(Fore.CYAN + "==========================================")


def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente números): ")
    cliente = filtrar_cliente(cpf, clientes)

    if cliente:
        print(Fore.YELLOW + "\n❗❗❗ Já existe cliente com esse CPF! ❗❗❗")
        print(Style.RESET_ALL)  # Resetando a cor
        return

    nome = input("Informe o nome completo: ")

    while True:
        data_nascimento = input("Informe a data de nascimento (dd/mm/aaaa): ")
        try:
            data_nascimento_dt = datetime.strptime(data_nascimento, "%d/%m/%Y")
            break
        except ValueError:
            print(
                Fore.RED
                + "\n❌❌❌ Formato de data inválido! Por favor, digite no formato dd/mm/aaaa. ❌❌❌"
            )
            print(Style.RESET_ALL)  # Resetando a cor

    endereco = input(
        "Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): "
    )

    # Convertendo a data de nascimento para o formato correto
    data_nascimento_formatada = data_nascimento_dt.strftime("%d-%m-%Y")

    cliente = PessoaFisica(
        nome=nome, data_nascimento=data_nascimento_formatada, cpf=cpf, endereco=endereco
    )

    clientes.append(cliente)

    # Registro da criação do novo cliente no arquivo .txt
    data_hora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    with open("log.txt", "a") as file:
        file.write(f"Cliente criado: {nome} | CPF: {cpf} | ({data_hora})\n")

    print(Fore.GREEN + f"\n✅✅✅ Cliente criado com sucesso! {data_hora} ✅✅✅")
    print(Style.RESET_ALL)  # Resetando a cor


def criar_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print(
            Fore.RED
            + "\n❌❌❌ Cliente não encontrado, fluxo de criação de conta encerrado! ❌❌❌"
        )
        print(Style.RESET_ALL)  # Resetando a cor
        return

    conta = ContaCorrente.nova_conta(cliente=cliente, numero=numero_conta)
    contas.append(conta)
    cliente.contas.append(conta)

    # Registro da criação da nova conta no arquivo .txt
    data_hora = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    with open("log.txt", "a") as file:
        file.write(
            f"Nova conta criada para o cliente {cliente.nome} | Conta: {numero_conta} | ({data_hora})\n"
        )

    print(Fore.GREEN + f"\n✅✅✅ Conta criada com sucesso! {data_hora} ✅✅✅")
    print(Style.RESET_ALL)  # Resetando a cor


def listar_contas(contas):
    for conta in contas:
        print(Fore.CYAN + "=" * 100)
        print(Fore.YELLOW + str(conta) + Style.RESET_ALL)


def main():
    clientes = []
    contas = []

    while True:
        opcao = menu()

        if opcao == "d":
            depositar(clientes)

        elif opcao == "s":
            sacar(clientes)

        elif opcao == "e":
            exibir_extrato(clientes)

        elif opcao == "nu":
            criar_cliente(clientes)

        elif opcao == "nc":
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "q":
            break

        else:
            print(
                Fore.RED
                + "\n❌❌❌ Operação inválida, por favor selecione novamente a operação desejada. ❌❌❌"
            )
            print(Style.RESET_ALL)  # Resetando a cor


if __name__ == "__main__":
    main()