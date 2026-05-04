<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: index.php');
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

if (!$simulacao) {
    die("Simulação não encontrada.");
}

$user_id = $_SESSION['user_id'];
$user_tipo = $_SESSION['tipo'];
$user_equipa = $_SESSION['equipa'];

// Access control: Admins see everything. Users only see their team.
if ($user_tipo !== 'Admin' && $simulacao['Equipa'] != $user_equipa) {
    die("Acesso negado. Esta simulação não pertence à sua equipa.");
}

// Ownership check: 
// 1. Admins can always edit.
// 2. Creator (IDUtilizador) can edit.
// 3. For legacy records where IDUtilizador is NULL, anyone from the same team can edit.
$is_owner = ($user_tipo === 'Admin') || 
            ($simulacao['IDUtilizador'] == $user_id) || 
            ($simulacao['IDUtilizador'] === null && $simulacao['Equipa'] == $user_equipa);

$readonly = !$is_owner;

if ($simulacao['Ativo'] && !$readonly) {
    // If it's active, we usually don't want to edit score/description while it's running
    // But if the user wants to be able to, we could. For now, let's keep the active check
    // but maybe just warn instead of die? The user said "cant access criar_jogo until its done"
    // which implies they have to wait.
    die("Não é possível alterar uma simulação ativa.");
}

if (!$readonly && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $descricao = $_POST['descricao'];
    $pontuacao = (int)$_POST['pontuacao'];

    try {
        // If it was NULL, we might want to take ownership or just leave it NULL.
        // Let's leave it NULL or set it if the user is the one editing.
        $stmt = $pdo->prepare("UPDATE Simulacao SET Descricao = ?, Pontuacao = ? WHERE IDSimulacao = ?");
        $stmt->execute([$descricao, $pontuacao, $id_simulacao]);

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
    <title>Ver / Alterar Jogo</title>
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
            <h2>
                <?= $readonly ? 'Ver' : 'Alterar' ?> Jogo #<?= htmlspecialchars($id_simulacao) ?>
                <?php if ($readonly): ?>
                    <span style="font-size: 0.75rem; color: var(--text-secondary); margin-left: 1rem;">(apenas leitura — não és o criador)</span>
                <?php endif; ?>
            </h2>

            <?php if (isset($error)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <?php if (isset($success)): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
            <?php endif; ?>

            <form method="POST">
                <div class="form-group">
                    <label>Descrição</label>
                    <input type="text" name="descricao" value="<?= htmlspecialchars($simulacao['Descricao']) ?>"
                        <?= $readonly ? 'disabled' : 'required' ?>>
                </div>
                <div class="form-group">
                    <label>Pontuação</label>
                    <input type="number" name="pontuacao" value="<?= htmlspecialchars($simulacao['Pontuacao']) ?>"
                        <?= $readonly ? 'disabled' : 'required' ?>>
                </div>
                <div class="form-group">
                    <label>Equipa</label>
                    <input type="text" value="<?= htmlspecialchars($simulacao['Equipa']) ?>" disabled>
                </div>
                <div class="form-group">
                    <label>Data de Início</label>
                    <input type="text" value="<?= htmlspecialchars($simulacao['DataHoraInicio']) ?>" disabled>
                </div>

                <?php if (!$readonly): ?>
                    <button type="submit" class="btn">Atualizar Jogo</button>
                <?php else: ?>
                    <a href="simulations.php" class="btn btn-secondary">Voltar às Simulações</a>
                <?php endif; ?>
            </form>
        </div>
    </div>
</body>
</html>
