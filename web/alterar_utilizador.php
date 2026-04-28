<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id'])) {
    header('Location: index.php');
    exit;
}

$user_id = $_SESSION['user_id'];

// Get current data
$stmt = $pdo->prepare("SELECT * FROM Utilizador WHERE IDUtilizador = ?");
$stmt->execute([$user_id]);
$user = $stmt->fetch();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nome = $_POST['nome'];
    $telemovel = $_POST['telemovel'];
    $email = $_POST['email'];
    $dataNasc = $_POST['data_nascimento'] ?: null;

    try {
        $stmt = $pdo->prepare("UPDATE Utilizador SET Nome = ?, Telemovel = ?, Email = ?, DataNascimento = ? WHERE IDUtilizador = ?");
        $stmt->execute([$nome, $telemovel, $email, $dataNasc, $user_id]);
        
        $_SESSION['nome'] = $nome;
        $_SESSION['email'] = $email;
        $success = "Perfil atualizado com sucesso!";
        
        // Refresh data
        $stmt = $pdo->prepare("SELECT * FROM Utilizador WHERE IDUtilizador = ?");
        $stmt->execute([$user_id]);
        $user = $stmt->fetch();
        
    } catch (\PDOException $e) {
        $error = "Erro: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Alterar Perfil</title>
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
        <div class="glass-panel" style="max-width: 600px; margin: 0 auto;">
            <h2>Alterar Perfil</h2>
            
            <?php if (isset($error)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <?php if (isset($success)): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
            <?php endif; ?>

            <form method="POST">
                <div class="form-group">
                    <label>Nome</label>
                    <input type="text" name="nome" value="<?= htmlspecialchars($user['Nome']) ?>" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" value="<?= htmlspecialchars($user['Email']) ?>" required>
                </div>
                <div class="form-group">
                    <label>Telemóvel</label>
                    <input type="text" name="telemovel" value="<?= htmlspecialchars($user['Telemovel'] ?? '') ?>">
                </div>
                <div class="form-group">
                    <label>Data de Nascimento</label>
                    <input type="date" name="data_nascimento" value="<?= htmlspecialchars($user['DataNascimento'] ?? '') ?>">
                </div>
                <button type="submit" class="btn">Atualizar Perfil</button>
            </form>
        </div>
    </div>
</body>
</html>
