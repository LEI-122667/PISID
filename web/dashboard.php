<?php
session_start();
if (!isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}
$tipo = $_SESSION['tipo'];
$can_create = in_array($tipo, ['Admin', 'User']);
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Dashboard</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="nav-bar">
        <h3>PISID</h3>
        <div class="nav-links">
            <a href="dashboard.php">Dashboard</a>
            <a href="simulations.php">Simulações</a>
            <a href="leaderboard.php">Leaderboard</a>
            <a href="alterar_utilizador.php">Perfil</a>
            <?php if ($tipo === 'Admin'): ?>
                <a href="criar_utilizador.php">Criar Utilizador</a>
            <?php endif; ?>
            <?php if ($can_create): ?>
                <a href="criar_jogo.php">Criar Jogo</a>
            <?php endif; ?>
            <a href="logout.php">Sair</a>
        </div>
    </div>
    <div class="container">
        <div class="glass-panel">
            <h2>Bem-vindo, <?= htmlspecialchars($_SESSION['nome']) ?>!</h2>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">
                Tipo: <strong><?= htmlspecialchars($tipo) ?></strong> | 
                Equipa: <strong><?= htmlspecialchars($_SESSION['equipa'] ?? 'Sem equipa') ?></strong>
            </p>

            <div class="dashboard-grid">
                <?php if ($tipo === 'Admin'): ?>
                <div class="glass-panel" style="background: rgba(30,41,59,0.4)">
                    <h3>Gestão de Utilizadores</h3>
                    <p style="margin-bottom: 1rem; color: var(--text-secondary);">Crie novas contas para administradores, criadores ou leitores.</p>
                    <a href="criar_utilizador.php" class="btn">Criar Utilizador</a>
                </div>
                <?php endif; ?>

                <?php if ($can_create): ?>
                <div class="glass-panel" style="background: rgba(30,41,59,0.4)">
                    <h3>Gestão de Jogos</h3>
                    <p style="margin-bottom: 1rem; color: var(--text-secondary);">Inicie novas simulações e altere parâmetros.</p>
                    <a href="criar_jogo.php" class="btn">Criar Novo Jogo</a>
                </div>
                <?php endif; ?>

                <div class="glass-panel" style="background: rgba(30,41,59,0.4)">
                    <h3>As Suas Simulações</h3>
                    <p style="margin-bottom: 1rem; color: var(--text-secondary);">Visualize as simulações em que participa.</p>
                    <a href="simulations.php" class="btn btn-secondary">Ver Simulações</a>
                </div>

                <div class="glass-panel" style="background: rgba(30,41,59,0.4)">
                    <h3>Classificações</h3>
                    <p style="margin-bottom: 1rem; color: var(--text-secondary);">Veja as pontuações e estatísticas das equipas.</p>
                    <a href="leaderboard.php" class="btn btn-secondary">Leaderboard</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
