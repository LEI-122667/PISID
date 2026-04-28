<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}

$equipa_user = $_SESSION['equipa'];
$tipo = $_SESSION['tipo'];

// Build query
$sql = "SELECT * FROM Simulacao";
$params = [];

if ($tipo !== 'Admin') {
    $sql .= " WHERE Equipa = ?";
    $params[] = $equipa_user;
}

$sql .= " ORDER BY DataHoraInicio DESC";
$stmt = $pdo->prepare($sql);
$stmt->execute($params);
$simulacoes = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Simulações</title>
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
        <div class="glass-panel">
            <h2>As Suas Simulações</h2>
            
            <?php if (count($simulacoes) === 0): ?>
                <p>Não há simulações para apresentar.</p>
            <?php else: ?>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Descrição</th>
                            <th>Equipa</th>
                            <th>Data de Início</th>
                            <th>Pontuação</th>
                            <th>Ar Cond.</th>
                            <th>Estado</th>
                            <th>Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($simulacoes as $s): ?>
                        <tr>
                            <td><?= htmlspecialchars($s['IDSimulacao']) ?></td>
                            <td><?= htmlspecialchars($s['Descricao']) ?></td>
                            <td><?= htmlspecialchars($s['Equipa']) ?></td>
                            <td><?= htmlspecialchars($s['DataHoraInicio']) ?></td>
                            <td><?= htmlspecialchars($s['Pontuacao']) ?></td>
                            <td><?= $s['ArCondicionado'] ? 'Ligado' : 'Desligado' ?></td>
                            <td>
                                <?php if ($s['Ativo']): ?>
                                    <span style="color: var(--success-color)">Ativo</span>
                                <?php else: ?>
                                    <span style="color: var(--text-secondary)">Terminado</span>
                                <?php endif; ?>
                            </td>
                            <td>
                                <?php if ($tipo === 'Criador' && $s['Equipa'] == $equipa_user && $s['Ativo'] == 0): ?>
                                    <!-- Apenas para simulações não ativas, de acordo com o SP -->
                                    <a href="alterar_jogo.php?id=<?= $s['IDSimulacao'] ?>" class="btn" style="padding: 0.5rem; font-size: 0.8rem;">Alterar</a>
                                <?php endif; ?>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>
