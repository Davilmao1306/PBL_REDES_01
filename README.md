# IoT Forno - relatorio tecnico

Este projeto simula uma solucao de Internet das Coisas para desacoplar sensores,
atuadores e aplicacoes cliente. A comunicacao foi implementada diretamente com
sockets TCP/UDP da arquitetura da Internet, sem MQTT, AMQP, Kafka, RabbitMQ ou
outro framework de troca de mensagens.

## Informacoes para avaliacao

### Pacotes e bibliotecas

O projeto foi implementado em Python 3.11.

Bibliotecas usadas:

- `socket`: comunicacao TCP e UDP;
- `threading`: concorrencia no broker;
- `time`: temporizacao e timeout;
- `random`: geracao de valores simulados dos sensores;
- `os`: leitura de variaveis de ambiente;
- `subprocess`, `pathlib`, `sys`: usados apenas nos testes.

Nao ha dependencias externas obrigatorias. Por isso o arquivo `requirements.txt`
esta vazio e a aplicacao funciona apenas com a biblioteca padrao do Python.

### Estrutura de diretorios

```text
iot_forno/
|-- actuators/
|   |-- atuador_aquecedor.py
|   `-- atuador_exaustor.py
|-- broker/
|   `-- broker.py
|-- client/
|   `-- client.py
|-- sensors/
|   |-- sensor_fumaca.py
|   `-- sensor_temp.py
|-- shared/
|   `-- protocol.py
|-- tests/
|   `-- integration_test.py
|-- .dockerignore
|-- docker-compose.yml
|-- Dockerfile
|-- README.md
`-- requirements.txt
```

Resumo dos diretorios:

- `broker/`: servico de integracao;
- `sensors/`: sensores virtuais;
- `actuators/`: atuadores virtuais;
- `client/`: interface de terminal;
- `shared/`: funcoes do protocolo;
- `tests/`: testes automatizados.

### Como executar

1. Abrir o projeto:

```bash
git clone https://github.com/Davilmao1306/PBL_REDES_01.git
cd PBL_REDES_01
```

2. Construir as imagens Docker:

```bash
docker compose build
```

3. Subir broker, sensores e atuadores:

```bash
docker compose up broker sensor_temp sensor_fumaca atuador_aquecedor atuador_exaustor
```

4. Em outro terminal, abrir o cliente:

```bash
docker compose run --rm client
```

Para encerrar:

```bash
docker compose down
```

### Como usar

No cliente, as opcoes disponiveis sao:

- `1`: listar sensores;
- `2`: listar atuadores;
- `3`: consultar um sensor;
- `4`: consultar um atuador;
- `5`: enviar comando para atuador;
- `6`: monitorar sensor em tempo real;
- `0`: encerrar o cliente.

IDs padrao:

- Sensores: `sensor_temp`, `sensor_fumaca`;
- Atuadores: `atuador_aquecedor`, `atuador_exaustor`.

Comandos aceitos:

- `atuador_aquecedor`: `ON`, `OFF`, `DESLIGAR`;
- `atuador_exaustor`: `ON`, `OFF`, `ACIONAR_ALARME`.

### Dockerfile

O `Dockerfile` foi preparado para facilitar a avaliacao dos tutores.

Ele contem:

- imagem base `python:3.11-slim`;
- definicao de `WORKDIR /app`;
- configuracoes de ambiente `PYTHONUNBUFFERED=1` e
  `PYTHONDONTWRITEBYTECODE=1`;
- copia do codigo-fonte para dentro do conteiner;
- instalacao de bibliotecas com `pip install -r requirements.txt`;
- etapa de validacao/compilacao com `python -m compileall ...`;
- comando padrao `python -m broker.broker`.

## 1. Arquitetura

O sistema foi dividido em quatro grupos de componentes:

- `broker/`: servico de integracao. Mantem em memoria o ultimo estado conhecido
  dos sensores e atuadores, recebe telemetria e encaminha comandos.
- `sensors/`: dispositivos virtuais que geram dados continuos. Foram criados
  `sensor_temp` e `sensor_fumaca`.
- `actuators/`: dispositivos virtuais que recebem comandos remotos. Foram
  criados `atuador_aquecedor` e `atuador_exaustor`.
- `client/`: aplicacao de terminal usada para listar dispositivos, consultar
  estado, acompanhar sensores em tempo real e enviar comandos.
- `shared/`: funcoes do protocolo textual comum entre os componentes.

O problema de alto acoplamento e resolvido pelo broker. Sensores e atuadores nao
conhecem as aplicacoes consumidoras; eles conhecem apenas o broker. A aplicacao
cliente tambem conhece apenas o broker. Assim, se no futuro existir um painel,
um banco de dados e um alarme, o sensor nao precisara manter tres conexoes
diretas: ele envia a telemetria para o servico de integracao, e o broker passa a
ser o ponto de distribuicao e controle.

## 2. Comunicacao

A implementacao usa a biblioteca padrao `socket` do Python.

- Telemetria: usa UDP na porta `5001`. O sensor envia datagramas para o broker.
  Esse caminho prioriza velocidade e baixa sobrecarga. Como as leituras sao
  continuas, uma perda eventual e aceitavel.
- Controle e consultas: usam TCP na porta `5002`. Cliente, sensores e atuadores
  usam TCP para registro, consulta e comandos criticos. TCP foi escolhido para
  comandos porque oferece entrega ordenada e confiavel dentro da conexao.

Essa separacao evita que o grande volume de telemetria bloqueie comandos de
controle. O broker possui um servidor UDP para dados continuos e um servidor TCP
para controle.

## 3. Protocolo (API remota)

As mensagens sao texto UTF-8. Os campos sao separados por `|`. No TCP, cada
mensagem termina com `\n` para delimitar o fim do quadro. Isso e necessario
porque TCP e fluxo de bytes, nao entrega mensagens prontas.

Formato geral em TCP:

```text
CAMPO_0|CAMPO_1|CAMPO_2\n
```

Formato geral em UDP:

```text
CAMPO_0|CAMPO_1|CAMPO_2
```

Limites usados na implementacao:

- `recv_tcp_message`: ate 4096 bytes por mensagem TCP.
- `udp_sock.recvfrom(1024)`: ate 1024 bytes por datagrama de telemetria.

Mensagens de registro:

```text
REGISTER_SENSOR|sensor_temp|temperatura
REGISTERED|sensor_temp

