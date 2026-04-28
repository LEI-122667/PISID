<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}

// Call Ler_Leaderboard SP
$stmt = $pdo->query("CALL Ler_Leaderboard()");
$leaderboard = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Leaderboard</title>
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
            <h2>Leaderboard Global</h2>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">As melhores pontuações e estatísticas de todas as simulações terminadas.</p>
            
            <?php if (count($leaderboard) === 0): ?>
                <p>Nenhuma simulação terminada encontrada.</p>
            <?php else: ?>
                <table>
                    <thead>
                        <tr>
                            <th>Posição</th>
                            <th>Equipa</th>
                            <th>Simulação ID</th>
                            <th>Pontuação</th>
                            <th>Data/Hora Início</th>
                            <th>Total Alertas</th>
                            <th>Corredores Fechados</th>
                            <th>Média Temp.</th>
                            <th>Média Som</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php $pos = 1; foreach ($leaderboard as $row): ?>
                        <tr>
                            <td><strong><?= $pos++ ?>º</strong></td>
                            <td>Equipa <?= htmlspecialchars($row['Equipa']) ?></td>
                            <td><?= htmlspecialchars($row['IDSimulacao']) ?></td>
                            <td><strong style="color: var(--success-color);"><?= htmlspecialchars($row['Pontuacao']) ?></strong></td>
                            <td><?= htmlspecialchars($row['DataHoraInicio']) ?></td>
                            <td><?= htmlspecialchars($row['TotalAlertas']) ?></td>
                            <td><?= htmlspecialchars($row['TotalCorredoresFechados']) ?></td>
                            <td><?= htmlspecialchars($row['MediaTemperatura'] ?? 'N/A') ?> ºC</td>
                            <td><?= htmlspecialchars($row['MediaSom'] ?? 'N/A') ?> dB</td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>
