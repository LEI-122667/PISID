<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id']) || $_SESSION['tipo'] !== 'Criador') {
    header('Location: dashboard.php');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $descricao = $_POST['descricao'];
    $equipa = $_POST['equipa'];
    $ac = isset($_POST['ar_condicionado']) ? 1 : 0;

    // Params for script
    $out_temp = $_POST['outliers_temp'];
    $out_som = $_POST['outliers_som'];
    $al_temp_h = $_POST['alerta_temp_h'];
    $al_temp_l = $_POST['alerta_temp_l'];
    $al_som = $_POST['alerta_som'];

    $amt_gatilhos = $_POST['amt_gatilhos'];

    if ($_POST['fechar_por'] === 'tempo') {
        $t_fechar = $_POST['fechar_valor'];
        $r_limite = 0;
    } else {
        $t_fechar = 0;
        $r_limite = $_POST['fechar_valor'];
    }

    try {
        // 1. Criar o jogo na BD Local
        $pdo->beginTransaction();

        // Call the SP (which internally checks for active simulations)
        $stmt = $pdo->prepare("CALL Criar_Jogo(?, ?, CURRENT_TIMESTAMP, 0, ?)");
        $stmt->execute([$descricao, $equipa, $ac]);

        $id_sim = $pdo->lastInsertId();

        $pdo->commit();

        // 2. Iniciar a simulação no Windows em background (now we know it is safe)
        $cmdMazerun = "start /B mazerun.exe 2 --flagMessage 1 --delay 1 --broker broker.hivemq.com --portbroker 1883";
        pclose(popen($cmdMazerun, "r"));

        // 3. Esperar 1 segundo para a simulação inserir tabelas na Nuvem
        sleep(1);

        // 4. Execute python script para sincronizar Nuvem -> DB Local e Mongo
        $cmd = escapeshellcmd("python ../scripts/nuvemToDBs/htmlNuvemToDatabases.py " .
            escapeshellarg($id_sim) . " " .
            escapeshellarg($out_temp) . " " .
            escapeshellarg($out_som) . " " .
            escapeshellarg($al_temp_h) . " " .
            escapeshellarg($al_temp_l) . " " .
            escapeshellarg($al_som) . " " .
            escapeshellarg($t_fechar) . " " .
            escapeshellarg($r_limite) . " " .
            escapeshellarg($amt_gatilhos));

        $output = shell_exec($cmd) ?? '(sem output)';

        $success = "Jogo criado com sucesso! Sincronização: " . htmlspecialchars($output);

    } catch (Exception $e) {
        if ($pdo->inTransaction()) {
            $pdo->rollBack();
        }
        $error = "Erro: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="pt">

<head>
    <meta charset="UTF-8">
    <title>Criar Jogo</title>
    <link rel="stylesheet" href="css/style.css">
</head>

<body>
    <div class="nav-bar">
        <h3>PISID</h3>
        <div class="nav-links">
            <a href="dashboard.php">Voltar</a>
        </div>
    </div>
    <div class="container">
        <div class="glass-panel" style="max-width: 800px; margin: 0 auto;">
            <h2>Criar Novo Jogo</h2>

            <?php if (isset($error)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <?php if (isset($success)): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
            <?php endif; ?>

            <form method="POST">
                <div class="dashboard-grid" style="margin-top: 0;">
                    <div>
                        <h3>Dados da Simulação</h3>
                        <div class="form-group">
                            <label>Descrição</label>
                            <input type="text" name="descricao" required>
                        </div>
                        <div class="form-group">
                            <label>Equipa</label>
                            <input type="number" name="equipa" required>
                        </div>
                        <div class="form-group">
                            <label>
                                <input type="checkbox" name="ar_condicionado"
                                    style="width: auto; display: inline-block;">
                                Ar Condicionado Ligado
                            </label>
                        </div>
                    </div>

                    <div>
                        <h3>Configuração do Jogo</h3>
                        <div class="form-group">
                            <label>Outliers Temperatura</label>
                            <input type="number" step="0.01" name="outliers_temp" required value="2.0">
                        </div>
                        <div class="form-group">
                            <label>Outliers Som</label>
                            <input type="number" step="0.01" name="outliers_som" required value="2.0">
                        </div>
                        <div class="form-group">
                            <label>Alerta Temp. High (graus abaixo do limite)</label>
                            <input type="number" name="alerta_temp_h" required value="5">
                        </div>
                        <div class="form-group">
                            <label>Alerta Temp. Low (graus acima do limite)</label>
                            <input type="number" name="alerta_temp_l" required value="5">
                        </div>
                        <div class="form-group">
                            <label>Alerta Som (unidades abaixo do limite)</label>
                            <input type="number" name="alerta_som" required value="5">
                        </div>
                        <div class="form-group">
                            <label>Fechar Corredores Por:</label>
                            <select name="fechar_por" id="fechar_por" required style="margin-bottom: 10px;">
                                <option value="tempo">Tempo (segundos)</option>
                                <option value="ruido">Ruído Limite (%)</option>
                            </select>
                            <input type="number" step="1" name="fechar_valor" id="fechar_valor" required value="10"
                                placeholder="Valor em segundos (ex: 10)">
                        </div>
                        <div class="form-group">
                            <label>Quantidade de Gatilhos (Movimento)</label>
                            <input type="number" name="amt_gatilhos" required value="3">
                        </div>
                    </div>
                </div>
                <button type="submit" class="btn" style="margin-top: 2rem;">Criar Jogo e Sincronizar</button>
            </form>
        </div>
    </div>
    <script>
        document.getElementById('fechar_por').addEventListener('change', function () {
            var input = document.getElementById('fechar_valor');
            if (this.value === 'tempo') {
                input.step = "1";
                input.value = "10";
                input.placeholder = "Valor em segundos (ex: 10)";
            } else {
                input.step = "0.01";
                input.value = "0.8";
                input.placeholder = "Valor em % (ex: 0.8)";
            }
        });
    </script>
</body>

</html>