REGISTER_ACTUATOR|atuador_aquecedor|aquecedor
REGISTERED|atuador_aquecedor
```

Mensagem de telemetria via UDP:

```text
SENSOR_DATA|sensor_temp|temperatura|35.2
```

Consultas do cliente:

```text
LIST_SENSORS
SENSORS|sensor_temp,temperatura,35.2,ONLINE;sensor_fumaca,fumaca,7.4,ONLINE

LIST_ACTUATORS
ACTUATORS|atuador_aquecedor,aquecedor,OFF,ONLINE

GET_SENSOR|sensor_temp
SENSOR|sensor_temp|temperatura|35.2|ONLINE

GET_ACTUATOR|atuador_aquecedor
ACTUATOR|atuador_aquecedor|aquecedor|OFF|ONLINE
```

Comandos de controle:

```text
COMMAND|atuador_aquecedor|ON
EXECUTE|ON
OK|ON
COMMAND_OK|atuador_aquecedor|ON
```

Fluxo de controle:

1. Sensores se registram por TCP e depois enviam telemetria por UDP.
2. Atuadores se registram por TCP e mantem a conexao aberta para receber
   comandos.
3. O cliente abre conexao TCP com o broker, envia uma requisicao e recebe uma
   resposta.
4. Para comandos, o broker envia `EXECUTE` ao atuador, espera `OK` e so entao
   responde `COMMAND_OK` ao cliente.

## 4. Encapsulamento e tratamento de dados

Os dados sao encapsulados como strings UTF-8 em mensagens delimitadas por `|`.
No recebimento, a funcao `parse_message` divide a mensagem em campos. Cada
handler valida a quantidade de campos e o tipo de comando antes de executar a
acao.

Exemplos de validacao:

- `SENSOR_DATA` so e aceito com 4 campos.
- `REGISTER_SENSOR` e `REGISTER_ACTUATOR` so sao aceitos com 3 campos.
- `COMMAND` so e aceito com 3 campos.
- Comandos invalidos retornam `ERROR|comando_invalido` ou
  `ERROR|comando_nao_suportado`.
- Atuadores ou sensores inexistentes retornam `ERROR|atuador_nao_encontrado` ou
  `ERROR|sensor_nao_encontrado`.

## 5. Concorrencia

O broker usa `threading`. Ao iniciar, ele cria uma thread para o servidor UDP e
outra para o servidor TCP. Cada nova conexao TCP aceita tambem recebe uma thread
propria.

As estruturas compartilhadas `sensors` e `actuators` ficam protegidas por
`threading.Lock`, evitando conflito quando varias threads atualizam ou consultam
estado ao mesmo tempo. Cada atuador tambem possui um lock proprio para impedir
que dois comandos simultaneos sejam enviados pela mesma conexao TCP de forma
intercalada.

Essa abordagem permite receber multiplos sensores e multiplos clientes
simultaneamente sem usar filas de mensagens externas ou frameworks proibidos
pelo enunciado.

## 6. Qualidade de servico

O tratamento de perfis de trafego foi separado por protocolo:

- Telemetria continua: UDP, sem confirmacao por mensagem. Isso reduz overhead e
  evita que o sensor fique preso aguardando ACK para leituras que logo serao
  substituidas por novas amostras.
- Comandos criticos: TCP, com confirmacao de aplicacao. O broker so retorna
  `COMMAND_OK` quando o atuador responde `OK`.

O broker guarda apenas o ultimo valor de cada sensor em memoria. Essa decisao
evita crescimento ilimitado de historico quando chegam muitas leituras por
segundo. O objetivo e representar o estado atual do dispositivo para consulta em
tempo real.

## 7. Interacao

A aplicacao cliente e uma interface de terminal. Ela permite:

- listar sensores;
- listar atuadores;
- consultar um sensor especifico;
- consultar um atuador especifico;
- enviar comandos para atuadores;
- monitorar um sensor em tempo real pela opcao `6`.

Os dispositivos simulados tambem expoem seu comportamento pelo terminal. Os
sensores imprimem a telemetria enviada, e os atuadores imprimem comandos
recebidos e mudancas de estado.

## 8. Confiabilidade basica

O sistema trata falhas com excecoes e timeouts basicos:

- O cliente usa timeout de 5 segundos ao conectar no broker.
- Sensores usam timeout de 5 segundos ao registrar no broker.
- O broker usa timeout de 5 segundos ao esperar resposta de comando de um
  atuador.
- Se o comando para um atuador falha, o broker marca o atuador como `OFFLINE` e
  retorna `ERROR|atuador_offline` para o cliente.
- Se um sensor para de enviar telemetria, o broker compara `last_update` com o
  tempo atual. Depois de 3 segundos sem nova leitura, o sensor passa a aparecer
  como `OFFLINE` nas consultas.

Como UDP nao mantem conexao, o broker nao "desconecta" sensores ativamente; ele
detecta ausencia de novas leituras pelo tempo desde a ultima telemetria.

## 9. Testes

Foi criado o teste `tests/integration_test.py`. Ele executa o broker localmente,
simula um atuador, registra um sensor, envia telemetria via UDP, consulta o
sensor via TCP e envia um comando critico para o atuador.

Para executar:

```bash
python -B tests/integration_test.py
```

Tambem foram usados estes comandos de verificacao:

```bash
python -B -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8'), filename=str(p)) for p in pathlib.Path('.').rglob('*.py')]; print('syntax ok')"
docker compose config
```

Para teste manual em carga simples, e possivel subir mais de uma instancia de
sensor no Docker alterando o nome do servico/conteiner ou executando novos
containers com `BROKER_HOST` apontando para o broker.

## 10. Emulacao com Docker

Todos os componentes rodam em conteineres Docker a partir do mesmo `Dockerfile`.
O `docker-compose.yml` cria uma rede bridge chamada `iot_net`, na qual os
servicos se comunicam pelo nome DNS do Compose, por exemplo `broker`.

Suba broker, sensores e atuadores:

```bash
docker compose up --build broker sensor_temp sensor_fumaca atuador_aquecedor atuador_exaustor
```

Em outro terminal, abra o cliente:

```bash
docker compose run --rm client
```

IDs disponiveis na configuracao padrao:

- Sensores: `sensor_temp`, `sensor_fumaca`.
- Atuadores: `atuador_aquecedor`, `atuador_exaustor`.

Comandos aceitos:

- `atuador_aquecedor`: `ON`, `OFF`, `DESLIGAR`.
- `atuador_exaustor`: `ON`, `OFF`, `ACIONAR_ALARME`.

Em uma unica maquina do laboratorio, a conectividade e resolvida pela rede
bridge do Docker Compose. Em maquinas distintas, o broker deve publicar as
portas `5001/udp` e `5002/tcp`, e os outros conteineres devem ser iniciados com
`BROKER_HOST` apontando para o IP da maquina onde o broker esta executando.
Exemplo:

```bash
docker compose run --rm -e BROKER_HOST=192.168.1.10 client
```

## Roteiro de apresentacao

1. Mostrar o `docker-compose.yml` e explicar que cada componente roda em um
   conteiner separado.
2. Subir broker, sensores e atuadores.
3. Abrir o cliente e listar sensores/atuadores.
4. Monitorar `sensor_temp` ou `sensor_fumaca` em tempo real.
5. Enviar `ON` e `OFF` para `atuador_aquecedor`.
6. Enviar `ACIONAR_ALARME` para `atuador_exaustor`.
7. Parar um sensor e mostrar que ele passa a ficar `OFFLINE` apos o timeout.
8. Explicar que o broker substitui a comunicacao ponto-a-ponto por uma
   arquitetura centralizada usando apenas TCP e UDP nativos.
