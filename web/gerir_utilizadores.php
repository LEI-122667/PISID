<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id']) || $_SESSION['tipo'] !== 'Admin') {
    header('Location: dashboard.php');
    exit;
}

$stmt = $pdo->query("SELECT * FROM Utilizador ORDER BY Nome ASC");
$users = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="pt">

<head>
    <meta charset="UTF-8">
    <title>Gerir Utilizadores</title>
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
            <h2>Gestão de Utilizadores</h2>
            <?php if (isset($_GET['success'])): ?>
                <div class="alert alert-success"><?= htmlspecialchars($_GET['success']) ?></div>
            <?php endif; ?>
            <?php if (isset($_GET['error'])): ?>
                <div class="alert alert-error"><?= htmlspecialchars($_GET['error']) ?></div>
            <?php endif; ?>

            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Tipo</th>
                        <th>Equipa</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($users as $u): ?>
                        <tr>
                            <td><?= htmlspecialchars($u['Nome']) ?></td>
                            <td><?= htmlspecialchars($u['Email']) ?></td>
                            <td><?= htmlspecialchars($u['Tipo']) ?></td>
                            <td><?= htmlspecialchars($u['Equipa'] ?? 'N/A') ?></td>
                            <td style="display: flex; gap: 0.5rem;">
                                <a href="alterar_utilizador.php?id=<?= $u['IDUtilizador'] ?>" class="btn"
                                    style="padding: 0.5rem; font-size: 0.8rem;">Alterar</a>
                                <?php if ($u['IDUtilizador'] != $_SESSION['user_id']): ?>
                                    <a href="remover_utilizador.php?id=<?= $u['IDUtilizador'] ?>" class="btn btn-secondary"
                                        style="padding: 0.5rem; font-size: 0.8rem; background: #ff4757;"
                                        onclick="return confirm('Tem a certeza que deseja remover este utilizador?')">Remover</a>
                                <?php endif; ?>
                            </td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    </div>
</body>

</html>