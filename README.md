# 🌌 Aurora — A Bruxa Entre Mundos ❄️

![Aurora](https://pbs.twimg.com/media/GWJKHU_asAAZA78?format=jpg&name=small)

> “Entre os ventos gelados de Freljord e o murmúrio dos espíritos,  
> eu observo... e celebro as almas que brilham sob a luz da aurora.”  
> — *Aurora, a Bruxa Entre Mundos*

---

## ✨ Sobre o projeto

**Aurora** é um bot do Discord inspirado na nova campeã **Aurora** de *League of Legends*.  
Ela é uma viajante entre o reino dos mortais e dos espíritos — e no Discord, assume o papel de **celebrar aniversários** dos membros do servidor de forma mágica e personalizada.

Criado para o servidor **Tripulação**, o bot envia mensagens temáticas tanto no chat quanto por DM, usando frases baseadas em sua **lore original**.

---

## ⚙️ Funcionalidades

- 🎂 **Mensagens automáticas de aniversário**
  - Aurora verifica todos os dias quem faz aniversário e envia uma mensagem inspirada em sua história.
  - Se ninguém faz aniversário, ela fica em silêncio — como o vento nas planícies de Freljord.

- 💬 **Mensagens personalizadas**
  - Cinco variações aleatórias baseadas na lore, diferentes para canal e DMs.

- 🧙‍♀️ **Comandos slash**
  | Comando | Descrição |
  |----------|------------|
  | `/cadastrar [dd/mm]` | Cadastra sua data de aniversário |
  | `/editar [dd/mm]` | Edita sua data de aniversário |
  | `/aniversarios` | Mostra todos os aniversários cadastrados |
  | `/setchannel [#canal]` | Define o canal para mensagens (admin) |
  | `/sync` | Sincroniza os comandos (admin) |
  | `/help` | Mostra todos os comandos |
  | `/sobre` | Exibe a lore completa da Aurora |

---

## 🧭 Instalação e execução

### 1️⃣ Clone o repositório
```bash
git clone https://github.com/frtvi/AuroraBot
cd AuroraBot
```

### 2️⃣ Instale as dependências
```bash
pip install -U discord tzdata
```

### 3️⃣ Configure o token
Abra o arquivo `aurorabot.py` e insira seu token:
```python
TOKEN = "SEU_TOKEN_DO_BOT_AQUI"
```

> ⚠️ Nunca publique seu token no GitHub!  
> Se quiser, use um arquivo `.env` para armazenar com segurança.

### 4️⃣ Execute o bot
```bash
python aurorabot.py
```

Aurora aparecerá **online** e pronta para celebrar sob o céu da aurora 🌌.

---

## 📜 Lore

> Desde que nasceu, Aurora vive com uma habilidade inigualável de viajar entre os reinos dos mortais e dos espíritos.  
> Determinada a aprender mais sobre os habitantes do reino espiritual, ela deixou seu lar para trás com o objetivo de conduzir mais pesquisas e acabou encontrando um semideus corrompido, perdido e deformado.  
> Testemunhando tamanho desespero, Aurora decidiu encontrar uma maneira de ajudar seu amigo selvagem a resgatar sua identidade perdida — uma jornada que a levaria até os cantos mais inóspitos de Freljord.

---

## 🛠️ Estrutura do projeto

```
AuroraBot/
├── aurorabot.py   # Código principal do bot
├── birthdays.db                   # Banco de dados SQLite (criado automaticamente)
└── README.md                      # Este arquivo
```

---

## ⚓ Créditos

- **Desenvolvido por:** Victor Barbosa 
- **Com carinho para o servidor da Tripulação**  
- **Inspirado em:** Aurora, de *League of Legends* (Riot Games)

---

> “Celebro cada alma que desperta entre mundos,  
> porque toda luz merece ser lembrada.”  
> — *Aurora, a Bruxa Entre Mundos*
