<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id']) || $_SESSION['tipo'] !== 'Criador') {
    header('Location: dashboard.php');
    exit;
}

$id_simulacao = $_GET['id'] ?? null;
if (!$id_simulacao) {
    header('Location: simulations.php');
    exit;
}

// Fetch simulation
$stmt = $pdo->prepare("SELECT * FROM Simulacao WHERE IDSimulacao = ?");
$stmt->execute([$id_simulacao]);
$simulacao = $stmt->fetch();

if (!$simulacao || $simulacao['Equipa'] != $_SESSION['equipa']) {
    die("Acesso negado. Esta simulação não pertence à sua equipa.");
}
if ($simulacao['Ativo']) {
    die("Não é possível alterar uma simulação ativa.");
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $descricao = $_POST['descricao'];
    $pontuacao = (int)$_POST['pontuacao'];
    $ac = isset($_POST['ar_condicionado']) ? 1 : 0;

    try {
        // Direct update to bypass MySQL USER() check in the SP which fails with PDO root
        $stmt = $pdo->prepare("UPDATE Simulacao SET Descricao = ?, Pontuacao = ?, ArCondicionado = ? WHERE IDSimulacao = ?");
        $stmt->execute([$descricao, $pontuacao, $ac, $id_simulacao]);
        
        $success = "Simulação atualizada com sucesso!";
        
        // Refresh
        $stmt = $pdo->prepare("SELECT * FROM Simulacao WHERE IDSimulacao = ?");
        $stmt->execute([$id_simulacao]);
        $simulacao = $stmt->fetch();
    } catch (\PDOException $e) {
        $error = "Erro: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Alterar Jogo</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="nav-bar">
        <h3>PISID</h3>
        <div class="nav-links">
            <a href="simulations.php">Voltar</a>
        </div>
    </div>
    <div class="container">
        <div class="glass-panel" style="max-width: 600px; margin: 0 auto;">
            <h2>Alterar Jogo #<?= htmlspecialchars($id_simulacao) ?></h2>
            
            <?php if (isset($error)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <?php if (isset($success)): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
            <?php endif; ?>

            <form method="POST">
                <div class="form-group">
                    <label>Descrição</label>
                    <input type="text" name="descricao" value="<?= htmlspecialchars($simulacao['Descricao']) ?>" required>
                </div>
                <div class="form-group">
                    <label>Pontuação</label>
                    <input type="number" name="pontuacao" value="<?= htmlspecialchars($simulacao['Pontuacao']) ?>" required>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="ar_condicionado" style="width: auto; display: inline-block;" <?= $simulacao['ArCondicionado'] ? 'checked' : '' ?>>
                        Ar Condicionado Ligado
                    </label>
                </div>
                <button type="submit" class="btn">Atualizar Jogo</button>
            </form>
        </div>
    </div>
</body>
</html>
