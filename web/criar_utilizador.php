<?php
session_start();
require_once 'db.php';

if (!isset($_SESSION['user_id']) || $_SESSION['tipo'] !== 'Admin') {
    header('Location: dashboard.php');
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nome = $_POST['nome'];
    $telemovel = $_POST['telemovel'];
    $tipo = $_POST['tipo'];
    $email = $_POST['email'];
    $dataNasc = $_POST['data_nascimento'] ?: null;
    $equipa = $_POST['equipa'] ?: null;

    try {
        $stmt = $pdo->prepare('CALL Criar_Utilizador(?, ?, ?, ?, ?, ?)');
        $stmt->execute([$nome, $telemovel, $tipo, $email, $dataNasc, $equipa]);
        $success = "Utilizador criado com sucesso!";
    } catch (\PDOException $e) {
        $error = "Erro: " . $e->getMessage();
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Criar Utilizador</title>
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
            <h2>Criar Novo Utilizador</h2>
            
            <?php if (isset($error)): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>
            <?php if (isset($success)): ?>
                <div class="alert alert-success"><?= htmlspecialchars($success) ?></div>
            <?php endif; ?>

            <form method="POST">
                <div class="form-group">
                    <label>Nome</label>
                    <input type="text" name="nome" required>
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>Telemóvel</label>
                    <input type="text" name="telemovel">
                </div>
                <div class="form-group">
                    <label>Tipo</label>
                    <select name="tipo" required>
                        <option value="Leitor">Leitor</option>
                        <option value="Criador">Criador</option>
                        <option value="Admin">Admin</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Data de Nascimento</label>
                    <input type="date" name="data_nascimento">
                </div>
                <div class="form-group">
                    <label>Equipa (Opcional, ID da Simulação)</label>
                    <input type="number" name="equipa">
                </div>
                <button type="submit" class="btn">Criar Utilizador</button>
            </form>
        </div>
    </div>
</body>
</html>
