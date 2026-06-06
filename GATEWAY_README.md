# Gateway Serial ESP32-P4 ↔ EMR

Ponte bidirecional entre o separador físico (ESP32-P4) e o painel web (FastAPI).

## Pré-requisito

```bash
pip install -r requirements.txt   # inclui pyserial
```

---

## Uso normal — modo interativo

Basta executar sem argumentos:

```bash
python serial_gateway.py
```

O assistente guia a configuração em 3 passos:

```
╔══════════════════════════════════════════════════════╗
║   Gateway Serial  ESP32-P4  ↔  EMR  (configuração)  ║
╚══════════════════════════════════════════════════════╝

Backend EMR
────────────────────────────────────────────────────────
  URL do servidor [http://127.0.0.1:8765]:
  Utilizador [teste]:
  Senha [123456]:

  Conectando ao backend EMR… OK

Separadores cadastrados no EMR
────────────────────────────────────────────────────────
  1. Alfa  (código: RB-ALFA)  [em execução]  OS: OS-001
  2. Beta  (código: RB-BETA)  [disponível]
  3. ESP32-P4-001  (código: ESP32-P4-001)  [disponível]
  Escolha o separador [1]: 3

Porta serial do ESP32
────────────────────────────────────────────────────────
  1. COM3       USB Serial Device (COM3)
  2. COM5       Silicon Labs CP210x USB to UART Bridge (COM5)
  Escolha a porta [1]: 2

  Baud rate [115200]:

  Salvar configuração para próxima vez? (s/n) [s]:
  Configuração salva em gateway_config.json

────────────────────────────────────────────────────────
  Separador : ESP32-P4-001 (ESP32-P4-001)
  Porta     : COM5 @ 115200 baud
  Backend   : http://127.0.0.1:8765
────────────────────────────────────────────────────────
```

Na segunda vez, os valores anteriores aparecem como padrão — basta pressionar Enter.

---

## Uso direto — linha de comando

Para iniciar sem o assistente:

```bash
python serial_gateway.py --port COM5 --robot-code ESP32-P4-001
```

Parâmetros completos:

| Argumento | Padrão | Descrição |
|-----------|--------|-----------|
| `--port` | (obrigatório no modo direto) | Porta serial (COM3, /dev/ttyUSB0…) |
| `--baud` | 115200 | Baud rate |
| `--url` | http://127.0.0.1:8765 | URL do backend EMR |
| `--user` | teste | Utilizador do EMR |
| `--password` | 123456 | Senha do EMR |
| `--robot-code` | (obrigatório no modo direto) | Código do separador no cadastro |
| `--list-ports` | — | Lista portas seriais e sai |
| `--list-robots` | — | Lista separadores do EMR e sai |
| `--debug` | — | Logs detalhados |

---

## Como registar o ESP32 no EMR

1. Abra o painel web (`http://127.0.0.1:8765`)
2. Vá em **Separadores → Cadastrar novo**
3. Preencha o campo **Código** com o valor de `BRIDGE_ROBOT_CODE` do firmware

```c
// main.c — altere se necessário
#define BRIDGE_ROBOT_CODE  "ESP32-P4-001"
```

4. Defina o **Status** inicial como `idle` (disponível)

---

## Sincronização bidirecional

| Origem | Evento | Destino |
|--------|--------|---------|
| ESP32 cria OS manual | `BRIDGE: os_start` | Web atualiza painel |
| ESP32 separa remédio | `BRIDGE: unit` | Web incrementa contador |
| ESP32 conclui OS | `BRIDGE: os_complete` | Web marca concluída |
| ESP32 cancela OS | `BRIDGE: os_cancel` | Web registra no histórico |
| **Web atribui OS** | `CMD: os_assign` | **ESP32 exibe na tela** |
| **Web conclui OS** | `CMD: os_complete` | **ESP32 volta ao estado idle** |
| **Web cancela OS** | `CMD: os_cancel` | **ESP32 registra no histórico** |

---

## Solução de problemas

| Sintoma | Solução |
|---------|---------|
| "Nenhuma porta serial detectada" | Conecte o ESP32 via USB |
| "Nenhum separador cadastrado" | Cadastre no painel web antes de iniciar |
| "Robô não encontrado" | O código no firmware deve ser igual ao cadastrado no EMR |
| "Não foi possível conectar" | Inicie o servidor: `python run_dev.py` |
| Eventos não chegam | Confirme que compilou o firmware após as últimas alterações |
