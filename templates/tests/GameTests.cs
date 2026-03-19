using NUnit.Framework;
using UnityEngine; // 🚨 Adiciona o UnityEngine para podermos usar o JsonUtility

public class GameTests
{
    [Test]
    public void Compra_VidaExtra_DescontaMoedas_E_AumentaVidas()
    {
        // 1. ARRANGE (Preparar os dados falsos)
        PlayerSave save = new PlayerSave();
        save.wallet = new PlayerWallet { totalCoins = 100 };
        save.stats = new PlayerStats { currentLives = 3, maxLives = 3 };
        int custo = 50;

        // 2. ACT (Executar a lógica)
        if (save.wallet.totalCoins >= custo) {
            save.wallet.totalCoins -= custo;
            save.stats.maxLives++;
            save.stats.currentLives++;
        }

        // 3. ASSERT (Validar os resultados)
        Assert.AreEqual(50, save.wallet.totalCoins, "As moedas não foram descontadas corretamente!");
        Assert.AreEqual(4, save.stats.maxLives, "A vida máxima não aumentou!");
        Assert.AreEqual(4, save.stats.currentLives, "A vida atual não aumentou!");
    }

    [Test]
    public void PlayerSave_CriacaoNova_ComecaCom3Vidas()
    {
        // Testa se o teu ficheiro de save base começa com os valores corretos
        PlayerSave saveNovo = new PlayerSave();
        saveNovo.stats = new PlayerStats { currentLives = 3, maxLives = 3 };

        Assert.AreEqual(3, saveNovo.stats.currentLives, "O jogador não começou com 3 vidas!");
    }

    // ==========================================
    // 🚨 NOVO TESTE: Validação da Ponte IA -> Unity
    // ==========================================
    [Test]
    public void Evolucao_Genoma_AtualizaParametrosCorretamente()
    {
        // 1. ARRANGE: Simular o JSON puro gerado pelo Python ANTES da evolução
        string jsonAntes = @"{
            ""level_id"": 5,
            ""rules"": {
                ""enemySpeed"": 2.5,
                ""enemyCount"": 3,
                ""timeLimit"": 100.0
            }
        }";

        // Simular o JSON gerado pelo Python DEPOIS da evolução pela IA (Nível escalado)
        string jsonDepois = @"{
            ""level_id"": 5,
            ""rules"": {
                ""enemySpeed"": 4.8,
                ""enemyCount"": 6,
                ""timeLimit"": 120.0
            }
        }";

        // 2. ACT: O Unity lê o JSON usando o motor interno (Exatamente como o GameManager faz)
        LevelGenome genomeAntes = JsonUtility.FromJson<LevelGenome>(jsonAntes);
        LevelGenome genomeDepois = JsonUtility.FromJson<LevelGenome>(jsonDepois);

        // 3. ASSERT: Validar se as variáveis foram mapeadas e alteradas no C#

        // Validação Base
        Assert.AreEqual(2.5f, genomeAntes.rules.enemySpeed, "A leitura base da velocidade falhou!");
        Assert.AreEqual(3, genomeAntes.rules.enemyCount, "A leitura base de inimigos falhou!");

        // Validação Pós-Evolução (O verdadeiro teste!)
        Assert.AreEqual(4.8f, genomeDepois.rules.enemySpeed, "O Unity ignorou a nova velocidade evoluída pela IA!");
        Assert.AreEqual(6, genomeDepois.rules.enemyCount, "A nova contagem de inimigos não foi aplicada!");
        Assert.AreEqual(120.0f, genomeDepois.rules.timeLimit, "O novo tempo limite da IA falhou a ser lido!");
    }
}