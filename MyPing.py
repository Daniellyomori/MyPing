#Universidade Estadual do Oeste do Parana - UNIOESTE
#Disciplina de Redes
#Academicos: Danielly Omori e Vinicius Bortolotto
#Este trabalho tem como objetivo implementar um cliente Ping, 
#que seja capaz de interagir com hospedeiros reais através do uso do protocolo IPV4.
#30/08/2021

import os
import select
from socket import *
import struct
import time

def checksum(cabecalho):

    soma = 0
    count_to = (len(cabecalho) / 2) * 2
    count = 0

    while count < count_to:
        this_val = cabecalho[count + 1] * 256 + cabecalho[count]
        soma = soma + this_val
        soma = soma & 0xffffffff
        count = count + 2

    if count_to < len(cabecalho):
        soma = soma + cabecalho[len(cabecalho) - 1]
        soma = soma & 0xffffffff

    soma = (soma >> 16) + (soma & 0xffff)
    soma = soma + (soma >> 16)

    resposta = ~soma
    resposta = resposta & 0xffff
    resposta = resposta >> 8 | (resposta << 8 & 0xff00)

    return resposta



def enviarPing(destino, socket_, ID,seq):
    # Cria o cabecalho para o calculo do checksum (Tipo dados, request ou reply, codigo, checksum, id, sequencia).
    # B -> char
    # H -> unsigned short
    # h -> short

    cabecalho_inicial = struct.pack("bbHHh", 8, 0, 0, ID, seq)
    pacotim = time.time() #string de dados

    dados = struct.pack("d", pacotim)

    # Concatena o cabecalho inicial e os dados para o calculo do checksum
    pacote_inicial = cabecalho_inicial + dados

    checksum_inicial = checksum(pacote_inicial)
    checksum_inicial = htons(checksum_inicial) #usado para ordenar os dados em little ou big endian, de acordo com o sistema


    cabecalho = struct.pack("bbHHh", 8, 0, checksum_inicial, ID, seq) #monta o cabecalho final
    pacote = cabecalho + dados

    print('Pacote final: {}'.format(pacote))

    socket_.sendto(pacote, (destino, 1))


def recebePing(destino, tempo, socket_, ID):
    tempoRestante = tempo

    while 1:
        tempoInicio = time.time()
        dados = select.select([socket_], [], [],
                              tempoRestante)  # Oq vai ser lido, oq vai ser escrito, exceções e tempo pra timeout

        tempo_select = time.time() - tempoInicio

        #Nao houve retorno
        if dados[0] == []:
            print("Tempo da Requisição esgotou.")
            print("\n")
            return -1

        tempoReposta = time.time()
        pacoteRecebido, endereco = socket_.recvfrom(1024)

        cabecalho = pacoteRecebido[20:]

        tipo, codigo, checksumm, ID_cabecalho, seq, dados = struct.unpack("bbHHhd", cabecalho)

        print('Os valores extraidos do cabecalho recebido foram -> Tipo: {} Codigo: {} Checksum: {} ID: {} Seq: {} Dados: {}'.format(tipo,
                                                                                                                  codigo,
                                                                                                                  checksumm,
                                                                                                                  ID_cabecalho,
                                                                                                                  seq,
                                                                                                                  dados))
        #Caso ocorra o erro de Destination Unreacheble
        if tipo == '3':
            if codigo == '0':
                print("Tipo 3 - Codigo 0 -> Rede inalcançável!")
                print("\n")
                return -1
            elif codigo == '1':
                print("Tipo 3 - Codigo 1 ->Host inalcançável!")
                print("\n")
                return -1

        # Calculo do checksum recebido
        cabecalho_recebido = struct.pack("bbHHh", tipo, codigo, 0, ID_cabecalho, seq)
        dados_recebido = struct.pack("d", dados)

        pacote_recebido = cabecalho_recebido + dados_recebido
        checksum_recebido = checksum(pacote_recebido)
        checksum_recebido = htons(checksum_recebido)

        if checksumm != checksum_recebido:
            print("Valor do campo checksum não correspondente!")
            print("\n")
            return -1

        # Verifica se o ID recebido é o mesmo que foi enviado
        if ID == ID_cabecalho:
            tamanhoDouble = struct.calcsize("d")
            tempoEnvio = struct.unpack("d", pacoteRecebido[28:28 + tamanhoDouble])[0]
            rtt = tempoReposta - tempoEnvio

            #print("O valor do RTT é: {}".format(rtt))
            return rtt

        tempoRestante = tempoRestante - tempo_select

        if tempoRestante <= 0:
            print("Tempo da Requisição esgotou.")
            return -1


def pingando(destino, tempo,n):
    # Cria socket
    Socket = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP)
    id = os.getpid() & 0xFFFF  # PEGA OS 16 BITS MAIS BAIXOS DO PID ATUAL

    enviarPing(destino, Socket, id,n+1)
    resposta = recebePing(destino, tempo, Socket, id)
    Socket.close()
    return resposta


def ping(host, timeout, n):
    try:
        destino = gethostbyname(host)
    except gaierror:
        print('Host inválido!')
        print("\n")
        return 0

    print("Ping no destino: {}".format(host))

    count = 0
    veveto = []

    while count < n:
        tempo = pingando(destino, timeout,count)
        if tempo != -1:
            veveto.append(tempo)
            print('Tempo: {:.3f}ms'.format(tempo*1000))
            print('\n')
        count = count + 1
        time.sleep(1)

    percentual = ((n - len(veveto)) / n) * 100

    if len(veveto):
        media = (sum(veveto)) / (len(veveto))
        print('Número de pacotes recebidos: {}'.format(len(veveto)))
        print('Número de pacotes perdidos: {}'.format(n-len(veveto)))
        print('{:.2f}% dos pacotes foram perdidos'.format(percentual))
        print('Maior RTT: {:.3f}ms'.format(max(veveto)*1000))
        print('Menor RTT: {:.3f}ms'.format(min(veveto)*1000))
        print('Média RTT: {:.3f}ms'.format((media)*1000))
        print('\n')

    else:
        print('Número de pacotes recebidos: {}'.format(len(veveto)))
        print('Número de pacotes perdidos: {}'.format(n - len(veveto)))
        print('{:.2f}% dos pacotes foram perdidos'.format(percentual))
        print('Maior RTT: Indefinido')
        print('Menor RTT: Indefinido')
        print('Média RTT: Indefinido')
        print('\n')

    return tempo

tempo = 1

host = input('Digite um host para realizar o ping: ')

while host.upper() != 'SAIR':
    while True:
        try:
            vezes = int(input('Digite a quantidade de pings a serem realizados: '))
            if vezes > 0:
                break
            else:
                print(('Número inválido. Digite novamente!'))
        except:
            print(('Número inválido. Digite novamente!'))

    host = str(host)

    ping(host, tempo, vezes)

    host = input('Digite um host para realizar o ping: ')
